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


class ProductoModel(models.Model):
    """
    Modelo ORM para Producto.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True, db_index=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    moneda_precio = models.CharField(max_length=3)
    monto_precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nombre']),
            models.Index(fields=['activo', 'stock_actual']),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.codigo})"


class OrdenModel(models.Model):
    """
    Modelo ORM para Orden.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cliente = models.ForeignKey(ClienteModel, on_delete=models.PROTECT, related_name='ordenes')
    estado = models.CharField(max_length=20)
    total_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_moneda = models.CharField(max_length=3, default='USD')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ordenes'
        verbose_name = 'Orden'
        verbose_name_plural = 'Ordenes'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
        ]

    def __str__(self) -> str:
        return f"Orden {self.id} - {self.cliente}"


class LineaOrdenModel(models.Model):
    """
    Modelo ORM para Línea de Orden.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    orden = models.ForeignKey(OrdenModel, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey(ProductoModel, on_delete=models.PROTECT, related_name='lineas_orden')
    cantidad = models.IntegerField()
    precio_unitario_monto = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario_moneda = models.CharField(max_length=3)
    subtotal_monto = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal_moneda = models.CharField(max_length=3)

    class Meta:
        db_table = 'lineas_orden'
        verbose_name = 'Línea de Orden'
        verbose_name_plural = 'Líneas de Orden'
        ordering = ['orden', 'producto']

    def __str__(self) -> str:
        return f"{self.cantidad}x {self.producto} en Orden {self.orden_id}"


class RegistroAuditoriaModel(models.Model):
    """
    Modelo ORM para Registro de Auditoría.
    
    Responsabilidades:
    - Trazabilidad inmutable de operaciones críticas
    - Soporte para compliance y forense
    - No se actualiza ni elimina después de crear
    """
    id = models.UUIDField(primary_key=True, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario_id = models.UUIDField(null=True, blank=True)
    entidad_tipo = models.CharField(max_length=50, db_index=True)
    entidad_id = models.UUIDField(db_index=True)
    accion = models.CharField(max_length=20, db_index=True)
    datos_previos = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    resultado = models.CharField(max_length=20)
    mensaje = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'auditoria_registros'
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entidad_tipo', 'entidad_id']),
            models.Index(fields=['accion', 'timestamp']),
            models.Index(fields=['resultado', 'timestamp']),
            models.Index(fields=['usuario_id', 'timestamp']),
        ]
        # Protección contra modificaciones accidentales
        permissions = [
            ('view_auditoria', 'Can view audit logs'),
        ]

    def __str__(self) -> str:
        return f"Auditoría {self.accion} - {self.entidad_tipo} {self.entidad_id} [{self.resultado}]"
    
    def save(self, *args, **kwargs):
        """Solo permite INSERT, no UPDATE"""
        if self.pk and RegistroAuditoriaModel.objects.filter(pk=self.pk).exists():
            raise ValueError("Los registros de auditoría son inmutables y no pueden actualizarse")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Bloquea eliminación de registros de auditoría"""
        raise ValueError("Los registros de auditoría no pueden eliminarse")


class AuditoriaAccesoAPI(models.Model):
    """
    Registra todos los accesos a la API REST
    
    Propósito:
    - Trazabilidad de autenticación
    - Detección de accesos no autorizados
    - Análisis de uso de la API
    - Compliance y seguridad
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
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
