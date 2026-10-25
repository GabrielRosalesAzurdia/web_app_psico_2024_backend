from rest_framework.relations import ManyRelatedField, RelatedField

from business.permissions import get_user_business


class BusinessScopedSerializerMixin:
    # Multi-tenant: limita los campos relacionados (FK / M2M) al negocio
    # de la cuenta que hace la peticion. Un ID de otro negocio falla
    # igual que un ID que no existe.
    #
    # Cada serializer declara: {campo: lookup hacia Business}
    #   'patient': 'business'            (Patient tiene business)
    #   'doctor':  'profile__business'   (User -> Profile -> business)
    business_scoped_fields = {}

    def get_business(self):
        request = self.context.get('request')
        if request is None:
            return None
        return get_user_business(request.user)

    def get_fields(self):
        fields = super().get_fields()
        business = self.get_business()

        for name, lookup in self.business_scoped_fields.items():
            field = fields.get(name)
            if field is None or field.read_only:
                continue
            # many=True envuelve el campo real en child_relation.
            if isinstance(field, ManyRelatedField):
                field = field.child_relation
            if not isinstance(field, RelatedField):
                continue  # ej. serializer anidado de solo lectura

            if business is None:
                # Sin negocio (o sin request en el context): no se acepta
                # ningun ID. Mejor fallar cerrado que dejar pasar todo.
                field.queryset = field.queryset.none()
            else:
                field.queryset = field.queryset.filter(**{lookup: business})
        return fields
