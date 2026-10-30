"""
Creates (or refreshes) the public demo accounts for FitTrack Pro.

    python manage.py seed_demo

Safe to run again and again: it never duplicates anything, and every run
rebuilds the demo member's workout history so it always ends last week.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import Exercise, PlanExercise, UserProfile, WorkoutLog, WorkoutPlan

# These are PUBLIC (they go in the README) - never reuse this password anywhere!
DEMO_PASSWORD = 'FitTrackDemo2026!'
TRAINER_USERNAME = 'demo_trainer'
MEMBER_USERNAME = 'demo_member'

# Marker on OUR demo accounts. Real sign-ups have an empty last name, so a
# real person who registered "demo_member" first is never touched.
DEMO_LAST_NAME = 'Demo Account'

PLAN_NAME = 'Beginner Strength A/B (Demo)'
PLAN_DESCRIPTION = ('Three sessions a week (Mon/Wed/Fri), alternating workout A and B. '
                    'Add a little weight every week.')
WEEKS_OF_HISTORY = 8
DELOAD_WEEK = 5  # one lighter week mid-way, like real training (a dip on the chart)

# name, muscle group, description, target sets, target reps, start kg, kg added per week
EXERCISES = [
    ('Hanging Knee Raise', 'core', 'Bodyweight - log it as 0 kg.', 3, 12, 0, 0),
    ('Squat', 'legs', 'Barbell back squat to parallel.', 3, 5, 60, 5),
    ('Bench Press', 'chest', 'Flat barbell bench press.', 3, 5, 50, 2.5),
    ('Barbell Row', 'back', 'Bent-over row with a flat back.', 3, 8, 40, 2.5),
    ('Overhead Press', 'shoulders', 'Standing barbell press.', 3, 5, 30, 1.25),
    ('Deadlift', 'back', 'Conventional deadlift from the floor.', 1, 5, 80, 5),
]

# Workout A and B alternate: Mon A, Wed B, Fri A, next Mon B ...
# Core goes FIRST (as a warm-up), so the LAST log of the newest session is
# Deadlift - My Progress charts the most recent exercise by default, and a
# flat 0 kg knee-raise line would make a boring first impression.
WORKOUT_A = ['Hanging Knee Raise', 'Squat', 'Bench Press', 'Barbell Row']
WORKOUT_B = ['Hanging Knee Raise', 'Squat', 'Overhead Press', 'Deadlift']


def round_to_plate(kg):
    """Gyms load bars in 1.25 kg steps, so 94.5 kg becomes 95.0 kg."""
    return round(kg / 1.25) * 1.25


class Command(BaseCommand):
    help = 'Create or refresh the demo trainer + demo member with sample data.'

    def handle(self, *args, **options):
        # atomic: if ANY step fails, nothing at all is saved
        with transaction.atomic():
            trainer = self.get_demo_user(TRAINER_USERNAME, is_staff=True)
            member = self.get_demo_user(MEMBER_USERNAME, is_staff=False)
            exercises = self.get_exercises()
            plan = self.build_plan(trainer, exercises)

            profile, _ = UserProfile.objects.get_or_create(user=member)
            profile.assigned_plan = plan
            profile.save()

            log_count = self.build_history(member, exercises)

        self.stdout.write(self.style.SUCCESS('Demo data ready!'))
        self.stdout.write(f'  Trainer: {TRAINER_USERNAME} / {DEMO_PASSWORD}')
        self.stdout.write(f'  Member:  {MEMBER_USERNAME} / {DEMO_PASSWORD}')
        self.stdout.write(f'  Plan "{plan.name}" with {len(exercises)} exercises, '
                          f'{log_count} workout logs over {WEEKS_OF_HISTORY} weeks')

    def get_demo_user(self, username, is_staff):
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User(username=username, first_name='FitTrack', last_name=DEMO_LAST_NAME)
        elif user.last_name != DEMO_LAST_NAME:
            # CommandError = a clean red error message, and atomic undoes everything
            raise CommandError(
                f'"{username}" belongs to a real account, so it was NOT touched. '
                f'Change the demo usernames at the top of seed_demo.py.'
            )
        user.is_staff = is_staff
        user.is_superuser = False  # a public account must NEVER be a superuser
        user.is_active = True
        user.set_password(DEMO_PASSWORD)  # also resets it if a visitor somehow changed it
        user.save()  # new users get their profile from the post_save signal
        return user

    def get_exercises(self):
        """Reuse library exercises that already exist (any capitals), create the rest."""
        found = {}
        for name, group, description, *_ in EXERCISES:
            exercise = Exercise.objects.filter(name__iexact=name).first()
            if exercise is None:
                exercise = Exercise.objects.create(name=name, muscle_group=group, description=description)
            found[name] = exercise
        return found

    def build_plan(self, trainer, exercises):
        plan, _ = WorkoutPlan.objects.get_or_create(
            name=PLAN_NAME,
            defaults={'description': PLAN_DESCRIPTION, 'created_by': trainer},  # only used when creating
        )
        # Same "clear and rebuild" trick as PlanForm.save()
        plan.plan_exercises.all().delete()
        PlanExercise.objects.bulk_create([
            PlanExercise(plan=plan, exercise=exercises[name], sets=sets, reps=reps, order=position)
            for position, (name, _group, _desc, sets, reps, _start, _step) in enumerate(EXERCISES, start=1)
        ])
        return plan

    def build_history(self, member, exercises):
        # Wipe ONLY the demo member's old logs, then rebuild them ending last week
        WorkoutLog.objects.filter(user=member).delete()

        targets = {name: (sets, reps, start, step)
                   for name, _group, _desc, sets, reps, start, step in EXERCISES}
        today = timezone.localdate()
        # Monday of THIS week, minus 8 weeks. The last session is then last
        # Friday - always in the past, so nothing lands in the future.
        first_monday = today - timedelta(days=today.weekday(), weeks=WEEKS_OF_HISTORY)

        logs = []
        session_number = 0
        for week in range(WEEKS_OF_HISTORY):
            for day_offset in (0, 2, 4):  # Monday, Wednesday, Friday
                date = first_monday + timedelta(weeks=week, days=day_offset)
                workout = WORKOUT_A if session_number % 2 == 0 else WORKOUT_B
                session_number += 1
                for name in workout:
                    sets, reps, start, step = targets[name]
                    weight = start + step * week
                    if week == DELOAD_WEEK:
                        weight *= 0.9  # 10% lighter on purpose
                    logs.append(WorkoutLog(
                        user=member,
                        exercise=exercises[name],
                        sets_done=sets,
                        reps_done=reps,
                        weight_used=round_to_plate(weight),
                        completed_on=date,
                        notes='Deload week - lighter on purpose' if week == DELOAD_WEEK else '',
                    ))
        # bulk_create: ONE insert for all logs instead of 96 separate ones
        WorkoutLog.objects.bulk_create(logs)
        return len(logs)