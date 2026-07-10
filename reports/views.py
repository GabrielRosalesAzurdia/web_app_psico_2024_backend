from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils.timezone import now
from django.db.models import Count
from io import BytesIO
import calendar
import qrcode
from PIL import Image as PILImage
from reportlab.platypus import Image as RLImage
from reportlab.lib.units import cm
from appointments.models import Appointment
from patient.models import Patient
from django.core import signing
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from rest_framework.response import Response

class MonthlyReportApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        year  = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        # Citas del mes
        appointments = Appointment.objects.filter(date__year=year, date__month=month)
        total = appointments.count()

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
        for age in patients.values_list('age', flat=True):
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
        elements.append(Paragraph(f"Generado: {today}  |  Total de citas: {total}", sub_style))

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