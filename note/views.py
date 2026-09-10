from rest_framework.generics import ListCreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, BasePermission

from note.models import Note
from note.serializers import NoteSerializer


class IsNoteAuthor(BasePermission):
    # RF-24: solo el autor de una nota puede borrarla. A diferencia de
    # filtrar el queryset por autor (que daria 404 en una nota ajena), esto
    # deja que se encuentre el objeto y responda 403 - el codigo que el
    # frontend distingue para "intento de borrar una nota ajena".
    message = 'Solo quien escribio la nota puede borrarla.'

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class NoteListCreateApiView(ListCreateAPIView):
    # GET /api/v1/note/  -> todas las notas del equipo, mas recientes primero
    #                       (Note.Meta.ordering ya lo hace, sin paginar).
    # POST /api/v1/note/ -> crea una nota; el autor sale del token, no del
    #                       body.
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    queryset = Note.objects.select_related('author').all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NoteDestroyApiView(DestroyAPIView):
    # DELETE /api/v1/note/{id}/ -> 204 sin cuerpo; 403 si no sos el autor.
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, IsNoteAuthor]
    queryset = Note.objects.all()
