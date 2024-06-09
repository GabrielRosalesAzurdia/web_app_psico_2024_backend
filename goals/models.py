from django.db import models

class Goal(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_time = models.DateField()
    end_time = models.DateField()
    apponitments_goal = models.IntegerField()

    def __str__(self):
        return f'{self.start_time} - {self.end_time} - {self.pk}'

class GoalMetrics(models.Model):
    appointments = models.IntegerField()
    monthly_goal_porcentage = models.FloatField()
    assistance = models.IntegerField()

    def __str__(self):
        return f'{self.appointments} - {self.monthly_goal_porcentage} - {self.assistance}'
