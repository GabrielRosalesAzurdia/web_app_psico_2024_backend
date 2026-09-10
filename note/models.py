from django.contrib.auth import get_user_model
from django.db import models


class Note(models.Model):
    # RF-24: tablon de recados cortos que ve todo el equipo. No cuelga de
    # un paciente ni de una cita, y no se edita (se borra y se escribe otra).
    author = models.ForeignKey(
        get_user_model(), related_name='notes', on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Nota de {self.author.username} ({self.created_at:%Y-%m-%d %H:%M})"
