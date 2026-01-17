"""
Throttling Classes para Protección Anti-Abuso

Este módulo implementa rate limiting y controles defensivos para proteger
la API contra:
- Ataques de fuerza bruta
- Scraping automatizado
- Abuso de recursos
- DoS a nivel de aplicación

OWASP References:
- API4:2023 - Unrestricted Resource Consumption
- API2:2023 - Broken Authentication

Autor: Sistema E-commerce
Fecha: Enero 2026
"""
from rest_framework.throttling import (
    AnonRateThrottle, 
    UserRateThrottle, 
    SimpleRateThrottle
)
from django.core.cache import cache
from django.conf import settings
from typing import Optional
import hashlib
import time


# ============================================================================
# CONFIGURACIÓN DE BLOQUEO TEMPORAL
# ============================================================================

class BloqueoTemporalConfig:
    """
    Configuración centralizada para bloqueo temporal.
    
    Valores configurables vía settings o defaults seguros.
    """
    # Intentos fallidos antes de bloqueo
    MAX_INTENTOS_FALLIDOS = getattr(settings, 'SECURITY_MAX_FAILED_ATTEMPTS', 5)
    
    # Duración del bloqueo en segundos (15 minutos)
    DURACION_BLOQUEO = getattr(settings, 'SECURITY_BLOCK_DURATION', 900)
    
    # Ventana de tiempo para contar intentos (5 minutos)
    VENTANA_INTENTOS = getattr(settings, 'SECURITY_ATTEMPT_WINDOW', 300)
    
    # Prefijos de cache
    CACHE_PREFIX_IP = 'security:blocked:ip:'
    CACHE_PREFIX_USER = 'security:blocked:user:'
    CACHE_PREFIX_ATTEMPTS = 'security:attempts:'


# ============================================================================
# THROTTLES GLOBALES (BASE)
# ============================================================================

class GlobalAnonRateThrottle(AnonRateThrottle):
    """
    Rate limiting global para usuarios anónimos.
    
    Protege contra:
    - Scraping masivo sin autenticación
    - Enumeración de endpoints
    - Reconocimiento automatizado
    
    Rate: 50 requests/minuto por IP
    """
    scope = 'anon_global'
    
    def get_cache_key(self, request, view):
        """
        Genera clave de cache basada en IP.
        Usa hash para evitar problemas con caracteres especiales en IPv6.
        """
        ident = self.get_ident(request)
        return f"throttle:anon:{hashlib.md5(ident.encode()).hexdigest()}"


class GlobalUserRateThrottle(UserRateThrottle):
    """
    Rate limiting global para usuarios autenticados.
    
    Protege contra:
    - Abuso de cuentas comprometidas
    - Automatización excesiva
    - Uso indebido de credenciales válidas
    
    Rate: 200 requests/minuto por usuario
    """
    scope = 'user_global'
    
    def get_cache_key(self, request, view):
        """
        Genera clave de cache basada en ID de usuario.
        """
        if request.user and request.user.is_authenticated:
            ident = str(request.user.pk)
            return f"throttle:user:{ident}"
        return None


# ============================================================================
# THROTTLES PARA ENDPOINTS CRÍTICOS
# ============================================================================

class LoginRateThrottle(SimpleRateThrottle):
    """
    Rate limiting estricto para endpoint de login.
    
    Protege contra:
    - Ataques de fuerza bruta
    - Credential stuffing
    - Enumeración de usuarios
    
    Rate: 5 intentos/minuto por IP
    """
    scope = 'login'
    
    def get_cache_key(self, request, view):
        """
        Clave basada en IP para login (usuarios aún no autenticados).
        """
        ident = self.get_ident(request)
        return f"throttle:login:{hashlib.md5(ident.encode()).hexdigest()}"
    
    def allow_request(self, request, view):
        """
        Verifica si la IP está bloqueada antes de aplicar throttling.
        """
        # Verificar bloqueo temporal por IP
        if self._esta_bloqueado_ip(request):
            return False
        
        return super().allow_request(request, view)
    
    def _esta_bloqueado_ip(self, request) -> bool:
        """
        Verifica si la IP está bloqueada temporalmente.
        """
        ip = self.get_ident(request)
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_IP}{ip_hash}"
        return cache.get(cache_key) is not None


class RefreshTokenRateThrottle(SimpleRateThrottle):
    """
    Rate limiting para refresh de tokens.
    
    Protege contra:
    - Abuso de renovación de tokens
    - Intentos de mantener sesiones comprometidas
    
    Rate: 10 requests/minuto por IP
    """
    scope = 'token_refresh'
    
    def get_cache_key(self, request, view):
        """
        Clave basada en IP para refresh.
        """
        ident = self.get_ident(request)
        return f"throttle:refresh:{hashlib.md5(ident.encode()).hexdigest()}"


