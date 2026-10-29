# ImportError al abrir la app publicada

Los registros del 29/10/2026 muestran reiteradamente:

```
ImportError: cannot import name 'registrar_navegacion' from 'utils.navegacion'
```

Se comprobó que GitHub main y el archivo local coinciden y contienen esa
función. En un proceso nuevo funcionan las cinco importaciones del punto de
entrada. El mensaje es compatible con el módulo anterior retenido durante
actualizaciones de una instancia existente; no indica ausencia de dependencias
ni un error en las URLs. El reinicio recomendado no resolvió lo reportado por
el usuario. No se tiene acceso al contenido en memoria del servidor para
afirmar el mecanismo interno exacto.

## Corrección

- Se mueve la implementación actual, sin cambios de comportamiento, a
  `utils/navegacion_portal.py`.
- `app.py` y el servicio de enlaces importan directamente el módulo nuevo.
  Una instancia antigua de `utils.navegacion` ya no interviene en el arranque.
- `utils/navegacion.py` queda como compatibilidad para importaciones anteriores,
  sin una segunda implementación de rutas ni permisos.
- Se adapta el destino del mock de navegación superior al módulo nuevo.

La comparación del AST confirma que toda la implementación movida es idéntica
a la anterior salvo el docstring. Sin cambios SQL, credenciales, permisos,
formularios, estilos ni dependencias.

## Regresión

`tests/test_arranque_cloud.py` inserta una versión antigua de `utils.navegacion`
en `sys.modules`, sin `registrar_navegacion`:

1. Confirma que la importación anterior produce el mismo ImportError.
2. Verifica que el arranque corregido muestra login y formulario público.
3. Verifica rutas y recarga de Administración y Cliente, sin Page not found
   y conservando el destino permitido por rol.

Las pruebas usan repositorio y cuentas ficticias, sin Supabase de producción.
La suite completa de esta entrega pasó: **198 pruebas aprobadas**.
La comprobación publicada debe realizarse después de que Community Cloud reciba
el commit: URL base muestra login; `?vista=solicitud` muestra el formulario
anónimo. Un HTTP 200 por sí solo no demuestra que el script haya arrancado.

```powershell
python -m unittest discover -s tests -p test_arranque_cloud.py -v
python -m unittest discover -s tests -p 'test_*.py' -q
```
