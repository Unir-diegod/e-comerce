"""
Value Object Documento de Identidad
"""
from domain.value_objects.base import ValueObject
from domain.exceptions.dominio import ValorInvalido
from shared.enums.tipos_documento import TipoDocumento


class DocumentoIdentidad(ValueObject):
    """
    Value Object para documentos de identidad.
    
    Responsabilidades:
    - Validar tipo y número
    - Normalizar formato
    - Garantizar inmutabilidad
    """
    
    def __init__(self, tipo: TipoDocumento, numero: str):
        numero_normalizado = numero.strip().replace(" ", "").replace("-", "")
        
        if not numero_normalizado:
            raise ValorInvalido("El número de documento no puede estar vacío")
        
        if len(numero_normalizado) < 5:
            raise ValorInvalido("El número de documento es demasiado corto")
        
        self._tipo = tipo
        self._numero = numero_normalizado
    
    @property
    def tipo(self) -> TipoDocumento:
        return self._tipo
    
    @property
    def numero(self) -> str:
        return self._numero
    
    def __str__(self) -> str:
        return f"{self._tipo.value}: {self._numero}"
