from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import StudyPlan

from datetime import date

@login_required
def home(request):
    plans = StudyPlan.objects.filter(user=request.user).order_by('-id')
    total_plans = plans.count()
    completed_plans = plans.filter(completed=True).count()
    progress_percentage = int((completed_plans / total_plans) * 100) if total_plans > 0 else 0
    
    return render(request, 'tracker/home.html', {
        'plans': plans, 
        'today': date.today(),
        'progress_percentage': progress_percentage
    })

@login_required
def add_task(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        study_date = request.POST.get('study_date')
        duration = request.POST.get('duration')
        
        if title and subject and study_date and duration:
            StudyPlan.objects.create(
                user=request.user,
                title=title,
                subject=subject,
                study_date=study_date,
                duration=duration
            )
    return redirect('home')

@login_required
def toggle_task(request, task_id):
    try:
        task = StudyPlan.objects.get(id=task_id, user=request.user)
        task.completed = not task.completed
        task.save()
    except StudyPlan.DoesNotExist:
        pass
    return redirect('home')

@login_required
def delete_task(request, task_id):
    try:
        task = StudyPlan.objects.get(id=task_id, user=request.user)
        task.delete()
    except StudyPlan.DoesNotExist:
        pass
    return redirect('home')

@login_required
def edit_task(request, task_id):
    try:
        task = StudyPlan.objects.get(id=task_id, user=request.user)
    except StudyPlan.DoesNotExist:
        return redirect('home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        study_date = request.POST.get('study_date')
        duration = request.POST.get('duration')
        
        if title and subject and study_date and duration:
            task.title = title
            task.subject = subject
            task.study_date = study_date
            task.duration = duration
            task.save()
            return redirect('home')
            
    # GET request - render the edit form
    return render(request, 'tracker/edit.html', {'task': task})
