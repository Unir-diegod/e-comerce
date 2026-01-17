import os
import sys
import django
import uuid
import json

# Configurar entorno para que Django encuentre los settings
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infrastructure.config.django_settings")
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

def verify_api_flow():
    print("[*] INICIANDO VERIFICACION DE API REST (E2E)")
    client = APIClient()
    base_url = "/api/v1"
    
    # 1. Crear Cliente
    print("\n[1] CREANDO CLIENTE...")
    suffix = str(uuid.uuid4())[:8]
    data_cliente = {
        "nombre": "Test",
        "apellido": "User",
        "email": f"test.user.{suffix}@example.com",
        "tipo_documento": "DNI",
        "numero_documento": suffix,
        "telefono": "555-12345678"
    }
    resp = client.post(f"{base_url}/clientes", data_cliente, format='json')
    if resp.status_code != 201:
        print(f"[ERROR] Fallo crear cliente: {resp.status_code}")
        if hasattr(resp, 'data'):
            print(f"[ERROR] Detail: {resp.data}")
        else:
            content = resp.content.decode()
            if "Exception Value" in content:
                # ... same logic ...
                pass
            print(f"[ERROR] Raw Content: {content[:200]}")
        return
    cliente_id = resp.data['id']
    print(f"[OK] Cliente creado ID: {cliente_id}")

    # 2. Crear Producto
    print("\n[2] CREANDO PRODUCTO...")
    data_producto = {
        "codigo": f"SKU-{suffix}",
        "nombre": "Producto Test",
        "descripcion": "Descripción de prueba",
        "precio_monto": 100.00,
        "precio_moneda": "USD",
        "stock_actual": 50,
        "stock_minimo": 5
    }
    resp = client.post(f"{base_url}/productos", data_producto, format='json')
    if resp.status_code != 201:
        content = resp.data if hasattr(resp, 'data') else resp.content.decode()
        print(f"[ERROR] Fallo crear producto: {resp.status_code} - {content}")
        return
    producto_id = resp.data['id']
    print(f"[OK] Producto creado ID: {producto_id}")

    # 3. Crear Orden
    print("\n[3] CREANDO ORDEN...")
    data_orden = {
        "cliente_id": cliente_id
    }
    resp = client.post(f"{base_url}/ordenes", data_orden, format='json')
    if resp.status_code != 201:
        content = resp.data if hasattr(resp, 'data') else resp.content.decode()
        print(f"[ERROR] Fallo crear orden: {resp.status_code} - {content}")
        return
    orden_id = resp.data['id']
    print(f"[OK] Orden creada ID: {orden_id}")

    # 4. Agregar Línea
    print("\n[4] AGREGANDO LINEA A ORDEN...")
    data_linea = {
        "producto_id": producto_id,
        "cantidad": 2
    }
    resp = client.post(f"{base_url}/ordenes/{orden_id}/lineas", data_linea, format='json')
    if resp.status_code != 201:
        content = resp.data if hasattr(resp, 'data') else resp.content.decode()
        print(f"[ERROR] Fallo agregar linea: {resp.status_code} - {content}")
        return
    print(f"[OK] Linea agregada. Total: {resp.data['total']}, Items: {resp.data['cantidad_items']}")

    # 5. Confirmar Orden
    print("\n[5] CONFIRMANDO ORDEN...")
    resp = client.post(f"{base_url}/ordenes/{orden_id}/confirmar", {}, format='json')
    if resp.status_code != 200:
        content = resp.data if hasattr(resp, 'data') else resp.content.decode()
        print(f"[ERROR] Fallo confirmar orden: {resp.status_code} - {content}")
        # Si falla por concurrencia o stock, es útil saber
        return
    
    estado = resp.data['estado']
    if estado == "CONFIRMADA":
        print(f"[OK] Orden confirmada exitosamente. Estado: {estado}")
    else:
        print(f"[WARN] Orden procesada pero estado es: {estado}")

    print("\n[*] VERIFICACION COMPLETADA EXITOSAMENTE")

if __name__ == "__main__":
    verify_api_flow()
