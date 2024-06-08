from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from activity.models import Activity
from activity.serializers import ActivityReadSerializer, ActivitySerializer
from django.utils.timezone import now


class ActivityCreateApiView(ListCreateAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

class ActivityRetrieveApiView(RetrieveUpdateAPIView):
    queryset = Activity.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return ActivitySerializer
        return ActivityReadSerializer
    permission_classes = [IsAuthenticated]
    
class ActivityGetPendingApiView(ListAPIView):
    today = now().date()
    queryset = Activity.objects.filter(date__gte=today, status="PENDING").order_by('date')
    serializer_class = ActivityReadSerializer
    permission_classes = [IsAuthenticated]