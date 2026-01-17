"""
Script de validación de persistencia de auditoría

Objetivo:
- Verificar que los registros de auditoría se persisten correctamente en PostgreSQL
- Validar la inmutabilidad de los registros
- Confirmar que la auditoría no interrumpe las operaciones principales
"""

import os
import sys
import django
from decimal import Decimal
from uuid import uuid4

# Configurar entorno
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infrastructure.config.django_settings")
django.setup()

from domain.entities.cliente import Cliente
from domain.entities.producto import Producto
from domain.entities.orden import Orden
from domain.value_objects.email import Email
from domain.value_objects.codigo_producto import CodigoProducto
from domain.value_objects.documento_identidad import DocumentoIdentidad
from domain.value_objects.dinero import Dinero
from domain.value_objects.linea_orden import LineaOrden
from shared.enums.tipos_documento import TipoDocumento

from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from infrastructure.persistence.repositories.producto_repository_impl import ProductoRepositoryImpl
from infrastructure.persistence.repositories.orden_repository_impl import OrdenRepositoryImpl
from infrastructure.persistence.django.models import RegistroAuditoriaModel


def test_auditoria_persistencia():
    print("=" * 70)
    print("TEST DE AUDITORÍA: PERSISTENCIA EN POSTGRESQL")
    print("=" * 70)
    
    # Contar registros iniciales
    registros_iniciales = RegistroAuditoriaModel.objects.count()
    print(f"\n📊 Registros de auditoría iniciales: {registros_iniciales}")
    
    repo_cliente = ClienteRepositoryImpl()
    repo_producto = ProductoRepositoryImpl()
    repo_orden = OrdenRepositoryImpl()
    
    # ========================================
    # TEST 1: CREAR CLIENTE
    # ========================================
    print("\n--- TEST 1: Crear Cliente ---")
    email_val = f"audit_test_{str(uuid4())[:6]}@test.com"
    cliente = Cliente(
        nombre="Juan",
        apellido="Pérez",
        email=Email(email_val),
        documento=DocumentoIdentidad(TipoDocumento.DNI, str(uuid4())[:8])
    )
    cliente = repo_cliente.guardar(cliente)
    print(f"✅ Cliente creado: {cliente.id}")
    
    # Verificar auditoría
    auditoria_cliente = RegistroAuditoriaModel.objects.filter(
        entidad_tipo="Cliente",
        entidad_id=cliente.id,
        accion="CREATE"
    )
    if auditoria_cliente.exists():
        print(f"✅ Registro de auditoría creado para Cliente")
        registro = auditoria_cliente.first()
        print(f"   - ID: {registro.id}")
        print(f"   - Timestamp: {registro.timestamp}")
        print(f"   - Resultado: {registro.resultado}")
    else:
        print("❌ No se encontró registro de auditoría para Cliente")
    
    # ========================================
    # TEST 2: ACTUALIZAR CLIENTE
    # ========================================
    print("\n--- TEST 2: Actualizar Cliente ---")
    cliente_recuperado = repo_cliente.obtener_por_id(cliente.id)
    cliente_recuperado.actualizar_email(Email(f"updated_{email_val}"))
    repo_cliente.guardar(cliente_recuperado)
    print(f"✅ Cliente actualizado")
    
    # Verificar auditoría de UPDATE
    auditoria_update = RegistroAuditoriaModel.objects.filter(
        entidad_tipo="Cliente",
        entidad_id=cliente.id,
        accion="UPDATE"
    )
    if auditoria_update.exists():
        print(f"✅ Registro de auditoría UPDATE creado")
    else:
        print("❌ No se encontró registro de auditoría UPDATE")
    
    # ========================================
    # TEST 3: CREAR PRODUCTO
    # ========================================
    print("\n--- TEST 3: Crear Producto ---")
    codigo_val = f"AUD-{str(uuid4())[:6]}"
    producto = Producto(
        codigo=CodigoProducto(codigo_val),
        nombre="Monitor 4K",
        descripcion="Monitor para testing",
        precio=Dinero(Decimal("799.99")),
        stock_actual=100
    )
    producto = repo_producto.guardar(producto)
    print(f"✅ Producto creado: {producto.id}")
    
    # Verificar auditoría
    auditoria_producto = RegistroAuditoriaModel.objects.filter(
        entidad_tipo="Producto",
        entidad_id=producto.id
    )
    if auditoria_producto.exists():
        print(f"✅ Registro de auditoría creado para Producto")
    else:
        print("❌ No se encontró registro de auditoría para Producto")
    
    # ========================================
    # TEST 4: CREAR ORDEN
    # ========================================
    print("\n--- TEST 4: Crear Orden ---")
    orden = Orden(cliente_id=cliente.id)
    linea = LineaOrden(
        producto_id=producto.id,
        cantidad=2,
        precio_unitario=producto.precio
    )
    orden.agregar_linea(linea)
    orden_guardada = repo_orden.guardar(orden)
    print(f"✅ Orden creada: {orden_guardada.id}")
    
    # Verificar auditoría
    auditoria_orden = RegistroAuditoriaModel.objects.filter(
        entidad_tipo="Orden",
        entidad_id=orden_guardada.id
    )
    if auditoria_orden.exists():
        print(f"✅ Registro de auditoría creado para Orden")
        registro = auditoria_orden.first()
        if registro.mensaje:
            print(f"   - Mensaje: {registro.mensaje}")
    else:
        print("❌ No se encontró registro de auditoría para Orden")
    
    # ========================================
    # TEST 5: INMUTABILIDAD
    # ========================================
    print("\n--- TEST 5: Verificar Inmutabilidad ---")
    try:
        registro_test = RegistroAuditoriaModel.objects.first()
        if registro_test:
            original_mensaje = registro_test.mensaje
            registro_test.mensaje = "INTENTO DE MODIFICACIÓN"
            registro_test.save()
            print("❌ FALLO: Se permitió modificar un registro de auditoría")
        else:
            print("⚠️ No hay registros para probar inmutabilidad")
    except ValueError as e:
        print(f"✅ Inmutabilidad protegida: {str(e)}")
    except Exception as e:
        print(f"⚠️ Excepción inesperada: {str(e)}")
    
    # ========================================
    # TEST 6: PROTECCIÓN CONTRA DELETE
    # ========================================
    print("\n--- TEST 6: Protección contra Eliminación ---")
    try:
        registro_test = RegistroAuditoriaModel.objects.first()
        if registro_test:
            registro_test.delete()
            print("❌ FALLO: Se permitió eliminar un registro de auditoría")
        else:
            print("⚠️ No hay registros para probar eliminación")
    except ValueError as e:
        print(f"✅ Eliminación bloqueada: {str(e)}")
    except Exception as e:
        print(f"⚠️ Excepción inesperada: {str(e)}")
    
    # ========================================
    # RESUMEN FINAL
    # ========================================
    print("\n" + "=" * 70)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    registros_finales = RegistroAuditoriaModel.objects.count()
    registros_nuevos = registros_finales - registros_iniciales
    
    print(f"📊 Registros iniciales: {registros_iniciales}")
    print(f"📊 Registros finales: {registros_finales}")
    print(f"📊 Registros nuevos creados: {registros_nuevos}")
    
    # Desglose por tipo de entidad
    print("\n📋 Desglose por entidad:")
    for entidad_tipo in ["Cliente", "Producto", "Orden"]:
        count = RegistroAuditoriaModel.objects.filter(entidad_tipo=entidad_tipo).count()
        print(f"   - {entidad_tipo}: {count} registros")
    
    # Desglose por acción
    print("\n📋 Desglose por acción:")
    for accion in ["CREATE", "UPDATE", "DELETE"]:
        count = RegistroAuditoriaModel.objects.filter(accion=accion).count()
        print(f"   - {accion}: {count} registros")
    
    # Últimos 5 registros
    print("\n📜 Últimos 5 registros de auditoría:")
    ultimos = RegistroAuditoriaModel.objects.order_by('-timestamp')[:5]
    for reg in ultimos:
        print(f"   [{reg.timestamp.strftime('%H:%M:%S')}] {reg.entidad_tipo} - {reg.accion} - {reg.resultado}")
    
    print("\n" + "=" * 70)
    print("✅ VALIDACIÓN COMPLETADA")
    print("=" * 70)
    
    # Verificación de éxito
    if registros_nuevos >= 3:  # Al menos Cliente CREATE, Producto CREATE, Orden CREATE
        print("\n✅ ÉXITO: La auditoría está persistiendo correctamente")
        return True
    else:
        print("\n❌ FALLO: Se esperaban al menos 3 registros nuevos")
        return False


if __name__ == "__main__":
    try:
        exito = test_auditoria_persistencia()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
