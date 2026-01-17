"""
Test de Concurrencia: Validación de Control de Stock

Objetivo:
- Simular múltiples usuarios intentando comprar el último item simultáneamente
- Verificar que solo UNA orden se confirma
- Validar que el stock NUNCA sea negativo
- Confirmar que las demás órdenes fallan con error controlado

Este test valida la corrección del mecanismo de bloqueos pesimistas (SELECT FOR UPDATE)
implementado en PostgreSQL para prevenir overselling.
"""

import os
import sys
import django
from decimal import Decimal
from uuid import uuid4
import threading
import time
from collections import defaultdict

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
from domain.exceptions.dominio import ReglaNegocioViolada, EntidadNoEncontrada

from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from infrastructure.persistence.repositories.producto_repository_impl import ProductoRepositoryImpl
from infrastructure.persistence.repositories.orden_repository_impl import OrdenRepositoryImpl


class ResultadosTest:
    """Contenedor thread-safe para resultados del test"""
    def __init__(self):
        self.lock = threading.Lock()
        self.ordenes_exitosas = []
        self.ordenes_fallidas = []
        self.errores = []
    
    def registrar_exito(self, thread_id, orden_id):
        with self.lock:
            self.ordenes_exitosas.append({
                'thread': thread_id,
                'orden_id': orden_id
            })
    
    def registrar_fallo(self, thread_id, orden_id, error):
        with self.lock:
            self.ordenes_fallidas.append({
                'thread': thread_id,
                'orden_id': orden_id,
                'error': str(error)
            })
    
    def registrar_error(self, thread_id, error):
        with self.lock:
            self.errores.append({
                'thread': thread_id,
                'error': str(error)
            })


def intentar_compra_concurrente(
    thread_id: int,
    cliente_id,
    producto_id,
    cantidad: int,
    resultados: ResultadosTest,
    delay: float = 0
):
    """
    Simula un usuario intentando comprar un producto.
    Se ejecuta en un thread separado para simular concurrencia.
    """
    time.sleep(delay)  # Simular llegada escalonada
    
    repo_orden = OrdenRepositoryImpl()
    
    try:
        # 1. Crear orden en BORRADOR
        orden = Orden(cliente_id=cliente_id)
        
        # 2. Agregar línea
        linea = LineaOrden(
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=Dinero(Decimal("999.99"), "USD")
        )
        orden.agregar_linea(linea)
        
        # 3. Guardar orden en BORRADOR
        orden_guardada = repo_orden.guardar(orden)
        
        print(f"[Thread {thread_id}] Orden creada: {orden_guardada.id}")
        
        # 4. PUNTO CRÍTICO: Confirmar con descuento de stock
        # Aquí es donde ocurre el SELECT FOR UPDATE
        orden_confirmada = repo_orden.confirmar_con_stock(orden_guardada.id)
        
        print(f"✅ [Thread {thread_id}] ÉXITO - Orden confirmada: {orden_confirmada.id}")
        resultados.registrar_exito(thread_id, str(orden_confirmada.id))
        
    except ReglaNegocioViolada as e:
        print(f"❌ [Thread {thread_id}] FALLO - Stock insuficiente: {str(e)[:80]}")
        resultados.registrar_fallo(thread_id, None, e)
        
    except Exception as e:
        print(f"💥 [Thread {thread_id}] ERROR - {str(e)[:80]}")
        resultados.registrar_error(thread_id, e)


