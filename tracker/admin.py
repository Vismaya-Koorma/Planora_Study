from django.contrib import admin
from .models import Task, Goal, Timetable, Reminder, UserProfile

admin.site.register(Task)
admin.site.register(Goal)
admin.site.register(Timetable)
admin.site.register(Reminder)
admin.site.register(UserProfile)
