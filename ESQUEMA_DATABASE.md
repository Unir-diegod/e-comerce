# Esquema de Base de Datos PostgreSQL - E-Commerce

## Resumen General

- **Base de Datos**: ecomerce_db  
- **Motor**: PostgreSQL 18.1  
- **Tablas Totales**: 11  
- **Estado**: Operativo

---

## Tablas del Sistema

### Tabla Principal: clientes

Tabla del agregado Cliente en Clean Architecture.

**Columnas:**

| Campo | Tipo | Longitud | Nulo | Descripcion |
|-------|------|----------|------|-------------|
| id | UUID | - | NO | Identificador unico (PK) |
| nombre | VARCHAR | 100 | NO | Nombre del cliente |
| apellido | VARCHAR | 100 | NO | Apellido del cliente |
| email | VARCHAR | 254 | NO | Email unico del cliente |
| tipo_documento | VARCHAR | 20 | NO | Tipo (DNI, PASAPORTE, etc.) |
| numero_documento | VARCHAR | 50 | NO | Numero de documento unico |
| telefono | VARCHAR | 20 | SI | Telefono (opcional) |
| activo | BOOLEAN | - | NO | Estado del cliente |
| fecha_creacion | TIMESTAMPTZ | - | NO | Timestamp de creacion |
| fecha_modificacion | TIMESTAMPTZ | - | NO | Timestamp ultima modificacion |

**Indices (8 total):**

- clientes_pkey (PRIMARY KEY) - Columna: id
- clientes_email_key (UNIQUE) - Columna: email  
- clientes_numero_documento_key (UNIQUE) - Columna: numero_documento
- clientes_email_fb2cd6_idx (INDEX) - Busqueda por email
- clientes_numero__b55e8a_idx (INDEX) - Busqueda por documento
- clientes_activo_dcf9ae_idx (INDEX) - Filtrado por estado
- clientes_email_c8fa8339_like (INDEX) - Busqueda parcial email
- clientes_numero_documento_28d785c8_like (INDEX) - Busqueda parcial documento

**Constraints:**

- NOT NULL en todos los campos excepto telefono
- PRIMARY KEY en id
- UNIQUE en email y numero_documento

---

### Tablas de Django (10 adicionales)

Tablas estandar de Django para autenticacion, permisos y administracion:

1. auth_group - Grupos de usuarios
2. auth_group_permissions - Permisos por grupo
3. auth_permission - Permisos del sistema
4. auth_user - Usuarios del sistema
5. auth_user_groups - Relacion usuario-grupos
6. auth_user_user_permissions - Permisos directos por usuario
7. django_admin_log - Log de acciones admin
8. django_content_type - Tipos de contenido
9. django_migrations - Control de migraciones
10. django_session - Sesiones de usuario

---

## Arquitectura de Persistencia

### Mapeo Domain a ORM

```
Domain Layer (Cliente)
    |
    v
Application Layer (ClienteDTO)
    |
    v
Infrastructure Layer (ClienteModel)
    |
    v
PostgreSQL (tabla clientes)
```

### Value Objects Mapeados

- **Email** -> Campo: email (Validacion: Formato RFC 5322, Unique)
- **DocumentoIdentidad** -> Campos: tipo_documento + numero_documento (Validacion: Tipo valido, Unique)
- **Telefono** -> Campo: telefono (Validacion: Formato internacional, opcional)

### Reglas de Negocio Implementadas

1. Email unico - Constraint + Indice unico
2. Documento unico - Constraint + Indice unico
3. Cliente activo/inactivo - Soft delete con campo activo
4. Auditoria temporal - fecha_creacion, fecha_modificacion
5. UUID como PK - Identificadores unicos distribuidos

---

## Estadisticas Actuales

- Clientes registrados: 2
- Migraciones aplicadas: 18
- Indices totales tabla clientes: 8
- Constraints tabla clientes: 12

---

## Comandos Utiles

### Verificar conexion
```bash
python manage.py check_database
```

### Crear migracion
```bash
python manage.py makemigrations
```

### Aplicar migraciones
```bash
python manage.py migrate
```

### Validar sistema completo
```bash
python manage.py validar_sistema
```

### Acceder a PostgreSQL
```bash
psql -U postgres -d ecomerce_db
```

### Queries utiles en PostgreSQL
```sql
-- Ver todos los clientes
SELECT * FROM clientes;

-- Contar clientes activos
SELECT COUNT(*) FROM clientes WHERE activo = true;

-- Ver estructura de tabla
\d clientes

-- Ver indices
\di

-- Ver constraints
\d+ clientes
```

---

## Proximos Pasos

- [ ] Implementar tabla productos
- [ ] Implementar tabla ordenes  
- [ ] Implementar tabla lineas_orden
- [ ] Agregar auditoria con tabla dedicada
- [ ] Implementar eventos de dominio

---

**Ultima actualizacion**: 16 de enero de 2026  
**Clean Architecture**: Preservada  
**PostgreSQL**: Configurado y operativo
