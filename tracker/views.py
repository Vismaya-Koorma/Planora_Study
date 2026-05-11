from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Task, Goal, Timetable, Reminder, UserProfile, StudentTeacherLink
from datetime import date, datetime
from django.contrib.auth.models import User

@login_required
def home(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'Student'})
    if profile.role == 'Admin':
        return redirect('admin_dashboard')
    elif profile.role == 'Teacher':
        return redirect('teacher_dashboard')

    tasks = Task.objects.filter(user=request.user).order_by('date', 'start_time')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='Completed').count()
    progress_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    return render(request, 'tracker/home.html', {
        'tasks': tasks,
        'plans': tasks,
        'today': date.today(),
        'progress_percentage': progress_percentage
    })

@login_required
def add_task(request):
    if request.method == 'POST':
        description = request.POST.get('description', request.POST.get('title', ''))
        subject = request.POST.get('subject')
        task_date = request.POST.get('study_date', date.today())
        start_time = request.POST.get('start_time', '14:00')
        end_time = request.POST.get('end_time', '15:00')
        priority = request.POST.get('priority', 'Medium')
        
        if description and subject:
            Task.objects.create(
                user=request.user,
                description=description,
                subject=subject,
                date=task_date,
                start_time=start_time,
                end_time=end_time,
                priority=priority,
                status='Pending'
            )
    return redirect('home')

@login_required
def toggle_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.status = 'Completed' if task.status != 'Completed' else 'Pending'
        task.save()
    except Task.DoesNotExist:
        pass
    return redirect('home')

@login_required
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.delete()
    except Task.DoesNotExist:
        pass
    return redirect('home')

@login_required
def edit_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
    except Task.DoesNotExist:
        return redirect('home')
        
    if request.method == 'POST':
        task.description = request.POST.get('description', request.POST.get('title', task.description))
        task.subject = request.POST.get('subject', task.subject)
        task.date = request.POST.get('study_date', task.date)
        task.start_time = request.POST.get('start_time', task.start_time)
        task.end_time = request.POST.get('end_time', task.end_time)
        task.priority = request.POST.get('priority', task.priority)
        task.save()
        return redirect('home')
            
    return render(request, 'tracker/edit.html', {'task': task, 'plan': task})

@login_required
def daily_planner(request):
    tasks = Task.objects.filter(user=request.user).order_by('date', 'start_time')
    return render(request, 'tracker/planner.html', {'tasks': tasks})

@login_required
def progress_analytics(request):
    tasks = Task.objects.filter(user=request.user)
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='Completed')
    completed_count = completed_tasks.count()
    completion_percentage = int((completed_count / total_tasks) * 100) if total_tasks > 0 else 0
    
    total_hours = 0
    for task in completed_tasks:
        if task.end_time and task.start_time:
            duration_minutes = (task.end_time.hour * 60 + task.end_time.minute) - (task.start_time.hour * 60 + task.start_time.minute)
            if duration_minutes < 0:
                duration_minutes += 24 * 60
            total_hours += duration_minutes / 60.0
            
    return render(request, 'tracker/analytics.html', {
        'completion_percentage': completion_percentage,
        'total_hours': int(total_hours)
    })

