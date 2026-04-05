from django.db import models
from django.contrib.auth.models import User

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    study_date = models.DateField()
    duration = models.IntegerField()  # in minutes
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

# Create your models here.
