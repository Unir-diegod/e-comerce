"""
Middleware de Protección contra Abuso

Este middleware proporciona protección a nivel de capa HTTP contra:
- Bloqueo de IPs con demasiados intentos fallidos
- Bloqueo de usuarios con actividad sospechosa
- Detección de patrones de abuso

Se integra con el sistema de auditoría existente.

OWASP References:
- API4:2023 - Unrestricted Resource Consumption
- API2:2023 - Broken Authentication
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
import hashlib
import time


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware que verifica bloqueos temporales ANTES de procesar requests.
    
    Funciona en conjunto con:
    - ServicioBloqueoTemporal (throttling.py)
    - Throttle classes de DRF
    
    Se ejecuta antes del routing de DRF para bloquear requests
    de IPs/usuarios bloqueados de forma temprana.
    """
    
    # Endpoints críticos que requieren verificación de bloqueo
    ENDPOINTS_CRITICOS = [
        '/api/v1/auth/login',
        '/api/v1/auth/refresh',
        '/api/v1/ordenes',
    ]
    
    # Endpoints excluidos de verificación (health checks, etc.)
    ENDPOINTS_EXCLUIDOS = [
        '/admin/',
        '/static/',
        '/health/',
        '/api/v1/auth/verify',  # Solo verifica tokens, no autenticación
    ]
    
    def process_request(self, request):
        """
        Verifica bloqueos antes de procesar la request.
        
        Returns:
            None si la request puede continuar
            JsonResponse 429 si está bloqueado
        """
        path = request.path
        
        # Excluir endpoints no críticos
        if self._es_excluido(path):
            return None
        
        # Solo verificar endpoints críticos
        if not self._es_critico(path):
            return None
        
        # Obtener IP del cliente
        ip = self._obtener_ip(request)
        
        # Verificar bloqueo de IP
        if self._esta_bloqueado_ip(ip):
            tiempo_restante = self._obtener_tiempo_restante(ip)
            return self._respuesta_bloqueado(
                tiempo_restante,
                motivo='ip_bloqueada'
            )
        
        # Verificar bloqueo de usuario (si está autenticado)
        usuario_id = self._obtener_usuario_id(request)
        if usuario_id and self._esta_bloqueado_usuario(usuario_id):
            return self._respuesta_bloqueado(
                self._obtener_tiempo_restante_usuario(usuario_id),
                motivo='usuario_bloqueado'
            )
        
        return None
    
    def process_response(self, request, response):
        """
        Procesa la respuesta para registrar intentos fallidos.
        
        Detecta fallos de autenticación y los registra para
        el sistema de bloqueo temporal.
        """
        path = request.path
        
        # Solo procesar endpoints de autenticación
        if '/auth/login' not in path:
            return response
        
        # Si es un fallo de autenticación (401)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            ip = self._obtener_ip(request)
            self._registrar_intento_fallido(ip, path)
        
        # Si es exitoso, limpiar intentos
        elif response.status_code == status.HTTP_200_OK:
            ip = self._obtener_ip(request)
            usuario_id = self._obtener_usuario_id(request)
            self._limpiar_intentos(ip, usuario_id)
        
        return response
    
    def _es_excluido(self, path: str) -> bool:
        """Verifica si el endpoint está excluido."""
        return any(path.startswith(excl) for excl in self.ENDPOINTS_EXCLUIDOS)
    
    def _es_critico(self, path: str) -> bool:
        """Verifica si el endpoint es crítico."""
        return any(path.startswith(crit) for crit in self.ENDPOINTS_CRITICOS)
    
    def _obtener_ip(self, request) -> str:
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip[:45]
    
    def _obtener_usuario_id(self, request) -> str:
        """Obtiene el ID del usuario si está autenticado."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        return None
    
    def _esta_bloqueado_ip(self, ip: str) -> bool:
        """Verifica si la IP está bloqueada."""
        try:
            from interfaces.api.rest.throttling import ServicioBloqueoTemporal
            return ServicioBloqueoTemporal.esta_bloqueado_ip(ip)
        except Exception:
            return False
    
    def _esta_bloqueado_usuario(self, usuario_id: str) -> bool:
        """Verifica si el usuario está bloqueado."""
        try:
            from interfaces.api.rest.throttling import ServicioBloqueoTemporal
            return ServicioBloqueoTemporal.esta_bloqueado_usuario(usuario_id)
        except Exception:
            return False
    
    def _obtener_tiempo_restante(self, ip: str) -> int:
        """Obtiene tiempo restante de bloqueo para IP."""
        try:
            from interfaces.api.rest.throttling import ServicioBloqueoTemporal
            return ServicioBloqueoTemporal.obtener_tiempo_restante_bloqueo(ip)
        except Exception:
            return 900  # Default 15 minutos
    
    def _obtener_tiempo_restante_usuario(self, usuario_id: str) -> int:
        """Obtiene tiempo restante de bloqueo para usuario."""
        from django.core.cache import cache
        from interfaces.api.rest.throttling import BloqueoTemporalConfig
        
        try:
            cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_USER}{usuario_id}"
            data = cache.get(cache_key)
            
            if data and 'expira_en' in data:
                restante = int(data['expira_en'] - time.time())
                return max(0, restante)
        except Exception:
            pass
        
        return 900
    
    def _registrar_intento_fallido(self, ip: str, endpoint: str) -> None:
        """Registra un intento fallido."""
        try:
            from interfaces.api.rest.throttling import ServicioBloqueoTemporal
            ServicioBloqueoTemporal.registrar_intento_fallido(
                ip=ip,
                endpoint=endpoint,
                motivo='login_fallido'
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error registrando intento: {e}")
    
    def _limpiar_intentos(self, ip: str, usuario_id: str = None) -> None:
        """Limpia intentos fallidos tras login exitoso."""
        try:
            from interfaces.api.rest.throttling import ServicioBloqueoTemporal
            ServicioBloqueoTemporal.limpiar_intentos(ip, usuario_id)
        except Exception:
            pass
    
    def _respuesta_bloqueado(self, tiempo_restante: int, motivo: str) -> JsonResponse:
        """
        Genera respuesta HTTP 429 para clientes bloqueados.
        
        IMPORTANTE: Mensajes genéricos que NO revelan reglas internas.
        """
        response = JsonResponse(
            {
                'error': 'Demasiadas solicitudes',
                'detail': 'Ha excedido el límite de solicitudes permitidas. '
                          'Por favor, espere antes de intentar nuevamente.',
                'code': 'too_many_requests'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
        
        # Header estándar de Retry-After
        response['Retry-After'] = str(tiempo_restante)
        
        # Headers de seguridad adicionales
        response['X-RateLimit-Reset'] = str(int(time.time()) + tiempo_restante)
        
        # Auditar el bloqueo
        self._auditar_bloqueo(motivo, tiempo_restante)
        
        return response
    
    def _auditar_bloqueo(self, motivo: str, tiempo_restante: int) -> None:
        """Registra el bloqueo en auditoría."""
        try:
            from infrastructure.logging.logger_service import LoggerService
            logger = LoggerService("RateLimitMiddleware")
            logger.warning(
                f"Request bloqueada",
                motivo=motivo,
                tiempo_restante=tiempo_restante
            )
        except Exception:
            pass


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware que agrega headers de seguridad adicionales a todas las respuestas.
    
    Complementa la configuración de Django con headers específicos para APIs.
    """
    
    def process_response(self, request, response):
        """Agrega headers de seguridad a la respuesta."""
        
        # Cache-Control para respuestas de API
        if request.path.startswith('/api/'):
            # No cachear respuestas de autenticación
            if '/auth/' in request.path:
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
            
            # No exponer información del servidor
            if 'Server' in response:
                del response['Server']
            
            # Content-Type siempre JSON para APIs
            if 'Content-Type' not in response:
                response['Content-Type'] = 'application/json'
        
        return response
