from django.db import migrations

NOMBRE_NEGOCIO = 'El Patojismo'
CORREO_ADMINISTRADORA = 'jhennyfer@elpatojismo.edu.gt'


def jenny_administradora(apps, schema_editor):
    # Jenny Peralta administra El Patojismo: es quien crea las cuentas del
    # personal y marca sus casillas. Se busca por correo; si no hay cuenta
    # con ese correo (ej. una base local), no se hace nada.
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    Business = apps.get_model('business', 'Business')
    Profile = apps.get_model('profiles', 'Profile')

    jenny = User.objects.filter(email__iexact=CORREO_ADMINISTRADORA).first()
    if jenny is None:
        return

    administrador, _ = Group.objects.get_or_create(name='administrador')
    jenny.groups.add(administrador)

    # 0003 no le asigna negocio a los superusuarios; Jenny lo necesita
    # para entrar a la app aunque lo sea.
    negocio, _ = Business.objects.get_or_create(name=NOMBRE_NEGOCIO)
    profile, _ = Profile.objects.get_or_create(user=jenny)
    if profile.business_id is None:
        profile.business = negocio
        profile.save(update_fields=['business'])


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0003_asignar_el_patojismo'),
        ('profiles', '0002_profile_business'),
        ('psico_auth', '0004_assign_staff_permissions'),
    ]

    operations = [
        migrations.RunPython(jenny_administradora, migrations.RunPython.noop),
    ]
