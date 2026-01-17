"""Permissions - Control de acceso y permisos"""

from .rbac import (
    EsAdministrador,
    EsOperadorOAdmin,
    PuedeLeer,
    PermisosPorMetodo,
    SoloLecturaParaTodos,
)

__all__ = [
    'EsAdministrador',
    'EsOperadorOAdmin',
    'PuedeLeer',
    'PermisosPorMetodo',
    'SoloLecturaParaTodos',
]