class OrdenCreacionRateThrottle(SimpleRateThrottle):
    """
    Rate limiting para creación de órdenes.
    
    Protege contra:
    - Creación masiva fraudulenta
    - Agotamiento de inventario malicioso
    - Ataques de denegación de servicio
    
    Rate: 20 órdenes/minuto por usuario
    """
    scope = 'orden_creacion'
    
    def get_cache_key(self, request, view):
        """
        Clave basada en usuario autenticado.
        """
        if request.user and request.user.is_authenticated:
            return f"throttle:orden:{request.user.pk}"
        
        # Fallback a IP para requests sin auth (no deberían llegar)
        ident = self.get_ident(request)
        return f"throttle:orden:anon:{hashlib.md5(ident.encode()).hexdigest()}"


class OrdenConfirmacionRateThrottle(SimpleRateThrottle):
    """
    Rate limiting para confirmación de órdenes.
    
    Protege contra:
    - Confirmaciones duplicadas
    - Intentos de manipulación de transacciones
    
    Rate: 10 confirmaciones/minuto por usuario
    """
    scope = 'orden_confirmacion'
    
    def get_cache_key(self, request, view):
        """
        Clave basada en usuario autenticado.
        """
        if request.user and request.user.is_authenticated:
            return f"throttle:confirmar:{request.user.pk}"
        
        ident = self.get_ident(request)
        return f"throttle:confirmar:anon:{hashlib.md5(ident.encode()).hexdigest()}"


# ============================================================================
# SERVICIO DE BLOQUEO TEMPORAL
# ============================================================================

class ServicioBloqueoTemporal:
    """
    Servicio para gestionar bloqueos temporales por IP y usuario.
    
    Funcionalidades:
    - Registro de intentos fallidos
    - Bloqueo automático tras N intentos
    - Desbloqueo automático por tiempo
    - Integración con auditoría
    """
    
    @staticmethod
    def registrar_intento_fallido(
        ip: str, 
        usuario_id: Optional[str] = None,
        endpoint: str = 'unknown',
        motivo: str = 'login_fallido'
    ) -> dict:
        """
        Registra un intento fallido y aplica bloqueo si es necesario.
        
        Args:
            ip: Dirección IP del cliente
            usuario_id: ID del usuario (si se conoce)
            endpoint: Endpoint donde ocurrió el fallo
            motivo: Motivo del fallo
            
        Returns:
            dict con estado del bloqueo
        """
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        intentos_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_ATTEMPTS}{ip_hash}"
        
        # Obtener intentos actuales
        intentos = cache.get(intentos_key, 0)
        intentos += 1
        
        # Guardar con TTL de ventana de intentos
        cache.set(
            intentos_key, 
            intentos, 
            BloqueoTemporalConfig.VENTANA_INTENTOS
        )
        
        resultado = {
            'ip': ip,
            'intentos': intentos,
            'max_intentos': BloqueoTemporalConfig.MAX_INTENTOS_FALLIDOS,
            'bloqueado': False,
            'tiempo_bloqueo': 0
        }
        
        # Verificar si debe bloquearse
        if intentos >= BloqueoTemporalConfig.MAX_INTENTOS_FALLIDOS:
            ServicioBloqueoTemporal._bloquear_ip(ip, ip_hash)
            resultado['bloqueado'] = True
            resultado['tiempo_bloqueo'] = BloqueoTemporalConfig.DURACION_BLOQUEO
            
            # Registrar en auditoría
            ServicioBloqueoTemporal._auditar_bloqueo(
                ip=ip,
                usuario_id=usuario_id,
                endpoint=endpoint,
                motivo=f"Bloqueo por {intentos} intentos fallidos: {motivo}"
            )
        
        # Si hay usuario, también rastrear por usuario
        if usuario_id:
            ServicioBloqueoTemporal._registrar_intento_usuario(
                usuario_id, intentos, endpoint, motivo
            )
        
        return resultado
    
    @staticmethod
    def _bloquear_ip(ip: str, ip_hash: str) -> None:
        """
        Bloquea una IP temporalmente.
        """
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_IP}{ip_hash}"
        cache.set(
            cache_key,
            {
                'ip': ip,
                'bloqueado_en': time.time(),
                'expira_en': time.time() + BloqueoTemporalConfig.DURACION_BLOQUEO
            },
            BloqueoTemporalConfig.DURACION_BLOQUEO
        )
    
    @staticmethod
    def _registrar_intento_usuario(
        usuario_id: str, 
        intentos: int,
        endpoint: str,
        motivo: str
    ) -> None:
        """
        Registra intentos por usuario.
        """
        user_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_ATTEMPTS}user:{usuario_id}"
        user_intentos = cache.get(user_key, 0)
        user_intentos += 1
        
        cache.set(
            user_key, 
            user_intentos, 
            BloqueoTemporalConfig.VENTANA_INTENTOS
        )
        
        # Bloquear usuario si excede límite
        if user_intentos >= BloqueoTemporalConfig.MAX_INTENTOS_FALLIDOS:
            cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_USER}{usuario_id}"
            cache.set(
                cache_key,
                {
                    'usuario_id': usuario_id,
                    'bloqueado_en': time.time(),
                    'expira_en': time.time() + BloqueoTemporalConfig.DURACION_BLOQUEO
                },
                BloqueoTemporalConfig.DURACION_BLOQUEO
            )
            
            ServicioBloqueoTemporal._auditar_bloqueo(
                ip='N/A',
                usuario_id=usuario_id,
                endpoint=endpoint,
                motivo=f"Bloqueo de usuario por {user_intentos} intentos fallidos: {motivo}"
            )
    
    @staticmethod
    def esta_bloqueado_ip(ip: str) -> bool:
        """
        Verifica si una IP está bloqueada.
        """
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_IP}{ip_hash}"
        return cache.get(cache_key) is not None
    
    @staticmethod
    def esta_bloqueado_usuario(usuario_id: str) -> bool:
        """
        Verifica si un usuario está bloqueado.
        """
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_USER}{usuario_id}"
        return cache.get(cache_key) is not None
    
    @staticmethod
    def obtener_tiempo_restante_bloqueo(ip: str) -> int:
        """
        Obtiene segundos restantes de bloqueo para una IP.
        """
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_IP}{ip_hash}"
        data = cache.get(cache_key)
        
        if data and 'expira_en' in data:
            restante = int(data['expira_en'] - time.time())
            return max(0, restante)
        
        return 0
    
    @staticmethod
    def limpiar_intentos(ip: str, usuario_id: Optional[str] = None) -> None:
        """
        Limpia el contador de intentos (tras login exitoso).
        """
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        cache.delete(f"{BloqueoTemporalConfig.CACHE_PREFIX_ATTEMPTS}{ip_hash}")
        
        if usuario_id:
            cache.delete(f"{BloqueoTemporalConfig.CACHE_PREFIX_ATTEMPTS}user:{usuario_id}")
    
    @staticmethod
    def desbloquear_ip(ip: str) -> bool:
        """
        Desbloquea manualmente una IP (para admin).
        """
        ip_hash = hashlib.md5(ip.encode()).hexdigest()
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_IP}{ip_hash}"
        cache.delete(cache_key)
        cache.delete(f"{BloqueoTemporalConfig.CACHE_PREFIX_ATTEMPTS}{ip_hash}")
        return True
    
    @staticmethod
    def desbloquear_usuario(usuario_id: str) -> bool:
        """
        Desbloquea manualmente un usuario (para admin).
        """
        cache_key = f"{BloqueoTemporalConfig.CACHE_PREFIX_USER}{usuario_id}"
        cache.delete(cache_key)
        cache.delete(f"{BloqueoTemporalConfig.CACHE_PREFIX_ATTEMPTS}user:{usuario_id}")
        return True
    
    @staticmethod
    def _auditar_bloqueo(
        ip: str,
        usuario_id: Optional[str],
        endpoint: str,
        motivo: str
    ) -> None:
        """
        Registra el bloqueo en el sistema de auditoría.
        """
        try:
            from infrastructure.logging.logger_service import LoggerService
            logger = LoggerService("ServicioBloqueoTemporal")
            
            logger.warning(
                f"BLOQUEO DE SEGURIDAD APLICADO",
                ip=ip,
                usuario_id=usuario_id or 'N/A',
                endpoint=endpoint,
                motivo=motivo,
                duracion_segundos=BloqueoTemporalConfig.DURACION_BLOQUEO
            )
            
            # También registrar en auditoría de base de datos
            from uuid import uuid4
            from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
            
            ServicioAuditoria().registrar(
                entidad_tipo='SEGURIDAD',
                entidad_id=uuid4(),
                accion='BLOQUEO_TEMPORAL',
                ip_address=ip,
                resultado='BLOQUEO',
                mensaje=motivo
            )
            
        except Exception as e:
            # Fail-safe: no interrumpir operación principal
            import logging
            logging.getLogger(__name__).error(f"Error al auditar bloqueo: {e}")


