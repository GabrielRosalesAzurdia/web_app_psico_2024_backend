from django.contrib import admin

from note.models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'content')
    list_filter = ('author',)
    ordering = ('-created_at',)
