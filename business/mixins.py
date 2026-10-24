from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from business.permissions import HasActiveBusiness, get_user_business


class BusinessScopedMixin:
    # Multi-tenant: filtro central. Toda vista con datos de un negocio
    # hereda de aqui (ANTES que la vista de DRF) y asi:
    #  1. exige cuenta con negocio activo (si no, 403),
    #  2. solo lista y abre registros del negocio de la cuenta
    #     (un id de otro negocio da 404, como si no existiera),
    #  3. al crear, guarda el negocio de la cuenta.

    @property
    def business(self):
        business = get_user_business(self.request.user)
        if business is None:
            raise PermissionDenied(HasActiveBusiness.message)
        return business

    def get_permissions(self):
        return super().get_permissions() + [HasActiveBusiness()]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.filter(business=self.business)

    def perform_create(self, serializer):
        serializer.save(business=self.business)

    def get_business_object(self, model, **lookup):
        return get_object_or_404(model, business=self.business, **lookup)
