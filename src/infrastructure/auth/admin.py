"""
Configuración de Django Admin para el modelo Usuario
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, RolUsuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin personalizado para Usuario"""
    
    list_display = ['email', 'nombre', 'rol', 'is_active', 'fecha_creacion']
    list_filter = ['rol', 'is_active', 'fecha_creacion']
    search_fields = ['email', 'nombre']
    ordering = ['-fecha_creacion']
    
    fieldsets = (
        ('Información de acceso', {
            'fields': ('email', 'password')
        }),
        ('Información personal', {
            'fields': ('nombre', 'rol')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Fechas importantes', {
            'fields': ('fecha_ultima_login', 'fecha_creacion')
        }),
    )
    
    add_fieldsets = (
        ('Crear nuevo usuario', {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'rol', 'password1', 'password2', 'is_active'),
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_ultima_login']
    
    def save_model(self, request, obj, form, change):
        """Asegurar que el password se hashee correctamente"""
        if not change or 'password' in form.changed_data:
            obj.set_password(form.cleaned_data.get('password'))
        super().save_model(request, obj, form, change)
