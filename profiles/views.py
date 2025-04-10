from django.contrib.auth import get_user_model
from rest_framework.generics import  RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated

from profiles.serializers import ProfileSerializer


class UserProfile(RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserProfileList(ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]