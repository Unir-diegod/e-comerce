"""
Configuración de Base de Datos para el proyecto E-Commerce

Responsabilidades:
- Centralizar configuración de base de datos
- Validar variables de entorno obligatorias
- Proveer configuración segura para Django
- Soportar múltiples entornos (dev, staging, prod)
"""
import os
from typing import Dict, Any
from dataclasses import dataclass


class ErrorConfiguracion(Exception):
    """Excepción lanzada cuando la configuración de BD es inválida"""
    pass


@dataclass
class DatabaseConfig:
    """
    Configuración centralizada de base de datos.
    
    Carga y valida todas las variables de entorno necesarias
    para conectarse a PostgreSQL de forma segura.
    """
    
    engine: str
    name: str
    user: str
    password: str
    host: str
    port: str
    ssl_mode: str
    
    @classmethod
    def from_env(cls) -> Dict[str, Any]:
        """
        Construye la configuración de Django DATABASES desde variables de entorno.
        
        Returns:
            Dict con configuración completa para Django DATABASES
            
        Raises:
            ErrorConfiguracion: Si falta alguna variable obligatoria o es inválida
        """
        # Leer variables de entorno
        db_engine = os.environ.get('DB_ENGINE', '').strip()
        db_name = os.environ.get('DB_NAME', '').strip()
        db_user = os.environ.get('DB_USER', '').strip()
        db_password = os.environ.get('DB_PASSWORD', '').strip()
        db_host = os.environ.get('DB_HOST', '').strip()
        db_port = os.environ.get('DB_PORT', '').strip()
        db_ssl_mode = os.environ.get('DB_SSL_MODE', 'require').strip()
        
        # Validaciones estrictas
        errores = []
        
        if not db_engine:
            errores.append("DB_ENGINE es obligatorio")
        elif db_engine not in ['postgresql', 'postgres']:
            errores.append(f"DB_ENGINE '{db_engine}' no soportado. Use 'postgresql'")
        
        if not db_name:
            errores.append("DB_NAME es obligatorio")
        
        if not db_user:
            errores.append("DB_USER es obligatorio")
        
        if not db_password:
            errores.append("DB_PASSWORD es obligatorio (nunca dejar vacío en producción)")
        
        if not db_host:
            errores.append("DB_HOST es obligatorio")
        
        if not db_port:
            errores.append("DB_PORT es obligatorio")
        else:
            try:
                port_int = int(db_port)
                if port_int < 1 or port_int > 65535:
                    errores.append(f"DB_PORT debe estar entre 1 y 65535, recibido: {db_port}")
            except ValueError:
                errores.append(f"DB_PORT debe ser un número, recibido: {db_port}")
        
        if db_ssl_mode not in ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']:
            errores.append(
                f"DB_SSL_MODE '{db_ssl_mode}' no válido. "
                f"Valores permitidos: disable, allow, prefer, require, verify-ca, verify-full"
            )
        
        # Lanzar excepción si hay errores
        if errores:
            raise ErrorConfiguracion(
                "Errores en configuración de base de datos:\n" +
                "\n".join(f"  - {error}" for error in errores)
            )
        
        # Construir configuración de Django
        config = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
                'OPTIONS': {
                    'sslmode': db_ssl_mode,
                    # Optimizaciones de conexión
                    'connect_timeout': 10,
                    'options': '-c search_path=public',
                },
                'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),
                'ATOMIC_REQUESTS': os.environ.get('DB_ATOMIC_REQUESTS', 'True') == 'True',
            }
        }
        
        # Configuración adicional para pool de conexiones en producción
        environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')
        
        if environment in ['production', 'staging']:
            config['default']['CONN_MAX_AGE'] = 600  # 10 minutos
            config['default']['CONN_HEALTH_CHECKS'] = True
            
            # VALIDACIÓN CRÍTICA: SSL obligatorio en producción
            if db_ssl_mode not in ['require', 'verify-ca', 'verify-full']:
                raise ErrorConfiguracion(
                    f"SSL inseguro en ambiente {environment}. "
                    f"DB_SSL_MODE debe ser 'require', 'verify-ca', o 'verify-full'. "
                    f"Valor actual: '{db_ssl_mode}'"
                )
        
        return config
    
    @classmethod
    def validate_connection(cls) -> bool:
        """
        Valida que se puede establecer conexión con la base de datos.
        Útil para health checks en producción.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            from django.db import connection
            connection.ensure_connection()
            return True
        except Exception as e:
            print(f"Error al conectar con la base de datos: {e}")
            return False
    
    @classmethod
    def get_info(cls) -> Dict[str, str]:
        """
        Retorna información NO sensible de la configuración.
        Útil para logs y debugging.
        
        Returns:
            Dict con información de configuración (sin passwords)
        """
        return {
            'engine': os.environ.get('DB_ENGINE', 'not_configured'),
            'name': os.environ.get('DB_NAME', 'not_configured'),
            'user': os.environ.get('DB_USER', 'not_configured'),
            'host': os.environ.get('DB_HOST', 'not_configured'),
            'port': os.environ.get('DB_PORT', 'not_configured'),
            'ssl_mode': os.environ.get('DB_SSL_MODE', 'require'),
            'password': '***HIDDEN***',
        }
