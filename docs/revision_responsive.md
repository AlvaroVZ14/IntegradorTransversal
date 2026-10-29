# Revisión responsive de Mente y Futuro

Alcance: presentación únicamente. No se modifican textos visibles, colores, campos, cálculos, consultas, permisos, sesiones ni operaciones de guardado. Los ajustes se concentran en `utils/estilos.py`; no requieren dependencias, SQL ni secretos nuevos.

## Hallazgos y ajustes por pantalla

| Pantalla | Hallazgo | Ajuste |
| --- | --- | --- |
| Hoy | El encabezado de tableta comprimía el reloj y el título en columnas; en celular el título reservaba demasiado espacio al motivo decorativo. | Acciones debajo del título hasta 1023 px, título móvil adaptativo, motivo más pequeño y márgenes de 16 px. Se conserva el orden de KPI y pendientes; botones al ancho disponible en celular. |
| Solicitudes / Casos y cotizaciones | Los campos del buscador y del detalle tenían 14 px; los nombres extensos y las tablas densas necesitaban límites de ancho explícitos. | Campos de 16 px, ajuste de palabras largas y límites para contenedores. Se conservan las tarjetas móviles existentes; las tablas anchas se desplazan dentro de su contenedor en tableta. |
| Detalle, tarifas, configuración y cotizador | Las filas densas de campos podían quedar estrechas en tableta. Los avisos flotantes del cotizador podían ocupar demasiado alto. | Columnas flexibles con ancho mínimo útil, apilado en celular, cuadros de descarga limitados al alto disponible con desplazamiento propio y acción de generación ajustada al ancho móvil. |
| Compartir | El QR tenía ancho fijo de 280 px; las confirmaciones de copia y los botones de descarga podían superar el espacio de una tarjeta estrecha. Dos controles del bloque QR medían 24 y 38 px de alto. | QR limitado al contenedor y centrado, enlaces largos con salto de línea y botones de copia/descarga al ancho disponible, con texto ajustable y controles del QR de al menos 44 px. Los archivos QR descargables no cambian. |
| Nueva solicitud interna | Los nombres de los tres pasos se recortaban dentro de las pastillas. Guardar quedaba al final de un formulario largo. | Pastillas con altura automática, campos al ancho disponible y Guardar fijo al pie en celular; espacio de reserva para alcanzar los campos finales. Se conservan las otras dos acciones y todos los datos. |
| Formulario público y cliente | El texto de los campos volvía a 14 px en tableta; el cambio de paso podía acercar campos a la barra fija. | Campos de 16 px, márgenes para desplazamiento/foco respecto al encabezado y a las acciones, etiquetas ajustables y botones de ayuda de 44 px. Se conserva la barra de acciones pública, el consentimiento y la identidad bloqueada del cliente. |
| Login y creación de cuenta | Campos de 14 px y botón principal fuera de la primera zona visible en celular; logo grande dentro de la tarjeta estrecha. | Campos de 16 px, logo móvil limitado a 200 px, texto del panel adaptativo y envío fijo al pie en celular con espacio reservado. Las pestañas, registro y autenticación no cambian. |
| Dashboard | Las parejas de gráficos y las acciones del encabezado quedaban estrechas en tableta. | Los gráficos se apilan cuando no tienen ancho útil, el encabezado dispone sus acciones debajo y los campos mantienen 16 px. Se conservan indicadores, filtros, gráficos y datos. |

## Comprobaciones

Se utilizan exclusivamente cuentas, empresas, solicitudes, cotizaciones y ventas ficticias, con repositorio local simulado. No se envían formularios a Supabase ni correos reales.

Revisión en Edge con ventanas de **360, 375, 430, 768 y 1280 px**: Hoy, Nueva solicitud, Casos, Compartir con URL configurada y QR, Dashboard con datos, login y formulario público. Se miden el desplazamiento horizontal del documento y del panel principal, el tamaño calculado de los campos y los límites de los elementos. Se revisan además el detalle de caso, las pestañas Tarifas y Configuración, cotizador, tres pasos internos/públicos, creación de cuenta, cuenta cliente y campos enfocados. La tipografía de los campos se fija en 16 px también en escritorio.

Las capturas y mediciones locales están en `output/responsive-antes`, `output/responsive-despues`, `output/responsive-detalles` y `output/responsive-final`; no son datos de producción ni forman parte del despliegue. La matriz principal de 35 combinaciones pasó sin desplazamiento horizontal; las revisiones de detalle y las comprobaciones finales de campos de escritorio, QR y gráficos también pasaron.

## Cómo revisarlo

1. Ejecutar `python -m streamlit run app.py` y abrir el enlace local mostrado en la terminal.
2. En las herramientas de desarrollo del navegador, seleccionar sucesivamente los cinco anchos indicados y recorrer cada pantalla. La página no debe desplazarse horizontalmente.
3. En celular, comprobar los tres pasos de Nueva solicitud y del formulario público. Los títulos de paso deben verse completos, los campos deben ocupar el ancho disponible y las acciones principales deben quedar accesibles al pie. Desplazarse al final para comprobar consentimiento y acciones secundarias.
4. En Casos, probar nombres de empresa largos, abrir un detalle y recorrer Tarifas, Configuración y Cotizaciones. Las tablas pueden desplazarse dentro de su propio marco; en celular el listado mantiene sus tarjetas.
5. En Compartir, revisar los seis canales, copiar un enlace, abrirlo, cambiar el canal del QR y descargar PNG/SVG. Deben verse el QR completo y los nombres de los botones, sin cambiar el tamaño/calidad del archivo descargado.
6. En login, alternar Iniciar sesión y Crear cuenta de cliente; enfocar los campos y verificar que el botón no impida llegar al último campo.
7. En Dashboard, abrir Filtros y Ver más gráficos; cambiar un filtro y comprobar la distribución de las tarjetas y las gráficas en los tres tipos de pantalla.

## Límites y pendientes

No hay un bloqueo funcional conocido en los ajustes de estilo. Queda la comprobación física en Safari de iPhone, Chrome de Android y navegadores internos de Instagram/Facebook: la emulación de Edge no reproduce exactamente su teclado virtual, barras del navegador, portapapeles ni áreas seguras. En particular debe confirmarse la posición del envío del login con el teclado abierto. No se cambió la lógica existente del teclado ni del portapapeles.

Los selectores internos utilizados corresponden a Streamlit 1.65 y están comentados en el CSS. Deben revisarse al actualizar esa versión.
