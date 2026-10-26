from dj_rest_auth import views as dra_views
from dj_rest_auth.jwt_auth import get_refresh_view

from django.urls import path

from rest_framework_simplejwt.views import TokenVerifyView

from psico_auth.views import password_reset_redirect, ProfessionalAccountCreateApiView

urlpatterns = [
    path('login/', dra_views.LoginView.as_view()),

    # Multi-tenant: no hay registro publico. El administrador del negocio
    # crea aqui cuentas de psicologos para su negocio (ver la vista).
    path('registration/', ProfessionalAccountCreateApiView.as_view()),

    path('token/verify/', TokenVerifyView.as_view()),
    path('token/refresh/', get_refresh_view().as_view()),

    path('password/reset/', dra_views.PasswordResetView.as_view()),
    path('password/reset/confirm/', dra_views.PasswordResetConfirmView.as_view()),
    path('password/reset/redirect/<uidb64>/<token>/',
         password_reset_redirect,
         name='password_reset_confirm'),
]
