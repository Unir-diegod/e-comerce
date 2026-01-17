"""
Modelo de auditoría para accesos a la API
"""
from django.db import models
from django.utils import timezone
import uuid


class AuditoriaAccesoAPI(models.Model):
    """
    Registra todos los accesos a la API REST
    
    Propósito:
    - Trazabilidad de autenticación
    - Detección de accesos no autorizados
    - Análisis de uso de la API
    - Compliance y seguridad
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Usuario (null si no autenticado)
    usuario_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    
    # Información del request
    endpoint = models.CharField(max_length=200, db_index=True)
    metodo = models.CharField(max_length=10)  # GET, POST, etc.
    
    # Información del cliente
    ip_address = models.CharField(max_length=45)  # IPv4 o IPv6
    user_agent = models.CharField(max_length=200, blank=True)
    
    # Resultado
    resultado_exitoso = models.BooleanField(default=False, db_index=True)
    codigo_estado = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'auditoria_acceso_api'
        verbose_name = 'Auditoría de Acceso API'
        verbose_name_plural = 'Auditorías de Acceso API'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'usuario_id']),
            models.Index(fields=['-timestamp', 'endpoint']),
            models.Index(fields=['-timestamp', 'resultado_exitoso']),
        ]
    
    def __str__(self):
        return f"{self.metodo} {self.endpoint} - {self.timestamp}"
