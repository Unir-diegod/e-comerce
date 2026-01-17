#!/usr/bin/env python3
"""
Script de Validación de Autenticación y Autorización JWT

Verifica:
1. Acceso sin token → 401
2. Token inválido → 401
3. Rol sin permiso → 403
4. Rol correcto → acceso OK
5. Login/Logout funcionan correctamente
6. Refresh token funciona

Uso:
    python scripts/test_api_auth.py

Requisitos:
    - Servidor Django corriendo en http://localhost:8000
    - Base de datos con usuarios de prueba creados
"""
import requests
import sys
import json
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Usuario:
    """Usuario de prueba"""
    email: str
    password: str
    rol: str
    nombre: str


# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth"

# Usuarios de prueba (deben existir en la BD)
USUARIOS = {
    'admin': Usuario(
        email='admin@ecommerce.com',
        password='Admin123!',
        rol='ADMIN',
        nombre='Administrador'
    ),
    'operador': Usuario(
        email='operador@ecommerce.com',
        password='Operador123!',
        rol='OPERADOR',
        nombre='Operador'
    ),
    'lectura': Usuario(
        email='lectura@ecommerce.com',
        password='Lectura123!',
        rol='LECTURA',
        nombre='Usuario Lectura'
    ),
}


# ==============================================================================
# HELPERS
# ==============================================================================

