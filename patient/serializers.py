from rest_framework import serializers
from patient.models import Patient

class PatientSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'