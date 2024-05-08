from django.apps import AppConfig


class PsicoAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'psico_auth'
    verbose_name = 'Auth configuration'

    def ready(self):
        import psico_auth.signals