@login_required
def goals(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        goal_type = request.POST.get('goal_type')
        deadline = request.POST.get('deadline')
        progress = request.POST.get('progress', 0)
        
        if title and deadline:
            Goal.objects.create(
                user=request.user,
                title=title,
                goal_type=goal_type,
                deadline=deadline,
                progress=int(progress) if progress else 0
            )
        return redirect('goals')
        
    user_goals = Goal.objects.filter(user=request.user)
    return render(request, 'tracker/goals.html', {'goals': user_goals})

@login_required
def update_goal(request, goal_id):
    if request.method == 'POST':
        try:
            goal = Goal.objects.get(id=goal_id, user=request.user)
            progress = request.POST.get('progress')
            if progress is not None:
                goal.progress = int(progress)
                if goal.progress >= 100:
                    goal.progress = 100
                    goal.completed = True
                else:
                    goal.completed = False
                goal.save()
        except Goal.DoesNotExist:
            pass
    return redirect('goals')

from django.contrib import messages

@login_required
def timetable(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        if subject and day and start_time and end_time:
            # Conflict detection
            overlapping = Timetable.objects.filter(
                user=request.user,
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if overlapping:
                messages.error(request, "This time slot overlaps with an existing class!")
            else:
                Timetable.objects.create(
                    user=request.user,
                    subject=subject,
                    day=day,
                    start_time=start_time,
                    end_time=end_time
                )
        return redirect('timetable')
        
    schedule_list = list(Timetable.objects.filter(user=request.user).order_by('start_time'))
    
    # Dynamically find the hour range, defaulting to 8-18 if empty
    min_hour = 8
    max_hour = 18
    if schedule_list:
        min_hour = min(c.start_time.hour for c in schedule_list)
        max_hour = max(c.end_time.hour for c in schedule_list)
        # Add some padding
        min_hour = max(0, min_hour - 1)
        max_hour = min(23, max_hour + 1)
        
    hours = [f"{h:02d}:00" for h in range(min_hour, max_hour + 1)]
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    grid = []
    for hour_str in hours:
        row = {'time': hour_str, 'days': []}
        hour_int = int(hour_str.split(':')[0])
        for day in days:
            classes = [c for c in schedule_list if c.day == day and c.start_time.hour == hour_int]
            row['days'].append(classes)
        grid.append(row)

    return render(request, 'tracker/timetable.html', {'grid': grid})

@login_required
def reminders(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        reminder_time = request.POST.get('reminder_time')
        
        if title and reminder_time:
            Reminder.objects.create(
                user=request.user,
                title=title,
                reminder_time=reminder_time
            )
        return redirect('reminders')
        
    user_reminders = Reminder.objects.filter(user=request.user).order_by('reminder_time')
    return render(request, 'tracker/reminders.html', {'reminders': user_reminders})

from collections import defaultdict

@login_required
def performance(request):
    completed_tasks = Task.objects.filter(user=request.user, status='Completed')
    
    subject_hours = defaultdict(float)
    from datetime import date
    today = date.today()
    trend_data = [0, 0, 0, 0] # Week 1, Week 2, Week 3, Week 4
    
    for task in completed_tasks:
        if task.start_time and task.end_time:
            duration_minutes = (task.end_time.hour * 60 + task.end_time.minute) - (task.start_time.hour * 60 + task.start_time.minute)
            if duration_minutes < 0:
                duration_minutes += 24 * 60
            hours = duration_minutes / 60.0
            
            subject_hours[task.subject] += hours
            
            # Trend calculation
            if task.date:
                delta = (today - task.date).days
                if 0 <= delta < 7:
                    trend_data[3] += hours
                elif 7 <= delta < 14:
                    trend_data[2] += hours
                elif 14 <= delta < 21:
                    trend_data[1] += hours
                elif 21 <= delta < 28:
                    trend_data[0] += hours
            
    sorted_subjects = sorted(subject_hours.items(), key=lambda x: x[1], reverse=True)
    
    labels = [item[0] for item in sorted_subjects]
    data = [round(item[1], 1) for item in sorted_subjects]
    trend_data = [round(w, 1) for w in trend_data]
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e', '#84cc16']
    
    rankings = []
    max_hours = sorted_subjects[0][1] if sorted_subjects else 1
    total_all_hours = sum(item[1] for item in sorted_subjects)
    
    for i, (subj, hours) in enumerate(sorted_subjects):
        rankings.append({
            'name': subj,
            'hours': round(hours, 1),
            'relative_percentage': int((hours / max_hours) * 100),
            'total_percentage': int((hours / total_all_hours) * 100) if total_all_hours > 0 else 0,
            'color': colors[i % len(colors)]
        })
        
    top_subject = sorted_subjects[0][0] if sorted_subjects else "None"
    
    # We still need to serialize lists for JavaScript
    import json
    context = {
        'labels_json': json.dumps(labels),
        'data_json': json.dumps(data),
        'trend_json': json.dumps(trend_data),
        'colors_json': json.dumps(colors[:len(labels)]),
        'rankings': rankings,
        'top_subject': top_subject,
        'has_data': len(sorted_subjects) > 0
    }
    
    return render(request, 'tracker/performance.html', context)

@login_required
def admin_dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'Student'})
    if profile.role != 'Admin':
        return redirect('home')
        
    if request.method == 'POST':
        if 'delete_user' in request.POST:
            user_id = request.POST.get('user_id')
            User.objects.filter(id=user_id).delete()
            messages.success(request, "User deleted successfully.")
            return redirect('admin_dashboard')
            
        elif 'change_role' in request.POST:
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('new_role')
            target_profile = UserProfile.objects.get(user_id=user_id)
            target_profile.role = new_role
            target_profile.save()
            messages.success(request, "Role updated successfully.")
            return redirect('admin_dashboard')

        elif 'add_user' in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role', 'Student')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists.")
            else:
                new_user = User.objects.create_user(username=username, email=email, password=password)
                UserProfile.objects.get_or_create(user=new_user, defaults={'role': role})
                messages.success(request, f"User '{username}' created successfully as {role}.")
            return redirect('admin_dashboard')
        
    profiles = UserProfile.objects.exclude(user=request.user).select_related('user')
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='Completed').count()
    
    return render(request, 'tracker/admin_dashboard.html', {
        'profiles': profiles,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'total_users': User.objects.count()
    })

@login_required
def teacher_dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'Student'})
    if profile.role != 'Teacher':
        return redirect('home')
        
    if request.method == 'POST' and 'assign_task' in request.POST:
        student_id = request.POST.get('student_id')
        description = request.POST.get('description')
        subject = request.POST.get('subject')
        task_date = request.POST.get('date')
        end_date = request.POST.get('end_date')
        priority = request.POST.get('priority', 'High')
        
        student_user = User.objects.get(id=student_id)
        Task.objects.create(
            user=student_user,
            assigned_by=request.user,
            description=description,
            subject=subject,
            date=task_date,
            end_date=end_date,
            start_time='00:00',
            end_time='00:00',
            priority=priority
        )
        return redirect('teacher_dashboard')
        
    # Get assigned students or all students for demo purposes
    links = StudentTeacherLink.objects.filter(teacher=request.user)
    if links.exists():
        students = [link.student for link in links]
    else:
        # Fallback to show all students if none are explicitly assigned
        students = User.objects.filter(userprofile__role='Student').exclude(username='vismaya_koorma')
        
    return render(request, 'tracker/teacher_dashboard.html', {
        'students': students
    })

