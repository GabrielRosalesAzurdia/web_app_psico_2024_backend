from django.urls import path

from notifications.views import (
    NotificationListApiView,
    NotificationMarkAllReadApiView,
    NotificationMarkReadApiView,
    NotificationUnreadCountApiView,
)

urlpatterns = [
    path('', NotificationListApiView.as_view(), name='notification-list'),
    path('unread-count/', NotificationUnreadCountApiView.as_view(), name='notification-unread-count'),
    path('read-all/', NotificationMarkAllReadApiView.as_view(), name='notification-read-all'),
    path('<int:pk>/read/', NotificationMarkReadApiView.as_view(), name='notification-read'),
]
