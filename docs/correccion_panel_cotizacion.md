# Paneles de cotización: corrección de superposición

Los paneles de generación y de descargas tenían posición fija y se tapaban entre sí. Ahora forman parte del contenido de la página. El cierre del aviso está arriba, con un área de toque de al menos 44 px, y las anclas de campos dejan espacio para el encabezado.

No cambia el cálculo, guardado, permisos ni generación de documentos.

## Verificación

- Dos pruebas automatizadas: cerrar conserva la versión, el borrador y las descargas del historial; los dos paneles no usan posición fija ni scroll interno.
- Seis pruebas de estilos existentes: aprobadas, incluido el presupuesto de CSS.
- Edge con Playwright contra una instancia local y repositorio ficticio: 390×844, 768×1024 y 1440×900. Sin scroll horizontal, superposición ni errores; cierre visible de 44 px de alto, funcional, con PDF del historial disponible después de cerrar.
- Capturas locales en `output/cotizacion-panel/` (no se incluyen en el repositorio).

Para comprobar en la app publicada: abrir una cotización, generar una versión, bajar hasta el aviso y cerrar con «Cerrar aviso». El formulario debe permanecer legible y las descargas deben seguir en el historial. No se probó una sesión de Administración en producción.
