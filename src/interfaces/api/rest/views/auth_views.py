"""
Views de Autenticación JWT

Endpoints para login, logout, refresh y verificación de tokens.

Incluye protección anti-abuso:
- Rate limiting estricto en login
- Bloqueo temporal por intentos fallidos
- Auditoría de todos los intentos
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
from interfaces.api.rest.throttling import (
    LoginRateThrottle,
    RefreshTokenRateThrottle,
    ServicioBloqueoTemporal
)

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para incluir información adicional del usuario
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar claims personalizados
        token['email'] = user.email
        token['nombre'] = user.nombre
        token['rol'] = user.rol
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información extra en la respuesta
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'nombre': self.user.nombre,
            'rol': self.user.rol,
        }
        
        # Auditar login exitoso
        ServicioAuditoria.registrar_acceso_api(
            usuario_id=str(self.user.id),
            endpoint='/api/v1/auth/login',
            metodo='POST',
            ip='unknown',
            user_agent='unknown',
            resultado_exitoso=True
        )
        
        return data


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login
    
    Autenticación con email y password.
    Retorna access_token y refresh_token.
    
    Permisos: Público (sin autenticación previa)
    
    Protección Anti-Abuso:
    - Rate limit: 5 intentos/minuto por IP
    - Bloqueo temporal tras 5 intentos fallidos consecutivos
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request, *args, **kwargs):
        """
        Sobrescribe post para manejar bloqueo temporal y auditoría.
        """
        # Obtener IP del cliente
        ip = self._get_client_ip(request)
        
        # Verificar si IP está bloqueada
        if ServicioBloqueoTemporal.esta_bloqueado_ip(ip):
            tiempo_restante = ServicioBloqueoTemporal.obtener_tiempo_restante_bloqueo(ip)
            return Response(
                {
                    'error': 'Demasiados intentos fallidos',
                    'detail': 'Ha excedido el número de intentos permitidos. '
                              'Por favor, espere antes de intentar nuevamente.',
                    'code': 'account_temporarily_locked'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={'Retry-After': str(tiempo_restante)}
            )
        
        try:
            response = super().post(request, *args, **kwargs)
            
            # Login exitoso: limpiar intentos fallidos
            if response.status_code == 200:
                ServicioBloqueoTemporal.limpiar_intentos(ip)
            
            return response
            
        except Exception as e:
            # Login fallido: registrar intento
            resultado = ServicioBloqueoTemporal.registrar_intento_fallido(
                ip=ip,
                endpoint='/api/v1/auth/login',
                motivo='credenciales_invalidas'
            )
            
            # Auditar intento fallido
            ServicioAuditoria.registrar_acceso_api(
                usuario_id=None,
                endpoint='/api/v1/auth/login',
                metodo='POST',
                ip=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', 'unknown')[:200],
                resultado_exitoso=False,
                codigo_estado=401
            )
            
            # Si se bloqueó, informar
            if resultado.get('bloqueado'):
                return Response(
                    {
                        'error': 'Cuenta bloqueada temporalmente',
                        'detail': 'Ha excedido el número de intentos permitidos. '
                                  'Por favor, espere antes de intentar nuevamente.',
                        'code': 'account_temporarily_locked'
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={'Retry-After': str(resultado.get('tiempo_bloqueo', 900))}
                )
            
            # Re-raise para que DRF maneje el error
            raise
    
    def _get_client_ip(self, request) -> str:
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip[:45]


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout
    
    Invalida el refresh token (blacklist).
    Requiere enviar el refresh_token en el body.
    
    Permisos: Usuario autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'refresh_token es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Invalidar el token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Auditar logout
            ServicioAuditoria.registrar_acceso_api(
                usuario_id=str(request.user.id),
                endpoint='/api/v1/auth/logout',
                metodo='POST',
                ip='unknown',
                user_agent='unknown',
                resultado_exitoso=True
            )
            
            return Response(
                {'mensaje': 'Sesión cerrada exitosamente'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': f'Error al cerrar sesión: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshTokenView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh
    
    Renueva el access_token usando el refresh_token.
    Genera un nuevo refresh_token y marca el anterior como inválido.
    
    Permisos: Público (usa refresh_token)
    
    Protección Anti-Abuso:
    - Rate limit: 10 requests/minuto por IP
    """
    permission_classes = [AllowAny]
    throttle_classes = [RefreshTokenRateThrottle]


class VerifyTokenView(TokenVerifyView):
    """
    POST /api/v1/auth/verify
    
    Verifica si un token es válido.
    
    Permisos: Público
    """
    permission_classes = [AllowAny]


class PerfilUsuarioView(APIView):
    """
    GET /api/v1/auth/perfil
    
    Obtiene información del usuario autenticado.
    
    Permisos: Usuario autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        return Response({
            'id': str(user.id),
            'email': user.email,
            'nombre': user.nombre,
            'rol': user.rol,
            'es_admin': user.es_admin,
            'es_operador': user.es_operador,
            'es_lectura': user.es_lectura,
            'puede_escribir': user.puede_escribir,
            'puede_eliminar': user.puede_eliminar,
            'fecha_creacion': user.fecha_creacion,
        }, status=status.HTTP_200_OK)
