from django.urls import path
from profiles.views import UserProfile, UserProfileList

urlpatterns = [
    path('profile/', UserProfile.as_view(), name='user-profile'),
    path('list/', UserProfileList.as_view(), name='user-profile-list'),
]