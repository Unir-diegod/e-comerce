"""
Admin configuration for Cliente model
"""
from django.contrib import admin
from .models import ClienteModel


@admin.register(ClienteModel)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'apellido', 'tipo_documento', 'numero_documento', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'tipo_documento', 'fecha_creacion')
    search_fields = ('nombre', 'apellido', 'email', 'numero_documento')
    readonly_fields = ('id', 'fecha_creacion', 'fecha_modificacion')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'email')
        }),
        ('Documento de Identidad', {
            'fields': ('tipo_documento', 'numero_documento')
        }),
        ('Contacto', {
            'fields': ('telefono',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Metadatos', {
            'fields': ('id', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
