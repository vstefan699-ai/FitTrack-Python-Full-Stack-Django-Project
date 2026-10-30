from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Exercise, WorkoutLog, WorkoutPlan
from .factories import PASSWORD, make_exercise, make_member, make_plan, make_trainer


def message_texts(response):
    """All flash messages ('Plan created!' etc.) that the view added."""
    return [str(m) for m in get_messages(response.wsgi_request)]


class LoginViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.member = make_member()

    def test_login_page_loads_with_a_form(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_member_login_goes_to_member_dashboard(self):
        response = self.client.post(reverse('login'), {'username': 'member', 'password': PASSWORD})
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_trainer_login_goes_to_trainer_dashboard(self):
        response = self.client.post(reverse('login'), {'username': 'trainer', 'password': PASSWORD})
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_wrong_password_shows_error_and_stays_logged_out(self):
        response = self.client.post(reverse('login'), {'username': 'member', 'password': 'wrong'})
        self.assertContains(response, 'Invalid username or password.')  # status 200 AND on the page
        self.assertNotIn('_auth_user_id', self.client.session)  # Django stores the logged-in id here
        # The username they typed is kept, so they only retype the password
        self.assertContains(response, 'value="member"')

    def test_missing_fields_show_errors_instead_of_crashing(self):
        # Before: request.POST['username'] -> KeyError -> 500 page
        response = self.client.post(reverse('login'), {})
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logged_in_member_visiting_login_is_redirected(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_logout_logs_the_user_out(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RegisterViewTests(TestCase):

    def register(self, **changes):
        data = {'username': 'newbie', 'email': 'newbie@example.com',
                'password1': 'Strong-pass-1', 'password2': 'Strong-pass-1'}
        data.update(changes)
        return self.client.post(reverse('register'), data)

    def assertNobodyCreated(self, response):
        # A failed sign-up shows the page again (200) and saves no user
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username__iexact='newbie').exists())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_register_creates_member_and_logs_them_in(self):
        response = self.register()
        self.assertRedirects(response, reverse('user_dashboard'))
        user = User.objects.get(username='newbie')
        self.assertFalse(user.is_staff)
        self.assertEqual(user.email, 'newbie@example.com')
        self.assertTrue(user.check_password('Strong-pass-1'))  # stored hashed, but it works
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertTrue(hasattr(user, 'profile'))  # the signal made a profile
        self.assertIn('Welcome to FitTrack Pro, newbie!', message_texts(response))

    def test_email_is_optional(self):
        response = self.register(email='')
        self.assertRedirects(response, reverse('user_dashboard'))
        self.assertEqual(User.objects.get(username='newbie').email, '')

    def test_invalid_email_is_rejected(self):
        response = self.register(email='not-an-email')
        self.assertNobodyCreated(response)
        self.assertIn('email', response.context['form'].errors)

    def test_mismatched_passwords_create_nobody(self):
        response = self.register(password2='Different-1')
        self.assertNobodyCreated(response)
        self.assertIn('password2', response.context['form'].errors)

    def test_weak_password_is_rejected(self):
        # Before: "1" was accepted. Now AUTH_PASSWORD_VALIDATORS run.
        response = self.register(password1='1', password2='1')
        self.assertNobodyCreated(response)
        self.assertIn('password2', response.context['form'].errors)  # Django puts it on password2

    def test_taken_username_is_rejected(self):
        make_member('newbie')
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username__iexact='newbie').count(), 1)
        self.assertIn('username', response.context['form'].errors)

    def test_taken_username_in_other_capitals_is_rejected(self):
        make_member('newbie')
        response = self.register(username='NewBie')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username__iexact='newbie').count(), 1)
        self.assertIn('That username is already taken.', response.context['form'].errors['username'])

    def test_blank_username_is_rejected(self):
        # Before: create_user('') crashed with a 500
        response = self.register(username='   ')
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 0)

    def test_missing_fields_show_errors_instead_of_crashing(self):
        # Before: request.POST['username'] -> KeyError -> 500 page
        response = self.client.post(reverse('register'), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        self.assertIn('username', response.context['form'].errors)

    def test_cannot_sign_up_as_a_trainer(self):
        # Sneaky extra fields in the POST must be ignored
        self.register(is_staff='on', is_superuser='on')
        user = User.objects.get(username='newbie')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_logged_in_member_visiting_register_is_redirected(self):
        self.client.force_login(make_member())
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('user_dashboard'))


class LandingViewTests(TestCase):

    def test_anonymous_visitor_sees_landing(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)

    def test_root_url_redirects_to_landing(self):
        response = self.client.get('/')
        self.assertRedirects(response, reverse('landing'))

    def test_logged_in_member_skips_landing(self):
        self.client.force_login(make_member())
        response = self.client.get(reverse('landing'))
        self.assertRedirects(response, reverse('user_dashboard'))


class DashboardViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.bench = make_exercise()
        cls.plan = make_plan(cls.trainer, exercises=[cls.bench])
        cls.member = make_member(plan=cls.plan)
        cls.no_plan_member = make_member('no_plan')
        WorkoutLog.objects.create(user=cls.member, exercise=cls.bench, sets_done=3, reps_done=10, weight_used=60)

    def test_trainer_dashboard_counts_members_and_logs(self):
        self.client.force_login(self.trainer)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.context['total_users'], 2)  # trainers are not counted
        self.assertEqual(response.context['total_logs'], 1)

    def test_manage_users_lists_members_only(self):
        self.client.force_login(self.trainer)
        users = list(self.client.get(reverse('manage_users')).context['users'])
        self.assertIn(self.member, users)
        self.assertNotIn(self.trainer, users)

    def test_member_dashboard_shows_their_plan(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.context['plan'], self.plan)
        self.assertEqual(len(response.context['plan_entries']), 1)
        self.assertEqual(response.context['total_logs'], 1)

    def test_member_without_plan_still_gets_a_page(self):
        self.client.force_login(self.no_plan_member)
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['plan'])


class WorkoutLogViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.squat = make_exercise('Squat', 'legs')  # NOT in the plan
        plan = make_plan(make_trainer(), exercises=[cls.bench])
        cls.member = make_member(plan=plan)
        cls.other_member = make_member('other', plan=plan)

    def setUp(self):
        self.client.force_login(self.member)

    def log_data(self, **changes):
        data = {'completed_on': timezone.localdate().isoformat(), 'exercise': self.bench.id,
                'sets_done': 3, 'reps_done': 10, 'weight_used': 60, 'notes': 'Felt strong'}
        data.update(changes)
        return data

    def test_page_loads(self):
        response = self.client.get(reverse('workout_log'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/workout_log.html')

    def test_log_this_link_preselects_the_exercise(self):
        response = self.client.get(reverse('workout_log'), {'exercise': self.bench.id})  # ?exercise=1
        self.assertEqual(response.context['form'].initial.get('exercise'), self.bench.id)

    def test_preselect_ignores_exercise_outside_the_plan(self):
        response = self.client.get(reverse('workout_log'), {'exercise': self.squat.id})
        self.assertIsNone(response.context['form'].initial.get('exercise'))

    def test_valid_post_saves_log_for_the_logged_in_member(self):
        response = self.client.post(reverse('workout_log'), self.log_data())
        self.assertRedirects(response, reverse('user_dashboard'))
        log = WorkoutLog.objects.get()
        self.assertEqual(log.user, self.member)
        self.assertEqual(log.weight_used, 60)

    def test_member_cannot_log_for_someone_else(self):
        # A sneaky extra "user" field in the POST must be ignored
        self.client.post(reverse('workout_log'), self.log_data(user=self.other_member.id))
        self.assertEqual(WorkoutLog.objects.get().user, self.member)

    def test_invalid_post_shows_form_again_and_saves_nothing(self):
        response = self.client.post(reverse('workout_log'), self.log_data(exercise=self.squat.id))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WorkoutLog.objects.exists())
        self.assertIn('exercise', response.context['form'].errors)


class MyProgressViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.squat = make_exercise('Squat', 'legs')
        plan = make_plan(make_trainer(), exercises=[cls.bench, cls.squat])
        cls.member = make_member(plan=plan)
        other = make_member('other', plan=plan)
        today = timezone.localdate()

        def log(user, weight, days_ago):
            return WorkoutLog.objects.create(user=user, exercise=cls.bench, sets_done=3, reps_done=10,
                                             weight_used=weight, completed_on=today - timedelta(days=days_ago))

        log(cls.member, 60, days_ago=2)
        log(cls.member, 65, days_ago=1)
        log(cls.member, 70, days_ago=1)  # same day, heavier: this is the one the chart uses
        cls.other_log = log(other, 100, days_ago=1)

    def setUp(self):
        self.client.force_login(self.member)

    def test_chart_uses_heaviest_weight_per_day(self):
        response = self.client.get(reverse('my_progress'))
        chart = response.context['chart_data']
        self.assertEqual(chart['exercise'], 'Bench Press')
        self.assertEqual(chart['weights'], [60, 70])
        self.assertEqual(response.context['session_count'], 2)
        self.assertEqual(response.context['best_weight'], 70)
        self.assertEqual(response.context['weight_change'], 10)

    def test_only_own_logs_are_shown(self):
        logs = self.client.get(reverse('my_progress')).context['logs']
        self.assertEqual(len(logs), 3)
        self.assertNotIn(self.other_log, logs)

    def test_unlogged_exercise_in_url_falls_back_to_latest(self):
        response = self.client.get(reverse('my_progress'), {'exercise': self.squat.id})
        self.assertEqual(response.context['selected'], self.bench)

    def test_member_with_no_logs_gets_an_empty_page(self):
        self.client.force_login(make_member('newbie'))
        response = self.client.get(reverse('my_progress'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['chart_data'])


class TrainerPlanViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.plan = make_plan(cls.trainer, exercises=[cls.bench])
        cls.member = make_member(plan=cls.plan)
        WorkoutLog.objects.create(user=cls.member, exercise=cls.bench, sets_done=3, reps_done=10, weight_used=60)

    def setUp(self):
        self.client.force_login(self.trainer)

    def test_manage_plans_page_lists_plans(self):
        response = self.client.get(reverse('manage_plans'))
        self.assertContains(response, 'Beginner Plan')  # checks status 200 AND the text

    def test_create_plan(self):
        data = {'name': 'Push Day', 'description': 'Chest focus',
                f'use_{self.bench.id}': 'on', f'sets_{self.bench.id}': 4,
                f'reps_{self.bench.id}': 8, f'order_{self.bench.id}': ''}
        response = self.client.post(reverse('plan_create'), data)
        self.assertRedirects(response, reverse('manage_plans'))
        plan = WorkoutPlan.objects.get(name='Push Day')
        self.assertEqual(plan.created_by, self.trainer)
        self.assertEqual(plan.plan_exercises.get().sets, 4)

    def test_edit_unknown_plan_gives_404(self):
        response = self.client.get(reverse('plan_edit', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_needs_post(self):
        response = self.client.get(reverse('plan_delete', args=[self.plan.id]))
        self.assertEqual(response.status_code, 405)  # 405 = "Method Not Allowed"
        self.assertTrue(WorkoutPlan.objects.filter(id=self.plan.id).exists())

    def test_delete_plan_keeps_member_history(self):
        response = self.client.post(reverse('plan_delete', args=[self.plan.id]))
        self.assertRedirects(response, reverse('manage_plans'))
        self.assertFalse(WorkoutPlan.objects.filter(id=self.plan.id).exists())
        self.member.profile.refresh_from_db()
        self.assertIsNone(self.member.profile.assigned_plan)
        self.assertEqual(WorkoutLog.objects.filter(user=self.member).count(), 1)


class PlanCreateEmptyLibraryTests(TestCase):

    def test_plan_builder_needs_exercises_first(self):
        self.client.force_login(make_trainer())
        response = self.client.get(reverse('plan_create'))
        self.assertRedirects(response, reverse('manage_plans'))
        self.assertIn('Add some exercises to the library before creating a plan.', message_texts(response))


class TrainerExerciseViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.bench = make_exercise('Bench Press', 'chest')
        make_plan(cls.trainer, exercises=[cls.bench])  # bench is now "in use"
        cls.plank = make_exercise('Plank', 'core')    # plank is unused

    def setUp(self):
        self.client.force_login(self.trainer)

    def test_create_exercise(self):
        response = self.client.post(reverse('exercise_create'),
                                    {'name': 'Lunges', 'muscle_group': 'legs', 'description': ''})
        self.assertRedirects(response, reverse('manage_plans'))
        self.assertTrue(Exercise.objects.filter(name='Lunges').exists())

    def test_edit_exercise(self):
        self.client.post(reverse('exercise_edit', args=[self.plank.id]),
                         {'name': 'Side Plank', 'muscle_group': 'core', 'description': ''})
        self.plank.refresh_from_db()
        self.assertEqual(self.plank.name, 'Side Plank')

    def test_delete_unused_exercise(self):
        self.client.post(reverse('exercise_delete', args=[self.plank.id]))
        self.assertFalse(Exercise.objects.filter(id=self.plank.id).exists())

    def test_exercise_in_use_is_not_deleted(self):
        response = self.client.post(reverse('exercise_delete', args=[self.bench.id]))
        self.assertTrue(Exercise.objects.filter(id=self.bench.id).exists())
        self.assertTrue(any("can't be deleted" in m for m in message_texts(response)))


class AssignPlanViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.plan = make_plan(cls.trainer)
        cls.member = make_member()

    def setUp(self):
        self.client.force_login(self.trainer)

    def assign(self, user_id, plan_id):
        return self.client.post(reverse('assign_plan', args=[user_id]), {'plan_id': plan_id})

    def test_trainer_can_assign_a_plan(self):
        response = self.assign(self.member.id, self.plan.id)
        self.assertRedirects(response, reverse('manage_users'))
        self.member.profile.refresh_from_db()
        self.assertEqual(self.member.profile.assigned_plan, self.plan)

    def test_unknown_member_gives_404(self):
        self.assertEqual(self.assign(9999, self.plan.id).status_code, 404)

    def test_cannot_assign_a_plan_to_a_trainer(self):
        other_trainer = make_trainer('trainer2')
        self.assertEqual(self.assign(other_trainer.id, self.plan.id).status_code, 404)

    def test_missing_plan_choice_does_not_crash(self):
        response = self.assign(self.member.id, '')
        self.assertRedirects(response, reverse('manage_users'))
        self.member.profile.refresh_from_db()
        self.assertIsNone(self.member.profile.assigned_plan)

    def test_unknown_plan_gives_404(self):
        self.assertEqual(self.assign(self.member.id, 9999).status_code, 404)

    def test_assign_needs_post(self):
        response = self.client.get(reverse('assign_plan', args=[self.member.id]))
        self.assertEqual(response.status_code, 405)