from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import WorkoutPlan, Exercise, WorkoutLog
from .forms import WorkoutLogForm, MAX_DAYS_BACK

# Login view
def login_view(request):
    # If the user is already logged in, redirect them
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        # Grab the username and password from the form
        username = request.POST['username']
        password = request.POST['password']
        
        # Check if credentials are correct
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Send them to the right dashboard based on role
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'core/login.html')


# Register view
def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        # Check passwords match
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        
        # Check username isn't taken
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('register')
        
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        # Log them in automatically
        login(request, user)
        messages.success(request, f'Welcome to FitTrack Pro, {username}!')
        return redirect('user_dashboard')
    
    return render(request, 'core/register.html')


# Logout view
def logout_view(request):
    logout(request)
    return redirect('login')


# Admin dashboard
@login_required(login_url='login')
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('user_dashboard')
    
    plans = WorkoutPlan.objects.all()
    total_users = User.objects.filter(is_staff=False).count()
    total_logs = WorkoutLog.objects.all().count()
    
    return render(request, 'core/admin_dashboard.html', {
        'plans': plans,
        'total_users': total_users,
        'total_logs': total_logs,
    })

# User dashboard
@login_required(login_url='login')
def user_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    
    total_logs = WorkoutLog.objects.filter(user=request.user).count()
    
    return render(request, 'core/user_dashboard.html', {
        'total_logs': total_logs,
    })

# Manage workout plans
@login_required(login_url='login')
def manage_plans(request):
    if not request.user.is_staff:
        return redirect('user_dashboard')
    
    plans = WorkoutPlan.objects.all()
    return render(request, 'core/manage_plans.html', {'plans': plans})


# Manage users/members
@login_required(login_url='login')
def manage_users(request):
    if not request.user.is_staff:
        return redirect('user_dashboard')
    
    users = User.objects.filter(is_staff=False)
    plans = WorkoutPlan.objects.all()
    return render(request, 'core/manage_users.html', {
        'users': users,
        'plans': plans,
    })

# Log a workout
@login_required(login_url='login')
def workout_log(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        # Fill the form with what the member submitted, then validate it
        form = WorkoutLogForm(request.POST, user=request.user)
        if form.is_valid():
            # commit=False: build the log but don't save yet,
            # because the form doesn't know WHO is logging
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            messages.success(request, 'Workout logged successfully!')
            return redirect('user_dashboard')
        # Not valid: fall through and show the form again WITH the errors
        messages.error(request, 'Please fix the errors below.')
    else:
        # GET: an empty form, with the exercise pre-selected if the member
        # clicked "Log This" on the dashboard (?exercise=5 in the URL)
        form = WorkoutLogForm(user=request.user)
        exercise_id = request.GET.get('exercise', '')
        if exercise_id.isdigit():
            chosen = form.fields['exercise'].queryset.filter(id=exercise_id).first()
            if chosen:
                form = WorkoutLogForm(user=request.user, initial={'exercise': chosen.id})

    # Limits for the date picker, so the browser greys out impossible dates
    today = timezone.localdate()
    return render(request, 'core/workout_log.html', {
        'form': form,
        'exercises': form.fields['exercise'].queryset,
        'today': today,
        'oldest_date': today - timedelta(days=MAX_DAYS_BACK),
    })


# My progress page
@login_required(login_url='login')
def my_progress(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    
    # select_related loads each log's exercise in the SAME database query
    logs = (WorkoutLog.objects.filter(user=request.user)
            .select_related('exercise')
            .order_by('-completed_on', '-id'))  # newest date first; same date = newest entry first
    
    return render(request, 'core/my_progress.html', {
        'logs': logs,
    })

# Assign a plan to a user
@login_required(login_url='login')
def assign_plan(request, user_id):
    if not request.user.is_staff:
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        plan_id = request.POST['plan_id']
        member = User.objects.get(id=user_id)
        plan = WorkoutPlan.objects.get(id=plan_id)
        
        # Update the member's profile
        member.profile.assigned_plan = plan
        member.profile.save()
        
        messages.success(request, f'Plan assigned to {member.username} successfully!')
    
    return redirect('manage_users')

def landing(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('user_dashboard')
    return render(request, 'core/landing.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)