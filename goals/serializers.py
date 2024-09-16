from rest_framework import serializers

from goals.models import Goal, GoalMetrics

from appointments.models import Appointment
from django.utils.translation import gettext as _


class GoalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Goal
        fields = '__all__'

    def validate(self, data):
        # If a end date is earlier than the start date
        if data['start_time'] > data['end_time']:
            raise serializers.ValidationError({"message": "End date must occur after start date"})
        
        # If a goal has the same range
        already_goal = Goal.objects.filter(
            start_time__lte=data['start_time'],
            end_time__gte=data['end_time']
        ).exists()

        if already_goal:
            raise serializers.ValidationError({"message": "A Goal already exists within this date range"})
        
        # If a goal has the same start
        already_goal_start = Goal.objects.filter(
            start_time__gte=data['start_time'],
        ).exists()

        if already_goal_start:
            raise serializers.ValidationError({"message": "A Goal already exists within this start range"})
        
        # If a goal has the same end
        already_goal_end = Goal.objects.filter(
            end_time__gte=data['end_time']
        ).exists()

        if already_goal_end:
            raise serializers.ValidationError({"message": "A Goal already exists within this end range"})

        return data

    # def validate_start_time(self, start_time):
    #     already_Goal = Goal.objects.filter(start_time__lte = start_time).exists()

    #     if already_Goal:
    #         raise serializers.ValidationError(
    #             _('A Goal already has this date'))

    #     return super().validate_start_time(start_time)
    
    # def validate_end_time(self, end_time):
    #     already_Goal = Goal.objects.filter(end_time__gte = end_time).exists()

    #     if already_Goal:
    #         raise serializers.ValidationError(
    #             _('A Goal already has this date'))

    #     return super().validate_end_time(end_time)

    def save(self,**kwargs):
        goal = super().save(**kwargs)
        try:
            set_goal = Goal.objects.latest('created_at')
            goal_appointments = Appointment.objects.filter(goal=set_goal.pk)
            #GoalMetrics.objects.create(appointments = goal_appointments.count(), monthly_goal_porcentage = goal_appointments.count()/set_goal.apponitments_goal, assistance =goal_appointments.filter(status="DONE").count())
        except Goal.DoesNotExist:
            pass
        return goal

        

class GoalMetricsSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoalMetrics
        fields = '__all__'