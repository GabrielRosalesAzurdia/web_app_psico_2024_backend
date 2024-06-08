from django.urls import path


from activity.views import (
    ActivityCreateApiView,
    ActivityGetPendingApiView,
    ActivityRetrieveApiView
)

urlpatterns = [
    path('',
         ActivityCreateApiView.as_view(),
         name='activity-create'),
    path('pending/',
         ActivityGetPendingApiView.as_view(),
         name='activity-pending'),
    path('<int:pk>/',
         ActivityRetrieveApiView.as_view(), name='activity-detail'),
]
