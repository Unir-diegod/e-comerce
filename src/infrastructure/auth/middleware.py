"""
Middleware de Auditoría para Autenticación y Accesos a la API

Registra automáticamente:
- Intentos de autenticación
- Accesos a endpoints protegidos
- Fallos de autorización
- NO registra credenciales ni tokens
"""
from django.utils.deprecation import MiddlewareMixin
from infrastructure.auditing.servicio_auditoria import ServicioAuditoria
import json


class AuditoriaAutenticacionMiddleware(MiddlewareMixin):
    """
    Middleware que audita todos los accesos a la API
    """
    
    # Endpoints que NO deben auditarse (para evitar ruido)
    ENDPOINTS_EXCLUIDOS = [
        '/admin/',
        '/static/',
        '/favicon.ico',
    ]
    
    # Endpoints sensibles que siempre se auditan
    ENDPOINTS_SENSIBLES = [
        '/api/v1/auth/login',
        '/api/v1/auth/logout',
        '/api/v1/ordenes',
        '/api/v1/clientes',
    ]
    
    def process_request(self, request):
        """
        Procesa la solicitud antes de llegar a la view
        """
        # Guardar información para usar en process_response
        request._audit_start = True
        return None
    
    def process_response(self, request, response):
        """
        Audita la respuesta después de procesarla
        """
        path = request.path
        
        # Verificar si debe auditarse
        if not self._debe_auditar(path):
            return response
        
        # Obtener información del usuario
        usuario_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            usuario_id = str(request.user.id)
        
        # Determinar si fue exitoso
        resultado_exitoso = 200 <= response.status_code < 400
        
        # Obtener IP y User-Agent
        ip = self._obtener_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:200]
        
        # Registrar en auditoría
        try:
            ServicioAuditoria.registrar_acceso_api(
                usuario_id=usuario_id,
                endpoint=path,
                metodo=request.method,
                ip=ip,
                user_agent=user_agent,
                resultado_exitoso=resultado_exitoso,
                codigo_estado=response.status_code
            )
        except Exception as e:
            # No fallar la request si la auditoría falla
            print(f"Error al auditar acceso: {e}")
        
        return response
    
    def _debe_auditar(self, path: str) -> bool:
        """
        Determina si un endpoint debe auditarse
        """
        # Excluir endpoints no relevantes
        for excluido in self.ENDPOINTS_EXCLUIDOS:
            if path.startswith(excluido):
                return False
        
        # Auditar endpoints sensibles
        for sensible in self.ENDPOINTS_SENSIBLES:
            if path.startswith(sensible):
                return True
        
        # Auditar todos los endpoints de la API
        if path.startswith('/api/'):
            return True
        
        return False
    
    def _obtener_ip(self, request) -> str:
        """
        Obtiene la IP real del cliente (considerando proxies)
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            # Tomar la primera IP (cliente real)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        return ip[:45]  # Limitar tamaño (IPv6 max)