def test_concurrencia_stock_critico():
    """
    Test principal: Producto con stock 1, múltiples compradores simultáneos.
    Solo uno debe tener éxito.
    """
    print("=" * 70)
    print("TEST DE CONCURRENCIA: STOCK CRÍTICO (1 unidad)")
    print("=" * 70)
    
    repo_cliente = ClienteRepositoryImpl()
    repo_producto = ProductoRepositoryImpl()
    
    # ========================================
    # SETUP: Crear cliente y producto con stock 1
    # ========================================
    print("\n📦 SETUP: Creando datos de prueba...")
    
    # Cliente
    cliente = Cliente(
        nombre="Usuario",
        apellido="Test",
        email=Email(f"concurrent_{str(uuid4())[:6]}@test.com"),
        documento=DocumentoIdentidad(TipoDocumento.DNI, str(uuid4())[:8])
    )
    cliente = repo_cliente.guardar(cliente)
    print(f"✅ Cliente creado: {cliente.id}")
    
    # Producto con STOCK = 1 (crítico)
    producto = Producto(
        codigo=CodigoProducto(f"STOCK1-{str(uuid4())[:4]}"),
        nombre="Laptop Última Unidad",
        descripcion="Test de concurrencia",
        precio=Dinero(Decimal("999.99"), "USD"),
        stock_actual=1  # ⚠️ CRÍTICO: Solo 1 unidad
    )
    producto = repo_producto.guardar(producto)
    print(f"✅ Producto creado: {producto.id}")
    print(f"   Stock inicial: {producto.stock_actual}")
    
    # ========================================
    # TEST: 5 usuarios intentan comprar simultáneamente
    # ========================================
    print("\n🏁 INICIANDO TEST DE CONCURRENCIA...")
    print("   Simulando 5 usuarios comprando 1 unidad cada uno")
    print("   Resultado esperado: 1 éxito, 4 fallos\n")
    
    resultados = ResultadosTest()
    threads = []
    num_compradores = 5
    
    # Crear threads
    for i in range(num_compradores):
        thread = threading.Thread(
            target=intentar_compra_concurrente,
            args=(i, cliente.id, producto.id, 1, resultados, 0.01 * i)
        )
        threads.append(thread)
    
    # Lanzar todos los threads casi simultáneamente
    inicio = time.time()
    for thread in threads:
        thread.start()
    
    # Esperar a que todos terminen
    for thread in threads:
        thread.join()
    
    duracion = time.time() - inicio
    
    # ========================================
    # VALIDACIÓN DE RESULTADOS
    # ========================================
    print("\n" + "=" * 70)
    print("RESULTADOS DEL TEST")
    print("=" * 70)
    
    print(f"\n⏱️  Duración: {duracion:.2f} segundos")
    print(f"📊 Intentos totales: {num_compradores}")
    print(f"✅ Órdenes exitosas: {len(resultados.ordenes_exitosas)}")
    print(f"❌ Órdenes fallidas (stock insuficiente): {len(resultados.ordenes_fallidas)}")
    print(f"💥 Errores inesperados: {len(resultados.errores)}")
    
    # Mostrar detalles de órdenes exitosas
    if resultados.ordenes_exitosas:
        print("\n📋 Órdenes confirmadas:")
        for orden in resultados.ordenes_exitosas:
            print(f"   Thread {orden['thread']}: {orden['orden_id']}")
    
    # Verificar stock final
    producto_final = repo_producto.obtener_por_id(producto.id)
    print(f"\n📦 Stock final del producto: {producto_final.stock_actual}")
    print(f"   Stock esperado: 0")
    
    # ========================================
    # ASSERTIONS
    # ========================================
    print("\n" + "=" * 70)
    print("VALIDACIONES")
    print("=" * 70)
    
    exito_total = True
    
    # Validación 1: Solo 1 orden exitosa
    if len(resultados.ordenes_exitosas) == 1:
        print("✅ CORRECTO: Solo 1 orden se confirmó")
    else:
        print(f"❌ ERROR: Se confirmaron {len(resultados.ordenes_exitosas)} órdenes (esperado: 1)")
        exito_total = False
    
    # Validación 2: 4 órdenes fallidas
    if len(resultados.ordenes_fallidas) == 4:
        print("✅ CORRECTO: 4 órdenes fallaron por stock insuficiente")
    else:
        print(f"❌ ERROR: {len(resultados.ordenes_fallidas)} órdenes fallaron (esperado: 4)")
        exito_total = False
    
    # Validación 3: Sin errores inesperados
    if len(resultados.errores) == 0:
        print("✅ CORRECTO: No hubo errores inesperados")
    else:
        print(f"❌ ERROR: {len(resultados.errores)} errores inesperados")
        for err in resultados.errores:
            print(f"   Thread {err['thread']}: {err['error']}")
        exito_total = False
    
    # Validación 4: Stock final es 0
    if producto_final.stock_actual == 0:
        print("✅ CORRECTO: Stock final es 0 (no hay overselling)")
    else:
        print(f"❌ ERROR: Stock final es {producto_final.stock_actual} (esperado: 0)")
        exito_total = False
    
    # Validación 5: Stock nunca negativo
    if producto_final.stock_actual >= 0:
        print("✅ CORRECTO: Stock nunca fue negativo")
    else:
        print(f"❌ CRÍTICO: Stock negativo detectado: {producto_final.stock_actual}")
        exito_total = False
    
    print("\n" + "=" * 70)
    if exito_total:
        print("✅ TEST EXITOSO: Control de concurrencia funciona correctamente")
        print("   No se detectó overselling")
    else:
        print("❌ TEST FALLIDO: Se detectaron problemas de concurrencia")
    print("=" * 70)
    
    return exito_total


