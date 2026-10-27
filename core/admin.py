from django.contrib import admin
from .models import WorkoutPlan, Exercise, PlanExercise, WorkoutLog, UserProfile

admin.site.register(UserProfile)


# Show a plan's exercises as editable rows inside the plan's admin page
class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 1


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    inlines = [PlanExerciseInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'muscle_group')
    list_filter = ('muscle_group',)
    search_fields = ('name',)


# Show the useful columns in the admin list instead of just "user - exercise"
@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'sets_done', 'reps_done', 'weight_used', 'completed_on')
    list_filter = ('completed_on', 'user')
    search_fields = ('user__username', 'exercise__name')