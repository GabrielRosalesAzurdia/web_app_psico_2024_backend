from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_select_related = ['user']
    list_display = [
        'pk',
        'email',
        'username',
        'fullname',
        'phone_number',
    ]

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
