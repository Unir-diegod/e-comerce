"""
Modelo de Usuario con Roles para Autenticación y Autorización

IMPORTANTE:
- Este modelo NO es parte del dominio de negocio
- Es infraestructura para seguridad de la API
- NO confundir con Cliente del dominio
- Los clientes del negocio siguen siendo entidades de dominio
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid


class RolUsuario(models.TextChoices):
    """
    Roles básicos del sistema para control de acceso
    
    ADMIN: Acceso total - crear, modificar, eliminar
    OPERADOR: Operaciones de negocio - crear, modificar
    LECTURA: Solo lectura - consultar
    """
    ADMIN = 'ADMIN', 'Administrador'
    OPERADOR = 'OPERADOR', 'Operador'
    LECTURA = 'LECTURA', 'Solo Lectura'


class UsuarioManager(BaseUserManager):
    """Manager personalizado para Usuario"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crea un usuario normal"""
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crea un superusuario (ADMIN)"""
        extra_fields.setdefault('rol', RolUsuario.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Usuario del sistema para autenticación
    
    NOTA: Este NO es el Cliente del dominio.
    - Usuario: Autenticación y autorización (infraestructura)
    - Cliente: Entidad de negocio (dominio)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    nombre = models.CharField(max_length=150)
    rol = models.CharField(
        max_length=20,
        choices=RolUsuario.choices,
        default=RolUsuario.LECTURA
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_ultima_login = models.DateTimeField(null=True, blank=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']
    
    class Meta:
        db_table = 'auth_usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.email} ({self.get_rol_display()})"
    
    @property
    def es_admin(self) -> bool:
        """Verifica si el usuario es administrador"""
        return self.rol == RolUsuario.ADMIN
    
    @property
    def es_operador(self) -> bool:
        """Verifica si el usuario es operador"""
        return self.rol == RolUsuario.OPERADOR
    
    @property
    def es_lectura(self) -> bool:
        """Verifica si el usuario solo tiene permisos de lectura"""
        return self.rol == RolUsuario.LECTURA
    
    @property
    def puede_escribir(self) -> bool:
        """Verifica si el usuario puede crear/modificar"""
        return self.rol in [RolUsuario.ADMIN, RolUsuario.OPERADOR]
    
    @property
    def puede_eliminar(self) -> bool:
        """Verifica si el usuario puede eliminar"""
        return self.rol == RolUsuario.ADMIN
