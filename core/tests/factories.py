"""
Small helpers that build test data, so each test reads like a sentence:
    trainer = make_trainer()
    plan = make_plan(trainer, exercises=[bench])
"""
from django.contrib.auth.models import User

from core.models import Exercise, PlanExercise, WorkoutPlan

# One shared password for every test user (only exists in the throwaway test DB)
PASSWORD = 'Test-pass-123'


def make_trainer(username='trainer'):
    """A staff user = a trainer in FitTrack Pro."""
    return User.objects.create_user(username=username, password=PASSWORD, is_staff=True)


def make_member(username='member', plan=None):
    """A normal (non-staff) user, optionally already on a plan."""
    user = User.objects.create_user(username=username, password=PASSWORD)
    # The post_save signal in models.py already created user.profile for us
    if plan is not None:
        user.profile.assigned_plan = plan
        user.profile.save()
    return user


def make_exercise(name='Bench Press', muscle_group='chest'):
    return Exercise.objects.create(name=name, muscle_group=muscle_group)


def make_plan(trainer, name='Beginner Plan', exercises=()):
    """A plan containing the given exercises, each with a 3x10 target."""
    plan = WorkoutPlan.objects.create(name=name, description='Plan used in tests', created_by=trainer)
    for position, exercise in enumerate(exercises, start=1):
        PlanExercise.objects.create(plan=plan, exercise=exercise, sets=3, reps=10, order=position)
    return plan