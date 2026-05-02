from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Teacher', 'Teacher'),
        ('Admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Student')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class StudentTeacherLink(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_links')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_links')

    class Meta:
        unique_together = ('student', 'teacher')

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.subject} - {self.description}"

class Goal(models.Model):
    GOAL_TYPES = [
        ('Short-term', 'Short-term'),
        ('Long-term', 'Long-term'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateField()
    progress = models.IntegerField(default=0) # 0 to 100
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES, default='Short-term')
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Timetable(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.subject

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    reminder_time = models.DateTimeField()
    related_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    related_goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title
