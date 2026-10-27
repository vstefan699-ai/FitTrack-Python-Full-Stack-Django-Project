from django.contrib import admin
from .models import WorkoutPlan, Exercise, WorkoutLog, UserProfile

# Register your models here
admin.site.register(WorkoutPlan)
admin.site.register(Exercise)
admin.site.register(UserProfile)


# Show the useful columns in the admin list instead of just "user - exercise"
@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'sets_done', 'reps_done', 'weight_used', 'completed_on')
    list_filter = ('completed_on', 'user')
    search_fields = ('user__username', 'exercise__name')