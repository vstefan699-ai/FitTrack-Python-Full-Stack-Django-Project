from django.db import migrations


def normalise(name):
    # "  bench   Press " -> "bench press", so near-duplicates are recognised
    return ' '.join(name.split()).lower()


def build_exercise_library(apps, schema_editor):
    # Historical models: how the tables look at THIS point in history
    Exercise = apps.get_model('core', 'Exercise')
    PlanExercise = apps.get_model('core', 'PlanExercise')
    WorkoutLog = apps.get_model('core', 'WorkoutLog')

    keepers = {}  # normalised name -> the Exercise row we keep in the library

    # Oldest first, so the first-created copy of each exercise is kept
    for old in Exercise.objects.order_by('id'):
        keeper = keepers.setdefault(normalise(old.name), old)

        # 1. The old row's plan + targets become a PlanExercise entry,
        #    pointing at the library copy (skip if that plan already has it)
        in_plan = PlanExercise.objects.filter(plan_id=old.workout_plan_id, exercise=keeper)
        if not in_plan.exists():
            PlanExercise.objects.create(
                plan_id=old.workout_plan_id,
                exercise=keeper,
                sets=max(old.sets, 1),
                reps=max(old.reps, 1),
                order=PlanExercise.objects.filter(plan_id=old.workout_plan_id).count() + 1,
            )

        # 2. A duplicate: move its workout history to the keeper, then remove it
        if keeper.pk != old.pk:
            WorkoutLog.objects.filter(exercise=old).update(exercise=keeper)
            old.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_planexercise'),
    ]

    operations = [
        migrations.RunPython(build_exercise_library, migrations.RunPython.noop),
    ]