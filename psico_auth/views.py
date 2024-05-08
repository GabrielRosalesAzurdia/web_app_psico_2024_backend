from django.conf import settings
from django.shortcuts import redirect

def password_reset_redirect(request, uidb64, token):
    return redirect(f'{settings.FRONTEND_URL}/accounts/password/reset/confirm/{uidb64}/{token}')
