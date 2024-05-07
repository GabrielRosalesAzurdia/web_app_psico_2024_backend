from django.urls import path

from profiles.views import UserProfile


urlpatterns = [
    path('profile/', UserProfile.as_view()),
]
