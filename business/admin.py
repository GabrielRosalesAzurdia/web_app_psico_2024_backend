from django.contrib import admin
from business.models import Business

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    # Solo nosotros (superusuario) creamos y editamos negocios. Un
    # administrador de negocio nunca debe ver ni tocar los de otros.
    list_display = ('id', 'name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)


    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser