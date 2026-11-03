import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.management.commands.seed_demo import (
    MEMBER_PASSWORD, MEMBER_USERNAME, MIN_TRAINER_PASSWORD_LENGTH, PLAN_NAME,
    TRAINER_FALLBACK_PASSWORD, TRAINER_PASSWORD_ENV_VAR, TRAINER_USERNAME,
)
from core.models import Exercise, WorkoutLog, WorkoutPlan, get_assigned_plan
from .factories import PASSWORD, make_exercise, make_member

# A pretend "private" production password, used only inside these tests
SECRET_TRAINER_PASSWORD = 'Private-Trainer-Pass-42'


def run_seed(trainer_password=None):
    """
    Runs seed_demo and returns everything it printed.

    trainer_password=None -> the env var is REMOVED (local fallback path).
    Anything else         -> the env var is set to that value.

    patch.dict snapshots os.environ and restores it afterwards, so the
    result never depends on what's set in YOUR terminal, and no test
    leaks its env var into the next one.
    """
    out = StringIO()  # StringIO: keep the test output clean, and lets us read it
    with mock.patch.dict(os.environ):
        os.environ.pop(TRAINER_PASSWORD_ENV_VAR, None)
        if trainer_password is not None:
            os.environ[TRAINER_PASSWORD_ENV_VAR] = trainer_password
        call_command('seed_demo', stdout=out)
    return out.getvalue()


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
        run_seed()  # no env var -> trainer gets the local fallback
        for username, password in ((TRAINER_USERNAME, TRAINER_FALLBACK_PASSWORD),
                                   (MEMBER_USERNAME, MEMBER_PASSWORD)):
            with self.subTest(username=username):
                self.assertTrue(self.client.login(username=username, password=password))
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

    # ---------- trainer password (the security fix) ----------

    def test_trainer_uses_the_password_from_the_env_var(self):
        output = run_seed(SECRET_TRAINER_PASSWORD)
        trainer = User.objects.get(username=TRAINER_USERNAME)
        self.assertTrue(trainer.check_password(SECRET_TRAINER_PASSWORD))
        # Neither public password works for the trainer
        self.assertFalse(trainer.check_password(MEMBER_PASSWORD))
        self.assertFalse(trainer.check_password(TRAINER_FALLBACK_PASSWORD))
        # The member keeps the public README password
        member = User.objects.get(username=MEMBER_USERNAME)
        self.assertTrue(member.check_password(MEMBER_PASSWORD))
        # The private password is never printed, and there's no warning
        self.assertNotIn(SECRET_TRAINER_PASSWORD, output)
        self.assertNotIn('WARNING', output)

    def test_missing_env_var_prints_a_warning(self):
        output = run_seed()
        self.assertIn('WARNING', output)
        self.assertIn(TRAINER_PASSWORD_ENV_VAR, output)

    def test_rejects_unsafe_env_passwords_before_touching_the_database(self):
        unsafe = {
            'empty': '',
            'only spaces': '   ',
            'public member password': MEMBER_PASSWORD,
            'public fallback password': TRAINER_FALLBACK_PASSWORD,
            'too short': 'x' * (MIN_TRAINER_PASSWORD_LENGTH - 1),
        }
        for reason, bad_password in unsafe.items():
            with self.subTest(reason=reason):
                with self.assertRaises(CommandError):
                    run_seed(bad_password)
                self.assertFalse(User.objects.filter(username__startswith='demo_').exists())

    def test_reseeding_with_env_var_replaces_the_old_trainer_password(self):
        # Exactly what happens on production: old password out, new one in
        run_seed()
        run_seed(SECRET_TRAINER_PASSWORD)
        trainer = User.objects.get(username=TRAINER_USERNAME)
        self.assertFalse(trainer.check_password(TRAINER_FALLBACK_PASSWORD))
        self.assertTrue(trainer.check_password(SECRET_TRAINER_PASSWORD))