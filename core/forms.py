from django import forms
from .models import WorkoutLog, Exercise


# Form for a member logging a workout.
# A ModelForm builds its fields (and validation) from the WorkoutLog model.
class WorkoutLogForm(forms.ModelForm):
    class Meta:
        model = WorkoutLog
        fields = ['exercise', 'sets_done', 'reps_done', 'weight_used', 'notes']

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