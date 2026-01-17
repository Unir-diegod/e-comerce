# Guía de Autenticación y Autorización JWT

## Resumen

El sistema e-commerce cuenta con autenticación JWT (JSON Web Tokens) y autorización basada en roles (RBAC) para proteger la API REST.

## Arquitectura de Seguridad

### Modelo de Usuario

**Ubicación**: `src/infrastructure/auth/models.py`

- **Usuario personalizado** usando `AbstractBaseUser`
- Email como identificador único
- 3 roles predefinidos: ADMIN, OPERADOR, LECTURA
- **Separado del dominio**: No confundir con la entidad `Cliente`

### Roles y Permisos

| Rol | Lectura | Crear/Modificar | Eliminar |
|-----|---------|-----------------|----------|
| **ADMIN** | ✓ | ✓ | ✓ |
| **OPERADOR** | ✓ | ✓ | ✗ |
| **LECTURA** | ✓ | ✗ | ✗ |

### JWT (JSON Web Tokens)

**Configuración**: `src/infrastructure/config/jwt_config.py`

- **Access Token**: 15 minutos de validez
- **Refresh Token**: 1 día de validez
- **Rotación automática**: Refresh token se renueva en cada uso
- **Blacklist**: Tokens invalidados al hacer logout
- **Algoritmo**: HS256 con SECRET_KEY existente

## Endpoints de Autenticación

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@ecommerce.com",
  "password": "Admin123!"
}
```

**Respuesta exitosa (200)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "admin@ecommerce.com",
    "nombre": "Administrador",
    "rol": "ADMIN"
  }
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta (200)**:
```json
{
  "access": "nuevo_token_de_acceso",
  "refresh": "nuevo_refresh_token"
}
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "refresh_token"
}
```

### Perfil del Usuario

```http
GET /api/v1/auth/perfil
Authorization: Bearer <access_token>
```

### Verify Token

```http
POST /api/v1/auth/verify
Content-Type: application/json

{
  "token": "token_a_verificar"
}
```

## Uso de la API Protegida

### Autenticación en cada request

Todos los endpoints de la API requieren el header `Authorization`:

```http
GET /api/v1/productos
Authorization: Bearer <access_token>
```

### Respuestas de Error

**401 Unauthorized**: Sin token o token inválido
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**: Token válido pero sin permisos
```json
{
  "detail": "Se requiere rol de Operador o Administrador."
}
```

## Permisos por Endpoint

### Productos

```python
# src/interfaces/api/rest/views/producto_view.py
permission_classes = [PermisosPorMetodo]

# GET /api/v1/productos → Todos los autenticados
# POST /api/v1/productos → OPERADOR o ADMIN
```

### Clientes

```python
# src/interfaces/api/rest/views/cliente_view.py
permission_classes = [PermisosPorMetodo]

# GET /api/v1/clientes/{id} → Todos los autenticados
# POST /api/v1/clientes → OPERADOR o ADMIN
```

### Órdenes

```python
# src/interfaces/api/rest/views/orden_view.py
permission_classes = [EsOperadorOAdmin]

# POST /api/v1/ordenes → OPERADOR o ADMIN
# POST /api/v1/ordenes/{id}/lineas → OPERADOR o ADMIN
# POST /api/v1/ordenes/{id}/confirmar → OPERADOR o ADMIN
```

## Sistema de Auditoría

**Middleware**: `src/infrastructure/auth/middleware.py`

### Qué se audita

- ✓ Login exitoso/fallido
- ✓ Logout
- ✓ Accesos a endpoints protegidos
- ✓ Fallos de autorización (401, 403)
- ✗ **NO** se registran credenciales ni tokens

### Modelo de Auditoría

**Tabla**: `auditoria_acceso_api`

```python
class AuditoriaAccesoAPI(models.Model):
    timestamp: datetime
    usuario_id: str (null si no autenticado)
    endpoint: str
    metodo: str
    ip_address: str
    user_agent: str
    resultado_exitoso: bool
    codigo_estado: int
```

### Consultar logs de auditoría

```python
from infrastructure.persistence.django.models import AuditoriaAccesoAPI

# Últimos 100 accesos
logs = AuditoriaAccesoAPI.objects.all()[:100]

# Accesos fallidos (401, 403)
fallos = AuditoriaAccesoAPI.objects.filter(resultado_exitoso=False)

# Accesos de un usuario
accesos_usuario = AuditoriaAccesoAPI.objects.filter(
    usuario_id='uuid-del-usuario'
)
```

## Crear Usuarios

### Usando Django Admin

```bash
python manage.py createsuperuser
```

### Usando Shell de Django

```python
python manage.py shell

from infrastructure.auth.models import Usuario, RolUsuario

# Crear ADMIN
admin = Usuario.objects.create_user(
    email='admin@ecommerce.com',
    password='Admin123!',
    nombre='Administrador',
    rol=RolUsuario.ADMIN,
    is_staff=True
)

