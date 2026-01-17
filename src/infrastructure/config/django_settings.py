"""
Configuración de Django para el proyecto e-commerce

IMPORTANTE:
- Todas las configuraciones sensibles DEBEN venir de variables de entorno
- Nunca hardcodear passwords, secrets o configuraciones de producción
- Validar configuración al inicio para evitar errores en runtime
- El sistema falla de forma segura (fail-fast) si la configuración es inválida

REQUISITOS:
- DJANGO_SECRET_KEY: Obligatorio siempre
- DJANGO_ENVIRONMENT: development|staging|production
- DJANGO_ALLOWED_HOSTS: Lista separada por comas de hosts permitidos
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ============================================================================
# ENVIRONMENT VALIDATION (FAIL-FAST)
# ============================================================================

class ConfigurationError(Exception):
    """Excepción crítica de configuración que impide arrancar el sistema"""
    pass


def get_environment() -> str:
    """
    Obtiene el ambiente de ejecución.
    
    Returns:
        'development', 'staging', o 'production'
        
    Raises:
        ConfigurationError: Si no está definido o es inválido
    """
    env = os.environ.get('DJANGO_ENVIRONMENT', '').strip().lower()
    
    valid_environments = ['development', 'staging', 'production']
    
    if not env:
        # En desarrollo local, asumir development
        if os.path.exists(BASE_DIR / '.env'):
            env = 'development'
        else:
            raise ConfigurationError(
                "DJANGO_ENVIRONMENT no está definido. "
                "Debe ser: development, staging, o production"
            )
    
    if env not in valid_environments:
        raise ConfigurationError(
            f"DJANGO_ENVIRONMENT inválido: '{env}'. "
            f"Debe ser uno de: {', '.join(valid_environments)}"
        )
    
    return env


ENVIRONMENT = get_environment()
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_STAGING = ENVIRONMENT == 'staging'
IS_DEVELOPMENT = ENVIRONMENT == 'development'

# ============================================================================
# SECURITY SETTINGS (HARDENED)
# ============================================================================

# SECRET_KEY - OBLIGATORIO SIN FALLBACK
def get_secret_key() -> str:
    """
    Obtiene SECRET_KEY de forma segura.
    
    FAIL-FAST: Si no está definido, el sistema NO arranca.
    
    Returns:
        SECRET_KEY desde variable de entorno
        
    Raises:
        ConfigurationError: Si SECRET_KEY no está definido
    """
    secret_key = os.environ.get('DJANGO_SECRET_KEY', '').strip()
    
    if not secret_key:
        raise ConfigurationError(
            "DJANGO_SECRET_KEY no está definido. "
            "Este valor es OBLIGATORIO y debe ser un string aleatorio seguro. \n"
            "Genera uno con: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
        )
    
    # Validación adicional: no permitir claves inseguras conocidas
    insecure_keys = [
        'django-insecure',
        'change-me',
        'secret',
        '1234',
        'password',
        'dev-key'
    ]
    
    if any(insecure in secret_key.lower() for insecure in insecure_keys):
        raise ConfigurationError(
            "DJANGO_SECRET_KEY parece ser inseguro. "
            "No usar valores de desarrollo o placeholders en producción."
        )
    
    if len(secret_key) < 50:
        raise ConfigurationError(
            f"DJANGO_SECRET_KEY demasiado corto ({len(secret_key)} caracteres). "
            "Debe tener al menos 50 caracteres."
        )
    
    return secret_key


SECRET_KEY = get_secret_key()

# DEBUG - ESTRICTAMENTE CONTROLADO POR AMBIENTE
def get_debug_mode() -> bool:
    """
    Determina si DEBUG debe estar activo.
    
    REGLAS:
    - production: DEBUG siempre False, no override
    - staging: DEBUG siempre False
    - development: DEBUG puede configurarse (default True)
    
    Returns:
        bool indicando si DEBUG está activo
    """
    if IS_PRODUCTION or IS_STAGING:
        # PRODUCCION/STAGING: DEBUG siempre False, ignora variable de entorno
        debug_env = os.environ.get('DJANGO_DEBUG', 'False')
        if debug_env.lower() == 'true':
            print(
                f"WARNING: DJANGO_DEBUG=True ignorado en ambiente {ENVIRONMENT}. "
                f"DEBUG forzado a False por seguridad.",
                file=sys.stderr
            )
        return False
    else:
        # DEVELOPMENT: Permitir configuración
        return os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'


DEBUG = get_debug_mode()

# ALLOWED_HOSTS - VALIDADO Y OBLIGATORIO
def get_allowed_hosts() -> list:
    """
    Obtiene lista de hosts permitidos.
    
    FAIL-FAST: En producción, debe estar definido explícitamente.
    
    Returns:
        Lista de hosts permitidos
        
    Raises:
        ConfigurationError: Si no está definido en producción o es inválido
    """
    allowed_hosts_str = os.environ.get('DJANGO_ALLOWED_HOSTS', '').strip()
    
    # En producción/staging: OBLIGATORIO
    if (IS_PRODUCTION or IS_STAGING) and not allowed_hosts_str:
        raise ConfigurationError(
            f"DJANGO_ALLOWED_HOSTS es OBLIGATORIO en ambiente {ENVIRONMENT}. "
            "Debe ser una lista separada por comas de dominios permitidos."
        )
    
    # En desarrollo: permitir localhost por defecto
    if IS_DEVELOPMENT and not allowed_hosts_str:
        return ['localhost', '127.0.0.1', '[::1]']
    
    # Parsear lista
    hosts = [h.strip() for h in allowed_hosts_str.split(',') if h.strip()]
    
    # Validar que no esté vacío después de parsear
    if not hosts:
        raise ConfigurationError(
            "DJANGO_ALLOWED_HOSTS no puede estar vacío. "
            "Debe contener al menos un host válido."
        )
    
    # Prohibir wildcard en producción
    if (IS_PRODUCTION or IS_STAGING) and '*' in hosts:
        raise ConfigurationError(
            f"DJANGO_ALLOWED_HOSTS no puede contener '*' en ambiente {ENVIRONMENT}. "
            "Debe especificar hosts explícitamente."
        )
    
    return hosts


ALLOWED_HOSTS = get_allowed_hosts()

# ============================================================================
# HTTP SECURITY HEADERS (HARDENED)
# ============================================================================

# SSL/HTTPS (obligatorio en producción)
SECURE_SSL_REDIRECT = IS_PRODUCTION or IS_STAGING
SESSION_COOKIE_SECURE = IS_PRODUCTION or IS_STAGING
CSRF_COOKIE_SECURE = IS_PRODUCTION or IS_STAGING
SECURE_HSTS_SECONDS = 31536000 if IS_PRODUCTION else 0  # 1 año en producción
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PRODUCTION
SECURE_HSTS_PRELOAD = IS_PRODUCTION

# Protección contra clickjacking
X_FRAME_OPTIONS = 'DENY'

# Prevención de MIME sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Protección XSS (legacy, navegadores modernos)
SECURE_BROWSER_XSS_FILTER = True

# Referrer Policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# Session timeout (30 minutos)
SESSION_COOKIE_AGE = 1800

# ============================================================================
# APPLICATION DEFINITION
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST Framework
    'rest_framework_simplejwt',  # JWT Authentication
    'rest_framework_simplejwt.token_blacklist',  # Blacklist para logout
    'infrastructure.persistence.django',
    'infrastructure.auth',  # Sistema de autenticación y autorización
    'infrastructure',  # Para los management commands
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'interfaces.api.rest.middleware.RateLimitMiddleware',  # Protección anti-abuso (ANTES de auth)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'infrastructure.auth.middleware.AuditoriaAutenticacionMiddleware',  # Auditoría de accesos
    'interfaces.api.rest.middleware.SecurityHeadersMiddleware',  # Headers de seguridad adicionales
]

ROOT_URLCONF = 'infrastructure.config.django_urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'infrastructure.config.django_wsgi.application'

# ============================================================================
# DATABASE CONFIGURATION - PostgreSQL ONLY
# ============================================================================
# Importar configuración centralizada de base de datos
from infrastructure.config.database_config import DatabaseConfig

# Cargar y validar configuración de PostgreSQL desde variables de entorno
# Esto lanzará ErrorConfiguracion si falta alguna variable obligatoria
DATABASES = DatabaseConfig.from_env()

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# CUSTOM USER MODEL
# ============================================================================
AUTH_USER_MODEL = 'ecommerce_auth.Usuario'

# ============================================================================
# LOGGING CONFIGURATION (SEGURO)
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'] if DEBUG else [],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'infrastructure': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# ============================================================================
# DJANGO REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'interfaces.api.rest.exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PAGINATION_CLASS': None,  # Sin paginación por defecto
    
    # Autenticación JWT
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    
    # Permisos por defecto: requiere autenticación
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # =========================================================================
    # RATE LIMITING / THROTTLING (Protección Anti-Abuso)
    # =========================================================================
    # Clases de throttling aplicadas globalmente a todos los endpoints
    'DEFAULT_THROTTLE_CLASSES': [
        'interfaces.api.rest.throttling.GlobalAnonRateThrottle',
        'interfaces.api.rest.throttling.GlobalUserRateThrottle',
    ],
    
    # Configuración de rates por scope
    # Formato: 'scope': 'num_requests/period'
    # Periods válidos: second, minute, hour, day
    'DEFAULT_THROTTLE_RATES': {
        # Throttling global
        'anon_global': '50/minute',      # Anónimos: 50 req/min
        'user_global': '200/minute',     # Autenticados: 200 req/min
        
        # Throttling por endpoint crítico
        'login': '5/minute',             # Login: 5 intentos/min
        'token_refresh': '10/minute',    # Refresh: 10/min
        'orden_creacion': '20/minute',   # Crear órdenes: 20/min
        'orden_confirmacion': '10/minute', # Confirmar órdenes: 10/min
    },
}

# ============================================================================
# JWT CONFIGURATION (SimpleJWT)
# ============================================================================
from infrastructure.config.jwt_config import SIMPLE_JWT

# ============================================================================
# RATE LIMITING / BLOQUEO TEMPORAL CONFIGURATION
# ============================================================================
# Configuración de protección anti-abuso

# Máximo de intentos fallidos antes de bloqueo temporal
SECURITY_MAX_FAILED_ATTEMPTS = int(os.environ.get('SECURITY_MAX_FAILED_ATTEMPTS', 5))

# Duración del bloqueo en segundos (default: 15 minutos = 900 segundos)
SECURITY_BLOCK_DURATION = int(os.environ.get('SECURITY_BLOCK_DURATION', 900))

# Ventana de tiempo para contar intentos fallidos (default: 5 minutos = 300 segundos)
SECURITY_ATTEMPT_WINDOW = int(os.environ.get('SECURITY_ATTEMPT_WINDOW', 300))

# ============================================================================
# CACHE CONFIGURATION (Requerido para Rate Limiting)
# ============================================================================
# En producción, usar Redis o Memcached para mejor rendimiento
# El cache por defecto de Django es local-memory (suficiente para desarrollo)

CACHES = {
    'default': {
        # En desarrollo: cache en memoria
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache' if IS_DEVELOPMENT else 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'rate-limiting-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 10000,  # Máximo de entradas en cache
        }
    }
}

# NOTA: Para producción con múltiples instancias, configurar Redis:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
#     }
# }

# ============================================================================
# SECURITY CHECKS (VALIDACIÓN AL ARRANQUE)
# ============================================================================

# Imprimir resumen de configuración (sin datos sensibles)
if not os.environ.get('DJANGO_SETTINGS_SUPPRESS_INFO'):
    print("=" * 70)
    print("DJANGO SECURITY CONFIGURATION")
    print("=" * 70)
    print(f"Environment: {ENVIRONMENT}")
    print(f"DEBUG: {DEBUG}")
    print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    print(f"SSL Redirect: {SECURE_SSL_REDIRECT}")
    print(f"Secure Cookies: {SESSION_COOKIE_SECURE}")
    print(f"HSTS Enabled: {SECURE_HSTS_SECONDS > 0}")
    print(f"JWT Enabled: True (Access: 15min, Refresh: 1day)")
    print("=" * 70)
