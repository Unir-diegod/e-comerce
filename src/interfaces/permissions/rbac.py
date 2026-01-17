"""
Sistema de Permisos RBAC (Role-Based Access Control)

Define permisos declarativos basados en roles del usuario.
Se aplican a nivel de view/endpoint para controlar acceso.

REGLAS:
- NO contiene lógica de negocio
- Solo valida autenticación y roles
- Es infraestructura de seguridad
"""
from rest_framework import permissions
from infrastructure.auth.models import RolUsuario


class EsAdministrador(permissions.BasePermission):
    """
    Permiso: Solo usuarios con rol ADMIN
    
    Uso: Endpoints críticos de administración
    """
    
    message = 'Solo administradores pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.rol == RolUsuario.ADMIN


class EsOperadorOAdmin(permissions.BasePermission):
    """
    Permiso: Usuarios con rol OPERADOR o ADMIN
    
    Uso: Operaciones de escritura (crear/modificar)
    """
    
    message = 'Se requiere rol de Operador o Administrador.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.rol in [RolUsuario.OPERADOR, RolUsuario.ADMIN]


class PuedeLeer(permissions.BasePermission):
    """
    Permiso: Cualquier usuario autenticado puede leer
    
    Uso: Endpoints de solo lectura
    """
    
    message = 'Debe estar autenticado para acceder.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class PermisosPorMetodo(permissions.BasePermission):
    """
    Permiso dinámico según método HTTP:
    
    - GET, HEAD, OPTIONS: Cualquier usuario autenticado (LECTURA)
    - POST, PUT, PATCH: OPERADOR o ADMIN
    - DELETE: Solo ADMIN
    
    Uso: Endpoints REST estándar
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            self.message = 'Autenticación requerida.'
            return False
        
        # Métodos de lectura: todos los roles autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST, PUT, PATCH: OPERADOR o ADMIN
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.user.rol not in [RolUsuario.OPERADOR, RolUsuario.ADMIN]:
                self.message = 'Se requiere rol de Operador o Administrador para esta operación.'
                return False
            return True
        
        # DELETE: Solo ADMIN
        if request.method == 'DELETE':
            if request.user.rol != RolUsuario.ADMIN:
                self.message = 'Solo administradores pueden eliminar recursos.'
                return False
            return True
        
        return False


class SoloLecturaParaTodos(permissions.BasePermission):
    """
    Permiso: Solo lectura para todos los usuarios autenticados
    
    Uso: Recursos públicos internos (configuración, catálogos)
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            self.message = 'Autenticación requerida.'
            return False
        
        if request.method not in permissions.SAFE_METHODS:
            self.message = 'Este recurso es de solo lectura.'
            return False
        
        return True
