from django.contrib import admin

from express_appointment.models import ExpressAppointment


@admin.register(ExpressAppointment)
class ExpressAppointmentAdmin(admin.ModelAdmin):
    ...