# Crear OPERADOR
operador = Usuario.objects.create_user(
    email='operador@ecommerce.com',
    password='Operador123!',
    nombre='Operador',
    rol=RolUsuario.OPERADOR
)

# Crear LECTURA
lectura = Usuario.objects.create_user(
    email='lectura@ecommerce.com',
    password='Lectura123!',
    nombre='Usuario Lectura',
    rol=RolUsuario.LECTURA
)
```

### Usando Management Command

```python
# src/infrastructure/management/commands/crear_usuarios_demo.py

from django.core.management.base import BaseCommand
from infrastructure.auth.models import Usuario, RolUsuario

class Command(BaseCommand):
    def handle(self, *args, **options):
        usuarios = [
            ('admin@ecommerce.com', 'Admin123!', RolUsuario.ADMIN, 'Admin'),
            ('operador@ecommerce.com', 'Operador123!', RolUsuario.OPERADOR, 'Operador'),
            ('lectura@ecommerce.com', 'Lectura123!', RolUsuario.LECTURA, 'Lectura'),
        ]
        
        for email, password, rol, nombre in usuarios:
            if not Usuario.objects.filter(email=email).exists():
                Usuario.objects.create_user(
                    email=email,
                    password=password,
                    nombre=nombre,
                    rol=rol
                )
                self.stdout.write(f"✓ Usuario {email} creado")
```

```bash
python manage.py crear_usuarios_demo
```

## Migrar Base de Datos

```bash
# Crear migraciones para el modelo Usuario
python manage.py makemigrations auth

# Crear migraciones para AuditoriaAccesoAPI
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

## Testing

### Script de Validación

```bash
# 1. Iniciar servidor Django
python manage.py runserver

# 2. En otra terminal, ejecutar tests
python scripts/test_api_auth.py
```

El script verifica:
- ✓ Servidor disponible
- ✓ Acceso sin token → 401
- ✓ Token inválido → 401
- ✓ Login y acceso ADMIN
- ✓ Permisos OPERADOR
- ✓ Permisos LECTURA → 403 al escribir
- ✓ Refresh token funciona
- ✓ Logout invalida token

### Testing Manual con curl

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecommerce.com","password":"Admin123!"}'

# Guardar token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Acceder a endpoint protegido
curl http://localhost:8000/api/v1/productos \
  -H "Authorization: Bearer $TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh":"refresh_token_aqui"}'
```

## Consideraciones de Seguridad

### ✓ Implementado

- JWT con expiración corta (15min)
- Refresh token rotativo
- Blacklist de tokens al logout
- Passwords hasheados (bcrypt)
- Auditoría de accesos
- Middleware de autenticación
- Permisos declarativos por rol
- SECRET_KEY desde variables de entorno
- HTTPS en producción (configurado)
- CORS configurado

### ⚠ Recomendaciones Adicionales

1. **Rate Limiting**: Implementar throttling en login
2. **2FA**: Autenticación de dos factores para ADMIN
3. **IP Whitelist**: Restringir acceso por IP en producción
4. **Rotación de SECRET_KEY**: Cada 90 días
5. **Monitoreo**: Alertas de múltiples fallos de login
6. **Expiración de passwords**: Cada 90 días para ADMIN

## Troubleshooting

### Error: "No se puede importar Usuario"

```bash
# Verificar que las migraciones se aplicaron
python manage.py migrate

# Verificar AUTH_USER_MODEL en settings
grep AUTH_USER_MODEL src/infrastructure/config/django_settings.py
```

### Error: "Token inválido"

- Verificar que SECRET_KEY no cambió
- Verificar que el token no expiró
- Verificar formato del header: `Bearer <token>`

### Error: "Permission denied"

- Verificar rol del usuario
- Verificar que el endpoint tiene `permission_classes`
- Revisar logs de auditoría

## Archivos Clave

```
src/
├── infrastructure/
│   ├── auth/
│   │   ├── models.py          # Usuario y RolUsuario
│   │   ├── admin.py           # Django Admin
│   │   └── middleware.py      # Auditoría de accesos
│   └── config/
│       ├── django_settings.py # AUTH_USER_MODEL, REST_FRAMEWORK
│       ├── django_urls.py     # Rutas de auth
│       └── jwt_config.py      # Configuración JWT
├── interfaces/
│   ├── api/rest/views/
│   │   ├── auth_views.py      # Login, logout, refresh
│   │   ├── producto_view.py   # + permisos
│   │   ├── cliente_view.py    # + permisos
│   │   └── orden_view.py      # + permisos
│   └── permissions/
│       └── rbac.py            # Permisos personalizados
scripts/
└── test_api_auth.py           # Tests de validación
```

## Referencias

- [Django REST Framework - Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [SimpleJWT Documentation](https://django-rest-framework-simplejwt.readthedocs.io/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
