from django.test import TestCase
from django.urls import reverse

from core.models import Exercise, WorkoutLog, WorkoutPlan
from .factories import make_exercise, make_member, make_plan, make_trainer


class PermissionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.plank = make_exercise('Plank', 'core')  # unused, so PROTECT can't be what saves it
        cls.plan = make_plan(cls.trainer, exercises=[cls.bench])
        cls.member = make_member(plan=cls.plan)
        cls.other_member = make_member('other')

        cls.trainer_pages = [
            reverse('admin_dashboard'),
            reverse('manage_plans'),
            reverse('manage_users'),
            reverse('plan_create'),
            reverse('plan_edit', args=[cls.plan.id]),
            reverse('exercise_create'),
            reverse('exercise_edit', args=[cls.bench.id]),
        ]
        cls.trainer_post_only = [
            reverse('plan_delete', args=[cls.plan.id]),
            reverse('exercise_delete', args=[cls.plank.id]),
            reverse('assign_plan', args=[cls.other_member.id]),
        ]
        cls.member_pages = [
            reverse('user_dashboard'),
            reverse('workout_log'),
            reverse('my_progress'),
        ]

    # ---------- Not logged in ----------

    def test_anonymous_visitors_are_sent_to_login(self):
        for url in self.trainer_pages + self.trainer_post_only + self.member_pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                # ?next= remembers where they wanted to go, for after login
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    # ---------- Members trying trainer things ----------

    def test_members_cannot_open_trainer_pages(self):
        self.client.force_login(self.member)
        for url in self.trainer_pages:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), reverse('user_dashboard'))

    def test_members_cannot_delete_plans(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('plan_delete', args=[self.plan.id]))
        self.assertRedirects(response, reverse('user_dashboard'))
        self.assertTrue(WorkoutPlan.objects.filter(id=self.plan.id).exists())

    def test_members_cannot_delete_exercises(self):
        self.client.force_login(self.member)
        self.client.post(reverse('exercise_delete', args=[self.plank.id]))
        self.assertTrue(Exercise.objects.filter(id=self.plank.id).exists())

    def test_members_cannot_assign_plans(self):
        self.client.force_login(self.member)
        self.client.post(reverse('assign_plan', args=[self.other_member.id]), {'plan_id': self.plan.id})
        self.other_member.profile.refresh_from_db()
        self.assertIsNone(self.other_member.profile.assigned_plan)

    def test_members_cannot_create_plans_by_posting(self):
        self.client.force_login(self.member)
        self.client.post(reverse('plan_create'), {
            'name': 'Hacked Plan', 'description': 'x',
            f'use_{self.bench.id}': 'on', f'sets_{self.bench.id}': 3, f'reps_{self.bench.id}': 10,
        })
        self.assertEqual(WorkoutPlan.objects.count(), 1)

    # ---------- Trainers trying member things ----------

    def test_trainers_are_sent_away_from_member_pages(self):
        self.client.force_login(self.trainer)
        for url in self.member_pages:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), reverse('admin_dashboard'))

    def test_trainers_cannot_log_workouts(self):
        self.client.force_login(self.trainer)
        self.client.post(reverse('workout_log'), {
            'completed_on': '2026-10-01', 'exercise': self.bench.id,
            'sets_done': 3, 'reps_done': 10, 'weight_used': 60, 'notes': '',
        })
        self.assertFalse(WorkoutLog.objects.exists())