from datetime import timedelta

from django import forms
from django.utils import timezone
from .models import WorkoutLog, Exercise

# How far back a member may log a workout (catches typos like 1926 instead of 2026)
MAX_DAYS_BACK = 365


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
        plan = None
        if user is not None and hasattr(user, 'profile'):
            plan = user.profile.assigned_plan

        if plan:
            self.fields['exercise'].queryset = plan.exercises.all()
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