"""
Servicio de auditoría
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import json


@dataclass
class RegistroAuditoria:
    """
    Registro de auditoría inmutable.
    
    Responsabilidades:
    - Registrar quién, qué, cuándo y dónde
    - Trazabilidad completa de operaciones
    - Soporte para cumplimiento normativo
    """
    id: UUID
    timestamp: datetime
    usuario_id: Optional[UUID]
    entidad_tipo: str
    entidad_id: UUID
    accion: str
    datos_previos: Optional[Dict[str, Any]]
    datos_nuevos: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resultado: str  # "EXITO", "FALLO"
    mensaje: Optional[str]


class ServicioAuditoria:
    """
    Servicio de auditoría para trazabilidad.
    
    Responsabilidades:
    - Registrar todas las operaciones críticas
    - Mantener historial inmutable en PostgreSQL
    - Facilitar investigación y compliance
    - Fail-safe: nunca interrumpir operaciones principales
    """
    
    # Lista de campos sensibles que no deben auditarse
    CAMPOS_SENSIBLES = {'password', 'token', 'secret', 'api_key', 'private_key'}
    
    def __init__(self):
        from infrastructure.logging.logger_service import LoggerService
        self._logger = LoggerService("ServicioAuditoria")
    
    def _sanitizar_datos(self, datos: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sanitiza datos sensibles antes de persistir.
        Reemplaza valores de campos sensibles con '[REDACTED]'.
        """
        if not datos:
            return datos
        
        datos_sanitizados = {}
        for clave, valor in datos.items():
            if any(campo in clave.lower() for campo in self.CAMPOS_SENSIBLES):
                datos_sanitizados[clave] = '[REDACTED]'
            else:
                datos_sanitizados[clave] = valor
        
        return datos_sanitizados
    
    def registrar(
        self,
        entidad_tipo: str,
        entidad_id: UUID,
        accion: str,
        usuario_id: Optional[UUID] = None,
        datos_previos: Optional[Dict[str, Any]] = None,
        datos_nuevos: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resultado: str = "EXITO",
        mensaje: Optional[str] = None
    ) -> RegistroAuditoria:
        """
        Registra una operación auditable en PostgreSQL.
        
        FAIL-SAFE: Si la persistencia falla, solo loguea el error
        sin interrumpir la operación principal.
        """
        registro_id = uuid4()
        
        registro = RegistroAuditoria(
            id=registro_id,
            timestamp=datetime.now(),
            usuario_id=usuario_id,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            accion=accion,
            datos_previos=datos_previos,
            datos_nuevos=datos_nuevos,
            ip_address=ip_address,
            user_agent=user_agent,
            resultado=resultado,
            mensaje=mensaje
        )
        
        # Persistir en base de datos (fail-safe)
        try:
            from infrastructure.persistence.django.models import RegistroAuditoriaModel
            
            # Sanitizar datos sensibles
            datos_previos_safe = self._sanitizar_datos(datos_previos)
            datos_nuevos_safe = self._sanitizar_datos(datos_nuevos)
            
            # Crear registro en base de datos
            RegistroAuditoriaModel.objects.create(
                id=registro_id,
                usuario_id=usuario_id,
                entidad_tipo=entidad_tipo,
                entidad_id=entidad_id,
                accion=accion,
                datos_previos=datos_previos_safe,
                datos_nuevos=datos_nuevos_safe,
                ip_address=ip_address,
                user_agent=user_agent,
                resultado=resultado,
                mensaje=mensaje
            )
            
            self._logger.info(
                f"Registro de auditoría persistido",
                registro_id=str(registro_id),
                entidad_tipo=entidad_tipo,
                accion=accion
            )
            
        except Exception as e:
            # FAIL-SAFE: No lanzar excepción, solo loguear
            self._logger.error(
                f"ERROR CRÍTICO: Fallo al persistir auditoría",
                error=str(e),
                entidad_tipo=entidad_tipo,
                entidad_id=str(entidad_id),
                accion=accion
            )
        
        return registro
    
    @staticmethod
    def registrar_acceso_api(
        usuario_id: Optional[str],
        endpoint: str,
        metodo: str,
        ip: str,
        user_agent: str,
        resultado_exitoso: bool,
        codigo_estado: Optional[int] = None
    ):
        """
        Registra accesos a la API REST (autenticación y endpoints protegidos)
        
        Args:
            usuario_id: ID del usuario autenticado (None si no autenticado)
            endpoint: Path del endpoint (/api/v1/productos)
            metodo: Método HTTP (GET, POST, etc.)
            ip: Dirección IP del cliente
            user_agent: User-Agent del cliente
            resultado_exitoso: Si el acceso fue exitoso
            codigo_estado: Código HTTP de respuesta
        """
        from infrastructure.logging.logger_service import LoggerService
        logger = LoggerService("AuditoriaAPI")
        
        try:
            from infrastructure.persistence.django.models import AuditoriaAccesoAPI
            
            AuditoriaAccesoAPI.objects.create(
                usuario_id=usuario_id,
                endpoint=endpoint,
                metodo=metodo,
                ip_address=ip,
                user_agent=user_agent,
                resultado_exitoso=resultado_exitoso,
                codigo_estado=codigo_estado
            )
            
            logger.info(
                f"Acceso API registrado: {metodo} {endpoint} - "
                f"Usuario: {usuario_id or 'Anónimo'} - "
                f"IP: {ip} - "
                f"Estado: {codigo_estado}"
            )
            
        except Exception as e:
            logger.error(f"Error al registrar acceso API: {e}")
            # Fail-safe: no interrumpir la operación principal
            pass
