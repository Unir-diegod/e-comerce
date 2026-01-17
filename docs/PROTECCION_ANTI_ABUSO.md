# Documentación de Protección Anti-Abuso

## Resumen

El sistema e-commerce implementa protección anti-abuso mediante rate limiting y controles defensivos para proteger la API contra:

- **Ataques de fuerza bruta** en endpoints de autenticación
- **Scraping automatizado** de datos
- **Abuso de recursos** del sistema
- **DoS a nivel de aplicación**

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE PROTECCIÓN                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  RateLimitMW     │───▶│  DRF Throttling  │───▶│  Views con       │  │
│  │  (Middleware)    │    │  (Global)        │    │  Throttle        │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
│           │                       │                       │            │
│           ▼                       ▼                       ▼            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   ServicioBloqueoTemporal                       │   │
│  │  • Registro de intentos fallidos                                │   │
│  │  • Bloqueo automático por IP/Usuario                            │   │
│  │  • Desbloqueo automático por tiempo                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   Sistema de Auditoría                          │   │
│  │  • Registro de bloqueos                                         │   │
│  │  • Registro de excesos de rate limit                           │   │
│  │  • Trazabilidad completa                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Configuración de Rate Limiting

### Límites Globales

| Tipo de Usuario | Rate Limit | Descripción |
|-----------------|------------|-------------|
| Anónimo | 50 req/min | Usuarios no autenticados |
| Autenticado | 200 req/min | Usuarios con JWT válido |

### Límites por Endpoint

| Endpoint | Rate Limit | Justificación |
|----------|------------|---------------|
| `/api/v1/auth/login` | 5/min | Prevención de fuerza bruta |
| `/api/v1/auth/refresh` | 10/min | Evitar abuso de renovación |
| `/api/v1/ordenes/*` | 20/min | Prevención de órdenes fraudulentas |
| `/api/v1/ordenes/*/confirmar` | 10/min | Operación crítica de negocio |

## Bloqueo Temporal

### Configuración

```python
# Variables de entorno (opcionales)
SECURITY_MAX_FAILED_ATTEMPTS=5      # Intentos antes de bloqueo
SECURITY_BLOCK_DURATION=900         # Duración del bloqueo (15 min)
SECURITY_ATTEMPT_WINDOW=300         # Ventana de conteo (5 min)
```

### Comportamiento

1. **Registro de intentos**: Cada intento fallido de login se registra
2. **Acumulación**: Los intentos se acumulan dentro de la ventana de tiempo
3. **Bloqueo**: Al alcanzar el límite, IP/usuario se bloquea temporalmente
4. **Desbloqueo**: Automático tras expirar el tiempo de bloqueo

## Respuestas HTTP 429

Cuando se excede un límite, el sistema responde:

```json
{
    "error": "Demasiadas solicitudes",
    "detail": "Ha realizado demasiadas solicitudes en un período corto. Por favor, espere antes de intentar nuevamente.",
    "code": "too_many_requests"
}
```

Headers incluidos:
- `Retry-After`: Segundos hasta poder reintentar
- `X-RateLimit-Reset`: Timestamp Unix de reset

## Archivos Implementados

### Nuevos Archivos

| Archivo | Descripción |
|---------|-------------|
| `interfaces/api/rest/throttling.py` | Clases de throttling y servicio de bloqueo |
| `interfaces/api/rest/middleware.py` | Middleware de protección anti-abuso |
| `scripts/test_rate_limit.py` | Script de validación |

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `infrastructure/config/django_settings.py` | Configuración de throttling y cache |
| `interfaces/api/rest/views/auth_views.py` | Throttling en login/refresh |
| `interfaces/api/rest/views/orden_view.py` | Throttling en órdenes |
| `interfaces/api/rest/exceptions.py` | Manejo de HTTP 429 |

## Integración con Auditoría

Todos los eventos de seguridad se registran:

```python
# Evento registrado en auditoría
{
    "entidad_tipo": "SEGURIDAD",
    "accion": "BLOQUEO_TEMPORAL" | "RATE_LIMIT_EXCEDIDO",
    "ip_address": "x.x.x.x",
    "resultado": "BLOQUEADO",
    "mensaje": "Detalle del bloqueo"
}
```

## Validación del Sistema

Ejecutar el script de validación:

```bash
# Asegurarse de que el servidor está corriendo
python manage.py runserver

# En otra terminal
python scripts/test_rate_limit.py
```

El script verifica:
- ✓ Requests normales pasan
- ✓ Exceso devuelve HTTP 429
- ✓ Bloqueo temporal se aplica
- ✓ Desbloqueo automático funciona
- ✓ Headers de seguridad presentes
- ✓ Mensajes genéricos (no revelan reglas)

## Consideraciones de Producción

### Cache Backend

Para producción con múltiples instancias, configurar Redis:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    }
}
```

### Ajuste de Límites

Los límites pueden ajustarse según el tráfico real:

```python
# Producción con alto tráfico
'DEFAULT_THROTTLE_RATES': {
    'anon_global': '100/minute',
    'user_global': '500/minute',
    'login': '10/minute',
    ...
}
```

### Monitoreo

Recomendaciones:
- Alertas cuando IPs se bloquean frecuentemente
- Dashboard de rate limits excedidos
- Análisis de patrones de abuso

## Cumplimiento OWASP

| Vulnerabilidad OWASP | Mitigación Implementada |
|----------------------|------------------------|
| API4:2023 - Unrestricted Resource Consumption | Rate limiting global y por endpoint |
| API2:2023 - Broken Authentication | Bloqueo temporal, rate limit estricto en login |
| API9:2023 - Improper Inventory Management | Auditoría de todos los accesos |

## Contacto

Para reportar problemas de seguridad o sugerir mejoras, contactar al equipo de desarrollo.

---
*Última actualización: Enero 2026*
