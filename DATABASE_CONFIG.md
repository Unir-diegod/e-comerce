# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS POSTGRESQL - GUÍA COMPLETA
# ============================================================================

## PROPÓSITO

Este documento explica la configuración de PostgreSQL para el proyecto e-commerce
siguiendo los principios de Clean Architecture.

## ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────┐
│                     CLEAN ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│  Domain Layer (entities, value objects, repositories)       │
│         ↓ NO conoce la infraestructura                      │
│  Application Layer (use cases, DTOs)                        │
│         ↓ Depende de abstracciones                          │
│  Infrastructure Layer                                        │
│    ├── database_config.py (Configuración centralizada)      │
│    ├── django_settings.py (Integración Django)              │
│    └── repositories (Implementaciones concretas)            │
└─────────────────────────────────────────────────────────────┘
```

## COMPONENTES

### 1. DatabaseConfig (`infrastructure/config/database_config.py`)

**Responsabilidad:** Configuración centralizada y validada de PostgreSQL

**Características:**
- ✅ Validación estricta de variables de entorno
- ✅ No permite valores por defecto inseguros
- ✅ Lanza ErrorConfiguracion si falta algo
- ✅ Soporta múltiples entornos (dev/staging/prod)
- ✅ Configuración de pool de conexiones
- ✅ SSL configurable por entorno

**Uso:**
```python
from infrastructure.config.database_config import DatabaseConfig

# En settings.py
DATABASES = DatabaseConfig.from_env()
```

### 2. Variables de Entorno (`.env`)

**Obligatorias:**
- `DB_ENGINE`: postgresql (fijo)
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario PostgreSQL
- `DB_PASSWORD`: Contraseña (NUNCA vacía)
- `DB_HOST`: Hostname/IP del servidor
- `DB_PORT`: Puerto (normalmente 5432)
- `DB_SSL_MODE`: Modo SSL (disable/require/verify-ca/verify-full)

**Opcionales:**
- `DB_CONN_MAX_AGE`: Tiempo máximo de conexión (default: 600)
- `DB_ATOMIC_REQUESTS`: Transacciones atómicas (default: True)

### 3. Django Settings (`infrastructure/config/django_settings.py`)

**Cambios:**
```python
# ANTES (Hardcoded)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        ...
    }
}

# AHORA (Desde configuración centralizada)
from infrastructure.config.database_config import DatabaseConfig
DATABASES = DatabaseConfig.from_env()
```

## CONFIGURACIÓN POR ENTORNO

### DESARROLLO LOCAL

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_db
DB_USER=ecommerce_user
DB_PASSWORD=dev_password
DB_HOST=localhost
DB_PORT=5432
DB_SSL_MODE=disable
```

**Crear BD localmente:**
```bash
# Conectar a PostgreSQL
psql -U postgres

# Crear base de datos y usuario
CREATE DATABASE ecommerce_db;
CREATE USER ecommerce_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO ecommerce_user;

# En PostgreSQL 15+
\c ecommerce_db
GRANT ALL ON SCHEMA public TO ecommerce_user;
```

### STAGING

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_staging
DB_USER=ecommerce_staging
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_HOST=staging-db.example.com
DB_PORT=5432
DB_SSL_MODE=require
DJANGO_DEBUG=False
DJANGO_ENV=staging
```

### PRODUCCIÓN

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_prod
DB_USER=ecommerce_prod
DB_PASSWORD=VERY_STRONG_PASSWORD_16_CHARS_MIN
DB_HOST=prod-db.example.com
DB_PORT=5432
DB_SSL_MODE=verify-full
DJANGO_DEBUG=False
DJANGO_ENV=production
DB_CONN_MAX_AGE=600
```

## VALIDACIONES IMPLEMENTADAS

La clase `DatabaseConfig` valida:

1. ✅ **DB_ENGINE** debe ser 'postgresql'
2. ✅ **DB_NAME** no puede estar vacío
3. ✅ **DB_USER** no puede estar vacío
4. ✅ **DB_PASSWORD** no puede estar vacío (obligatorio)
5. ✅ **DB_HOST** no puede estar vacío
6. ✅ **DB_PORT** debe ser número entre 1-65535
7. ✅ **DB_SSL_MODE** debe ser valor válido (disable/require/verify-ca/verify-full)

Si alguna validación falla, Django NO iniciará.

## COMANDOS ÚTILES

### Verificar Configuración
```bash
python manage.py check_database
```

### Crear Migraciones
```bash
python manage.py makemigrations
```

### Aplicar Migraciones
```bash
python manage.py migrate
```

### Validar Sistema Completo
```bash
python manage.py validar_sistema
```

## SEGURIDAD

### ✅ BUENAS PRÁCTICAS

1. **NUNCA** commitear `.env` con contraseñas reales
2. **SIEMPRE** usar `.env.example` como plantilla
3. **OBLIGATORIO** `DB_SSL_MODE=verify-full` en producción
4. **RECOMENDADO** rotar passwords periódicamente
5. **CRÍTICO** `DEBUG=False` en producción

### ❌ MALAS PRÁCTICAS

1. ❌ Hardcodear passwords en código
2. ❌ Usar `DB_PASSWORD=` (vacío)
3. ❌ Usar `DB_SSL_MODE=disable` en producción
4. ❌ Compartir credenciales de producción
5. ❌ Commitear `.env` al repositorio

## TROUBLESHOOTING

### Error: "ErrorConfiguracion: DB_PASSWORD es obligatorio"
**Solución:** Configurar variable `DB_PASSWORD` en `.env`

### Error: "could not connect to server"
**Solución:** 
1. Verificar que PostgreSQL esté corriendo
2. Verificar host y puerto correctos
3. Verificar firewall/red

### Error: "FATAL: password authentication failed"
**Solución:**
1. Verificar usuario y contraseña
2. Verificar permisos en `pg_hba.conf`

### Error: "database 'ecommerce_db' does not exist"
**Solución:** Crear la base de datos con `CREATE DATABASE`

## MIGRACIONES

### Crear Migraciones Iniciales
```bash
python manage.py makemigrations
python manage.py migrate
```

### Verificar Migraciones Pendientes
```bash
python manage.py showmigrations
```

### Rollback de Migraciones
```bash
python manage.py migrate <app_name> <migration_number>
```

## POOL DE CONEXIONES

Configuración optimizada para producción:

```python
DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutos
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
```

**Beneficios:**
- ✅ Reduce overhead de conexiones
- ✅ Mejora performance
- ✅ Detecta conexiones rotas

## CLEAN ARCHITECTURE COMPLIANCE

✅ **Dominio** NO conoce PostgreSQL
✅ **Application** NO conoce Django ORM
✅ **Infrastructure** implementa interfaces del dominio
✅ **Configuración** centralizada y validada
✅ **Dependencias** fluyen hacia el dominio

## REFERENCIAS

- [PostgreSQL SSL Modes](https://www.postgresql.org/docs/current/libpq-ssl.html)
- [Django PostgreSQL Notes](https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes)
- [psycopg3 Documentation](https://www.psycopg.org/psycopg3/docs/)
