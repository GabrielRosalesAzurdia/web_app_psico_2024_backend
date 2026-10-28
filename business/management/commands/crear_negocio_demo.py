"""Crea el negocio "Demo" con datos inventados para mostrar la app.

    python manage.py crear_negocio_demo          # lo crea si no existe
    python manage.py crear_negocio_demo --reset  # borra el Demo y lo vuelve a crear

Las fechas se calculan desde el dia en que se corre: siempre hay citas
pasadas, de hoy y futuras. Todas las cuentas usan la misma contraseña: la de
la variable de entorno DEMO_PASSWORD o, si no existe, una al azar que se
muestra una sola vez al crear el Demo (en Render, en el log del despliegue).
Solo toca datos del negocio "Demo"; los demas negocios no se modifican.
"""
import os
import random
import secrets
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from activity.models import Activity
from appointments.models import Appointment
from audit.models import AuditLog
from business.models import Business
from express_appointment.models import ExpressAppointment
from note.models import Note
from patient.models import (CaseReassignment, ConsentTextVersion, Patient,
                            PatientConsent, PatientNote)
from profiles.models import Profile
from psico_auth.permissions import set_staff_permissions

BUSINESS_NAME = "Demo"

PROFESSIONAL = ["view_clinical_info", "export_patient_file",
                "manage_patients", "manage_appointments", "view_reports"]
RECEPTION = ["manage_patients", "manage_appointments", "view_reports"]

# (usuario, correo, nombre, apellido, telefono, grupo, casillas)
STAFF = [
    ("demo.admin", "admin@tulip-demo.test", "Valeria", "Castillo", "50001001", "administrador", None),
    ("demo.laura", "laura@tulip-demo.test", "Laura", "Morales", "50001002", "profesional", PROFESSIONAL),
    ("demo.marco", "marco@tulip-demo.test", "Marco", "Herrera", "50001003", "profesional", PROFESSIONAL),
    ("demo.recepcion", "recepcion@tulip-demo.test", "Paola", "Gómez", "50001004", "recepcion", RECEPTION),
]

# (nombre, genero, nacimiento, grado, lugar, tutor, psicologo: 0=Laura 1=Marco)
PATIENTS = [
    ("Mateo Alvarado", "MASCULINO", date(2012, 4, 18), "Primero Básico", "CDO", "Rosa Alvarado", 0),
    ("Isabella Chávez", "FEMENINO", date(2010, 9, 3), "Cuarto Bachillerato", "SEMILLERO", "Carmen Chávez", 0),
    ("Santiago Juárez", "MASCULINO", date(2014, 1, 27), "Quinto Primaria", "CDO", "Pedro Juárez", 1),
    ("Camila Ortiz", "FEMENINO", date(2011, 6, 12), "Segundo Básico", "CDO", "Lucía Ortiz", 1),
    ("Diego Hernández", "MASCULINO", date(2009, 11, 30), "Quinto Bachillerato", "SEMILLERO", "Mario Hernández", 0),
    ("Valentina Ruiz", "FEMENINO", date(2013, 2, 9), "Sexto Primaria", "EXTERNAL", "Gloria Ruiz", 1),
    ("Sebastián Méndez", "MASCULINO", date(2012, 8, 21), "Primero Básico", "CDO", "Luis Méndez", 0),
    ("Mariana López", "FEMENINO", date(2010, 3, 15), "Cuarto Bachillerato", "SEMILLERO", "Elena López", 1),
    ("Emiliano Pérez", "MASCULINO", date(2011, 12, 5), "Tercero Básico", "CDO", "Jorge Pérez", 0),
    ("Sofía Ramírez", "FEMENINO", date(2013, 7, 22), "Sexto Primaria", "EXTERNAL", "Ana Ramírez", 1),
    ("Andrés Cifuentes", "MASCULINO", date(2009, 5, 2), "Quinto Bachillerato", "CDO", "Rodolfo Cifuentes", 0),
    ("Lucía Barrios", "FEMENINO", date(2012, 10, 14), "Segundo Básico", "SEMILLERO", "Marta Barrios", 1),
]
INACTIVE_PATIENT = "Andrés Cifuentes"  # para probar el filtro de inactivos

HOURS = [time(8, 0), time(8, 40), time(9, 20), time(10, 0),
         time(10, 40), time(11, 20), time(12, 0), time(12, 40)]

