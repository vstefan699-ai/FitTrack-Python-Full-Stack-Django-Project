"""
Creates (or refreshes) the demo accounts for FitTrack Pro.

    python manage.py seed_demo

Passwords:
  - demo MEMBER password is PUBLIC (it's in the README).
  - demo TRAINER password is PRIVATE on production. Set it in the
    DEMO_TRAINER_PASSWORD environment variable before running.
    If that variable is missing, a LOCAL-ONLY fallback is used (fine for
    the dev branch, NEVER for production) and a warning is printed.

Safe to run again and again: it never duplicates anything, and every run
rebuilds the demo member's workout history so it always ends last week.
"""
import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import Exercise, PlanExercise, UserProfile, WorkoutLog, WorkoutPlan

TRAINER_USERNAME = 'demo_trainer'
MEMBER_USERNAME = 'demo_member'

# PUBLIC - it's in the README. Never reuse this password anywhere!
MEMBER_PASSWORD = 'FitTrackDemo2026!'

# The real trainer password lives ONLY in this environment variable.
TRAINER_PASSWORD_ENV_VAR = 'DEMO_TRAINER_PASSWORD'
# This file is in a public repo, so this fallback is effectively public too.
# It only exists so local dev and the tests work without extra setup.
TRAINER_FALLBACK_PASSWORD = 'TrainerLocalOnly2026!'
MIN_TRAINER_PASSWORD_LENGTH = 12

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


def get_trainer_password():
    """
    Returns (password, came_from_env).

    Read at RUN time (not when the file is imported), so tests can change
    the environment variable between runs.
    """
    raw = os.environ.get(TRAINER_PASSWORD_ENV_VAR)

    # Variable missing completely -> local fallback (handle() prints a warning)
    if raw is None:
        return TRAINER_FALLBACK_PASSWORD, False

    # strip(): a stray space from pasting into Read-Host won't sneak in
    password = raw.strip()

    # Variable SET but empty = almost certainly a mistake (Enter pressed too
    # early). Stop loudly instead of silently using the public fallback.
    if not password:
        raise CommandError(
            f'{TRAINER_PASSWORD_ENV_VAR} is set but empty. Set it again, or remove it '
            f'to use the local fallback (dev branch only!).'
        )
    if password in (MEMBER_PASSWORD, TRAINER_FALLBACK_PASSWORD):
        raise CommandError(
            f'{TRAINER_PASSWORD_ENV_VAR} must NOT be one of the public passwords '
            f'from seed_demo.py. Choose a new, private one.'
        )
    if len(password) < MIN_TRAINER_PASSWORD_LENGTH:
        raise CommandError(
            f'{TRAINER_PASSWORD_ENV_VAR} must be at least '
            f'{MIN_TRAINER_PASSWORD_LENGTH} characters long.'
        )
    return password, True


class Command(BaseCommand):
    help = 'Create or refresh the demo trainer + demo member with sample data.'

    def handle(self, *args, **options):
        # Checked BEFORE touching the database: a bad password stops
        # everything before a single row is written.
        trainer_password, from_env = get_trainer_password()

        # atomic: if ANY step fails, nothing at all is saved
        with transaction.atomic():
            trainer = self.get_demo_user(TRAINER_USERNAME, trainer_password, is_staff=True)
            member = self.get_demo_user(MEMBER_USERNAME, MEMBER_PASSWORD, is_staff=False)
            exercises = self.get_exercises()
            plan = self.build_plan(trainer, exercises)

            profile, _ = UserProfile.objects.get_or_create(user=member)
            profile.assigned_plan = plan
            profile.save()

            log_count = self.build_history(member, exercises)

        self.stdout.write(self.style.SUCCESS('Demo data ready!'))
        if from_env:
            # Never print the private password - terminal output can end up in screenshots
            self.stdout.write(f'  Trainer: {TRAINER_USERNAME} / '
                              f'(password from {TRAINER_PASSWORD_ENV_VAR} - not shown)')
        else:
            self.stdout.write(f'  Trainer: {TRAINER_USERNAME} / {TRAINER_FALLBACK_PASSWORD}')
            self.stdout.write(self.style.WARNING(
                f'  WARNING: {TRAINER_PASSWORD_ENV_VAR} is not set, so the trainer got the '
                f'LOCAL fallback password. NEVER run it like this on production!'
            ))
        self.stdout.write(f'  Member:  {MEMBER_USERNAME} / {MEMBER_PASSWORD}')
        self.stdout.write(f'  Plan "{plan.name}" with {len(exercises)} exercises, '
                          f'{log_count} workout logs over {WEEKS_OF_HISTORY} weeks')

    def get_demo_user(self, username, password, is_staff):
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
        user.set_password(password)  # also resets it if a visitor somehow changed it
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