from django.db import models


class Business(models.Model):
    # Multi-tenant: cada organizacion usa Tulip, todos los datos
    # (pacientes, citas, actividades, notas...) pertenecen a un Business.
    name = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'negocio'
        verbose_name_plural = 'negocios'

    def __str__(self):
        return self.name


class BusinessOwnedModel(models.Model):
    # Multi-tenant: todo modelo con datos de un negocio hereda de aqui.
    # El negocio se asigna en el servidor desde la cuenta del usuario,
    # nunca desde un formulario o peticion (por eso editable=False).
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
        # TEMPORAL: null=True solo para poder migrar los datos existentes.
        # Despues de asignarlos a El Patojismo se quita.
        null=True,
    )

    class Meta:
        abstract = True
