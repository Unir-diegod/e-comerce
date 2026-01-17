from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
import logging
import time

from domain.exceptions.dominio import (
    ReglaNegocioViolada,
    EntidadNoEncontrada,
    ValorInvalido,
    ExcepcionDominio
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler global de excepciones para traducir errores de dominio a respuestas HTTP.
    
    Mappings:
    - Throttled -> 429 Too Many Requests (rate limiting)
    - ReglaNegocioViolada -> 409 Conflict
    - EntidadNoEncontrada -> 404 Not Found
    - ValorInvalido -> 400 Bad Request
    - Otras excepciones de dominio -> 500 Internal Server Error (o 400 si se decide)
    
    IMPORTANTE: Los mensajes de error para rate limiting son genéricos
    para no revelar reglas internas de seguridad.
    """
    
    # Manejar Throttled exception (rate limiting)
    if isinstance(exc, Throttled):
        return _handle_throttled_exception(exc, context)

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Si ya fue manejado por DRF (ej: ValidationError), retornalo
    if response is not None:
        return response

    # Manejo de excepciones de dominio
    if isinstance(exc, EntidadNoEncontrada):
        logger.warning(f"Entidad no encontrada: {exc}")
        return Response(
            {"detail": str(exc), "code": "not_found"},
            status=status.HTTP_404_NOT_FOUND
        )
        
    if isinstance(exc, ReglaNegocioViolada):
        logger.warning(f"Regla de negocio violada: {exc}")
        return Response(
            {"detail": str(exc), "code": "conflict"},
            status=status.HTTP_409_CONFLICT
        )
        
    if isinstance(exc, ValorInvalido):
        logger.warning(f"Valor inválido: {exc}", exc_info=True)
        return Response(
            {"detail": str(exc), "code": "invalid_value"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    if isinstance(exc, ExcepcionDominio):
        # Fallback para otras excepciones de dominio
        logger.error(f"Excepción de dominio no manejada explícitamente: {exc}")
        return Response(
            {"detail": "Error de procesamiento de regla de negocio.", "code": "domain_error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Dejar que Django maneje 500 para errores inesperados no-dominio
    return None


def _handle_throttled_exception(exc: Throttled, context) -> Response:
    """
    Maneja excepciones de rate limiting (HTTP 429).
    
    OWASP Compliance:
    - NO revelar reglas internas de throttling
    - Mensajes genéricos y amigables
    - Headers estándar Retry-After
    
    Args:
        exc: Excepción Throttled de DRF
        context: Contexto de la request
        
    Returns:
        Response HTTP 429 con mensaje genérico
    """
    wait_seconds = int(exc.wait) if exc.wait else 60
    
    # Auditar el evento de rate limit
    _audit_rate_limit_exceeded(context, wait_seconds)
    
    # Respuesta genérica que NO revela detalles internos
    response = Response(
        {
            'error': 'Demasiadas solicitudes',
            'detail': 'Ha realizado demasiadas solicitudes en un período corto. '
                      'Por favor, espere antes de intentar nuevamente.',
            'code': 'too_many_requests'
        },
        status=status.HTTP_429_TOO_MANY_REQUESTS
    )
    
    # Headers estándar para rate limiting
    response['Retry-After'] = str(wait_seconds)
    response['X-RateLimit-Reset'] = str(int(time.time()) + wait_seconds)
    
    return response


def _audit_rate_limit_exceeded(context, wait_seconds: int) -> None:
    """
    Registra en auditoría cuando se excede el rate limit.
    
    Fail-safe: nunca interrumpe la respuesta al cliente.
    """
    try:
        request = context.get('request')
        if not request:
            return
        
        # Obtener información del cliente
        ip = _get_client_ip(request)
        usuario_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            usuario_id = str(request.user.id)
        
        endpoint = request.path
        
        # Obtener scope del throttle si está disponible
        view = context.get('view')
        throttle_scope = 'unknown'
        if view and hasattr(view, 'throttle_classes'):
            throttle_classes = view.throttle_classes
            if throttle_classes:
                throttle_scope = getattr(throttle_classes[0], 'scope', 'unknown')
        
        # Registrar en auditoría
        from interfaces.api.rest.throttling import AuditoriaRateLimit
        AuditoriaRateLimit.registrar_exceso(
            ip=ip,
            usuario_id=usuario_id,
            endpoint=endpoint,
            throttle_scope=throttle_scope,
            wait_seconds=wait_seconds
        )
        
    except Exception as e:
        # Fail-safe: nunca interrumpir la respuesta
        logger.error(f"Error al auditar rate limit: {e}")


def _get_client_ip(request) -> str:
    """Obtiene la IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip[:45]
