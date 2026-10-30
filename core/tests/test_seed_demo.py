from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.management.commands.seed_demo import (
    DEMO_PASSWORD, MEMBER_USERNAME, PLAN_NAME, TRAINER_USERNAME,
)
from core.models import Exercise, WorkoutLog, WorkoutPlan, get_assigned_plan
from .factories import PASSWORD, make_exercise, make_member


def run_seed():
    call_command('seed_demo', stdout=StringIO())  # StringIO: keep the test output clean


class SeedDemoTests(TestCase):

    def test_creates_both_accounts_with_the_right_roles(self):
        run_seed()
        trainer = User.objects.get(username=TRAINER_USERNAME)
        member = User.objects.get(username=MEMBER_USERNAME)
        self.assertTrue(trainer.is_staff)
        self.assertFalse(trainer.is_superuser)
        self.assertFalse(member.is_staff)
        self.assertEqual(get_assigned_plan(member).name, PLAN_NAME)

    def test_demo_accounts_can_log_in(self):
        run_seed()
        for username in (TRAINER_USERNAME, MEMBER_USERNAME):
            with self.subTest(username=username):
                self.assertTrue(self.client.login(username=username, password=DEMO_PASSWORD))
                self.client.logout()

    def test_history_is_in_the_past_and_shows_on_progress_page(self):
        run_seed()
        member = User.objects.get(username=MEMBER_USERNAME)
        logs = WorkoutLog.objects.filter(user=member)
        self.assertEqual(logs.count(), 96)  # 8 weeks x 3 sessions x 4 exercises
        self.assertFalse(logs.filter(completed_on__gt=timezone.localdate()).exists())

        self.client.force_login(member)
        response = self.client.get(reverse('my_progress'))
        self.assertEqual(response.context['selected'].name, 'Deadlift')  # the default chart
        self.assertEqual(response.context['session_count'], 12)          # every workout B

    def test_running_twice_creates_no_duplicates(self):
        run_seed()
        run_seed()
        self.assertEqual(User.objects.filter(username__startswith='demo_').count(), 2)
        self.assertEqual(WorkoutPlan.objects.filter(name=PLAN_NAME).count(), 1)
        self.assertEqual(Exercise.objects.count(), 6)
        self.assertEqual(WorkoutPlan.objects.get(name=PLAN_NAME).plan_exercises.count(), 6)
        self.assertEqual(WorkoutLog.objects.count(), 96)

    def test_reuses_an_existing_library_exercise(self):
        make_exercise('bench press', 'chest')  # already in the library, different capitals
        run_seed()
        self.assertEqual(Exercise.objects.filter(name__iexact='bench press').count(), 1)

    def test_refuses_to_touch_a_real_account_with_a_demo_username(self):
        make_member(MEMBER_USERNAME)  # a real person registered this name first
        with self.assertRaises(CommandError):
            run_seed()
        # Their password is untouched...
        self.assertTrue(User.objects.get(username=MEMBER_USERNAME).check_password(PASSWORD))
        # ...and atomic() undid everything, even the trainer created a moment earlier
        self.assertFalse(User.objects.filter(username=TRAINER_USERNAME).exists())