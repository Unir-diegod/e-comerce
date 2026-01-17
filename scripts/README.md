# Validación del Sistema E-Commerce

## Scripts de Validación Disponibles

### Opción 1: Script Automatizado

```bash
python scripts/validar_sistema.py
```

Este script ejecuta una validación completa end-to-end del sistema.

### Opción 2: Django Shell Interactivo

```bash
python manage.py shell
```

Luego ejecutar:

```python
exec(open('scripts/shell_commands.py').read())
```

### Opción 3: Comandos Manuales en Django Shell

```bash
python manage.py shell
```

Copiar y pegar comandos del archivo `scripts/shell_commands.py`

---

## Validaciones Ejecutadas

### ✅ 1. Creación de Cliente Válido
- Persistencia en PostgreSQL
- Generación de UUID
- Timestamps automáticos
- Value Objects correctos

### ✅ 2. Recuperación desde BD
- Mapeo ORM → Dominio
- Reconstrucción de Value Objects
- Integridad de datos

### ✅ 3. Reglas de Negocio
- Email único (ReglaNegocioViolada)
- Documento único
- Validaciones de Value Objects

### ✅ 4. Búsquedas y Consultas
- Por ID
- Por email
- Por documento
- Por nombre (parcial)
- Clientes activos

### ✅ 5. Auditoría
- Registro CREATE
- Datos previos/nuevos
- Timestamps
- Usuario (opcional)

### ✅ 6. Logging
- Operaciones registradas
- Contexto de trazabilidad
- Errores capturados

---

## Comandos Rápidos

### Crear Cliente

```python
from application.use_cases.cliente_use_cases import CrearClienteUseCase
from application.dto.cliente_dto import CrearClienteDTO
from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from shared.enums.tipos_documento import TipoDocumento

repo = ClienteRepositoryImpl()
uc = CrearClienteUseCase(repo)

dto = CrearClienteDTO(
    nombre="Test",
    apellido="User",
    email="test@example.com",
    tipo_documento=TipoDocumento.DNI,
    numero_documento="99999999"
)

result = uc.ejecutar(dto)
print(f"Cliente creado: {result.id}")
```

### Listar Clientes

```python
from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl

repo = ClienteRepositoryImpl()
clientes = repo.obtener_activos()

for c in clientes:
    print(f"{c.nombre_completo} - {c.email.valor}")
```

---

## Estructura Validada

```
✓ Domain Layer
  ├── Entities (Cliente)
  ├── Value Objects (Email, Telefono, DocumentoIdentidad)
  ├── Repositories (Interfaces)
  └── Exceptions (ReglaNegocioViolada)

✓ Application Layer
  ├── Use Cases (CrearClienteUseCase, ObtenerClienteUseCase)
  └── DTOs (CrearClienteDTO, ClienteDTO)

✓ Infrastructure Layer
  ├── Persistence (ClienteRepositoryImpl)
  ├── ORM (ClienteModel)
  ├── Auditing (ServicioAuditoria)
  └── Logging (LoggerService)
```

---

## Clean Architecture Preservada

- ❌ Dominio NO importa infraestructura
- ❌ Dominio NO importa Django
- ✅ Infraestructura implementa interfaces del dominio
- ✅ Casos de uso dependen de abstracciones
- ✅ Flujo de dependencias correcto
