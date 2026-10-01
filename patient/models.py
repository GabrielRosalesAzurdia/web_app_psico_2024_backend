from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.timezone import localdate
from django.db.models.functions import Lower
from web_app_psico_2024_backend.encrypted_fields import EncryptedBinaryField, EncryptedTextField

class Patient(models.Model):

    class PlaceTypes(models.TextChoices):
        CDO = 'CDO', _('CDO')
        SEMILLERO = 'SEMILLERO', _('Semillero')
        EXTERNAL = 'EXTERNAL', _('Externo')
    class GenderTypes(models.TextChoices):
        MALE = 'MASCULINO', _('masculino')
        FEMALE = 'FEMENINO',_('femenino')
        OTHER = 'OTRO',_('otro')
    name = models.TextField()
    phone = models.CharField(max_length=250, blank=True, default='')
    age = models.IntegerField()
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=50,
        choices=GenderTypes.choices,
        default=GenderTypes.OTHER
    )
    
    grade = models.CharField(max_length=250, blank=True, default='')
    address = models.CharField(max_length=250, default='')
    tutor = models.CharField(max_length=250,default='')
    managers_phone_number = models.CharField(max_length=250, blank=True, default=' ')
    place = models.CharField(
        max_length=50,
        choices=PlaceTypes.choices,
        default=PlaceTypes.CDO)
    
    external_Id = models.CharField(max_length=250,blank=False, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    state = models.BooleanField()
    stateDescription = EncryptedTextField(blank=True, default='')

    # RF-19: distinto de "state" (que es el estado de asistencia
    # Activo/Inasistencia/Pendiente, ver PatientForm.tsx). is_active
    # controla si el paciente fue "eliminado" -> en vez de borrar la fila
    # (y perder el historial de citas asociadas), se desactiva.
    is_active = models.BooleanField(default=True)

    # RF-33: el consentimiento firmado se resguarda en fisico; aqui solo se
    # marca si ya se tiene. Se edita con el resto del paciente y se marca
    # solo al cargar el escaneado (PatientConsent), que es opcional.
    consent_signed = models.BooleanField(default=False)

    # RNF-07: fecha de la ultima cita atendida (status DONE), para aplicar
    # despues la politica de conservacion del expediente. No se edita a
    # mano: la recalcula Appointment.save() con refresh_last_attention_date.
    # Vacia si el paciente nunca ha sido atendido.
    last_attention_date = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='patient'
    )

    # RF-31: psicologo *responsable* del paciente, distinto del doctor de
    # cada cita individual (RF-20). No se edita directo (ver
    # PatientSerializer): solo cambia via CaseReassignment, para que el
    # traspaso siempre quede con motivo y no toque citas pasadas (RF-30).
    assigned_psychologist = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='assigned_patients',
    )

    class Meta:
        constraints = [
            # RF-19: el nombre del paciente es unico en toda la tabla, sin
            # importar mayus/minus ("Juan" y "juan" chocan). Lower('name')
            # crea un indice unico sobre el nombre convertido a minusculas.
            # Incluye a los pacientes desactivados (is_active=False), porque
            # su fila sigue existiendo en la BD (soft delete).
            models.UniqueConstraint(
                Lower('name'),
                name='unique_patient_name_ci',
            ),
        ]

    @staticmethod
    def calculate_age(birth_date, on_date=None):
        on_date = on_date or localdate()
        years = on_date.year - birth_date.year
        had_birthday_this_year = (on_date.month, on_date.day) >= (birth_date.month, birth_date.day)
        if not had_birthday_this_year:
            years -= 1
        return years

    def save(self, *args, **kwargs):
        if self.birth_date:
            self.age = self.calculate_age(self.birth_date)
        super().save(*args, **kwargs)

    def refresh_last_attention_date(self):
        # RNF-07: recalcula la fecha de ultima atencion desde las citas.
        # Se recalcula siempre (en vez de solo copiar la fecha de la cita
        # que se acaba de guardar) para que tambien quede bien si una cita
        # deja de estar atendida, se desactiva o se registra con fecha vieja.
        last = self.appointment.filter(
            status='DONE', is_active=True,
        ).aggregate(last=models.Max('date'))['last']
        # update() y no save(): solo toca esta columna, sin pasar por
        # Patient.save() (recalculo de edad).
        Patient.objects.filter(pk=self.pk).update(last_attention_date=last)
        self.last_attention_date = last

    def __str__(self):
        return f'{self.name} - {self.phone} - {self.age}'


