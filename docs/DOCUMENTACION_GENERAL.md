# 📚 Documentación General - Sistema E-Commerce

## 🎯 Visión General del Proyecto

Sistema empresarial de e-commerce construido con **Clean Architecture**, implementando principios de Domain-Driven Design (DDD) y patrones empresariales modernos.

### Características Principales

- ✅ **Clean Architecture** - Separación completa entre dominio y tecnología
- ✅ **Domain-Driven Design** - Modelado centrado en el negocio
- ✅ **REST API** - Django REST Framework + FastAPI
- ✅ **PostgreSQL** - Base de datos relacional robusta
- ✅ **Control de Concurrencia** - Bloqueos pesimistas para stock
- ✅ **Auditoría Automática** - Logging estructurado de operaciones
- ✅ **Seguridad Hardened** - Headers de seguridad, validaciones, SSL

---

## 📁 Estructura del Proyecto

```
e-comerce/
├── src/
│   ├── domain/              # 💎 Núcleo del Negocio (PURO Python)
│   │   ├── entities/        # Entidades: Cliente, Producto, Orden
│   │   ├── value_objects/   # VOs: Email, Dinero, DocumentoIdentidad
│   │   ├── repositories/    # Interfaces (contratos)
│   │   └── exceptions/      # Excepciones de dominio
│   │
│   ├── application/         # ⚙️ Casos de Uso y DTOs
│   │   ├── use_cases/       # Lógica de aplicación
│   │   └── dto/             # Data Transfer Objects
│   │
│   ├── infrastructure/      # 🔌 Adaptadores Técnicos
│   │   ├── persistence/     # Django ORM, Repositorios
│   │   ├── config/          # Configuración de Django
│   │   ├── auditing/        # Sistema de auditoría
│   │   └── logging/         # Logging estructurado
│   │
│   └── interfaces/          # 📡 Puntos de Entrada
│       └── api/
│           ├── rest/        # Django REST Framework
│           └── fastapi/     # FastAPI (alternativa)
│
├── scripts/                 # Scripts de verificación
├── docs/                    # Documentación
└── manage.py               # CLI de Django
```

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

- Python 3.14+
- PostgreSQL 16+
- Git

### 2. Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd e-comerce

# Crear entorno virtual
python -m venv .venv

# Activar entorno
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración de Base de Datos

Crear archivo `.env` en la raíz:

```env
# Django
DJANGO_SECRET_KEY=<generar-key-segura>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_ENVIRONMENT=development

# PostgreSQL
DB_ENGINE=postgresql
DB_NAME=ecomerce_db
DB_USER=postgres
DB_PASSWORD=<tu-password>
DB_HOST=localhost
DB_PORT=5432
DB_SSL_MODE=disable
```

**Generar SECRET_KEY segura:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Migrar Base de Datos

```bash
python manage.py migrate
```

### 5. Ejecutar Servidor

```bash
# Desarrollo
python manage.py runserver

# Producción (con Gunicorn)
gunicorn infrastructure.config.django_wsgi:application
```

---

## 🔗 API REST Endpoints

Base URL: `http://localhost:8000/api/v1/`

### Clientes

- `POST /clientes` - Crear cliente
- `GET /clientes/{id}` - Obtener cliente por ID

**Ejemplo Request:**
```json
POST /api/v1/clientes
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "tipo_documento": "DNI",
  "numero_documento": "12345678",
  "telefono": "555-12345678"
}
```

### Productos

- `GET /productos` - Listar productos disponibles
- `POST /productos` - Crear producto
- `GET /productos/{id}` - Obtener producto por ID

**Ejemplo Request:**
```json
POST /api/v1/productos
{
  "codigo": "SKU-001",
  "nombre": "Laptop Dell XPS",
  "descripcion": "Laptop de alto rendimiento",
  "precio_monto": 1500.00,
  "precio_moneda": "USD",
  "stock_actual": 50,
  "stock_minimo": 10
}
```

### Órdenes

- `POST /ordenes` - Crear orden
- `POST /ordenes/{id}/lineas` - Agregar producto a orden
- `POST /ordenes/{id}/confirmar` - Confirmar orden (descuenta stock)

**Flujo Completo:**
```json
// 1. Crear orden
POST /api/v1/ordenes
{
  "cliente_id": "uuid-cliente"
}

// 2. Agregar productos
POST /api/v1/ordenes/{orden_id}/lineas
{
  "producto_id": "uuid-producto",
  "cantidad": 2
}

// 3. Confirmar orden
POST /api/v1/ordenes/{orden_id}/confirmar
{}
```

---

## 🧪 Pruebas y Verificación

### Script de Verificación E2E

```bash
# Verificar flujo completo
python scripts/verify_api_rest.py
```

Este script:
1. ✅ Crea un cliente
2. ✅ Crea un producto
3. ✅ Crea una orden
4. ✅ Agrega línea a la orden
5. ✅ Confirma la orden (descuenta stock)

### Tests Unitarios (Próximamente)

```bash
pytest
pytest --cov=src tests/
```

---

## 🔒 Seguridad

### Headers Implementados

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security` (HSTS en producción)
- `Secure Cookies` (producción)

### Validaciones

- **Formato**: Django REST Framework serializers
- **Dominio**: Value Objects (Email, Telefono, etc.)
- **Negocio**: Reglas en Entidades

---

## 📊 Modelos de Dominio

### Cliente

Propiedades:
- `nombre`, `apellido`
- `email` (Value Object - validado)
- `documento` (VO: tipo + número)
- `telefono` (VO - formato validado)

### Producto

Propiedades:
- `codigo` (SKU único)
- `nombre`, `descripcion`
- `precio` (Value Object: monto + moneda)
- `stock_actual`, `stock_minimo`

### Orden

Estados: `CREADA` → `CONFIRMADA` → `ENVIADA` → `ENTREGADA` / `CANCELADA`

Propiedades:
- `cliente_id`
- `lineas` (lista de productos + cantidad)
- `total` calculado automáticamente
- `estado` (máquina de estados)

---

## 🛠️ Comandos Útiles

### Django

```bash
# Crear superusuario
python manage.py createsuperuser

# Shell interactivo
python manage.py shell

# Ver migraciones pendientes
python manage.py showmigrations
```

### Base de Datos

```bash
# Conectar a PostgreSQL
psql -U postgres -d ecomerce_db

# Backup
pg_dump -U postgres ecomerce_db > backup.sql

# Restore
psql -U postgres ecomerce_db < backup.sql
```

---

## 📈 Siguientes Pasos

### Funcionalidades Pendientes

- [ ] Autenticación JWT
- [ ] Paginación en listados
- [ ] Tests automatizados (pytest)
- [ ] Documentación OpenAPI/Swagger
- [ ] Caché con Redis
- [ ] Rate limiting
- [ ] Notificaciones por email

### Despliegue

- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] CI/CD pipeline
- [ ] Configuración Nginx
- [ ] SSL/HTTPS en producción

---

## 📞 Soporte

Para problemas o dudas:
1. Revisar logs en `logs/django.log`
2. Verificar variables de entorno en `.env`
3. Consultar documentación técnica detallada

---

## 📝 Convenciones

### Git Workflow

```bash
# Feature branch
git checkout -b feature/nueva-funcionalidad

# Commit messages
git commit -m "feat: agregar endpoint de búsqueda de productos"
git commit -m "fix: corregir validación de email"
git commit -m "docs: actualizar README"
```

### Código

- **Python**: PEP 8
- **Línea máxima**: 120 caracteres
- **Imports**: absolutos desde `src/`
- **Docstrings**: estilo Google

---

**Última actualización**: 2026-01-17
