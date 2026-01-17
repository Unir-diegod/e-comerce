"""
Configuración de JWT (JSON Web Tokens) para Autenticación

Este módulo centraliza la configuración de SimpleJWT para el proyecto.
"""
from datetime import timedelta
from infrastructure.config.django_settings import SECRET_KEY, IS_PRODUCTION, IS_STAGING


# ============================================================================
# SIMPLE JWT CONFIGURATION
# ============================================================================

SIMPLE_JWT = {
    # Tiempo de vida de los tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Token de acceso: 15 minutos
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),     # Token de refresco: 1 día
    
    # Rotación de refresh tokens (seguridad adicional)
    'ROTATE_REFRESH_TOKENS': True,      # Generar nuevo refresh token al refrescar
    'BLACKLIST_AFTER_ROTATION': True,   # Invalidar refresh token anterior
    
    # Algoritmo de firma
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Token en cookies (opcional, por defecto en header)
    'AUTH_COOKIE': None,
    'AUTH_COOKIE_SECURE': IS_PRODUCTION or IS_STAGING,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SAMESITE': 'Strict',
    
    # Claims personalizados
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',  # JWT ID para blacklist
    
    # Sliding tokens (opcional, deshabilitado)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    
    # Validaciones
    'UPDATE_LAST_LOGIN': True,  # Actualizar fecha de último login
    
    # Serializers personalizados (usando los default)
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
}
