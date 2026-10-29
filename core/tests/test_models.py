from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from core.models import Exercise, PlanExercise, UserProfile, WorkoutLog, get_assigned_plan
from .factories import make_exercise, make_member, make_plan, make_trainer


class UserProfileTests(TestCase):

    def test_new_user_gets_a_profile_automatically(self):
        member = make_member()
        self.assertTrue(UserProfile.objects.filter(user=member).exists())
        self.assertIsNone(member.profile.assigned_plan)

    def test_get_assigned_plan_returns_the_members_plan(self):
        plan = make_plan(make_trainer())
        member = make_member(plan=plan)
        self.assertEqual(get_assigned_plan(member), plan)

    def test_get_assigned_plan_is_safe_without_a_profile(self):
        member = make_member()
        UserProfile.objects.filter(user=member).delete()
        # Fresh copy from the database. The old object still REMEMBERS its
        # profile in memory (Django caches it), which would fool this test.
        member = User.objects.get(pk=member.pk)
        self.assertIsNone(get_assigned_plan(member))


class PlanExerciseTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.bench = make_exercise()
        cls.plan = make_plan(make_trainer(), exercises=[cls.bench])

    def test_str_shows_plan_exercise_and_target(self):
        entry = self.plan.plan_exercises.get()
        self.assertEqual(str(entry), 'Beginner Plan: Bench Press (3x10)')

    def test_same_exercise_cannot_be_added_twice_to_one_plan(self):
        # The database itself refuses (UniqueConstraint), so we expect an IntegrityError.
        # transaction.atomic(): a failed query "breaks" the current transaction;
        # wrapping it keeps the rest of the test (and the cleanup) working.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlanExercise.objects.create(plan=self.plan, exercise=self.bench, sets=5, reps=5)

    def test_same_exercise_can_be_in_two_different_plans(self):
        make_plan(self.plan.created_by, name='Advanced Plan', exercises=[self.bench])
        self.assertEqual(self.bench.plan_entries.count(), 2)


class ExerciseDeleteProtectionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.squat = make_exercise('Squat', 'legs')

    def test_exercise_used_in_a_plan_cannot_be_deleted(self):
        make_plan(self.trainer, exercises=[self.bench])
        with self.assertRaises(ProtectedError):
            self.bench.delete()

    def test_exercise_with_workout_history_cannot_be_deleted(self):
        WorkoutLog.objects.create(user=make_member(), exercise=self.squat,
                                  sets_done=3, reps_done=8, weight_used=100)
        with self.assertRaises(ProtectedError):
            self.squat.delete()

    def test_unused_exercise_can_be_deleted(self):
        self.squat.delete()
        self.assertFalse(Exercise.objects.filter(name='Squat').exists())


class WorkoutPlanDeleteTests(TestCase):

    def test_deleting_a_plan_keeps_member_history(self):
        bench = make_exercise()
        plan = make_plan(make_trainer(), exercises=[bench])
        member = make_member(plan=plan)
        WorkoutLog.objects.create(user=member, exercise=bench, sets_done=3, reps_done=10, weight_used=60)

        plan.delete()

        member.profile.refresh_from_db()  # reload: the database changed behind our back
        self.assertIsNone(member.profile.assigned_plan)                  # SET_NULL worked
        self.assertEqual(WorkoutLog.objects.filter(user=member).count(), 1)  # history kept
        self.assertFalse(PlanExercise.objects.exists())                   # CASCADE cleaned up


class WorkoutLogModelTests(TestCase):

    def test_completed_on_defaults_to_today(self):
        log = WorkoutLog.objects.create(user=make_member(), exercise=make_exercise(),
                                        sets_done=3, reps_done=10, weight_used=50)
        self.assertEqual(log.completed_on, timezone.localdate())

    def test_str_shows_member_and_exercise(self):
        log = WorkoutLog.objects.create(user=make_member(), exercise=make_exercise(),
                                        sets_done=3, reps_done=10, weight_used=50)
        self.assertEqual(str(log), 'member - Bench Press')