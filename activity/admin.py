from django.contrib import admin

from activity.models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    ...