@login_required
def student_report(request, student_id):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'Student'})
    if profile.role != 'Teacher':
        return redirect('home')
        
    student = User.objects.get(id=student_id)
    completed_tasks = Task.objects.filter(user=student, status='Completed')
    
    subject_hours = defaultdict(float)
    from datetime import date
    today = date.today()
    trend_data = [0, 0, 0, 0] # Week 1, Week 2, Week 3, Week 4
    
    for task in completed_tasks:
        if task.start_time and task.end_time:
            duration_minutes = (task.end_time.hour * 60 + task.end_time.minute) - (task.start_time.hour * 60 + task.start_time.minute)
            if duration_minutes < 0:
                duration_minutes += 24 * 60
            hours = duration_minutes / 60.0
            
            subject_hours[task.subject] += hours
            
            # Trend calculation
            if task.date:
                delta = (today - task.date).days
                if 0 <= delta < 7:
                    trend_data[3] += hours
                elif 7 <= delta < 14:
                    trend_data[2] += hours
                elif 14 <= delta < 21:
                    trend_data[1] += hours
                elif 21 <= delta < 28:
                    trend_data[0] += hours
            
    sorted_subjects = sorted(subject_hours.items(), key=lambda x: x[1], reverse=True)
    
    labels = [item[0] for item in sorted_subjects]
    data = [round(item[1], 1) for item in sorted_subjects]
    trend_data = [round(w, 1) for w in trend_data]
    
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e', '#84cc16']
    
    rankings = []
    max_hours = sorted_subjects[0][1] if sorted_subjects else 1
    total_all_hours = sum(item[1] for item in sorted_subjects)
    
    for i, (subj, hours) in enumerate(sorted_subjects):
        rankings.append({
            'name': subj,
            'hours': round(hours, 1),
            'relative_percentage': int((hours / max_hours) * 100),
            'total_percentage': int((hours / total_all_hours) * 100) if total_all_hours > 0 else 0,
            'color': colors[i % len(colors)]
        })
        
    top_subject = sorted_subjects[0][0] if sorted_subjects else "None"
    
    import json
    context = {
        'labels_json': json.dumps(labels),
        'data_json': json.dumps(data),
        'trend_json': json.dumps(trend_data),
        'colors_json': json.dumps(colors[:len(labels)]),
        'rankings': rankings,
        'top_subject': top_subject,
        'has_data': len(sorted_subjects) > 0,
        'student_name': student.username,
        'is_teacher_view': True
    }
    
    return render(request, 'tracker/performance.html', context)
