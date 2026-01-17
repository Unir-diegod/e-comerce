# 🔧 Documentación Técnica - Sistema E-Commerce

## 🏗️ Arquitectura Detallada

### Principios Arquitectónicos

Este sistema implementa **Clean Architecture** con las siguientes capas concéntricas:

```
┌──────────────────────────────────────────┐
│  Interfaces (API REST / FastAPI)        │ ← Adaptadores de entrada
├──────────────────────────────────────────┤
│  Application (Use Cases / DTOs)          │ ← Orquestación
├──────────────────────────────────────────┤
│  Domain (Entities / Value Objects)       │ ← NÚCLEO (Reglas de negocio)
├──────────────────────────────────────────┤
│  Infrastructure (ORM / Repos / Config)   │ ← Adaptadores de salida
└──────────────────────────────────────────┘
```

**Reglas de Dependencia:**
- ✅ Las capas externas dependen de las internas
- ❌ El dominio NO depende de nada (Python puro)
- ✅ La infraestructura implementa interfaces definidas en el dominio

---

## 📦 Capa de Dominio

### Entidades

#### Cliente ([src/domain/entities/cliente.py](file:///c:/Users/diego/Desktop/e-comerce/src/domain/entities/cliente.py))

```python
class Cliente(EntidadBase):
    def __init__(
        self,
        nombre: str,
        apellido: str,
        email: Email,  # Value Object
        documento: DocumentoIdentidad,  # Value Object
        telefono: Optional[Telefono] = None,
        ...
    ):
        # Validaciones en el dominio
        self._nombre = nombre
        self._email = email
        ...
```

#### Producto ([src/domain/entities/producto.py](file:///c:/Users/diego/Desktop/e-comerce/src/domain/entities/producto.py))

```python
class Producto(EntidadBase):
    @property
    def disponible(self) -> bool:
        """Regla de negocio: disponible si está activo y tiene stock"""
        return self.activo and self.stock_actual > 0
    
    def reservar_stock(self, cantidad: int):
        """Controla la reserva de stock con validaciones"""
        if cantidad > self.stock_actual:
            raise ReglaNegocioViolada("Stock insuficiente")
        self.stock_actual -= cantidad
```

#### Orden ([src/domain/entities/orden.py](file:///c:/Users/diego/Desktop/e-comerce/src/domain/entities/orden.py))

Implementa **Máquina de Estados** para transiciones válidas:

```python
class Orden(EntidadBase):
    def confirmar(self):
        if self.estado != EstadoOrden.CREADA:
            raise EstadoInvalido("Solo se pueden confirmar órdenes creadas")
        
        if not self.lineas:
            raise ReglaNegocioViolada("No se puede confirmar orden vacía")
        
        self._estado = EstadoOrden.CONFIRMADA
```

### Value Objects

Los VOs encapsulan validaciones y garantizan inmutabilidad:

#### Email ([src/domain/value_objects/email.py](file:///c:/Users/diego/Desktop/e-comerce/src/domain/value_objects/email.py))

```python
class Email(ValueObject):
    def __init__(self, direccion: str):
        normalizado = direccion.strip().lower()
        
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', normalizado):
            raise ValorInvalido(f"Email '{direccion}' inválido")
        
        self._valor = normalizado
```

#### Dinero ([src/domain/value_objects/dinero.py](file:///c:/Users/diego/Desktop/e-comerce/src/domain/value_objects/dinero.py))

```python
class Dinero(ValueObject):
    def __init__(self, monto: Decimal, moneda: str = "USD"):
        if monto < 0:
            raise ValorInvalido("El monto no puede ser negativo")
        
        self._monto = monto
        self._moneda = moneda
    
    def __add__(self, otro: 'Dinero') -> 'Dinero':
        if self._moneda != otro.moneda:
            raise ValorInvalido("No se pueden sumar diferentes monedas")
        return Dinero(self._monto + otro.monto, self._moneda)
```

### Excepciones de Dominio

