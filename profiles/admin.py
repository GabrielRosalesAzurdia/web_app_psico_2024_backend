from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from profiles.models import Profile

User = get_user_model()


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


@admin.register(User)
class UserAdmin(BaseUserAdmin):
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
