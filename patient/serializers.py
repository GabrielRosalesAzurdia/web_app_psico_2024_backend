from rest_framework import serializers
from patient.models import Patient

class PatientSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    id = serializers.IntegerField(read_only=True)
    age = serializers.IntegerField(required=False)

    class Meta:
        model = Patient
        fields = '__all__'

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