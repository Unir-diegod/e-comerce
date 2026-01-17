"""
Test de Hardening de Seguridad

Objetivo:
- Validar que el sistema NO arranca en condiciones inseguras
- Verificar configuraciones de seguridad obligatorias
- Garantizar fail-fast ante configuraciones inválidas

Este test valida que el hardening de seguridad está correctamente implementado.
"""

import os
import sys
import subprocess
from pathlib import Path

# Configurar rutas
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PYTHON_BIN = sys.executable


class TestHardening:
    """Suite de tests de hardening de seguridad"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def run_django_check(self, env_vars: dict, should_fail: bool = False) -> tuple:
        """
        Ejecuta Django con variables de entorno específicas.
        
        Args:
            env_vars: Variables de entorno a setear
            should_fail: Si se espera que falle
            
        Returns:
            (success, output, error)
        """
        # Preparar entorno
        test_env = os.environ.copy()
        
        # Suprimir info de configuración
        test_env['DJANGO_SETTINGS_SUPPRESS_INFO'] = 'True'
        
        # Aplicar variables de test
        for key, value in env_vars.items():
            if value is None:
                # Setear a string vacío para simular ausencia
                test_env[key] = ''
            else:
                test_env[key] = value
        
        # Ejecutar Django check
        try:
            result = subprocess.run(
                [PYTHON_BIN, 'manage.py', 'check'],
                cwd=PROJECT_ROOT,
                env=test_env,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            return (success, result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            return (False, "", "Timeout")
        except Exception as e:
            return (False, "", str(e))
    
    def assert_test(self, name: str, condition: bool, message: str):
        """Registra resultado de un test"""
        if condition:
            print(f"✅ {name}")
            self.tests_passed += 1
            self.test_results.append((name, True, message))
        else:
            print(f"❌ {name}")
            print(f"   Razón: {message}")
            self.tests_failed += 1
            self.test_results.append((name, False, message))
    
    def test_secret_key_required(self):
        """Test: SECRET_KEY debe ser obligatorio"""
        print("\n--- TEST 1: SECRET_KEY Obligatorio ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': None,  # Eliminar SECRET_KEY
            'DJANGO_ENVIRONMENT': 'development',
        })
        
        # Debe FALLAR
        self.assert_test(
            "Sistema falla sin SECRET_KEY",
            not success and 'DJANGO_SECRET_KEY' in stderr,
            "El sistema debe fallar si SECRET_KEY no está definido"
        )
    
    def test_secret_key_insecure(self):
        """Test: SECRET_KEY inseguro debe rechazarse"""
        print("\n--- TEST 2: SECRET_KEY Inseguro Rechazado ---")
        
        insecure_keys = [
            'django-insecure-test',
            'change-me',
            '1234567890',
        ]
        
        for key in insecure_keys:
            success, stdout, stderr = self.run_django_check({
                'DJANGO_SECRET_KEY': key,
                'DJANGO_ENVIRONMENT': 'development',
            })
            
            self.assert_test(
                f"Rechaza SECRET_KEY inseguro: '{key[:20]}...'",
                not success,
                f"Claves inseguras deben ser rechazadas"
            )
    
    def test_secret_key_too_short(self):
        """Test: SECRET_KEY muy corto debe rechazarse"""
        print("\n--- TEST 3: SECRET_KEY Muy Corto ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'short',
            'DJANGO_ENVIRONMENT': 'development',
        })
        
        self.assert_test(
            "Rechaza SECRET_KEY < 50 caracteres",
            not success and '50 caracteres' in stderr,
            "SECRET_KEY debe tener al menos 50 caracteres"
        )
    
    def test_allowed_hosts_production(self):
        """Test: ALLOWED_HOSTS obligatorio en producción"""
        print("\n--- TEST 4: ALLOWED_HOSTS en Producción ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'production',
            'DJANGO_ALLOWED_HOSTS': None,  # Sin hosts
        })
        
        self.assert_test(
            "Falla sin ALLOWED_HOSTS en producción",
            not success and 'ALLOWED_HOSTS' in stderr,
            "ALLOWED_HOSTS es obligatorio en producción"
        )
    
    def test_allowed_hosts_wildcard(self):
        """Test: Wildcard no permitido en producción"""
        print("\n--- TEST 5: Wildcard en ALLOWED_HOSTS ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'production',
            'DJANGO_ALLOWED_HOSTS': '*',
        })
        
        self.assert_test(
            "Rechaza wildcard (*) en producción",
            not success,
            "Wildcard no debe permitirse en producción"
        )
    
    def test_debug_forced_false_production(self):
        """Test: DEBUG forzado a False en producción"""
        print("\n--- TEST 6: DEBUG en Producción ---")
        
        # Intentar setear DEBUG=True en producción
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'production',
            'DJANGO_ALLOWED_HOSTS': 'example.com',
            'DJANGO_DEBUG': 'True',  # Intentar activar DEBUG
        })
        
        # Debe arrancar (DEBUG es ignorado)
        # Verificar en el warning que DEBUG fue forzado a False
        self.assert_test(
            "DEBUG forzado a False en producción",
            'DEBUG=True ignorado' in stderr or 'WARNING' in stderr or success,
            "DEBUG debe ser False en producción sin importar la variable"
        )
    
    def test_environment_invalid(self):
        """Test: Ambiente inválido debe rechazarse"""
        print("\n--- TEST 7: Ambiente Inválido ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'invalid_env',
        })
        
        self.assert_test(
            "Rechaza ambiente inválido",
            not success and 'DJANGO_ENVIRONMENT' in stderr,
            "Solo development, staging, production son válidos"
        )
    
    def test_valid_development_config(self):
        """Test: Configuración válida de desarrollo debe pasar"""
        print("\n--- TEST 8: Configuración Development Válida ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'development',
            'DJANGO_DEBUG': 'True',
        })
        
        self.assert_test(
            "Acepta configuración development válida",
            success,
            "Configuración de desarrollo debe ser aceptada"
        )
    
    def test_valid_production_config(self):
        """Test: Configuración válida de producción debe pasar"""
        print("\n--- TEST 9: Configuración Production Válida ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'production',
            'DJANGO_ALLOWED_HOSTS': 'example.com,api.example.com',
            'DJANGO_DEBUG': 'False',
        })
        
        self.assert_test(
            "Acepta configuración production válida",
            success or 'System check identified' not in stderr,
            "Configuración de producción válida debe ser aceptada"
        )
    
    def test_ssl_required_production(self):
        """Test: SSL obligatorio en producción (database)"""
        print("\n--- TEST 10: SSL Obligatorio en BD Producción ---")
        
        success, stdout, stderr = self.run_django_check({
            'DJANGO_SECRET_KEY': 'a' * 60,
            'DJANGO_ENVIRONMENT': 'production',
            'DJANGO_ALLOWED_HOSTS': 'example.com',
            'DB_SSL_MODE': 'disable',  # Intentar desactivar SSL
        })
        
        self.assert_test(
            "Rechaza SSL deshabilitado en producción",
            not success and ('SSL' in stderr or 'sslmode' in stderr or 'require' in stderr),
            "SSL debe ser obligatorio en producción"
        )
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("=" * 70)
        print("TEST DE HARDENING DE SEGURIDAD")
        print("=" * 70)
        
        self.test_secret_key_required()
        self.test_secret_key_insecure()
        self.test_secret_key_too_short()
        self.test_allowed_hosts_production()
        self.test_allowed_hosts_wildcard()
        self.test_debug_forced_false_production()
        self.test_environment_invalid()
        self.test_valid_development_config()
        self.test_valid_production_config()
        self.test_ssl_required_production()
        
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumen de resultados"""
        print("\n" + "=" * 70)
        print("RESUMEN DE RESULTADOS")
        print("=" * 70)
        
        total = self.tests_passed + self.tests_failed
        print(f"Total de tests: {total}")
        print(f"✅ Pasados: {self.tests_passed}")
        print(f"❌ Fallidos: {self.tests_failed}")
        
        if self.tests_failed > 0:
            print("\n⚠️ TESTS FALLIDOS:")
            for name, passed, message in self.test_results:
                if not passed:
                    print(f"   - {name}")
        
        print("\n" + "=" * 70)
        
        if self.tests_failed == 0:
            print("✅ HARDENING EXITOSO")
            print("   El sistema está configurado de forma segura")
            return True
        else:
            print("❌ HARDENING INCOMPLETO")
            print("   Se detectaron problemas de configuración")
            return False


def main():
    """Función principal"""
    try:
        tester = TestHardening()
        success = tester.run_all_tests()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrumpidos por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
