"""
Interfaz del Repositorio de Producto
"""
from abc import abstractmethod
from typing import Optional, List
from .base import RepositorioBase
from ..entities.producto import Producto
from ..value_objects.codigo_producto import CodigoProducto


class ProductoRepository(RepositorioBase[Producto]):
    """
    Contrato de persistencia para Producto.
    
    Punto de extensión: consultas de inventario, búsquedas
    """
    
    @abstractmethod
    def obtener_por_codigo(self, codigo: CodigoProducto) -> Optional[Producto]:
        """Busca un producto por código"""
        pass
    
    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        """Busca productos por nombre (búsqueda parcial)"""
        pass
    
    @abstractmethod
    def obtener_con_stock_bajo(self) -> List[Producto]:
        """Obtiene productos que requieren reabastecimiento"""
        pass
    
    @abstractmethod
    def obtener_disponibles(self) -> List[Producto]:
        """Obtiene productos disponibles para venta"""
        pass
    
    @abstractmethod
    def obtener_con_bloqueo(self, id) -> Optional[Producto]:
        """
        Obtiene un producto con bloqueo pesimista (SELECT FOR UPDATE).
        
        IMPORTANTE: Debe ejecutarse dentro de transaction.atomic()
        para evitar bloqueos perpetuos.
        
        Uso: Control de concurrencia en operaciones críticas de stock.
        """
        pass
