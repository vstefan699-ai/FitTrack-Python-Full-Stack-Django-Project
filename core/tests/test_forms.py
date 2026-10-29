from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.forms import MAX_DAYS_BACK, ExerciseForm, PlanForm, WorkoutLogForm
from .factories import make_exercise, make_member, make_plan, make_trainer


class WorkoutLogFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.squat = make_exercise('Squat', 'legs')  # in the library, but NOT in the plan
        plan = make_plan(make_trainer(), exercises=[cls.bench])
        cls.member = make_member(plan=plan)

    def make_form(self, **changes):
        """A valid form by default; pass changes to break one thing at a time."""
        data = {
            'completed_on': timezone.localdate().isoformat(),  # "2026-10-29", like a browser sends
            'exercise': self.bench.id,
            'sets_done': 3,
            'reps_done': 10,
            'weight_used': 60,
            'notes': '',
        }
        data.update(changes)
        return WorkoutLogForm(data=data, user=self.member)

    def test_valid_log_passes(self):
        form = self.make_form()
        self.assertTrue(form.is_valid(), form.errors)  # 2nd argument = shown if it fails

    def test_exercise_outside_the_members_plan_is_rejected(self):
        form = self.make_form(exercise=self.squat.id)
        self.assertFalse(form.is_valid())
        self.assertIn('exercise', form.errors)

    def test_member_without_a_plan_has_no_exercises_to_choose(self):
        form = WorkoutLogForm(user=make_member('no_plan_member'))
        self.assertEqual(form.fields['exercise'].queryset.count(), 0)

    def test_negative_weight_is_rejected(self):
        form = self.make_form(weight_used=-5)
        self.assertFalse(form.is_valid())
        self.assertIn("can't be negative", form.errors['weight_used'][0])

    def test_zero_weight_is_allowed_for_bodyweight(self):
        self.assertTrue(self.make_form(weight_used=0).is_valid())

    def test_weight_over_500_is_rejected(self):
        form = self.make_form(weight_used=501)
        self.assertFalse(form.is_valid())
        self.assertIn('weight_used', form.errors)

    def test_future_date_is_rejected(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        form = self.make_form(completed_on=tomorrow.isoformat())
        self.assertFalse(form.is_valid())
        self.assertIn('completed_on', form.errors)

    def test_oldest_allowed_date_is_accepted(self):
        oldest = timezone.localdate() - timedelta(days=MAX_DAYS_BACK)
        self.assertTrue(self.make_form(completed_on=oldest.isoformat()).is_valid())

    def test_date_older_than_the_limit_is_rejected(self):
        too_old = timezone.localdate() - timedelta(days=MAX_DAYS_BACK + 1)
        form = self.make_form(completed_on=too_old.isoformat())
        self.assertFalse(form.is_valid())
        self.assertIn('completed_on', form.errors)

    def test_zero_sets_is_rejected(self):
        form = self.make_form(sets_done=0)
        self.assertFalse(form.is_valid())
        self.assertIn('sets_done', form.errors)


class ExerciseFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.bench = make_exercise('Bench Press', 'chest')

    def test_extra_spaces_are_tidied(self):
        form = ExerciseForm(data={'name': '  Incline   Bench  ', 'muscle_group': 'chest', 'description': ''})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['name'], 'Incline Bench')

    def test_duplicate_name_in_different_case_is_rejected(self):
        form = ExerciseForm(data={'name': 'bench PRESS', 'muscle_group': 'chest', 'description': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('already in the library', form.errors['name'][0])

    def test_editing_an_exercise_can_keep_its_own_name(self):
        form = ExerciseForm(data={'name': 'Bench Press', 'muscle_group': 'chest', 'description': 'Updated'},
                            instance=self.bench)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_muscle_group_is_rejected(self):
        form = ExerciseForm(data={'name': 'Mystery Move', 'muscle_group': 'tail', 'description': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('muscle_group', form.errors)


class PlanFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.trainer = make_trainer()
        cls.bench = make_exercise('Bench Press', 'chest')
        cls.squat = make_exercise('Squat', 'legs')
        cls.deadlift = make_exercise('Deadlift', 'back')

    def base_data(self):
        return {'name': 'Push Day', 'description': 'Chest focus'}

    def row(self, exercise, sets=3, reps=10, order=''):
        """The 4 builder fields for one TICKED exercise row."""
        return {
            f'use_{exercise.id}': 'on',  # a ticked checkbox sends "on"
            f'sets_{exercise.id}': sets,
            f'reps_{exercise.id}': reps,
            f'order_{exercise.id}': order,
        }

    def test_must_tick_at_least_one_exercise(self):
        form = PlanForm(data=self.base_data())
        self.assertFalse(form.is_valid())
        self.assertIn('Tick at least one exercise', form.non_field_errors()[0])

    def test_ticked_exercise_needs_sets_and_reps(self):
        form = PlanForm(data={**self.base_data(), **self.row(self.bench, sets='', reps='')})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors[f'sets_{self.bench.id}'], ['Required'])
        self.assertEqual(form.errors[f'reps_{self.bench.id}'], ['Required'])

    def test_unticked_row_is_ignored(self):
        data = {**self.base_data(), **self.row(self.bench), f'sets_{self.squat.id}': 4}  # squat NOT ticked
        form = PlanForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.trainer
        plan = form.save()
        self.assertEqual(list(plan.plan_exercises.values_list('exercise__name', flat=True)), ['Bench Press'])

    def test_save_puts_numbered_rows_first_then_a_to_z(self):
        data = {**self.base_data(),
                **self.row(self.bench),
                **self.row(self.squat, order=1),
                **self.row(self.deadlift)}
        form = PlanForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.instance.created_by = self.trainer
        plan = form.save()
        self.assertEqual(
            list(plan.plan_exercises.values_list('exercise__name', 'order')),
            [('Squat', 1), ('Bench Press', 2), ('Deadlift', 3)],
        )

    def test_edit_form_is_prefilled_from_the_plan(self):
        plan = make_plan(self.trainer, exercises=[self.bench])
        form = PlanForm(instance=plan)
        self.assertTrue(form.fields[f'use_{self.bench.id}'].initial)
        self.assertEqual(form.fields[f'sets_{self.bench.id}'].initial, 3)
        self.assertFalse(form.fields[f'use_{self.squat.id}'].initial)

    def test_editing_replaces_the_exercise_list(self):
        plan = make_plan(self.trainer, exercises=[self.bench])
        form = PlanForm(data={**self.base_data(), **self.row(self.squat, sets=5, reps=5)}, instance=plan)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        entry = plan.plan_exercises.get()  # .get() also proves there's exactly ONE left
        self.assertEqual((entry.exercise, entry.sets, entry.reps), (self.squat, 5, 5))