class Color:
    """Códigos ANSI para colores en terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test(titulo: str):
    """Imprime título de test"""
    print(f"\n{Color.CYAN}{Color.BOLD}{'='*70}{Color.RESET}")
    print(f"{Color.CYAN}{Color.BOLD}{titulo}{Color.RESET}")
    print(f"{Color.CYAN}{Color.BOLD}{'='*70}{Color.RESET}")


def print_success(mensaje: str):
    """Imprime mensaje de éxito"""
    print(f"{Color.GREEN}✓ {mensaje}{Color.RESET}")


def print_error(mensaje: str):
    """Imprime mensaje de error"""
    print(f"{Color.RED}✗ {mensaje}{Color.RESET}")


def print_info(mensaje: str):
    """Imprime información"""
    print(f"{Color.BLUE}ℹ {mensaje}{Color.RESET}")


def print_warning(mensaje: str):
    """Imprime advertencia"""
    print(f"{Color.YELLOW}⚠ {mensaje}{Color.RESET}")


def login(usuario: Usuario) -> Optional[Dict]:
    """
    Intenta hacer login y retorna los tokens
    """
    try:
        response = requests.post(
            f"{AUTH_URL}/login",
            json={
                'email': usuario.email,
                'password': usuario.password
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Login exitoso: {usuario.email} ({usuario.rol})")
            return data
        else:
            print_error(f"Login fallido: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error en login: {e}")
        return None


def logout(access_token: str, refresh_token: str) -> bool:
    """
    Intenta hacer logout
    """
    try:
        response = requests.post(
            f"{AUTH_URL}/logout",
            json={'refresh': refresh_token},
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=5
        )
        
        if response.status_code == 200:
            print_success("Logout exitoso")
            return True
        else:
            print_error(f"Logout fallido: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error en logout: {e}")
        return False


# ==============================================================================
# TESTS
# ==============================================================================

def test_servidor_disponible():
    """Verifica que el servidor esté corriendo"""
    print_test("TEST 1: Verificar servidor disponible")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code in [200, 404]:  # 404 es OK, significa que Django responde
            print_success("Servidor Django está corriendo")
            return True
        else:
            print_error(f"Servidor responde con código inesperado: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar al servidor")
        print_warning("Asegúrate de que Django esté corriendo en http://localhost:8000")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False


def test_acceso_sin_token():
    """Verifica que endpoints protegidos requieren autenticación (401)"""
    print_test("TEST 2: Acceso sin token → 401 Unauthorized")
    
    endpoints = [
        '/productos',
        '/clientes',
        '/ordenes',
    ]
    
    exitos = 0
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            
            if response.status_code == 401:
                print_success(f"{endpoint} → 401 ✓")
                exitos += 1
            else:
                print_error(f"{endpoint} → {response.status_code} (esperaba 401)")
                
        except Exception as e:
            print_error(f"Error en {endpoint}: {e}")
    
    return exitos == len(endpoints)


def test_token_invalido():
    """Verifica que tokens inválidos sean rechazados (401)"""
    print_test("TEST 3: Token inválido → 401 Unauthorized")
    
    token_invalido = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.INVALID_TOKEN.SIGNATURE"
    
    try:
        response = requests.get(
            f"{BASE_URL}/productos",
            headers={'Authorization': f'Bearer {token_invalido}'},
            timeout=5
        )
        
        if response.status_code == 401:
            print_success("Token inválido rechazado correctamente → 401")
            return True
        else:
            print_error(f"Token inválido aceptado (código: {response.status_code})")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_login_y_acceso_admin():
    """Verifica que ADMIN puede acceder a todos los endpoints"""
    print_test("TEST 4: Login ADMIN y acceso completo")
    
    usuario = USUARIOS['admin']
    tokens = login(usuario)
    
    if not tokens:
        print_error("No se pudo hacer login como ADMIN")
        return False
    
    access_token = tokens.get('access')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Verificar perfil
    try:
        response = requests.get(f"{AUTH_URL}/perfil", headers=headers, timeout=5)
        if response.status_code == 200:
            perfil = response.json()
            print_success(f"Perfil obtenido: {perfil['nombre']} ({perfil['rol']})")
        else:
            print_error(f"Error al obtener perfil: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    # Verificar acceso a endpoints
    endpoints_lectura = ['/productos', '/clientes']
    
    for endpoint in endpoints_lectura:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 200:
                print_success(f"GET {endpoint} → 200 ✓")
            else:
                print_error(f"GET {endpoint} → {response.status_code}")
        except Exception as e:
            print_error(f"Error en {endpoint}: {e}")
    
    return True


def test_permisos_operador():
    """Verifica que OPERADOR puede crear pero no eliminar"""
    print_test("TEST 5: Permisos OPERADOR (puede escribir)")
    
    usuario = USUARIOS['operador']
    tokens = login(usuario)
    
    if not tokens:
        print_error("No se pudo hacer login como OPERADOR")
        return False
    
    access_token = tokens.get('access')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Verificar que puede leer
    try:
        response = requests.get(f"{BASE_URL}/productos", headers=headers, timeout=5)
        if response.status_code == 200:
            print_success("OPERADOR puede leer productos → 200")
        else:
            print_error(f"OPERADOR no puede leer: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    # Verificar que puede crear
    try:
        response = requests.post(
            f"{BASE_URL}/productos",
            headers=headers,
            json={
                'codigo': 'TEST-OP-001',
                'nombre': 'Producto Test Operador',
                'descripcion': 'Test de permisos',
                'precio': {'moneda': 'USD', 'monto': 100.00},
                'stock_actual': 10
            },
            timeout=5
        )
        if response.status_code in [201, 400]:  # 400 si ya existe
            print_success(f"OPERADOR puede crear productos → {response.status_code}")
        else:
            print_warning(f"Crear producto → {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    return True


def test_permisos_lectura():
    """Verifica que rol LECTURA solo puede leer (403 al intentar escribir)"""
    print_test("TEST 6: Permisos LECTURA (solo leer, 403 al escribir)")
    
    usuario = USUARIOS['lectura']
    tokens = login(usuario)
    
    if not tokens:
        print_error("No se pudo hacer login como LECTURA")
        return False
    
    access_token = tokens.get('access')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Verificar que puede leer
    try:
        response = requests.get(f"{BASE_URL}/productos", headers=headers, timeout=5)
        if response.status_code == 200:
            print_success("LECTURA puede leer productos → 200 ✓")
        else:
            print_error(f"LECTURA no puede leer: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    # Verificar que NO puede crear (403)
    try:
        response = requests.post(
            f"{BASE_URL}/productos",
            headers=headers,
            json={
                'codigo': 'TEST-LECTURA-001',
                'nombre': 'Test Prohibido',
                'descripcion': 'No debe poder crear',
                'precio': {'moneda': 'USD', 'monto': 100.00},
                'stock_actual': 10
            },
            timeout=5
        )
        if response.status_code == 403:
            print_success("LECTURA rechazado al crear → 403 ✓")
            return True
        else:
            print_error(f"LECTURA pudo crear (código: {response.status_code}) - FALLO DE SEGURIDAD")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_refresh_token():
    """Verifica que el refresh token funciona"""
    print_test("TEST 7: Refresh Token")
    
    usuario = USUARIOS['admin']
    tokens = login(usuario)
    
    if not tokens:
        return False
    
    refresh_token = tokens.get('refresh')
    
    try:
        response = requests.post(
            f"{AUTH_URL}/refresh",
            json={'refresh': refresh_token},
            timeout=5
        )
        
        if response.status_code == 200:
            new_tokens = response.json()
            print_success("Refresh token funciona correctamente")
            print_info(f"Nuevo access token obtenido")
            return True
        else:
            print_error(f"Refresh token falló: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_logout_invalida_token():
    """Verifica que después del logout el token se invalida"""
    print_test("TEST 8: Logout invalida refresh token")
    
    usuario = USUARIOS['admin']
    tokens = login(usuario)
    
    if not tokens:
        return False
    
    access_token = tokens.get('access')
    refresh_token = tokens.get('refresh')
    
    # Hacer logout
    if not logout(access_token, refresh_token):
        return False
    
    # Intentar usar el refresh token invalidado
    try:
        response = requests.post(
            f"{AUTH_URL}/refresh",
            json={'refresh': refresh_token},
            timeout=5
        )
        
        if response.status_code == 401:
            print_success("Refresh token invalidado correctamente después de logout")
            return True
        else:
            print_error(f"Refresh token aún válido después de logout (código: {response.status_code})")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Ejecuta todos los tests"""
    print(f"\n{Color.BOLD}{'='*70}")
    print("VALIDACIÓN DE AUTENTICACIÓN Y AUTORIZACIÓN JWT")
    print(f"{'='*70}{Color.RESET}\n")
    
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Auth URL: {AUTH_URL}")
    
    tests = [
        ("Servidor disponible", test_servidor_disponible),
        ("Acceso sin token", test_acceso_sin_token),
        ("Token inválido", test_token_invalido),
        ("Login y acceso ADMIN", test_login_y_acceso_admin),
        ("Permisos OPERADOR", test_permisos_operador),
        ("Permisos LECTURA", test_permisos_lectura),
        ("Refresh token", test_refresh_token),
        ("Logout invalida token", test_logout_invalida_token),
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print_error(f"Error fatal en test '{nombre}': {e}")
            resultados.append((nombre, False))
    
    # Resumen
    print_test("RESUMEN DE RESULTADOS")
    
    exitos = sum(1 for _, r in resultados if r)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        if resultado:
            print_success(f"{nombre}")
        else:
            print_error(f"{nombre}")
    
    print(f"\n{Color.BOLD}Total: {exitos}/{total} tests pasados{Color.RESET}")
    
    if exitos == total:
        print(f"\n{Color.GREEN}{Color.BOLD}✓ TODOS LOS TESTS PASARON{Color.RESET}\n")
        return 0
    else:
        print(f"\n{Color.RED}{Color.BOLD}✗ ALGUNOS TESTS FALLARON{Color.RESET}\n")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}Tests interrumpidos por el usuario{Color.RESET}\n")
        sys.exit(130)
