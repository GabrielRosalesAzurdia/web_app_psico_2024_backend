from django.db import migrations

# Casillas del personal escritas a mano (no se importan del modelo): una
# migracion debe dar siempre el mismo resultado aunque el codigo cambie.
CASILLAS = [
    ('view_clinical_info', 'Ver y escribir información clínica'),
    ('export_patient_file', 'Exportar expediente completo'),
    ('manage_patients', 'Crear y editar pacientes'),
    ('toggle_patient_active', 'Activar y desactivar pacientes'),
    ('reassign_patient', 'Reasignar psicólogo/a'),
    ('manage_appointments', 'Manejar citas'),
    ('view_reports', 'Ver reportes'),
    ('view_audit_log', 'Ver bitácora'),
]

# Lo que hoy puede hacer cualquier cuenta, tenga el rol que tenga.
CASILLAS_DE_TODOS = ['manage_patients', 'manage_appointments', 'view_reports']
# Lo que hoy solo puede hacer el rol profesional.
CASILLAS_DE_PROFESIONAL = ['view_clinical_info', 'export_patient_file']


def asignar_casillas(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')

    # Django crea los permisos al FINAL de migrate (señal post_migrate).
    # En una base nueva (Render) todavia no existen en este punto, asi que
    # se crean aqui. post_migrate despues los encuentra y no los duplica.
    content_type, _ = ContentType.objects.get_or_create(
        app_label='psico_auth', model='staffpermission')
    permisos = {}
    for codename, name in CASILLAS:
        permisos[codename], _ = Permission.objects.get_or_create(
            content_type=content_type, codename=codename,
            defaults={'name': name})

    # El administrador del negocio puede todo: las casillas van en su
    # grupo, asi cualquier cuenta administradora las tiene sin marcarlas.
    administrador, _ = Group.objects.get_or_create(name='administrador')
    administrador.permissions.add(*permisos.values())

    # Nadie pierde acceso: cada cuenta recibe las casillas de lo que ya
    # podia hacer con su rol. Van en la cuenta (no en el grupo) para que
    # el administrador pueda quitarlas una por una.
    for user in User.objects.filter(is_superuser=False):
        codenames = list(CASILLAS_DE_TODOS)
        if user.groups.filter(name='profesional').exists():
            codenames += CASILLAS_DE_PROFESIONAL
        user.user_permissions.add(*(permisos[c] for c in codenames))


class Migration(migrations.Migration):

    dependencies = [
        ('psico_auth', '0003_staff_permission_catalog'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(asignar_casillas, migrations.RunPython.noop),
    ]
