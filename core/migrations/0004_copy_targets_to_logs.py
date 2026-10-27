from django.db import migrations


def copy_targets_to_logs(apps, schema_editor):
    # Use the "historical" version of the model, as it looked at THIS point
    # in the migration history - not whatever models.py says later on.
    WorkoutLog = apps.get_model('core', 'WorkoutLog')

    # Old logs never stored sets/reps; the app used to show the plan's
    # target instead. Copy that target into each old log so history is kept.
    for log in WorkoutLog.objects.select_related('exercise'):
        log.sets_done = log.exercise.sets
        log.reps_done = log.exercise.reps
        log.save(update_fields=['sets_done', 'reps_done'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_workoutlog_reps_done_workoutlog_sets_done'),
    ]

    operations = [
        # noop = "do nothing" when rolling back, so the migration can be undone
        migrations.RunPython(copy_targets_to_logs, migrations.RunPython.noop),
    ]