from django.db import migrations

# RNF-02 (B-1): los nombres van escritos a mano y no con GroupName porque
# una migracion debe dar siempre el mismo resultado aunque el codigo cambie.
ROLES = ['profesional', 'recepcion', 'administrador']


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')

    for name in ROLES:
        Group.objects.get_or_create(name=name)

    # Hoy todos los usuarios ven todo. Pasan a profesional para que nadie
    # pierda acceso cuando se validen los permisos (RNF-02 B-2).
    professional = Group.objects.get(name='profesional')
    for user in User.objects.all():
        user.groups.add(professional)

    # "client" era el unico grupo y queda reemplazado por los roles.
    Group.objects.filter(name='client').delete()


def remove_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')

    client, _ = Group.objects.get_or_create(name='client')
    for user in User.objects.all():
        user.groups.add(client)
    Group.objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_roles, remove_roles),
    ]
