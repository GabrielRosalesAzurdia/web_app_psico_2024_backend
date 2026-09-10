from django.urls import path

from note.views import NoteListCreateApiView, NoteDestroyApiView

urlpatterns = [
    path('', NoteListCreateApiView.as_view(), name='note-list-create'),
    path('<int:pk>/', NoteDestroyApiView.as_view(), name='note-destroy'),
]
