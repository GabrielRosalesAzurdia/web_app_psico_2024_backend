from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from profiles.models import Profile
from psico_auth.enums import GroupName
from psico_auth.models import StaffPermission
from psico_auth.permissions import (
    STAFF_PERMISSION_CODENAMES,
    is_business_administrator,
    set_staff_permissions,
)

User = get_user_model()


class StaffUserChangeForm(UserChangeForm):
    # Casillas del personal en la pantalla del usuario: las mismas 8 que
    # marca el administrador del negocio en el frontend, en lugar de la
    # lista generica "User permissions" de Django (cientos de permisos).
    staff_permissions = forms.MultipleChoiceField(
        label='Permisos',
        choices=StaffPermission._meta.permissions,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['staff_permissions']
        user = self.instance
        if is_business_administrator(user):
            # Sus casillas vienen del grupo administrador: todas, siempre.
            field.initial = STAFF_PERMISSION_CODENAMES
            field.disabled = True
            field.help_text = ('Tiene todos los permisos por ser administrador. '
                               'Para limitarlos, quitale el grupo administrador.')
        else:
            field.initial = list(user.user_permissions.filter(
                content_type__app_label='psico_auth',
            ).values_list('codename', flat=True))
            field.help_text = ('"Ver y escribir informacion clinica" da acceso '
                               'a datos confidenciales de los pacientes.')


class ProfileInline(admin.StackedInline):
    # Multi-tenant: negocio y telefono de la cuenta en la misma pantalla
    # del usuario. El rol se elige arriba, en "Groups".
    model = Profile
    fields = ['business', 'phone_number', 'image', 'completed']
    
    can_delete = False
    verbose_name = 'perfil y negocio'
    verbose_name_plural = 'perfil y negocio'


# Reemplazamos la pantalla de usuarios que trae Django por una con el
# inline del perfil.
admin.site.unregister(User)


# Pantalla de EDITAR usuario: la de Django, pero sin "User permissions"
# (la reemplaza "Permisos del personal") y con las casillas al final.
# Crear usuario sigue usando add_fieldsets: las casillas aparecen despues,
# al editar, igual que "Perfil y negocio".
USER_FIELDSETS = tuple(
    (name, {**opts, 'fields': tuple(f for f in opts['fields'] if f != 'user_permissions')})
    for name, opts in BaseUserAdmin.fieldsets
) + (
    ('Permisos del personal', {
        'fields': ('staff_permissions',),
        'description': 'Lo que esta cuenta puede hacer en la app de su negocio.',
    }),
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = StaffUserChangeForm
    fieldsets = USER_FIELDSETS
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'business', 'is_staff']
    list_filter = ['profile__business', 'groups', 'is_staff', 'is_active']
    list_select_related = ['profile__business']

    def get_inline_instances(self, request, obj=None):
        # Al CREAR el usuario, profiles/signals.py ya crea su Profile vacio;
        # si el inline tambien lo creara habria dos (IntegrityError). Por
        # eso el inline solo aparece al EDITAR, y Django lleva ahi justo
        # despues de crear la cuenta.
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Rol: solo importa el grupo administrador. "profesional" y
        # "recepcion" ya no dan permisos (ahora son las casillas), asi que
        # no se ofrecen para que nadie crea que sirven de algo.
        if db_field.name == 'groups':
            kwargs['queryset'] = Group.objects.filter(
                name=GroupName.ADMINISTRATOR.value)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_related(self, request, form, formsets, change):
        # Aqui y no en save_model: Django guarda grupos y demas relaciones
        # en save_related, y hay que ver el grupo ya actualizado.
        super().save_related(request, form, formsets, change)
        field = form.fields.get('staff_permissions')
        user = form.instance
        if field is None or field.disabled or is_business_administrator(user):
            return
        set_staff_permissions(user, form.cleaned_data.get('staff_permissions', []))

    @admin.display(ordering='profile__business__name', description='negocio')
    def business(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.business if profile and profile.business else '-'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_select_related = ['user', 'business']
    list_display = [
        'pk',
        'email',
        'username',
        'fullname',
        'phone_number',
        'business',
    ]
    list_filter = ['business']

    @admin.display(ordering='user__email', description=_('Email'))
    def email(self, obj: Profile):
        html = f"""
            <a href="/admin/profiles/profile/{obj.pk}/change/">
                {obj.user.email}
            <a/>
        """

        return format_html(html)

    @admin.display(ordering='user__username', description=_('Username'))
    def username(self, obj: Profile):
        return obj.user.username

    @admin.display(ordering='user__first_name', description=_('Fullname'))
    def fullname(self, obj: Profile):
        return f'{obj.user.first_name} {obj.user.last_name}'
