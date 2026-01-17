"""
Implementación del Repositorio de Cliente con Django ORM
"""
from typing import Optional, List
from uuid import UUID

from domain.repositories.cliente_repository import ClienteRepository
from domain.entities.cliente import Cliente
from domain.value_objects.email import Email
from domain.value_objects.telefono import Telefono
from domain.value_objects.documento_identidad import DocumentoIdentidad
from shared.enums.tipos_documento import TipoDocumento
from infrastructure.persistence.django.models import ClienteModel
from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
from infrastructure.logging.logger_service import LoggerService


class ClienteRepositoryImpl(ClienteRepository):
    """
    Implementación concreta del repositorio de Cliente usando Django ORM.
    
    Responsabilidades:
    - Mapear entre modelos Django y entidades de dominio
    - Ejecutar operaciones CRUD en base de datos
    - Mantener aislamiento entre dominio e infraestructura
    - Registrar auditoría y logs
    """
    
    def __init__(
        self,
        auditoria: Optional[ServicioAuditoria] = None,
        logger: Optional[LoggerService] = None
    ):
        self._auditoria = auditoria or ServicioAuditoria()
        self._logger = logger or LoggerService("ClienteRepository")
    
    def _to_domain(self, model: ClienteModel) -> Cliente:
        """
        Mapea modelo Django a entidad de dominio.
        
        Args:
            model: Modelo Django ClienteModel
            
        Returns:
            Entidad Cliente del dominio
        """
        telefono = None
        if model.telefono:
            telefono = Telefono(model.telefono)
        
        return Cliente(
            id=model.id,
            nombre=model.nombre,
            apellido=model.apellido,
            email=Email(model.email),
            documento=DocumentoIdentidad(
                tipo=TipoDocumento(model.tipo_documento),
                numero=model.numero_documento
            ),
            telefono=telefono,
            fecha_creacion=model.fecha_creacion,
            fecha_modificacion=model.fecha_modificacion,
            activo=model.activo
        )
    
    def _to_model(self, entity: Cliente) -> ClienteModel:
        """
        Mapea entidad de dominio a modelo Django.
        
        Args:
            entity: Entidad Cliente del dominio
            
        Returns:
            Modelo Django ClienteModel
        """
        telefono_valor = None
        if entity.telefono:
            telefono_valor = entity.telefono.valor
        
        return ClienteModel(
            id=entity.id,
            nombre=entity.nombre,
            apellido=entity.apellido,
            email=entity.email.valor,
            tipo_documento=entity.documento.tipo.value,
            numero_documento=entity.documento.numero,
            telefono=telefono_valor,
            activo=entity.activo,
            fecha_creacion=entity.fecha_creacion,
            fecha_modificacion=entity.fecha_modificacion
        )
    
    def obtener_por_id(self, id: UUID) -> Optional[Cliente]:
        """
        Obtiene un cliente por su ID.
        
        Args:
            id: UUID del cliente
            
        Returns:
            Cliente si existe, None en caso contrario
        """
        self._logger.info(f"Obteniendo cliente por ID", cliente_id=str(id))
        
        try:
            model = ClienteModel.objects.get(id=id)
            cliente = self._to_domain(model)
            self._logger.info(f"Cliente encontrado", cliente_id=str(id))
            return cliente
        except ClienteModel.DoesNotExist:
            self._logger.warning(f"Cliente no encontrado", cliente_id=str(id))
            return None
    
    def obtener_por_email(self, email: Email) -> Optional[Cliente]:
        """
        Busca un cliente por email.
        
        Args:
            email: Email del cliente
            
        Returns:
            Cliente si existe, None en caso contrario
        """
        self._logger.info(f"Buscando cliente por email", email=email.valor)
        
        try:
            model = ClienteModel.objects.get(email=email.valor)
            cliente = self._to_domain(model)
            self._logger.info(f"Cliente encontrado por email", cliente_id=str(cliente.id))
            return cliente
        except ClienteModel.DoesNotExist:
            self._logger.warning(f"Cliente no encontrado por email", email=email.valor)
            return None
    
    def obtener_por_documento(self, documento: DocumentoIdentidad) -> Optional[Cliente]:
        """
        Busca un cliente por documento de identidad.
        
        Args:
            documento: Documento de identidad del cliente
            
        Returns:
            Cliente si existe, None en caso contrario
        """
        self._logger.info(
            f"Buscando cliente por documento",
            tipo_documento=documento.tipo.value,
            numero_documento=documento.numero
        )
        
        try:
            model = ClienteModel.objects.get(
                tipo_documento=documento.tipo.value,
                numero_documento=documento.numero
            )
            cliente = self._to_domain(model)
            self._logger.info(
                f"Cliente encontrado por documento",
                cliente_id=str(cliente.id)
            )
            return cliente
        except ClienteModel.DoesNotExist:
            self._logger.warning(
                f"Cliente no encontrado por documento",
                tipo_documento=documento.tipo.value,
                numero_documento=documento.numero
            )
            return None
    
    def buscar_por_nombre(self, nombre: str) -> List[Cliente]:
        """
        Busca clientes por nombre (búsqueda parcial).
        
        Args:
            nombre: Nombre a buscar
            
        Returns:
            Lista de clientes que coinciden
        """
        self._logger.info(f"Buscando clientes por nombre", nombre=nombre)
        
        models = ClienteModel.objects.filter(
            nombre__icontains=nombre
        ) | ClienteModel.objects.filter(
            apellido__icontains=nombre
        )
        
        clientes = [self._to_domain(model) for model in models]
        self._logger.info(
            f"Búsqueda por nombre completada",
            nombre=nombre,
            resultados=len(clientes)
        )
        
        return clientes
    
    def obtener_activos(self) -> List[Cliente]:
        """
        Obtiene todos los clientes activos.
        
        Returns:
            Lista de clientes activos
        """
        self._logger.info("Obteniendo clientes activos")
        
        models = ClienteModel.objects.filter(activo=True)
        clientes = [self._to_domain(model) for model in models]
        
        self._logger.info(f"Clientes activos obtenidos", cantidad=len(clientes))
        return clientes
    
    def obtener_todos(self, limite: int = 100, offset: int = 0) -> List[Cliente]:
        """
        Obtiene todos los clientes con paginación.
        
        Args:
            limite: Número máximo de resultados
            offset: Posición inicial
            
        Returns:
            Lista de clientes
        """
        self._logger.info(
            f"Obteniendo todos los clientes",
            limite=limite,
            offset=offset
        )
        
        models = ClienteModel.objects.all()[offset:offset + limite]
        clientes = [self._to_domain(model) for model in models]
        
        self._logger.info(f"Clientes obtenidos", cantidad=len(clientes))
        return clientes
    
    def guardar(self, entidad: Cliente) -> Cliente:
        """
        Guarda o actualiza un cliente.
        
        Args:
            entidad: Cliente a guardar
            
        Returns:
            Cliente guardado
        """
        cliente_id = str(entidad.id)
        self._logger.info(f"Guardando cliente", cliente_id=cliente_id)
        
        try:
            # Verificar si existe para determinar CREATE vs UPDATE
            existe = ClienteModel.objects.filter(id=entidad.id).exists()
            accion = "UPDATE" if existe else "CREATE"
            
            # Obtener datos previos para auditoría
            datos_previos = None
            if existe:
                model_anterior = ClienteModel.objects.get(id=entidad.id)
                datos_previos = {
                    "nombre": model_anterior.nombre,
                    "apellido": model_anterior.apellido,
                    "email": model_anterior.email,
                    "telefono": model_anterior.telefono,
                    "activo": model_anterior.activo
                }
            
            # Convertir a modelo y guardar
            model = self._to_model(entidad)
            
            # Django ORM: Usar update_or_create o save con force_update/force_insert
            if existe:
                model.save(force_update=True)
            else:
                model.save(force_insert=True)
            
            # Datos nuevos para auditoría
            datos_nuevos = {
                "nombre": model.nombre,
                "apellido": model.apellido,
                "email": model.email,
                "telefono": model.telefono,
                "activo": model.activo
            }
            
            # Registrar auditoría
            self._auditoria.registrar(
                entidad_tipo="Cliente",
                entidad_id=entidad.id,
                accion=accion,
                datos_previos=datos_previos,
                datos_nuevos=datos_nuevos,
                resultado="EXITO",
                mensaje=f"Cliente {accion.lower()}do exitosamente"
            )
            
            self._logger.info(
                f"Cliente guardado exitosamente",
                cliente_id=cliente_id,
                accion=accion
            )
            
            # Retornar entidad actualizada desde BD
            return self._to_domain(model)
            
        except Exception as e:
            self._logger.error(
                f"Error al guardar cliente",
                cliente_id=cliente_id,
                excepcion=e
            )
            
            # Registrar fallo en auditoría
            self._auditoria.registrar(
                entidad_tipo="Cliente",
                entidad_id=entidad.id,
                accion="SAVE",
                resultado="FALLO",
                mensaje=f"Error al guardar cliente: {str(e)}"
            )
            
            raise
    
    def eliminar(self, id: UUID) -> bool:
        """
        Elimina un cliente por su ID (eliminación lógica).
        
        Args:
            id: UUID del cliente
            
        Returns:
            True si se eliminó, False si no existía
        """
        self._logger.info(f"Eliminando cliente", cliente_id=str(id))
        
        try:
            model = ClienteModel.objects.get(id=id)
            
            # Eliminación lógica
            model.activo = False
            model.save()
            
            # Registrar auditoría
            self._auditoria.registrar(
                entidad_tipo="Cliente",
                entidad_id=id,
                accion="DELETE",
                datos_previos={"activo": True},
                datos_nuevos={"activo": False},
                resultado="EXITO",
                mensaje="Cliente eliminado lógicamente"
            )
            
            self._logger.info(f"Cliente eliminado", cliente_id=str(id))
            return True
            
        except ClienteModel.DoesNotExist:
            self._logger.warning(f"Cliente no encontrado para eliminar", cliente_id=str(id))
            return False
    
    def existe(self, id: UUID) -> bool:
        """
        Verifica si existe un cliente con el ID dado.
        
        Args:
            id: UUID del cliente
            
        Returns:
            True si existe, False en caso contrario
        """
        return ClienteModel.objects.filter(id=id).exists()

