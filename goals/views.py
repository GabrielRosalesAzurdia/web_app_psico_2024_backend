from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from appointments.models import Appointment
from django.utils.timezone import now
from goals.models import Goal, GoalMetrics
from goals.serializers import GoalSerializer, GoalMetricsSerializer
from django.core import exceptions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from django_xhtml2pdf.utils import pisa
from io import BytesIO
from django.shortcuts import HttpResponse

class GoalCreateApiView(ListCreateAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

class GoalRetrieveApiView(RetrieveUpdateAPIView):
    queryset = Goal.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return GoalSerializer
        return GoalSerializer
    permission_classes = [IsAuthenticated]
    
class GoalMetricsApiView(ListAPIView):
    
    def get(self, request, format=None):

        try:
            set_goal = Goal.objects.get(start_time__lte = now().date(), end_time__gte = now().date())
            goal_appointments = Appointment.objects.filter(goal=set_goal.pk)
            goal_metric = GoalMetrics(appointments = goal_appointments.count(), monthly_goal_porcentage = goal_appointments.count()/set_goal.apponitments_goal, assistance =goal_appointments.filter(status="DONE").count())
            goal_metric_serialied = GoalMetricsSerializer(goal_metric)
            return Response(goal_metric_serialied.data)
        except exceptions.ObjectDoesNotExist:
            return Response(
                {'message': 'No set goal'},
                status=HTTP_404_NOT_FOUND
            )
        
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)#, link_callback=fetch_resources)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def handleReport(request):
    if request.method == "GET":
        try:
            set_goal = Goal.objects.get(start_time__lte = now().date(), end_time__gte = now().date())
            goal_appointments = Appointment.objects.filter(goal=set_goal.pk)
            data = {"appointments" : goal_appointments.count(), "monthly_goal_porcentage" : goal_appointments.count()/set_goal.apponitments_goal, "assistance" : goal_appointments.filter(status="DONE").count()}
            pdf = render_to_pdf('goal/report.html',data)
            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = "report.pdf"
                content = "inline; filename='%s'" %(filename)
                content = "attachment; filename=%s" %(filename)
                response['Content-Disposition'] = content
                return response
            return HttpResponse("Not found")
        except exceptions.ObjectDoesNotExist:
            return Response(
                {'message': 'No set goal'},
                status=HTTP_404_NOT_FOUND
            )