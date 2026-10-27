from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver

# A workout plan created by an admin
class WorkoutPlan(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_plans')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# An exercise in the shared library (used by any number of plans)
class Exercise(models.Model):
    MUSCLE_GROUPS = [
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('legs', 'Legs'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms'),
        ('core', 'Core'),
    ]
    name = models.CharField(max_length=200, unique=True)
    muscle_group = models.CharField(max_length=50, choices=MUSCLE_GROUPS)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['muscle_group', 'name']

    def __str__(self):
        return self.name


# One exercise inside one plan, with that plan's target sets/reps.
# The same library exercise can appear in many plans with different targets.
class PlanExercise(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='plan_exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name='plan_entries')
    sets = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    reps = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            # The same exercise can't be added twice to one plan
            models.UniqueConstraint(fields=['plan', 'exercise'], name='unique_exercise_per_plan'),
        ]

    def __str__(self):
        return f"{self.plan.name}: {self.exercise.name} ({self.sets}x{self.reps})"


# A log entry when a user completes an exercise
class WorkoutLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    # PROTECT: an exercise with workout history can't be deleted
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    # What the member ACTUALLY did (the plan's sets/reps are only the target)
    sets_done = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    reps_done = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Reps per set"
    )
    weight_used = models.FloatField()
    # Defaults to today, but the member can change it (e.g. logging yesterday's session)
    completed_on = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name}"


# Extra information linked to each user
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    assigned_plan = models.ForeignKey(WorkoutPlan, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

# The plan assigned to a member, or None (also safe for users without a profile)
def get_assigned_plan(user):
    profile = getattr(user, 'profile', None)
    return profile.assigned_plan if profile else None


# Automatically create a profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)