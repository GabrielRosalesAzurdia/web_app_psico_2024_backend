from django.urls import path


from events.views import (
    EventsCreateApiView,
    EventsRetrieveApiView
)

urlpatterns = [
    path('',
         EventsCreateApiView.as_view(),
         name='events-create'),
    path('<int:pk>/',
         EventsRetrieveApiView.as_view(), name='events-detail'),
]
