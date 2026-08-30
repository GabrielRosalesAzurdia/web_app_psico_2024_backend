from rest_framework import serializers
from patient.models import Patient

class PatientSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    id = serializers.IntegerField(read_only=True)
    age = serializers.IntegerField(required=False)
    # external_Id no es snake_case ni camelCase puro (tiene una "I" mayúscula
    # a mitad de palabra), así que djangorestframework-camel-case nunca
    # produce/reconoce la clave correcta automáticamente en ninguna dirección.
    # El parser de entrada convierte "externalId" -> "external_id" antes de
    # que el serializer lo vea, así que el campo debe declararse con ese
    # nombre exacto (minúscula); el renderer de salida lo vuelve a camelizar
    # a "externalId" para el frontend.
    external_id = serializers.CharField(source='external_Id', required=False, allow_blank=True)

    class Meta:
        model = Patient
        # Se excluye el atributo crudo del modelo para no duplicar el dato
        # junto con el campo "external_id" declarado arriba (mismo source).
        exclude = ['external_Id']

    def validate_name(self, value):
        # RF-19: nombre unico en toda la base de datos al crear (incluye
        # pacientes desactivados, ya que is_active no borra la fila). Solo
        # aplica al crear: al editar, el paciente puede conservar su propio
        # nombre sin chocar consigo mismo.
        if self.instance is None:
            if Patient.objects.filter(name__iexact=value.strip()).exists():
                raise serializers.ValidationError(
                    "Ya existe un paciente registrado con este nombre."
                )
        return value

    def validate(self, data):
        birth_date = data.get('birth_date') or (self.instance.birth_date if self.instance else None)
        age = data.get('age') if 'age' in data else (self.instance.age if self.instance else None)
        if not birth_date and age is None:
            raise serializers.ValidationError(
                {"age": "Se requiere age o birth_date."}
            )
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.birth_date:
            data['age'] = Patient.calculate_age(instance.birth_date)
        return data