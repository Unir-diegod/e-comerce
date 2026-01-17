"""
Modelo Django para Cliente
NOTA: Esta es la capa de infraestructura, separada del dominio
"""
from django.db import models
from uuid import uuid4


class ClienteModel(models.Model):
    """
    Modelo ORM para Cliente.
    Mapea la entidad de dominio a la base de datos.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    tipo_documento = models.CharField(max_length=20)
    numero_documento = models.CharField(max_length=50, unique=True, db_index=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['numero_documento']),
            models.Index(fields=['activo', '-fecha_creacion']),
        ]
    
    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido} ({self.email})"
