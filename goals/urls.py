from django.urls import path


from goals.views import (
    GoalMetricsApiView,
    GoalCreateApiView,
    GoalRetrieveApiView,
    handleReport
)

urlpatterns = [
    path('', GoalCreateApiView.as_view(), name='goal-create'),
    path('metrics/', GoalMetricsApiView.as_view(), name='goal-metrics'),
    path('<int:pk>/', GoalRetrieveApiView.as_view(), name='goal-detail'),
    path('metrics/report/', handleReport, name="handlereport")
]