Ubicación: [src/domain/exceptions/dominio.py](file:///c:/Users/diego/Desktop/e-comerce/src/domain/exceptions/dominio.py)

```python
class ExcepcionDominio(Exception): pass
class ValorInvalido(ExcepcionDominio): pass
class ReglaNegocioViolada(ExcepcionDominio): pass
class EntidadNoEncontrada(ExcepcionDominio): pass
class EstadoInvalido(ExcepcionDominio): pass
```

---

## ⚙️ Capa de Aplicación

### Use Cases

Los Use Cases orquestan la lógica de aplicación pero NO contienen reglas de negocio.

#### CrearClienteUseCase ([src/application/use_cases/cliente_use_cases.py](file:///c:/Users/diego/Desktop/e-comerce/src/application/use_cases/cliente_use_cases.py))

```python
class CrearClienteUseCase(CasoUsoBase[CrearClienteDTO, ClienteDTO]):
    def __init__(self, cliente_repository: ClienteRepository):
        self._cliente_repository = cliente_repository
    
    def ejecutar(self, request: CrearClienteDTO) -> ClienteDTO:
        # 1. Validar duplicados (lógica de aplicación)
        email = Email(request.email)
        if self._cliente_repository.obtener_por_email(email):
            raise ReglaNegocioViolada(f"Email {request.email} ya existe")
        
        # 2. Crear entidad (lógica de dominio)
        cliente = Cliente(
            nombre=request.nombre,
            apellido=request.apellido,
            email=email,
            documento=DocumentoIdentidad(request.tipo_documento, request.numero_documento),
            telefono=Telefono(request.telefono) if request.telefono else None
        )
        
        # 3. Persistir
        cliente_guardado = self._cliente_repository.guardar(cliente)
        
        # 4. Retornar DTO
        return ClienteDTO.desde_entidad(cliente_guardado)
```

### DTOs

Los DTOs son clases simples de transferencia de datos entre capas.

```python
@dataclass
class CrearClienteDTO:
    nombre: str
    apellido: str
    email: str
    tipo_documento: TipoDocumento
    numero_documento: str
    telefono: Optional[str] = None

@dataclass
class ClienteDTO:
    id: UUID
    nombre: str
    email: str
    # ...
    
    @classmethod
    def desde_entidad(cls, cliente: Cliente) -> 'ClienteDTO':
        return cls(
            id=cliente.id,
            nombre=cliente.nombre,
            email=cliente.email.valor,  # Extraer valor del VO
            # ...
        )
```

---

## 🔌 Capa de Infraestructura

### Repositorios

Los repositorios implementan las interfaces definidas en el dominio.

#### ClienteRepositoryImpl ([src/infrastructure/persistence/repositories/cliente_repository_impl.py](file:///c:/Users/diego/Desktop/e-comerce/src/infrastructure/persistence/repositories/cliente_repository_impl.py))

```python
class ClienteRepositoryImpl(ClienteRepository):
    def __init__(self, auditoria=None, logger=None):
        self._auditoria = auditoria or ServicioAuditoria()
        self._logger = logger or LoggerService("ClienteRepository")
    
    def obtener_por_id(self, id: UUID) -> Optional[Cliente]:
        try:
            model = ClienteModel.objects.get(id=id)
            return self._to_domain(model)  # Mapear ORM → Entidad
        except ClienteModel.DoesNotExist:
            return None
    
    def guardar(self, entidad: Cliente) -> Cliente:
        model = self._to_model(entidad)  # Mapear Entidad → ORM
        model.save()
        
        # Auditoría
        self._auditoria.registrar_operacion(
            tabla="clientes",
            operacion="CREATE" if not existe else "UPDATE",
            datos_nuevos={"email": entidad.email.valor, ...}
        )
        
        return self._to_domain(model)
```

### ORM Models

Ubicación: [src/infrastructure/persistence/django/models.py](file:///c:/Users/diego/Desktop/e-comerce/src/infrastructure/persistence/django/models.py)

```python
class ClienteModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    tipo_documento = models.CharField(max_length=20)
    numero_documento = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clientes'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['numero_documento']),
        ]
```

### Control de Concurrencia

**Problema:** Dos usuarios compran el último producto simultáneamente.

**Solución:** Bloqueo pesimista con `SELECT FOR UPDATE` en PostgreSQL.

```python
class ProductoRepositoryImpl:
    def obtener_con_bloqueo(self, id: UUID) -> Optional[Producto]:
        """
        CRÍTICO: Bloquea la fila hasta que termine la transacción.
        Otras transacciones esperan.
        """
        model = ProductoModel.objects.select_for_update().get(id=id)
        return self._to_domain(model)

class OrdenRepositoryImpl:
    @transaction.atomic  # Garantiza atomicidad
    def confirmar_con_stock(self, orden_id: UUID) -> Orden:
        # 1. Bloquear orden
        orden = self.obtener_por_id(orden_id)
        
        # 2. Para cada línea, bloquear producto y descontar stock
        for linea in orden.lineas:
            producto = self._producto_repo.obtener_con_bloqueo(linea.producto_id)
            producto.reservar_stock(linea.cantidad)
            self._producto_repo.guardar(producto)
        
        # 3. Confirmar orden
        orden.confirmar()
        return self.guardar(orden)
```

---

## 📡 Capa de Interfaces (API REST)

### Serializers

Validación de formato (NO reglas de negocio).

```python
class CrearClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField()  # Validación de formato
    telefono = serializers.CharField(max_length=20, required=False)
    
    def to_dto(self) -> CrearClienteDTO:
        return CrearClienteDTO(
            nombre=self.validated_data['nombre'],
            email=self.validated_data['email'],
            # ...
        )
```

### Views (Controllers)

Los controllers NO contienen lógica de negocio.

```python
class ClienteListCreateView(APIView):
    def post(self, request):
        # 1. Validar formato
        serializer = CrearClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Convertir a DTO
        dto = serializer.to_dto()
        
        # 3. Llamar Use Case
        repo = ClienteRepositoryImpl()
        use_case = CrearClienteUseCase(repo)
        resultado = use_case.ejecutar(dto)
        
        # 4. Serializar respuesta
        output_serializer = ClienteSerializer(resultado)
        return Response(output_serializer.data, status=201)
```

### Exception Handler

Mapea excepciones de dominio a códigos HTTP.

```python
def custom_exception_handler(exc, context):
    if isinstance(exc, EntidadNoEncontrada):
        return Response(
            {"detail": str(exc), "code": "not_found"},
            status=404
        )
    
    if isinstance(exc, ReglaNegocioViolada):
        return Response(
            {"detail": str(exc), "code": "conflict"},
            status=409
        )
    
    if isinstance(exc, ValorInvalido):
        return Response(
            {"detail": str(exc), "code": "invalid_value"},
            status=400
        )
    
    # Dejar que Django maneje el resto
    return None
```

---

## 🔒 Seguridad

### Django Settings

Ubicación: [src/infrastructure/config/django_settings.py](file:///c:/Users/diego/Desktop/e-comerce/src/infrastructure/config/django_settings.py)

```python
# Validación estricta de SECRET_KEY
def get_secret_key() -> str:
    secret_key = os.environ.get('DJANGO_SECRET_KEY', '').strip()
    
    if not secret_key:
        raise ConfigurationError("DJANGO_SECRET_KEY es OBLIGATORIO")
    
    if len(secret_key) < 50:
        raise ConfigurationError("SECRET_KEY demasiado corto")
    
    return secret_key

# Security Headers
SECURE_SSL_REDIRECT = IS_PRODUCTION
SESSION_COOKIE_SECURE = IS_PRODUCTION
CSRF_COOKIE_SECURE = IS_PRODUCTION
SECURE_HSTS_SECONDS = 31536000 if IS_PRODUCTION else 0
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### Validaciones en Capas

```
┌─────────────────────────────────────────┐
│ 1. Serializers (REST)                   │ → Formato (email válido, max_length)
├─────────────────────────────────────────┤
│ 2. Value Objects (Dominio)              │ → Semántica (teléfono >= 8 dígitos)
├─────────────────────────────────────────┤
│ 3. Entidades (Dominio)                  │ → Consistencia (orden no vacía)
├─────────────────────────────────────────┤
│ 4. Base de Datos                        │ → Integridad (FK, UNIQUE)
└─────────────────────────────────────────┘
```

---

## 📊 Auditoría y Logging

### Sistema de Auditoría

Ubicación: [src/infrastructure/auditing/](file:///c:/Users/diego/Desktop/e-comerce/src/infrastructure/auditing/)

```python
class ServicioAuditoria:
    def registrar_operacion(
        self,
        tabla: str,
        operacion: str,  # CREATE, UPDATE, DELETE
        datos_previos: dict = None,
        datos_nuevos: dict = None
    ):
        AuditoriaModel.objects.create(
            tabla=tabla,
            operacion=operacion,
            datos_previos=json.dumps(datos_previos),
            datos_nuevos=json.dumps(datos_nuevos),
            timestamp=datetime.utcnow()
        )
```

### Logging Estructurado

```python
from infrastructure.logging.logger import LoggerService

logger = LoggerService("ClienteRepository")
logger.info("Cliente creado", cliente_id=str(id), email=email)
logger.warning("Email duplicado", email=email, accion="rechazado")
logger.error("Error al guardar", cliente_id=str(id), error=str(e))
```

---

## 🧪 Testing

### Estrategia de Testing

```
┌──────────────────────────────────────────┐
│ Tests Unitarios (Dominio)                │ → Puro Python, sin DB
├──────────────────────────────────────────┤
│ Tests de Integración (Repositorios)      │ → Con DB de prueba
├──────────────────────────────────────────┤
│ Tests E2E (API)                           │ → Scripts completos
└──────────────────────────────────────────┘
```

### Ejemplo: Test Unitario de Dominio

```python
def test_cliente_email_invalido():
    with pytest.raises(ValorInvalido):
        Cliente(
            nombre="Juan",
            apellido="Pérez",
            email=Email("correo-invalido"),  # Lanza excepción
            documento=DocumentoIdentidad(TipoDocumento.DNI, "12345678")
        )
```

### Ejemplo: Test E2E

Script: [scripts/verify_api_rest.py](file:///c:/Users/diego/Desktop/e-comerce/scripts/verify_api_rest.py)

```python
def verify_api_flow():
    client = APIClient()
    
    # 1. Crear cliente
    resp = client.post("/api/v1/clientes", {...})
    assert resp.status_code == 201
    cliente_id = resp.data['id']
    
    # 2. Crear producto
    resp = client.post("/api/v1/productos", {...})
    assert resp.status_code == 201
    producto_id = resp.data['id']
    
    # 3. Crear y confirmar orden
    resp = client.post("/api/v1/ordenes", {"cliente_id": cliente_id})
    orden_id = resp.data['id']
    
    resp = client.post(f"/api/v1/ordenes/{orden_id}/lineas", {
        "producto_id": producto_id,
        "cantidad": 2
    })
    assert resp.status_code == 201
    
    resp = client.post(f"/api/v1/ordenes/{orden_id}/confirmar", {})
    assert resp.status_code == 200
    assert resp.data['estado'] == "CONFIRMADA"
```

---

## 🚀 Despliegue

### Variables de Entorno (Producción)

```env
# Django
DJANGO_SECRET_KEY=<generated-secure-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_ENVIRONMENT=production

# PostgreSQL
DB_HOST=db.yourdomain.com
DB_NAME=ecomerce_prod
DB_USER=app_user
DB_PASSWORD=<secure-password>
DB_SSL_MODE=require
```

### Gunicorn (WSGI)

```bash
gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60 \
  infrastructure.config.django_wsgi:application
```

### Nginx (Proxy Reverso)

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
}
```

---

## 📈 Optimizaciones

### Índices de Base de Datos

```python
class ClienteModel(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['email']),  # Búsquedas frecuentes
            models.Index(fields=['numero_documento']),
            models.Index(fields=['activo', 'fecha_creacion']),
        ]
```

### Query Optimization

```python
# ❌ N+1 Problem
ordenes = OrdenModel.objects.all()
for orden in ordenes:
    lineas = orden.lineas.all()  # Query por cada orden

# ✅ Solución: prefetch_related
ordenes = OrdenModel.objects.prefetch_related('lineas').all()
```

---

## 🔧 Troubleshooting

### Logs

```bash
# Ver logs en tiempo real
tail -f logs/django.log

# Buscar errores
grep ERROR logs/django.log

# Ver últimas 50 líneas
tail -n 50 logs/django.log
```

### Database

```bash
# Conectar a PostgreSQL
psql -U postgres -d ecomerce_db

# Ver conexiones activas
SELECT * FROM pg_stat_activity;

# Locks activos
SELECT * FROM pg_locks;
```

---

**Última actualización**: 2026-01-17  
**Mantenido por**: Equipo de Desarrollo
