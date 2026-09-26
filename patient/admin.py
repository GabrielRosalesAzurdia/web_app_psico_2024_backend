from django.contrib import admin

from patient.models import Patient, ConsentTextVersion, PatientConsent, PatientNote, CaseReassignment


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    ...
    

@admin.register(ConsentTextVersion)
class ConsentTextVersionAdmin(admin.ModelAdmin):
    ...
    

@admin.register(PatientConsent)
class PatientConsentAdmin(admin.ModelAdmin):
    ...
    

@admin.register(PatientNote)
class PatientNoteAdmin(admin.ModelAdmin):
    ...
    

@admin.register(CaseReassignment)
class CaseReassignmentAdmin(admin.ModelAdmin):
    ...
    
