"""
Implementación del Repositorio de Producto con Django ORM
"""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from domain.repositories.producto_repository import ProductoRepository
from domain.entities.producto import Producto
from domain.value_objects.codigo_producto import CodigoProducto
from domain.value_objects.dinero import Dinero
from infrastructure.persistence.django.models import ProductoModel
from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
from infrastructure.logging.logger_service import LoggerService


class ProductoRepositoryImpl(ProductoRepository):
    """
    Implementación concreta del repositorio de Producto usando Django ORM.
    """
    
    def __init__(
        self,
        auditoria: Optional[ServicioAuditoria] = None,
        logger: Optional[LoggerService] = None
    ):
        self._auditoria = auditoria or ServicioAuditoria()
        self._logger = logger or LoggerService("ProductoRepository")
    
    def _to_domain(self, model: ProductoModel) -> Producto:
        """
        Mapea modelo Django a entidad de dominio.
        """
        return Producto(
            id=model.id,
            codigo=CodigoProducto(model.codigo),
            nombre=model.nombre,
            descripcion=model.descripcion,
            precio=Dinero(model.monto_precio, model.moneda_precio),
            stock_actual=model.stock_actual,
            stock_minimo=model.stock_minimo,
            fecha_creacion=model.fecha_creacion,
            fecha_modificacion=model.fecha_modificacion,
            activo=model.activo
        )
    
    def _to_model(self, entity: Producto) -> ProductoModel:
        """
        Mapea entidad de dominio a modelo Django.
        """
        return ProductoModel(
            id=entity.id,
            codigo=entity.codigo.valor,
            nombre=entity.nombre,
            descripcion=entity.descripcion,
            moneda_precio=entity.precio.moneda,
            monto_precio=entity.precio.monto,
            stock_actual=entity.stock_actual,
            stock_minimo=entity.stock_minimo,
            activo=entity.activo,
            fecha_creacion=entity.fecha_creacion,
            fecha_modificacion=entity.fecha_modificacion
        )
    
    def obtener_por_id(self, id: UUID) -> Optional[Producto]:
        self._logger.info(f"Obteniendo producto por ID", producto_id=str(id))
        try:
            model = ProductoModel.objects.get(id=id)
            return self._to_domain(model)
        except ProductoModel.DoesNotExist:
            return None
    
    def obtener_por_codigo(self, codigo: CodigoProducto) -> Optional[Producto]:
        self._logger.info(f"Buscando producto por código", codigo=codigo.valor)
        try:
            model = ProductoModel.objects.get(codigo=codigo.valor)
            return self._to_domain(model)
        except ProductoModel.DoesNotExist:
            return None
            
    def buscar_por_nombre(self, nombre: str) -> List[Producto]:
        self._logger.info(f"Buscando productos por nombre", nombre=nombre)
        models = ProductoModel.objects.filter(
            nombre__icontains=nombre
        )
        return [self._to_domain(model) for model in models]

    def obtener_con_stock_bajo(self) -> List[Producto]:
        self._logger.info("Buscando productos con stock bajo")
        # En SQL: WHERE stock_actual <= stock_minimo
        # Django F expression para comparar columnas
        from django.db.models import F
        models = ProductoModel.objects.filter(stock_actual__lte=F('stock_minimo'), activo=True)
        return [self._to_domain(model) for model in models]
        
    def obtener_disponibles(self) -> List[Producto]:
        self._logger.info("Obteniendo productos disponibles")
        models = ProductoModel.objects.filter(activo=True, stock_actual__gt=0)
        return [self._to_domain(model) for model in models]
    
    def obtener_con_bloqueo(self, id: UUID) -> Optional[Producto]:
        """
        Obtiene producto con bloqueo pesimista (SELECT FOR UPDATE).
        
        CRÍTICO: Previene race conditions en operaciones de stock.
        PostgreSQL bloquea la fila hasta que la transacción termine.
        
        REQUIERE: Estar dentro de transaction.atomic()
        """
        self._logger.info("Obteniendo producto con bloqueo", producto_id=str(id))
        
        try:
            # SELECT FOR UPDATE: Bloqueo pesimista a nivel de fila
            # Otras transacciones esperarán hasta que esta termine
            model = ProductoModel.objects.select_for_update().get(id=id)
            producto = self._to_domain(model)
            
            self._logger.info(
                "Producto bloqueado para actualización",
                producto_id=str(id),
                stock_actual=producto.stock_actual
            )
            
            return producto
            
        except ProductoModel.DoesNotExist:
            self._logger.warning("Producto no encontrado para bloqueo", producto_id=str(id))
            return None

    def guardar(self, entidad: Producto) -> Producto:
        producto_id = str(entidad.id)
        self._logger.info(f"Guardando producto", producto_id=producto_id)
        
        try:
            existe = ProductoModel.objects.filter(id=entidad.id).exists()
            accion = "UPDATE" if existe else "CREATE"
            
            # Obtener datos previos para auditoría
            datos_previos = None
            if existe:
                model_anterior = ProductoModel.objects.get(id=entidad.id)
                datos_previos = {
                    "codigo": model_anterior.codigo,
                    "stock": model_anterior.stock_actual,
                    "precio": f"{model_anterior.monto_precio} {model_anterior.moneda_precio}"
                }
            
            model = self._to_model(entidad)
            model.save()
            
            datos_nuevos = {
                "codigo": model.codigo,
                "stock": model.stock_actual,
                "precio": f"{model.monto_precio} {model.moneda_precio}"
            }
            
            self._auditoria.registrar(
                entidad_tipo="Producto",
                entidad_id=entidad.id,
                accion=accion,
                datos_previos=datos_previos,
                datos_nuevos=datos_nuevos,
                resultado="EXITO",
                mensaje=f"Producto {accion.lower()}do exitosamente"
            )
            
            return self._to_domain(model)
            
        except Exception as e:
            self._logger.error(f"Error al guardar producto", error=str(e))
            self._auditoria.registrar(
                entidad_tipo="Producto",
                entidad_id=entidad.id,
                accion="SAVE",
                resultado="FALLO",
            )
            raise

    def eliminar(self, id: UUID) -> bool:
        self._logger.info(f"Eliminando producto", producto_id=str(id))
        try:
            model = ProductoModel.objects.get(id=id)
            model.activo = False  # Soft delete
            model.save()
            
            self._auditoria.registrar(
                entidad_tipo="Producto",
                entidad_id=id,
                accion="DELETE",
                resultado="EXITO",
                mensaje="Producto eliminado lógicamente"
            )
            return True
        except ProductoModel.DoesNotExist:
            return False

    def existe(self, id: UUID) -> bool:
        return ProductoModel.objects.filter(id=id).exists()

    def obtener_todos(self, limite: int = 100, offset: int = 0) -> List[Producto]:
        self._logger.info(f"Obteniendo todos los productos", limite=limite, offset=offset)
        models = ProductoModel.objects.all()[offset:offset + limite]
        return [self._to_domain(model) for model in models]

