from rest_framework import serializers

from note.models import Note


class NoteSerializer(serializers.ModelSerializer):
    # Igual que DoctorSerializer en appointments: nombre para mostrar ya
    # resuelto, el frontend no arma nombres a partir de first/last name.
    author_name = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'content', 'author_name', 'created_at', 'is_mine']
        read_only_fields = ['id', 'author_name', 'created_at', 'is_mine']

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def get_is_mine(self, obj):
        # Calculado en el backend a proposito (ver CONTRATO_API_NOTAS.md):
        # el frontend no guarda el id de usuario en sesion, y asi el mismo
        # criterio decide isMine y quien puede borrar.
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.author_id == request.user.id)
