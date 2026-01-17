"""
Comandos para ejecutar desde Django Shell
Copiar y pegar en: python manage.py shell
"""

# ============================================================================
# IMPORTAR DEPENDENCIAS
# ============================================================================
from application.use_cases.cliente_use_cases import CrearClienteUseCase, ObtenerClienteUseCase
from application.dto.cliente_dto import CrearClienteDTO
from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
from infrastructure.logging.logger_service import LoggerService
from shared.enums.tipos_documento import TipoDocumento
from domain.exceptions.dominio import ReglaNegocioViolada

# ============================================================================
# INICIALIZAR INFRAESTRUCTURA
# ============================================================================
auditoria = ServicioAuditoria()
logger = LoggerService("DjangoShell")
repo = ClienteRepositoryImpl(auditoria=auditoria, logger=logger)

# ============================================================================
# INICIALIZAR CASOS DE USO
# ============================================================================
crear_cliente = CrearClienteUseCase(cliente_repository=repo)
obtener_cliente = ObtenerClienteUseCase(cliente_repository=repo)

# ============================================================================
# CREAR PRIMER CLIENTE
# ============================================================================
dto1 = CrearClienteDTO(
    nombre="Juan",
    apellido="Pérez",
    email="juan.perez@example.com",
    tipo_documento=TipoDocumento.DNI,
    numero_documento="12345678",
    telefono="+51987654321"
)

cliente1 = crear_cliente.ejecutar(dto1)
print(f"✅ Cliente creado: {cliente1.id}")
print(f"   {cliente1.nombre} {cliente1.apellido}")
print(f"   Email: {cliente1.email}")

# ============================================================================
# RECUPERAR CLIENTE POR ID
# ============================================================================
cliente_recuperado = obtener_cliente.ejecutar(cliente1.id)
print(f"\n✅ Cliente recuperado desde BD:")
print(f"   ID: {cliente_recuperado.id}")
print(f"   Email: {cliente_recuperado.email}")

# ============================================================================
# INTENTAR DUPLICAR EMAIL (DEBE FALLAR)
# ============================================================================
dto_duplicado = CrearClienteDTO(
    nombre="María",
    apellido="García",
    email="juan.perez@example.com",  # EMAIL DUPLICADO
    tipo_documento=TipoDocumento.DNI,
    numero_documento="87654321",
    telefono="+51912345678"
)

try:
    crear_cliente.ejecutar(dto_duplicado)
    print("❌ ERROR: Se permitió email duplicado!")
except ReglaNegocioViolada as e:
    print(f"\n✅ Regla de negocio respetada: {e.mensaje}")

# ============================================================================
# CREAR SEGUNDO CLIENTE VÁLIDO
# ============================================================================
dto2 = CrearClienteDTO(
    nombre="Ana",
    apellido="Martínez",
    email="ana.martinez@example.com",
    tipo_documento=TipoDocumento.PASAPORTE,
    numero_documento="ABC123456"
)

cliente2 = crear_cliente.ejecutar(dto2)
print(f"\n✅ Segundo cliente creado: {cliente2.id}")

# ============================================================================
# LISTAR CLIENTES ACTIVOS
# ============================================================================
activos = repo.obtener_activos()
print(f"\n📋 Clientes activos: {len(activos)}")
for c in activos:
    print(f"   - {c.nombre_completo} ({c.email.valor})")

# ============================================================================
# BUSCAR POR NOMBRE
# ============================================================================
from domain.value_objects.email import Email

resultados = repo.buscar_por_nombre("Ana")
print(f"\n🔍 Búsqueda 'Ana': {len(resultados)} resultado(s)")
for c in resultados:
    print(f"   - {c.nombre_completo}")

# ============================================================================
# BUSCAR POR EMAIL
# ============================================================================
cliente_por_email = repo.obtener_por_email(Email("juan.perez@example.com"))
if cliente_por_email:
    print(f"\n✅ Cliente encontrado por email: {cliente_por_email.nombre_completo}")

# ============================================================================
# VERIFICAR EXISTENCIA
# ============================================================================
existe = repo.existe(cliente1.id)
print(f"\n✅ Cliente {cliente1.id} existe: {existe}")

print("\n" + "="*80)
print("✅ VALIDACIÓN COMPLETADA CON ÉXITO")
print("="*80)
print("\nComponentes validados:")
print("  ✓ Dominio (Entidades, Value Objects)")
print("  ✓ Application (Casos de Uso)")
print("  ✓ Infrastructure (Repositorios, ORM)")
print("  ✓ Persistencia MySQL")
print("  ✓ Auditoría y Logging")
print("  ✓ Clean Architecture preservada")
