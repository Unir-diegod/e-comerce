"""
Configuración de la aplicación de autenticación
"""
from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.auth'
    label = 'ecommerce_auth'  # Evitar conflicto con django.contrib.auth
    verbose_name = 'Autenticación y Autorización'
