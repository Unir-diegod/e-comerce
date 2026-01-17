"""
Interfaz del Repositorio de Orden
"""
from abc import abstractmethod
from typing import List
from uuid import UUID
from .base import RepositorioBase
from ..entities.orden import Orden
from shared.enums.estados import EstadoOrden


class OrdenRepository(RepositorioBase[Orden]):
    """
    Contrato de persistencia para Orden.
    
    Punto de extensión: consultas por estado, cliente, fecha
    """
    
    @abstractmethod
    def obtener_por_cliente(self, cliente_id: UUID) -> List[Orden]:
        """Obtiene todas las órdenes de un cliente"""
        pass
    
    @abstractmethod
    def obtener_por_estado(self, estado: EstadoOrden) -> List[Orden]:
        """Obtiene órdenes por estado"""
        pass
    
    @abstractmethod
    def obtener_pendientes_procesamiento(self) -> List[Orden]:
        """Obtiene órdenes confirmadas pendientes de procesamiento"""
        pass    
    @abstractmethod
    def confirmar_con_stock(self, orden_id) -> 'Orden':
        """
        Confirma una orden validando y descontando stock atómicamente.
        
        IMPORTANTE: Implementa control de concurrencia con bloqueos pesimistas.
        
        Args:
            orden_id: UUID de la orden a confirmar
            
        Returns:
            Orden confirmada con stock descontado
            
        Raises:
            EntidadNoEncontrada: Si la orden no existe
            ReglaNegocioViolada: Si no hay stock suficiente o la orden no es válida
        """
        pass