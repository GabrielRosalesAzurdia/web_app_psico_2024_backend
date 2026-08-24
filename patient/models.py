from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.timezone import now


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
    managers_phone_number = models.CharField(max_length=250, default=' ')
    place = models.CharField(
        max_length=50,
        choices=PlaceTypes.choices,
        default=PlaceTypes.CDO)
    
    external_Id = models.CharField(max_length=250,blank=False, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    state = models.BooleanField()
    stateDescription =models.TextField(blank=True, default='')

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='patient'
    )

    @staticmethod
    def calculate_age(birth_date, on_date=None):
        on_date = on_date or now().date()
        years = on_date.year - birth_date.year
        had_birthday_this_year = (on_date.month, on_date.day) >= (birth_date.month, birth_date.day)
        if not had_birthday_this_year:
            years -= 1
        return years

    def save(self, *args, **kwargs):
        if self.birth_date:
            self.age = self.calculate_age(self.birth_date)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} - {self.phone} - {self.age}'