def test_concurrencia_stock_multiple():
    """
    Test secundario: Producto con stock 3, 5 compradores.
    3 deben tener éxito, 2 deben fallar.
    """
    print("\n\n" + "=" * 70)
    print("TEST DE CONCURRENCIA: STOCK MÚLTIPLE (3 unidades)")
    print("=" * 70)
    
    repo_cliente = ClienteRepositoryImpl()
    repo_producto = ProductoRepositoryImpl()
    
    # Setup
    print("\n📦 SETUP: Creando datos de prueba...")
    
    cliente = Cliente(
        nombre="Usuario",
        apellido="Test2",
        email=Email(f"concurrent2_{str(uuid4())[:6]}@test.com"),
        documento=DocumentoIdentidad(TipoDocumento.DNI, str(uuid4())[:8])
    )
    cliente = repo_cliente.guardar(cliente)
    
    producto = Producto(
        codigo=CodigoProducto(f"STOCK3-{str(uuid4())[:4]}"),
        nombre="Mouse Gaming",
        descripcion="Test concurrencia stock múltiple",
        precio=Dinero(Decimal("79.99"), "USD"),
        stock_actual=3  # 3 unidades
    )
    producto = repo_producto.guardar(producto)
    print(f"✅ Producto creado con stock: {producto.stock_actual}")
    
    # Test
    print("\n🏁 INICIANDO TEST...")
    print("   5 usuarios intentan comprar 1 unidad cada uno")
    print("   Resultado esperado: 3 éxitos, 2 fallos\n")
    
    resultados = ResultadosTest()
    threads = []
    
    for i in range(5):
        thread = threading.Thread(
            target=intentar_compra_concurrente,
            args=(i, cliente.id, producto.id, 1, resultados, 0.01 * i)
        )
        threads.append(thread)
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Resultados
    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)
    print(f"✅ Órdenes exitosas: {len(resultados.ordenes_exitosas)}")
    print(f"❌ Órdenes fallidas: {len(resultados.ordenes_fallidas)}")
    
    producto_final = repo_producto.obtener_por_id(producto.id)
    print(f"📦 Stock final: {producto_final.stock_actual} (esperado: 0)")
    
    exito = (
        len(resultados.ordenes_exitosas) == 3 and
        len(resultados.ordenes_fallidas) == 2 and
        producto_final.stock_actual == 0
    )
    
    if exito:
        print("\n✅ TEST EXITOSO")
    else:
        print("\n❌ TEST FALLIDO")
    
    return exito


if __name__ == "__main__":
    try:
        print("\n🚀 INICIANDO SUITE DE TESTS DE CONCURRENCIA\n")
        
        # Test 1: Stock crítico (1 unidad)
        test1_ok = test_concurrencia_stock_critico()
        
        # Test 2: Stock múltiple (3 unidades)
        test2_ok = test_concurrencia_stock_multiple()
        
        # Resumen final
        print("\n\n" + "=" * 70)
        print("RESUMEN FINAL")
        print("=" * 70)
        print(f"Test 1 (Stock crítico): {'✅ PASS' if test1_ok else '❌ FAIL'}")
        print(f"Test 2 (Stock múltiple): {'✅ PASS' if test2_ok else '❌ FAIL'}")
        
        if test1_ok and test2_ok:
            print("\n🎉 TODOS LOS TESTS PASARON")
            print("   El sistema está protegido contra overselling")
            sys.exit(0)
        else:
            print("\n⚠️ ALGUNOS TESTS FALLARON")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
