"""
Serializers para Cliente - Validación de entrada/salida
"""
from rest_framework import serializers
from shared.enums.tipos_documento import TipoDocumento
from application.dto.cliente_dto import CrearClienteDTO, ClienteDTO


class CrearClienteSerializer(serializers.Serializer):
    """
    Serializer para crear un cliente.
    
    Solo valida formato, NO reglas de negocio.
    """
    nombre = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    apellido = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    email = serializers.EmailField(
        required=True,
        max_length=255
    )
    tipo_documento = serializers.ChoiceField(
        choices=[td.value for td in TipoDocumento],
        required=True
    )
    numero_documento = serializers.CharField(
        max_length=20,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    telefono = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    
    def to_dto(self) -> CrearClienteDTO:
        """Convierte datos validados a DTO de aplicación"""
        validated = self.validated_data
        return CrearClienteDTO(
            nombre=validated['nombre'],
            apellido=validated['apellido'],
            email=validated['email'],
            tipo_documento=TipoDocumento(validated['tipo_documento']),
            numero_documento=validated['numero_documento'],
            telefono=validated.get('telefono') or None
        )


class ClienteSerializer(serializers.Serializer):
    """
    Serializer de salida para Cliente.
    
    Mapea desde ClienteDTO.
    """
    id = serializers.UUIDField(read_only=True)
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    tipo_documento = serializers.CharField()
    numero_documento = serializers.CharField()
    telefono = serializers.CharField(allow_null=True)
    activo = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
    fecha_modificacion = serializers.DateTimeField()
    
    @staticmethod
    def from_dto(dto: ClienteDTO) -> dict:
        """Convierte DTO a diccionario para serializar"""
        return {
            'id': dto.id,
            'nombre': dto.nombre,
            'apellido': dto.apellido,
            'email': dto.email,
            'tipo_documento': dto.tipo_documento,
            'numero_documento': dto.numero_documento,
            'telefono': dto.telefono,
            'activo': dto.activo,
            'fecha_creacion': dto.fecha_creacion,
            'fecha_modificacion': dto.fecha_modificacion
        }
