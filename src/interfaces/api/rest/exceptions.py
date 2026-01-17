from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

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
    - ReglaNegocioViolada -> 409 Conflict
    - EntidadNoEncontrada -> 404 Not Found
    - ValorInvalido -> 400 Bad Request
    - Otras excepciones de dominio -> 500 Internal Server Error (o 400 si se decide)
    """
    
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
