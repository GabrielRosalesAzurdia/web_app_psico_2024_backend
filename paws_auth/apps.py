from django.apps import AppConfig


class PawsAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paws_auth'
    verbose_name = 'Auth configuration'

    def ready(self):
        import paws_auth.signals
