"""
Django App Configuration
"""
from django.apps import AppConfig


class DjangoPersistenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.persistence.django'
    label = 'ecommerce_persistence'
    verbose_name = 'E-Commerce Persistence'
