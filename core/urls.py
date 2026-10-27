from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('manage-plans/', views.manage_plans, name='manage_plans'),
    # Plan builder (trainer)
    path('manage-plans/new/', views.plan_create, name='plan_create'),
    path('manage-plans/<int:plan_id>/edit/', views.plan_edit, name='plan_edit'),
    path('manage-plans/<int:plan_id>/delete/', views.plan_delete, name='plan_delete'),
    # Shared exercise library (trainer)
    path('manage-plans/exercises/new/', views.exercise_create, name='exercise_create'),
    path('manage-plans/exercises/<int:exercise_id>/edit/', views.exercise_edit, name='exercise_edit'),
    path('manage-plans/exercises/<int:exercise_id>/delete/', views.exercise_delete, name='exercise_delete'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('log-workout/', views.workout_log, name='workout_log'),
    path('my-progress/', views.my_progress, name='my_progress'),
    path('assign-plan/<int:user_id>/', views.assign_plan, name='assign_plan'),
    path('register/', views.register_view, name='register'),
    path('home/', views.landing, name='landing'),
]