# ============================================================================
# AUDITORÍA DE RATE LIMIT EXCEDIDO
# ============================================================================

class AuditoriaRateLimit:
    """
    Servicio para auditar cuando se exceden los límites de rate.
    """
    
    @staticmethod
    def registrar_exceso(
        ip: str,
        usuario_id: Optional[str],
        endpoint: str,
        throttle_scope: str,
        wait_seconds: int
    ) -> None:
        """
        Registra cuando un cliente excede el rate limit.
        """
        try:
            from infrastructure.logging.logger_service import LoggerService
            logger = LoggerService("AuditoriaRateLimit")
            
            logger.warning(
                f"RATE LIMIT EXCEDIDO",
                ip=ip,
                usuario_id=usuario_id or 'Anónimo',
                endpoint=endpoint,
                throttle_scope=throttle_scope,
                espera_segundos=wait_seconds
            )
            
            # Registrar en auditoría persistente
            from uuid import uuid4
            from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
            
            ServicioAuditoria().registrar(
                entidad_tipo='SEGURIDAD',
                entidad_id=uuid4(),
                accion='RATE_LIMIT_EXCEDIDO',
                ip_address=ip,
                resultado='BLOQUEADO',
                mensaje=f"Excedió límite {throttle_scope}. Espera: {wait_seconds}s"
            )
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error al auditar rate limit: {e}")
