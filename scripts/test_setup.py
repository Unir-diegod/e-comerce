"""
Script de validación ejecutable desde Python directamente
"""
import os
import sys

# Configuración
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infrastructure.config.django_settings')

import django
django.setup()

print("=" * 80)
print("VALIDACIÓN DEL SISTEMA E-COMMERCE - CLEAN ARCHITECTURE")
print("=" * 80)
print()

# Ejecutar comandos de validación desde aquí
from infrastructure.persistence.django.models import ClienteModel
from uuid import uuid4

print("✅ Django configurado correctamente")
print(f"✅ Modelo ClienteModel importado: {ClienteModel}")
print(f"✅ Base de datos lista")
print()

# Verificar que la tabla existe
try:
    count = ClienteModel.objects.count()
    print(f"✅ Tabla 'clientes' existe - {count} registro(s)")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 80)
print("AHORA PUEDES USAR EL DJANGO SHELL:")
print("=" * 80)
print()
print("  python manage.py shell")
print()
print("Luego ejecutar:")
print()
print("  exec(open('scripts/shell_commands.py').read())")
print()
print("=" * 80)