class PatientNote(models.Model):
    # RF-26: notas y observaciones generales del expediente clinico, no
    # atadas a una cita puntual (a diferencia del campo `notes` de
    # Appointment, que son las observaciones de ESA cita). Tampoco es RF-24
    # (el tablon compartido tipo post-it entre psicologos): esto es
    # contenido clinico del paciente, y cae bajo RNF-02 (solo profesional
    # autenticado, igual que el resto de la API).
    # Acumulativas y no se sobrescriben: no hay UPDATE, solo se agregan.
    # Por eso no hay campo "updated_at" ni endpoint de edicion.
    patient = models.ForeignKey(
        Patient, related_name='clinical_notes', on_delete=models.CASCADE)
    author = models.ForeignKey(
        get_user_model(), related_name='patient_notes', on_delete=models.CASCADE)
    content = EncryptedTextField()
    edited_by = models.ForeignKey(
        get_user_model(), null=True, blank=True,
        related_name='edited_patient_notes', on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    annulled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        # Orden cronologico inverso (la mas reciente primero), como pide
        # el criterio de aceptacion.
        ordering = ['-created_at']

    def __str__(self):
        return f'Nota de {self.patient.name} por {self.author.username} ({self.created_at:%Y-%m-%d %H:%M})'

class CaseReassignment(models.Model):
    patient = models.ForeignKey(
        Patient, related_name='reassignments', on_delete=models.CASCADE)
    previous_psychologist = models.ForeignKey(
        get_user_model(), null= True, blank=True,
        related_name='+', on_delete=models.PROTECT)
    new_psychologist = models.ForeignKey(
        get_user_model(), related_name='+', on_delete=models.PROTECT)
    reason = EncryptedTextField()
    created_by = models.ForeignKey(
        get_user_model(),related_name='+', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
                    ordering = ['-created_at']

    def __str__(self):
        return f'{self.patient.name}: {self.previous_psychologist}->{self.new_psychologist}'


class ConsentTextVersion(models.Model):
    # RF-33: el texto del consentimiento informado se versiona. Una version
    # publicada no se edita: si cambia el texto se crea una version nueva,
    # asi cada paciente queda ligado al texto exacto que se le entrego.
    version = models.CharField(max_length=20, unique=True)
    content = models.TextField()
    is_current = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        get_user_model(), related_name='+', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Consentimiento informado v{self.version}'


class PatientConsent(models.Model):
    # RF-33: escaneado opcional del consentimiento firmado de UN paciente,
    # ligado a la version del texto. Si el paciente firmo o no lo dice
    # Patient.consent_signed, no este modelo.
    patient = models.ForeignKey(
        Patient, related_name='consents', on_delete=models.CASCADE)
    text_version = models.ForeignKey(
        ConsentTextVersion, related_name='patient_consents', on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        get_user_model(), related_name='+', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        get_user_model(), null=True, blank=True, related_name='+', on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    # RF-33 (B-3): escaneado del consentimiento firmado (PDF o imagen).
    # Opcional: el original se resguarda en fisico. Se guarda en la BD y no
    # en media/ porque el disco de Render se borra en cada deploy, y solo se
    # entrega por un endpoint autenticado, nunca con un enlace publico.
    file_data = EncryptedBinaryField(null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, default='')
    file_content_type = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.patient.name} - v{self.text_version.version} ({self.file_name})'
