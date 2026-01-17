# Guia de Contribucion

Gracias por tu interes en contribuir a E-Commerce Clean Architecture!

## Como Contribuir

### Reportar Bugs

1. Usa la plantilla de Bug Report en Issues
2. Describe el problema claramente
3. Incluye pasos para reproducir
4. Agrega capturas de pantalla si es posible

### Sugerir Funcionalidades

1. Usa la plantilla de Feature Request en Issues
2. Explica claramente el problema que resuelve
3. Describe la solucion propuesta
4. Considera alternativas

### Pull Requests

1. **Fork** el repositorio
2. Crea una **rama** desde `main`:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Commits** siguiendo Conventional Commits:
   ```
   feat: agregar nueva funcionalidad
   fix: corregir bug en Cliente
   docs: actualizar README
   style: formatear codigo
   refactor: mejorar estructura
   test: agregar tests
   chore: actualizar dependencias
   ```
4. **Tests**: Asegurate que todos los tests pasen
   ```bash
   pytest
   python manage.py validar_sistema
   ```
5. **Code Style**: Sigue las convenciones del proyecto
   ```bash
   black src/
   flake8 src/
   ```
6. **Push** tu rama:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
7. Abre un **Pull Request** con:
   - Titulo descriptivo
   - Descripcion de cambios
   - Referencias a issues relacionados
   - Screenshots si aplica

## Estandares de Codigo

### Python

- Usar **Black** para formateo
- Seguir **PEP 8**
- Type hints en funciones publicas
- Docstrings en clases y metodos complejos

### Clean Architecture

- **Domain Layer**: Sin dependencias externas
- **Application Layer**: Solo depende de Domain
- **Infrastructure**: Implementa interfaces del Domain
- **Nunca**: Domain importa Infrastructure

### Commits

Formato: `<tipo>: <descripcion>`

Tipos validos:
- `feat`: Nueva funcionalidad
- `fix`: Correccion de bug
- `docs`: Documentacion
- `style`: Formateo, no cambia logica
- `refactor`: Refactorizacion de codigo
- `test`: Agregar o modificar tests
- `chore`: Mantenimiento, dependencias

### Testing

- Minimo 80% de coverage en Domain Layer
- Tests unitarios para cada entidad
- Tests de integracion para repositorios
- Tests end-to-end para flujos completos

## Estructura de Branches

- `main`: Codigo estable en produccion
- `develop`: Integracion de features (si se usa)
- `feature/nombre`: Nuevas funcionalidades
- `fix/nombre`: Correcciones de bugs
- `docs/nombre`: Cambios en documentacion

## Proceso de Review

1. Pull Request es creado
2. CI/CD ejecuta tests automaticamente
3. Code review por al menos 1 colaborador
4. Aprobar y mergear a `main`

## Configuracion de Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/Yoiser16/e-comerce.git
cd e-comerce

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Crear base de datos
createdb ecomerce_db

# Ejecutar migraciones
python manage.py migrate

# Validar instalacion
python manage.py validar_sistema
```

## Preguntas Frecuentes

**Q: ¿Puedo contribuir sin saber Clean Architecture?**  
A: Si! Lee la documentacion en `docs/` y los diagramas UML para entender la estructura.

**Q: ¿Necesito configurar PostgreSQL?**  
A: Si, para desarrollo usa PostgreSQL local. Ver `docs/DATABASE_CONFIG.md`.

**Q: ¿Como ejecuto los tests?**  
A: `pytest` para tests unitarios, `python manage.py validar_sistema` para validacion completa.

**Q: ¿Donde pido ayuda?**  
A: Abre un Issue con la etiqueta "question" o contacta a los mantenedores.

## Codigo de Conducta

Este proyecto sigue el [Contributor Covenant](https://www.contributor-covenant.org/). 

Se espera:
- Respeto y profesionalismo
- Comunicacion constructiva
- Colaboracion abierta
- Aceptacion de feedback

## Licencia

Al contribuir, aceptas que tus contribuciones sean licenciadas bajo la misma licencia MIT del proyecto.

---

Gracias por contribuir a E-Commerce Clean Architecture! 🎉
