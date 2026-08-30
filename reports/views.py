from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncMonth, ExtractWeekDay
from io import BytesIO
import calendar
import qrcode
from PIL import Image as PILImage
from reportlab.platypus import Image as RLImage
from reportlab.lib.units import cm
from appointments.models import Appointment
from activity.models import Activity
from patient.models import Patient
from django.core import signing
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from rest_framework.response import Response

_DIAS_SEMANA = {1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles', 5: 'Jueves', 6: 'Viernes', 7: 'Sábado'}

def _apply_filters(queryset, params):
    """Aplica filtros combinables al queryset de Appointment."""
    doctor_id     = params.get('doctor_id')
    doctor_name   = params.get('doctor_name')
    grade         = params.get('grade')
    gender        = params.get('gender')
    nombre        = params.get('nombre')
    date_from     = params.get('date_from')
    date_to       = params.get('date_to')
    age_min       = params.get('age_min')
    age_max       = params.get('age_max')
    internal_code = params.get('internal_code')
    hour          = params.get('hour')

    if doctor_id:
        queryset = queryset.filter(doctor_id=doctor_id)
    if doctor_name:
        queryset = queryset.filter(
            doctor__first_name__icontains=doctor_name
        ) | queryset.filter(
            doctor__last_name__icontains=doctor_name
        )
    if grade:
        queryset = queryset.filter(patient__grade=grade)
    if gender:
        queryset = queryset.filter(patient__gender=gender)
    if nombre:
        queryset = queryset.filter(patient__name__icontains=nombre)
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)
    if age_min:
        queryset = queryset.filter(patient__age__gte=int(age_min))
    if age_max:
        queryset = queryset.filter(patient__age__lte=int(age_max))
    if internal_code:
        queryset = queryset.filter(patient__external_Id=internal_code)
    if hour:
        queryset = queryset.filter(hour=hour)

    return queryset

class MonthlyReportApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        year  = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        # Citas del mes (con los filtros combinables de RF-10: antes esta
        # vista nunca llamaba a _apply_filters, asi que ningun filtro del
        # formulario de Reportes -incluida la "Hora" recien agregada-
        # afectaba al PDF real, solo al chequeo previo de /monthly-stats/).
        appointments = _apply_filters(
            Appointment.objects.filter(date__year=year, date__month=month),
            request.query_params
        )
        total = appointments.count()

        # RF-18: actividades del mes (con su horario), para que el reporte
        # no muestre solo el horario de citas.
        activities = Activity.objects.filter(date__year=year, date__month=month)
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id:
            activities = activities.filter(doctors__id=doctor_id)
        activities = activities.distinct()
        total_activities = activities.count()

        # Asistencia
        done      = appointments.filter(status='DONE').count()
        pending   = appointments.filter(status='PENDING').count()
        cancelled = appointments.filter(status='CANCELLED').count()

        # Pacientes únicos del mes (sin nombres)
        patient_ids = appointments.values_list('patient_id', flat=True).distinct()
        patients = Patient.objects.filter(id__in=patient_ids)

        # Género
        gender_dist = patients.values('gender').annotate(count=Count('id'))

        # Edad agrupada en rangos
        age_groups = {'0-10': 0, '11-17': 0, '18-25': 0, '26-40': 0, '40+': 0}
        for birth_date, stored_age in patients.values_list('birth_date', 'age'):
            age = Patient.calculate_age(birth_date) if birth_date else stored_age
            if age <= 10:   age_groups['0-10'] += 1
            elif age <= 17: age_groups['11-17'] += 1
            elif age <= 25: age_groups['18-25'] += 1
            elif age <= 40: age_groups['26-40'] += 1
            else:           age_groups['40+'] += 1

        # Grado
        grade_dist = patients.values('grade').annotate(count=Count('id')).order_by('-count')

        # Horarios más usados (top 5)
        hour_dist = (
            appointments.values('hour')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Generar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=16, spaceAfter=4)
        sub_style   = ParagraphStyle('sub', parent=styles['Normal'], fontSize=10, textColor=colors.grey, spaceAfter=20)

        month_name = calendar.month_name[month]
        elements.append(Paragraph("Daniel Padnos Wellness Center", title_style))
        elements.append(Paragraph(f"Reporte Mensual — {month_name} {year}", title_style))
        elements.append(Paragraph(
            f"Generado: {today}  |  Total de citas: {total}  |  Total de actividades: {total_activities}",
            sub_style
        ))

        table_style = TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 11),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f2f2')]),
            ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 1), (-1, -1), 10),
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])

        def pct(n):
            return f"{round(n / total * 100)}%" if total else "0%"

        def ppct(n):
            total_p = patients.count()
            return f"{round(n / total_p * 100)}%" if total_p else "0%"

        # Sección 1: Asistencia
        elements.append(Paragraph("1. Estadísticas de Asistencia", styles['Heading2']))
        elements.append(Spacer(1, 6))
        att_data = [
            ['Estado',       'Cantidad', 'Porcentaje'],
            ['Cumplida',     done,       pct(done)],
            ['Pendiente',    pending,    pct(pending)],
            ['No cumplida',  cancelled,  pct(cancelled)],
            ['Total',        total,      '100%'],
        ]
        t = Table(att_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        t.setStyle(table_style)
        elements.append(t)
        elements.append(Spacer(1, 20))

        # Sección 2: Género
        elements.append(Paragraph("2. Distribución por Género", styles['Heading2']))
        elements.append(Spacer(1, 6))
        gender_data = [['Género', 'Cantidad', 'Porcentaje']]
        for g in gender_dist:
            gender_data.append([g['gender'], g['count'], ppct(g['count'])])
        t = Table(gender_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        t.setStyle(table_style)
        elements.append(t)
        elements.append(Spacer(1, 20))

        # Sección 3: Edad
        elements.append(Paragraph("3. Distribución por Edad", styles['Heading2']))
        elements.append(Spacer(1, 6))
        age_data = [['Rango de Edad', 'Cantidad', 'Porcentaje']]
        for rango, count in age_groups.items():
            age_data.append([rango, count, ppct(count)])
        t = Table(age_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        t.setStyle(table_style)
        elements.append(t)
        elements.append(Spacer(1, 20))

        # Sección 4: Grado
        grade_data = [['Grado', 'Cantidad']]
        for g in grade_dist:
            grade_data.append([g['grade'] or 'Sin grado', g['count']])
        t4 = Table(grade_data, colWidths=[3*inch, 1.5*inch])
        t4.setStyle(table_style)
        elements.append(KeepTogether([
            Paragraph("4. Distribución por Grado", styles['Heading2']),
            Spacer(1, 6),
            t4,
        ]))
        elements.append(Spacer(1, 20))

        # Sección 5: Horarios
        elements.append(Paragraph("5. Horarios Más Utilizados", styles['Heading2']))
        elements.append(Spacer(1, 6))
        hour_data = [['Hora', 'Cantidad de Citas']]
        for h in hour_dist:
            hour_data.append([str(h['hour']), h['count']])
        t = Table(hour_data, colWidths=[3*inch, 1.5*inch])
        t.setStyle(table_style)
        elements.append(t)

        # Sección 6: Lista de citas anonimizadas
        patient_map = {}
        counter = 1
        for pid in patient_ids:
            patient_map[pid] = f"Paciente {counter}"
            counter += 1

        appt_list_data = [['Identificador', 'Fecha', 'Hora', 'Estado']]
        for appt in appointments.order_by('date', 'hour'):
            appt_list_data.append([
                patient_map.get(appt.patient_id, '-'),
                str(appt.date),
                str(appt.hour),
                appt.status,
            ])
        t6 = Table(appt_list_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        t6.setStyle(table_style)
        elements.append(KeepTogether([
            Paragraph("6. Citas del mes anonimizadas", styles['Heading2']),
            Spacer(1, 6),
            t6,
        ]))
        elements.append(Spacer(1, 20))

        # Sección 7: Horarios de actividades del mes (RF-18)
        activity_data = [['Título', 'Fecha', 'Hora inicio', 'Hora fin', 'Lugar']]
        for act in activities.order_by('date', 'start_hour'):
            activity_data.append([
                act.title,
                str(act.date),
                str(act.start_hour),
                str(act.end_hour) if act.end_hour else '-',
                act.place,
            ])
        if len(activity_data) == 1:
            activity_data.append(['Sin actividades registradas este mes.', '', '', '', ''])
        t7 = Table(activity_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.1*inch])
        t7.setStyle(table_style)
        elements.append(KeepTogether([
            Paragraph("7. Horarios de Actividades del Mes", styles['Heading2']),
            Spacer(1, 6),
            t7,
        ]))
        elements.append(Spacer(1, 20))



        #Token firmado con datos del reporte
        
        token_data ={
            'year':year,
            'month':month,
            'total': total,
            'generated': str(today),
        }
        token = signing.dumps(token_data)
        verify_url = f"{request.scheme}://{request.get_host()}/api/v1/reports/verify/{token}/"
        qr_content = verify_url
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color ="black", back_color ="white")
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        elements.append(Spacer(1, 30))
        elements.append(RLImage(qr_buffer, width= 1.5*inch, height=1.5*inch))
        elements.append(Spacer(1,6))
        elements.append(Paragraph(
            f"Documento generado automaticamente por el sistema.<br/>"
            f"Daniel Padnos Wellness Center -{today}",
            ParagraphStyle('firma', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        ))
        
        doc.build(elements)
        buffer.seek(0)

        filename = f"reporte_{year}_{str(month).zfill(2)}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
class ReportVerifyApiView(APIView):
    permission_classes= [] #publico
    
    def get(self, request, token):
        try:
            data = signing.loads(token, max_age=60*60*24*365)
            return Response({
                'valid':True,
                'issued_by': 'Daniel Padnos Wellness Center',
                'year':data['year'],
                'month':data['month'],
                'total_appoinments':data['total'],
                'generated': data["generated"],
                
            })
        except signing.BadSignature:
            return Response({
                'valid': False,
                'message': 'Documento no valido o fue alterado',

            },status=400
            )

class MonthlyStatsApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = _apply_filters(Appointment.objects.all(), request.query_params)

        total     = queryset.count()
        done      = queryset.filter(status='DONE').count()
        pending   = queryset.filter(status='PENDING').count()
        cancelled = queryset.filter(status='CANCELLED').count()

        # RF-18: el reporte tambien incluye actividades, asi que el chequeo de
        # "hay algo que exportar" no debe depender solo de que existan citas.
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        doctor_id = request.query_params.get('doctor_id')
        activities_qs = Activity.objects.all()
        if date_from:
            activities_qs = activities_qs.filter(date__gte=date_from)
        if date_to:
            activities_qs = activities_qs.filter(date__lte=date_to)
        if doctor_id:
            activities_qs = activities_qs.filter(doctors__id=doctor_id)
        total_activities = activities_qs.distinct().count()

        # Pacientes unicos que aparecen en las citas filtradas
        patient_ids = queryset.values_list('patient_id', flat=True).distinct()
        patients    = Patient.objects.filter(id__in=patient_ids)

        gender_dist = list(patients.values('gender').annotate(count=Count('id')).order_by('-count'))
        grade_dist  = list(patients.values('grade').annotate(count=Count('id')).order_by('-count'))

        age_groups = {'0-10': 0, '11-17': 0, '18-25': 0, '26-40': 0, '40+': 0}
        for birth_date, stored_age in patients.values_list('birth_date', 'age'):
            age = Patient.calculate_age(birth_date) if birth_date else stored_age
            if age <= 10:   age_groups['0-10'] += 1
            elif age <= 17: age_groups['11-17'] += 1
            elif age <= 25: age_groups['18-25'] += 1
            elif age <= 40: age_groups['26-40'] += 1
            else:           age_groups['40+'] += 1

        monthly_breakdown = [
            {'month': entry['month'].strftime('%Y-%m'), 'total': entry['total']}
            for entry in (
                queryset
                .annotate(month=TruncMonth('date'))
                .values('month')
                .annotate(total=Count('id'))
                .order_by('month')
            )
        ]

        return Response({
            'total_appointments': total,
            'total_activities': total_activities,
            'by_status': {'DONE': done, 'PENDING': pending, 'CANCELLED': cancelled},
            'unique_patients': patients.count(),
            'by_gender': gender_dist,
            'by_age_group': age_groups,
            'by_grade': grade_dist,
            'monthly_breakdown': monthly_breakdown,
        })


class ScheduleStatsApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = _apply_filters(Appointment.objects.all(), request.query_params)

        # Distribucion por hora
        by_hour = list(
            queryset.values('hour').annotate(count=Count('id')).order_by('hour')
        )

        # Distribucion por dia de semana (1=Domingo ... 7=Sabado en Django/SQL)
        by_day = [
            {'day': _DIAS_SEMANA.get(e['weekday'], str(e['weekday'])), 'count': e['count']}
            for e in (
                queryset
                .annotate(weekday=ExtractWeekDay('date'))
                .values('weekday')
                .annotate(count=Count('id'))
                .order_by('weekday')
            )
        ]

        # Distribucion por doctor
        by_doctor = [
            {
                'doctor_id': d['doctor_id'],
                'doctor': f"{d['doctor__first_name']} {d['doctor__last_name']}".strip(),
                'count': d['count'],
            }
            for d in (
                queryset
                .values('doctor_id', 'doctor__first_name', 'doctor__last_name')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
        ]

        # Distribucion por lugar
        by_place = list(
            queryset.values('place').annotate(count=Count('id')).order_by('-count')
        )

        return Response({
            'total_appointments': queryset.count(),
            'by_hour': by_hour,
            'by_day_of_week': by_day,
            'by_doctor': by_doctor,
            'by_place': by_place,
        })