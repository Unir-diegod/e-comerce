# INSTRUCCIONES DE ACTIVACIÓN - AUTENTICACIÓN JWT

## ✅ SISTEMA IMPLEMENTADO

Se ha implementado exitosamente:

1. **Modelo de Usuario** con roles ADMIN, OPERADOR, LECTURA
2. **JWT** con access token (15min) y refresh token (1 día, rotativo)
3. **RBAC** con permisos declarativos por rol
4. **Protección de endpoints** con autenticación obligatoria
5. **Auditoría de accesos** automática
6. **Script de validación** completo

## 📋 PASOS PARA ACTIVAR

### 1. Instalar Dependencias

```bash
pip install djangorestframework-simplejwt==5.3.1
```

O reinstalar todo:

```bash
pip install -r requirements.txt
```

### 2. Crear Migraciones

```bash
# Crear migraciones para el nuevo modelo Usuario
python manage.py makemigrations

# Aplicar todas las migraciones
python manage.py migrate
```

**IMPORTANTE**: Si hay conflictos con modelos anteriores de usuarios, ejecutar:

```bash
python manage.py makemigrations auth
python manage.py migrate auth
python manage.py migrate
```

### 3. Crear Usuarios de Prueba

```bash
python manage.py crear_usuarios_demo
```

Esto crea automáticamente:
- `admin@ecommerce.com` / `Admin123!` (ADMIN)
- `operador@ecommerce.com` / `Operador123!` (OPERADOR)
- `lectura@ecommerce.com` / `Lectura123!` (LECTURA)

### 4. Iniciar Servidor

```bash
python manage.py runserver
```

### 5. Validar el Sistema

En otra terminal:

```bash
python scripts/test_api_auth.py
```

Debe mostrar:
```
✓ Servidor disponible
✓ Acceso sin token → 401
✓ Token inválido → 401
✓ Login y acceso ADMIN
✓ Permisos OPERADOR
✓ Permisos LECTURA → 403 al escribir
✓ Refresh token funciona
✓ Logout invalida token

Total: 8/8 tests pasados
✓ TODOS LOS TESTS PASARON
```

## 🔐 USO DE LA API

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecommerce.com","password":"Admin123!"}'
```

Respuesta:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "admin@ecommerce.com",
    "nombre": "Administrador Sistema",
    "rol": "ADMIN"
  }
}
```

### Usar la API

```bash
# Guardar el access token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Acceder a productos (requiere autenticación)
curl http://localhost:8000/api/v1/productos \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token

```bash
REFRESH="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"
```

### Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"
```

## 📊 VERIFICAR AUDITORÍA

### Django Shell

```bash
python manage.py shell
```

```python
from infrastructure.persistence.django.models import AuditoriaAccesoAPI

# Últimos 10 accesos
logs = AuditoriaAccesoAPI.objects.all()[:10]
for log in logs:
    print(f"{log.timestamp} - {log.metodo} {log.endpoint} - Usuario: {log.usuario_id} - Código: {log.codigo_estado}")

# Accesos fallidos
fallos = AuditoriaAccesoAPI.objects.filter(resultado_exitoso=False)
print(f"Total accesos fallidos: {fallos.count()}")
```

### Django Admin

1. Crear superusuario (si no existe):
   ```bash
   python manage.py createsuperuser
   ```

2. Acceder a: http://localhost:8000/admin

3. Ver:
   - **Usuarios** → Gestión de usuarios y roles
   - **Auditorías de Acceso API** → Logs de accesos

## 🎯 MATRIZ DE PERMISOS

| Endpoint | GET | POST | DELETE |
|----------|-----|------|--------|
| `/api/v1/productos` | Todos | OPERADOR/ADMIN | - |
| `/api/v1/clientes` | Todos | OPERADOR/ADMIN | - |
| `/api/v1/ordenes` | - | OPERADOR/ADMIN | - |
| `/api/v1/auth/*` | Público | Público | - |

**Todos** = Cualquier usuario autenticado (LECTURA, OPERADOR, ADMIN)

## ⚠ TROUBLESHOOTING

### Error: "No module named 'rest_framework_simplejwt'"

```bash
pip install djangorestframework-simplejwt
```

### Error: "No such table: auth_usuarios"

```bash
python manage.py migrate
```

### Error: "User model not found"

Verificar en `django_settings.py`:
```python
AUTH_USER_MODEL = 'auth.Usuario'
```

### Tests fallan: "Connection refused"

Asegurarse de que Django esté corriendo:
```bash
python manage.py runserver
```

## 📁 ARCHIVOS CREADOS/MODIFICADOS

### Nuevos Archivos

```
src/infrastructure/auth/
├── __init__.py
├── models.py                    # Modelo Usuario + Roles
├── admin.py                     # Django Admin
└── middleware.py                # Auditoría automática

src/infrastructure/config/
└── jwt_config.py                # Configuración JWT

src/interfaces/permissions/
└── rbac.py                      # Permisos RBAC

src/interfaces/api/rest/views/
└── auth_views.py                # Login, logout, refresh

src/infrastructure/management/commands/
└── crear_usuarios_demo.py       # Command para usuarios demo

docs/
└── AUTENTICACION_JWT.md         # Documentación completa

scripts/
└── test_api_auth.py             # Tests de validación
```

### Archivos Modificados

```
src/infrastructure/config/
├── django_settings.py           # + AUTH_USER_MODEL, JWT config
└── django_urls.py               # + rutas de auth

src/infrastructure/persistence/django/
└── models.py                    # + AuditoriaAccesoAPI

src/interfaces/api/rest/views/
├── producto_view.py             # + permisos
├── cliente_view.py              # + permisos
└── orden_view.py                # + permisos

src/infrastructure/auditing/
└── servicio_auditoria.py        # + registrar_acceso_api()

requirements.txt                 # + djangorestframework-simplejwt
```

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] Migraciones aplicadas sin errores
- [ ] Usuarios de prueba creados
- [ ] Servidor Django arranca sin errores
- [ ] Script `test_api_auth.py` pasa 8/8 tests
- [ ] Login retorna access y refresh tokens
- [ ] Endpoints sin token retornan 401
- [ ] Usuario LECTURA recibe 403 al intentar POST
- [ ] Refresh token genera nuevos tokens
- [ ] Logout invalida el refresh token
- [ ] Auditoría registra accesos en la BD
- [ ] Django Admin muestra usuarios y logs

## 🚀 LISTO PARA PRODUCCIÓN

Una vez validado localmente:

1. **Variables de entorno en producción**:
   ```bash
   DJANGO_SECRET_KEY=<key-segura-64-chars>
   DJANGO_ENVIRONMENT=production
   DJANGO_ALLOWED_HOSTS=tudominio.com
   ```

2. **HTTPS obligatorio**:
   - Ya configurado en `django_settings.py` (IS_PRODUCTION)

3. **Rotación de SECRET_KEY**:
   - Cada 90 días (documentar proceso)

4. **Monitoreo**:
   - Alertas por múltiples fallos de login
   - Dashboard de accesos

## 📚 DOCUMENTACIÓN COMPLETA

Ver: [docs/AUTENTICACION_JWT.md](../docs/AUTENTICACION_JWT.md)

---

**Sistema de Autenticación JWT y RBAC implementado exitosamente** ✅