CLINICAL_NOTES = [
    "Se muestra más tranquilo que en la sesión anterior. Se trabajó respiración diafragmática.",
    "Refiere dificultad para dormir por preocupaciones escolares. Se acuerda registro de sueño.",
    "Buena participación. Identifica situaciones que le generan ansiedad en el aula.",
    "Se revisan acuerdos con la familia. La tutora reporta mejora en casa.",
    "Se trabaja autoestima con ejercicio de fortalezas personales.",
]
TEAM_NOTES = [
    "Recordatorio: el viernes no hay atención por capacitación.",
    "Ya llegaron los formularios de consentimiento impresos, están en recepción.",
    "Favor actualizar teléfonos de tutores que estén incompletos.",
    "Reunión de equipo el lunes a las 12:40.",
]
ACTIVITIES = [
    ("Taller de manejo de emociones", "GRUPAL", -20, "CDO"),
    ("Charla de orientación vocacional", "GRUPAL", -9, "SEMILLERO"),
    ("Dinámica de integración de grupo", "GRUPAL", -2, "CDO"),
    ("Taller para padres: límites y afecto", "GRUPAL", 3, "CDO"),
    ("Jornada de prevención del acoso escolar", "GRUPAL", 10, "SEMILLERO"),
]


class Command(BaseCommand):
    help = 'Crea el negocio "Demo" con datos inventados.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help='Borra todo lo del negocio "Demo" y lo vuelve a crear.')

    @transaction.atomic
    def handle(self, *args, **options):
        existing = Business.objects.filter(name=BUSINESS_NAME).first()
        if existing and options["reset"]:
            self._delete(existing)
            existing = None
        if existing:
            self.stdout.write(self.style.WARNING(
                'El negocio "Demo" ya existe. Usa --reset para volver a crearlo.'))
            return

        # Corre en cada deploy (build.sh): avisa en vez de fallar el build.
        taken = [email for _, email, *_ in STAFF
                 if get_user_model().objects.filter(email__iexact=email).exists()]
        if taken:
            self.stdout.write(self.style.WARNING(
                f'No se creó el Demo: ya existen cuentas con {", ".join(taken)}.'))
            return

        # La contraseña no va en el codigo: el repo lo ve mas gente que la
        # que deberia poder entrar al Demo de produccion.
        password = os.environ.get("DEMO_PASSWORD")
        from_env = bool(password)
        if not password:
            password = secrets.token_urlsafe(9)

        rng = random.Random(2026)  # mismos datos cada vez
        business = Business.objects.create(name=BUSINESS_NAME)
        admin, laura, marco, recepcion = self._create_staff(business, password)
        doctors = [laura, marco]
        patients = self._create_patients(business, admin, doctors)
        n_appts = self._create_appointments(business, patients, doctors, rng)
        self._create_extras(business, admin, laura, marco, recepcion, patients, doctors, rng)

        self.stdout.write(self.style.SUCCESS(
            f'Negocio "Demo" creado: {len(STAFF)} cuentas, {len(patients)} pacientes, '
            f'{n_appts} citas, {len(ACTIVITIES)} actividades.'))
        if from_env:
            self.stdout.write("Contraseña de todas las cuentas: la de la variable DEMO_PASSWORD.")
        else:
            self.stdout.write(f"Contraseña de todas las cuentas (guárdala, no se vuelve a mostrar): {password}")
        for _, email, first, last, _, group, _ in STAFF:
            self.stdout.write(f"  {email:30} {first} {last} ({group})")

    def _delete(self, business):
        # Orden por los PROTECT: primero lo que apunta a pacientes.
        users = get_user_model().objects.filter(profile__business=business)
        for model in (AuditLog, PatientConsent, CaseReassignment, PatientNote,
                      ExpressAppointment, Appointment, Activity, Note,
                      Patient, ConsentTextVersion):
            model.objects.filter(business=business).delete()
        users.delete()
        business.delete()
        self.stdout.write('Negocio "Demo" anterior borrado.')

    def _create_staff(self, business, password):
        User = get_user_model()
        accounts = []
        for username, email, first, last, phone, group, perms in STAFF:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first, last_name=last)
            user.groups.add(Group.objects.get(name=group))
            if perms is not None:
                set_staff_permissions(user, perms)
            # La señal de profiles ya crea el Profile vacio.
            Profile.objects.filter(user=user).update(
                business=business, phone_number=phone, completed=True)
            accounts.append(user)
        return accounts

    def _create_patients(self, business, admin, doctors):
        patients = []
        for i, (name, gender, birth, grade, place, tutor, doc) in enumerate(PATIENTS, start=1):
            patients.append(Patient.objects.create(
                business=business, name=name, gender=gender, birth_date=birth,
                age=0,  # Patient.save() la calcula desde birth_date
                grade=grade, place=place, tutor=tutor,
                phone=f"5520{i:04d}", managers_phone_number=f"5530{i:04d}",
                address="Antigua Guatemala, Sacatepéquez",
                external_Id=f"D-{i:03d}", state=True,
                is_active=name != INACTIVE_PATIENT,
                consent_signed=i % 3 != 0,
                created_by=admin, assigned_psychologist=doctors[doc]))
        return patients

    def _create_appointments(self, business, patients, doctors, rng):
        today = date.today()
        used = set()  # (psicologo, fecha, hora) para no encimar citas
        count = 0

        def free_slot(doctor, day):
            for hour in rng.sample(HOURS, len(HOURS)):
                if (doctor.id, day, hour) not in used:
                    used.add((doctor.id, day, hour))
                    return hour
            return None

        for patient, (*_, doc) in zip(patients, PATIENTS):
            doctor = doctors[doc]
            # Una cita por semana: de 6 semanas atras a 2 adelante.
            for week in range(-6, 3):
                day = today + timedelta(weeks=week, days=rng.randint(-2, 2))
                if day.weekday() >= 5:
                    day -= timedelta(days=day.weekday() - 4)  # fin de semana -> viernes
                if not patient.is_active and day >= today:
                    continue
                hour = free_slot(doctor, day)
                if hour is None:
                    continue
                if day < today:
                    status = rng.choices(["DONE", "CANCELLED", "PENDING"], [80, 12, 8])[0]
                else:
                    status = "PENDING"
                Appointment.objects.create(
                    business=business, patient=patient, doctor=doctor, date=day,
                    hour=hour, time_block=hour.strftime("%H:%M"), status=status,
                    place=patient.place if patient.place != "EXTERNAL" else "OTHER",
                    notes="Seguimiento" if week else "Sesión de evaluación")
                count += 1

        # Citas de hoy para la asistencia del dia y el dashboard.
        for patient in patients[:4]:
            doctor = patient.assigned_psychologist
            hour = free_slot(doctor, today)
            if hour:
                Appointment.objects.create(
                    business=business, patient=patient, doctor=doctor, date=today,
                    hour=hour, time_block=hour.strftime("%H:%M"), status="PENDING",
                    place="CDO", notes="Seguimiento")
                count += 1
        return count

    def _create_extras(self, business, admin, laura, marco, recepcion, patients, doctors, rng):
        today = date.today()
        for title, kind, offset, place in ACTIVITIES:
            day = today + timedelta(days=offset)
            activity = Activity.objects.create(
                business=business, title=title, activity_type=kind, place=place,
                description="Actividad de demostración.", date=day,
                start_hour=time(10, 0), end_hour=time(11, 20), time_block="10:00",
                status="DONE" if offset < 0 else "PENDING")
            activity.doctors.set(doctors if offset % 2 else [rng.choice(doctors)])
            activity.patients.set(rng.sample(patients[:10], 4))

        for i, patient in enumerate(patients[:6]):
            ExpressAppointment.objects.create(
                business=business, patient=patient, doctor=patient.assigned_psychologist,
                date=today - timedelta(days=3 + i * 4), hour=HOURS[i % len(HOURS)],
                place="CDO", notes="Atención breve sin cita previa.")

        for patient in patients[:8]:
            for content in rng.sample(CLINICAL_NOTES, 2):
                PatientNote.objects.create(
                    business=business, patient=patient,
                    author=patient.assigned_psychologist, content=content)

        CaseReassignment.objects.create(
            business=business, patient=patients[5], previous_psychologist=laura,
            new_psychologist=marco, created_by=admin,
            reason="Ajuste de carga de casos entre profesionales.")

        ConsentTextVersion.objects.create(
            business=business, version="1.0", is_current=True, created_by=admin,
            content=("Autorizo la atención psicológica del menor a mi cargo y el "
                     "registro confidencial de la información de sus sesiones."))

        for author, content in zip([admin, recepcion, laura, marco], TEAM_NOTES):
            Note.objects.create(business=business, author=author, content=content)
