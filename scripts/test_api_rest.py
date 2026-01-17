"""
Script de validación de API REST
Valida el flujo completo: Cliente → Producto → Orden → Confirmación
"""
import os
import sys
import django
import requests
from decimal import Decimal
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'infrastructure.config.django_settings')
django.setup()

# Configuración
BASE_URL = 'http://localhost:8000/api/v1'

def print_header(title):
    """Imprime encabezado de sección"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"✅ {message}")

def print_error(message):
    """Imprime mensaje de error"""
    print(f"❌ {message}")

def print_info(message):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {message}")

def test_crear_cliente():
    """Test: Crear cliente vía API"""
    print_header("TEST 1: Crear Cliente")
    
    payload = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "email": "juan.perez@example.com",
        "tipo_documento": "DNI",
        "numero_documento": "12345678",
        "telefono": "+51987654321"
    }
    
    print_info(f"POST {BASE_URL}/clientes")
    print_info(f"Payload: {payload}")
    
    response = requests.post(f'{BASE_URL}/clientes', json=payload)
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"Cliente creado: {data['id']}")
        print_info(f"Nombre: {data['nombre']} {data['apellido']}")
        print_info(f"Email: {data['email']}")
        return data['id']
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return None

def test_obtener_cliente(cliente_id):
    """Test: Obtener cliente por ID"""
    print_header("TEST 2: Obtener Cliente")
    
    print_info(f"GET {BASE_URL}/clientes/{cliente_id}")
    
    response = requests.get(f'{BASE_URL}/clientes/{cliente_id}')
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Cliente obtenido correctamente")
        print_info(f"ID: {data['id']}")
        print_info(f"Nombre: {data['nombre']} {data['apellido']}")
        return True
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return False

def test_crear_producto():
    """Test: Crear producto vía API"""
    print_header("TEST 3: Crear Producto")
    
    payload = {
        "codigo": "LAPTOP-001",
        "nombre": "Laptop Dell Inspiron",
        "descripcion": "Laptop 15 pulgadas, 8GB RAM, 256GB SSD",
        "precio_monto": "1200.50",
        "precio_moneda": "USD",
        "stock_actual": 10,
        "stock_minimo": 2
    }
    
    print_info(f"POST {BASE_URL}/productos/crear")
    print_info(f"Payload: {payload}")
    
    response = requests.post(f'{BASE_URL}/productos/crear', json=payload)
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"Producto creado: {data['id']}")
        print_info(f"Código: {data['codigo']}")
        print_info(f"Nombre: {data['nombre']}")
        print_info(f"Precio: {data['precio']}")
        print_info(f"Stock: {data['stock_actual']}")
        return data['id']
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return None

def test_listar_productos():
    """Test: Listar productos"""
    print_header("TEST 4: Listar Productos")
    
    print_info(f"GET {BASE_URL}/productos")
    
    response = requests.get(f'{BASE_URL}/productos')
    
    if response.status_code == 200:
        productos = response.json()
        print_success(f"Se encontraron {len(productos)} producto(s)")
        for p in productos:
            print_info(f"  - {p['codigo']}: {p['nombre']} (${p['precio_monto']})")
        return True
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return False

def test_crear_orden(cliente_id):
    """Test: Crear orden"""
    print_header("TEST 5: Crear Orden")
    
    payload = {
        "cliente_id": cliente_id
    }
    
    print_info(f"POST {BASE_URL}/ordenes")
    print_info(f"Payload: {payload}")
    
    response = requests.post(f'{BASE_URL}/ordenes', json=payload)
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"Orden creada: {data['id']}")
        print_info(f"Cliente: {data['cliente_id']}")
        print_info(f"Estado: {data['estado']}")
        print_info(f"Total: ${data['total']}")
        return data['id']
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return None

def test_agregar_linea(orden_id, producto_id):
    """Test: Agregar línea a orden"""
    print_header("TEST 6: Agregar Línea a Orden")
    
    payload = {
        "producto_id": producto_id,
        "cantidad": 2
    }
    
    print_info(f"POST {BASE_URL}/ordenes/{orden_id}/lineas")
    print_info(f"Payload: {payload}")
    
    response = requests.post(f'{BASE_URL}/ordenes/{orden_id}/lineas', json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Línea agregada a orden {data['id']}")
        print_info(f"Cantidad de items: {data['cantidad_items']}")
        print_info(f"Total: ${data['total']}")
        for linea in data['lineas']:
            print_info(f"  - Producto: {linea['producto_id']}")
            print_info(f"    Cantidad: {linea['cantidad']}")
            print_info(f"    Subtotal: ${linea['subtotal']}")
        return True
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return False

def test_confirmar_orden(orden_id):
    """Test: Confirmar orden (descuenta stock)"""
    print_header("TEST 7: Confirmar Orden")
    
    print_info(f"POST {BASE_URL}/ordenes/{orden_id}/confirmar")
    
    response = requests.post(f'{BASE_URL}/ordenes/{orden_id}/confirmar')
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Orden confirmada: {data['id']}")
        print_info(f"Estado: {data['estado']}")
        print_info(f"Total: ${data['total']}")
        print_info(f"Items: {data['cantidad_items']}")
        return True
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return False

def test_validar_stock_descontado(producto_id):
    """Test: Validar que el stock se descontó"""
    print_header("TEST 8: Validar Descuento de Stock")
    
    print_info(f"GET {BASE_URL}/productos/{producto_id}")
    
    response = requests.get(f'{BASE_URL}/productos/{producto_id}')
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Stock actual: {data['stock_actual']} unidades")
        
        if data['stock_actual'] == 8:  # 10 - 2 = 8
            print_success("Stock descontado correctamente")
            return True
        else:
            print_error(f"Stock incorrecto. Esperado: 8, Actual: {data['stock_actual']}")
            return False
    else:
        print_error(f"Error {response.status_code}: {response.text}")
        return False

def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 70)
    print("  VALIDACIÓN DE API REST - E-COMMERCE")
    print("=" * 70)
    print_info("Asegúrate de que el servidor Django está corriendo en localhost:8000")
    print_info("Comando: python manage.py runserver")
    
    try:
        # Test de conexión
        print_header("TEST 0: Conexión al servidor")
        try:
            response = requests.get('http://localhost:8000')
            print_success("Servidor Django accesible")
        except requests.exceptions.ConnectionError:
            print_error("No se puede conectar al servidor Django")
            print_info("Ejecuta: python manage.py runserver")
            sys.exit(1)
        
        # Flujo completo
        cliente_id = test_crear_cliente()
        if not cliente_id:
            print_error("Flujo abortado: No se pudo crear cliente")
            sys.exit(1)
        
        if not test_obtener_cliente(cliente_id):
            print_error("Flujo abortado: No se pudo obtener cliente")
            sys.exit(1)
        
        producto_id = test_crear_producto()
        if not producto_id:
            print_error("Flujo abortado: No se pudo crear producto")
            sys.exit(1)
        
        if not test_listar_productos():
            print_error("Flujo abortado: No se pudo listar productos")
            sys.exit(1)
        
        orden_id = test_crear_orden(cliente_id)
        if not orden_id:
            print_error("Flujo abortado: No se pudo crear orden")
            sys.exit(1)
        
        if not test_agregar_linea(orden_id, producto_id):
            print_error("Flujo abortado: No se pudo agregar línea")
            sys.exit(1)
        
        if not test_confirmar_orden(orden_id):
            print_error("Flujo abortado: No se pudo confirmar orden")
            sys.exit(1)
        
        if not test_validar_stock_descontado(producto_id):
            print_error("Flujo abortado: Stock no se descontó correctamente")
            sys.exit(1)
        
        # Resumen final
        print_header("RESUMEN DE VALIDACIÓN")
        print_success("Todos los tests pasaron correctamente")
        print_info("✅ API REST funcional")
        print_info("✅ Flujo completo validado")
        print_info("✅ Control de stock funcional")
        print_info("✅ Auditoría registrada (verificar en BD)")
        
        print("\n" + "=" * 70)
        print("  VALIDACIÓN EXITOSA")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
