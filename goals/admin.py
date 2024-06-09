from django.contrib import admin

from goals.models import Goal, GoalMetrics


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    ...

@admin.register(GoalMetrics)
class GoalMetricsAdmin(admin.ModelAdmin):
    ...
