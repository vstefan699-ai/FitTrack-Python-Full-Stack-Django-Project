from datetime import timedelta

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .models import WorkoutLog, WorkoutPlan, Exercise, PlanExercise, get_assigned_plan

# How far back a member may log a workout (catches typos like 1926 instead of 2026)
MAX_DAYS_BACK = 365


# ---- Accounts: register + login ------------------------------------------

# Sign-up form. UserCreationForm already gives us:
#   - username (required, max 150 chars, only letters/digits/@.+-_)
#   - password1 + password2 (must match)
#   - AUTH_PASSWORD_VALIDATORS from settings.py (so "1" is rejected)
#   - save() that HASHES the password (never stored as plain text)
# We only add the optional email field and a case-insensitive username check.
class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # 'email' is a real User field (blank=True), so it's optional here too
        fields = ('username', 'email')

    def clean_username(self):
        username = self.cleaned_data['username']
        # Block "Newbie" when "newbie" already exists - people forget their capitals
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username


# Login form. AuthenticationForm checks the username + password with
# authenticate() and also refuses inactive accounts (is_active=False).
# We only swap Django's long error text for a shorter, friendlier one.
class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "Invalid username or password.",
    }


# ---- Workouts --------------------------------------------------------------

# Form for a member logging a workout.
# A ModelForm builds its fields (and validation) from the WorkoutLog model.
class WorkoutLogForm(forms.ModelForm):
    class Meta:
        model = WorkoutLog
        fields = ['completed_on', 'exercise', 'sets_done', 'reps_done', 'weight_used', 'notes']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Only allow exercises from THIS member's assigned plan.
        # Anything else sent by the browser fails validation.
        plan = get_assigned_plan(user) if user is not None else None
        if plan:
            self.fields['exercise'].queryset = Exercise.objects.filter(plan_entries__plan=plan)
        else:
            self.fields['exercise'].queryset = Exercise.objects.none()

    def clean_weight_used(self):
        weight = self.cleaned_data['weight_used']
        if weight < 0:
            raise forms.ValidationError("Weight can't be negative. Use 0 for bodyweight exercises.")
        if weight > 500:
            raise forms.ValidationError("That looks like a typo - the maximum is 500 kg.")
        return weight

    def clean_completed_on(self):
        date = self.cleaned_data['completed_on']
        today = timezone.localdate()
        if date > today:
            raise forms.ValidationError("You can't log a workout in the future.")
        if date < today - timedelta(days=MAX_DAYS_BACK):
            raise forms.ValidationError(f"You can only log workouts from the last {MAX_DAYS_BACK} days.")
        return date


# Form for adding/editing an exercise in the shared library
class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['name', 'muscle_group', 'description']

    def clean_name(self):
        # Tidy spaces: "  bench   press " -> "bench press"
        name = ' '.join(self.cleaned_data['name'].split())
        # Block near-duplicates like "bench press" vs "Bench Press"
        duplicates = Exercise.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)  # editing: ignore itself
        if duplicates.exists():
            raise forms.ValidationError("This exercise is already in the library.")
        return name


# The "New Plan" / "Edit Plan" builder.
# Plan name + description come from the model; then, for EVERY library
# exercise, we add 4 extra fields: a tick box, sets, reps and order.
class PlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.library = list(Exercise.objects.all())

        # When editing, look up what's already in the plan
        current = {}
        if self.instance.pk:
            current = {pe.exercise_id: pe for pe in self.instance.plan_exercises.all()}

        for ex in self.library:
            entry = current.get(ex.id)
            self.fields[f'use_{ex.id}'] = forms.BooleanField(
                required=False, initial=entry is not None)
            self.fields[f'sets_{ex.id}'] = forms.IntegerField(
                required=False, min_value=1, max_value=20,
                initial=entry.sets if entry else None)
            self.fields[f'reps_{ex.id}'] = forms.IntegerField(
                required=False, min_value=1, max_value=100,
                initial=entry.reps if entry else None)
            self.fields[f'order_{ex.id}'] = forms.IntegerField(
                required=False, min_value=1, max_value=99,
                initial=entry.order if entry else None)

    def exercise_rows(self):
        # Groups each exercise with its 4 fields, so the template can loop simply
        for ex in self.library:
            yield {
                'exercise': ex,
                'use': self[f'use_{ex.id}'],
                'sets': self[f'sets_{ex.id}'],
                'reps': self[f'reps_{ex.id}'],
                'order': self[f'order_{ex.id}'],
            }

    def clean(self):
        cleaned = super().clean()
        self.chosen = []
        for ex in self.library:
            if not cleaned.get(f'use_{ex.id}'):
                continue  # not ticked: ignore whatever is typed in that row
            for part in ('sets', 'reps'):
                field = f'{part}_{ex.id}'
                # Only add "required" if the field doesn't already have an error
                if cleaned.get(field) is None and field not in self.errors:
                    self.add_error(field, 'Required')
            self.chosen.append((
                ex,
                cleaned.get(f'sets_{ex.id}'),
                cleaned.get(f'reps_{ex.id}'),
                cleaned.get(f'order_{ex.id}'),
            ))
        if not self.chosen:
            raise forms.ValidationError("Tick at least one exercise for this plan.")
        return cleaned

    def save(self, commit=True):
        plan = super().save(commit=False)

        # Rows with an order number first (1, 2, 3...), then the rest A-Z
        rows = sorted(self.chosen, key=lambda r: (r[3] is None, r[3] or 0, r[0].name))

        # atomic = all of this succeeds, or none of it is saved
        with transaction.atomic():
            plan.save()
            # Simplest correct way to "edit" the list: clear it and rebuild it.
            # Safe because workout logs point at Exercise, not PlanExercise.
            plan.plan_exercises.all().delete()
            PlanExercise.objects.bulk_create([
                PlanExercise(plan=plan, exercise=ex, sets=sets, reps=reps, order=position)
                for position, (ex, sets, reps, _) in enumerate(rows, start=1)
            ])
        return plan