from rest_framework import serializers
from shared.enums.tipos_documento import TipoDocumento
from application.dto.cliente_dto import CrearClienteDTO

class CrearClienteSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    apellido = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    tipo_documento = serializers.ChoiceField(choices=[t.value for t in TipoDocumento])
    numero_documento = serializers.CharField(max_length=50)
    telefono = serializers.CharField(max_length=20, required=False, allow_null=True)

    def to_dto(self) -> CrearClienteDTO:
        return CrearClienteDTO(
            nombre=self.validated_data['nombre'],
            apellido=self.validated_data['apellido'],
            email=self.validated_data['email'],
            tipo_documento=TipoDocumento(self.validated_data['tipo_documento']),
            numero_documento=self.validated_data['numero_documento'],
            telefono=self.validated_data.get('telefono')
        )

class ClienteSerializer(serializers.Serializer):
    """Serializer de salida para Cliente"""
    id = serializers.UUIDField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    tipo_documento = serializers.CharField()
    numero_documento = serializers.CharField()
    telefono = serializers.CharField(allow_null=True)
    activo = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
    fecha_modificacion = serializers.DateTimeField()
