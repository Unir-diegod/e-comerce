"""
Casos de uso relacionados con Orden
"""
from typing import List
from uuid import UUID
from decimal import Decimal

from application.use_cases.base import CasoUsoBase
from application.dto.orden_dto import CrearOrdenDTO, OrdenDTO, AgregarLineaOrdenDTO
from domain.repositories.orden_repository import OrdenRepository
from domain.repositories.cliente_repository import ClienteRepository
from domain.repositories.producto_repository import ProductoRepository
from domain.entities.orden import Orden
from domain.value_objects.linea_orden import LineaOrden
from domain.value_objects.dinero import Dinero
from domain.exceptions.dominio import EntidadNoEncontrada, ReglaNegocioViolada


class CrearOrdenUseCase(CasoUsoBase[CrearOrdenDTO, OrdenDTO]):
    """
    Caso de uso: Crear una nueva orden.
    
    Punto de extensión: validaciones, reserva de stock, eventos
    """
    
    def __init__(
        self,
        orden_repository: OrdenRepository,
        cliente_repository: ClienteRepository
    ):
        self._orden_repository = orden_repository
        self._cliente_repository = cliente_repository
    
    def ejecutar(self, request: CrearOrdenDTO) -> OrdenDTO:
        """Crea una nueva orden"""
        
        # Validar que el cliente existe
        cliente = self._cliente_repository.obtener_por_id(request.cliente_id)
        if not cliente:
            raise EntidadNoEncontrada(f"Cliente {request.cliente_id} no encontrado")
        
        # Crear orden
        orden = Orden(cliente_id=request.cliente_id)
        
        # Persistir
        orden_guardada = self._orden_repository.guardar(orden)
        
        # Punto de extensión: emitir evento OrdenCreada
        
        return OrdenDTO.desde_entidad(orden_guardada)


class AgregarLineaOrdenUseCase(CasoUsoBase[AgregarLineaOrdenDTO, OrdenDTO]):
    """
    Caso de uso: Agregar una línea a una orden.
    """
    
    def __init__(
        self,
        orden_repository: OrdenRepository,
        producto_repository: ProductoRepository
    ):
        self._orden_repository = orden_repository
        self._producto_repository = producto_repository
    
    def ejecutar(self, request: AgregarLineaOrdenDTO) -> OrdenDTO:
        """Agrega una línea a la orden"""
        
        # Obtener orden
        orden = self._orden_repository.obtener_por_id(request.orden_id)
        if not orden:
            raise EntidadNoEncontrada(f"Orden {request.orden_id} no encontrada")
        
        # Obtener producto
        producto = self._producto_repository.obtener_por_id(request.producto_id)
        if not producto:
            raise EntidadNoEncontrada(f"Producto {request.producto_id} no encontrado")
        
        # Validar disponibilidad
        if not producto.disponible:
            raise ReglaNegocioViolada(f"Producto {producto.nombre} no está disponible")
        
        # Crear línea
        linea = LineaOrden(
            producto_id=producto.id,
            cantidad=request.cantidad,
            precio_unitario=producto.precio
        )
        
        # Agregar a orden
        orden.agregar_linea(linea)
        
        # Persistir
        orden_actualizada = self._orden_repository.guardar(orden)
        
        return OrdenDTO.desde_entidad(orden_actualizada)


class ConfirmarOrdenUseCase(CasoUsoBase[UUID, OrdenDTO]):
    """
    Caso de uso: Confirmar una orden.
    
    Punto de extensión: validación de stock, reservas, pagos
    """
    
    def __init__(self, orden_repository: OrdenRepository):
        self._orden_repository = orden_repository
    
    def ejecutar(self, request: UUID) -> OrdenDTO:
        """Confirma una orden"""
        orden = self._orden_repository.obtener_por_id(request)
        
        if not orden:
            raise EntidadNoEncontrada(f"Orden {request} no encontrada")
        
        # Confirmar orden (validaciones en la entidad)
        orden.confirmar()
        
        # Persistir
        orden_confirmada = self._orden_repository.guardar(orden)
        
        # Punto de extensión: emitir evento OrdenConfirmada
        
        return OrdenDTO.desde_entidad(orden_confirmada)


class ConfirmarOrdenConStockUseCase(CasoUsoBase[UUID, OrdenDTO]):
    """
    Caso de uso: Confirmar orden con validación y descuento de stock.
    
    CRÍTICO: Implementa control de concurrencia para evitar overselling.
    Usa bloqueos pesimistas (SELECT FOR UPDATE) en PostgreSQL.
    
    Responsabilidades:
    - Validar stock disponible bajo bloqueo
    - Descontar stock atómicamente
    - Confirmar orden
    - Garantizar consistencia ante concurrencia
    """
    
    def __init__(
        self,
        orden_repository: OrdenRepository,
        producto_repository: ProductoRepository
    ):
        self._orden_repository = orden_repository
        self._producto_repository = producto_repository
    
    def ejecutar(self, request: UUID) -> OrdenDTO:
        """
        Confirma orden con descuento de stock.
        
        IMPORTANTE: Este método delega el control de concurrencia
        al repositorio de Orden, que debe implementar la transacción
        atómica completa con bloqueos.
        """
        # Delegar al repositorio que tiene acceso a transaction.atomic
        orden_confirmada = self._orden_repository.confirmar_con_stock(request)
        
        return OrdenDTO.desde_entidad(orden_confirmada)
