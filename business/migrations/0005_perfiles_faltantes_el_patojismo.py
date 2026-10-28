from django.db import migrations

NOMBRE_NEGOCIO = 'El Patojismo'


def crear_perfiles_faltantes(apps, schema_editor):
    # 0003 asigna El Patojismo a los Profile que ya existen. Una cuenta vieja
    # sin fila de Profile (creada antes de la señal de profiles, o desde una
    # migracion, donde las señales no corren) quedaba sin negocio y recibia
    # 403 en toda la API. Aqui se le crea su Profile en El Patojismo.
    # Igual que en 0003, los superusuarios se quedan sin negocio.
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('profiles', 'Profile')
    Business = apps.get_model('business', 'Business')

    sin_perfil = User.objects.filter(profile__isnull=True, is_superuser=False)
    if not sin_perfil.exists():
        return

    negocio, _ = Business.objects.get_or_create(name=NOMBRE_NEGOCIO)
    Profile.objects.bulk_create(
        [Profile(user=user, business=negocio) for user in sin_perfil])


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0004_jenny_administradora'),
    ]

    operations = [
        migrations.RunPython(crear_perfiles_faltantes, migrations.RunPython.noop),
    ]
