# Diseño de Mente y Futuro

Solo presentación. Se conservan páginas, permisos, formularios, validaciones, autoguardado, filtros, exportaciones y cálculos comerciales. No se agregan consultas ni escrituras. **Sin dependencias ni SQL nuevos**: se usa Streamlit 1.65, Plotly 6 y los componentes nativos existentes. La activación SQL de [datos en vivo](actualizacion_en_vivo.md) sigue siendo la misma de la entrega anterior.

## Qué debería verse

| Página | Con datos | Sin datos |
|---|---|---|
| Hoy | Saludo según hora de Chile, fecha/hora, ampolleta y tres chips: por cotizar, pagos y acciones. Cada KPI tiene una frase útil y una mini gráfica | KPI en cero y una ampolleta ilustrada junto a «Todo al día. Buen trabajo». Ningún pendiente se inventa |
| Nueva solicitud | El mismo encabezado, ampolleta y chips de las secciones. Tarjetas de formulario, foco azul y botones amarillos | Los campos conservan su ayuda y validación. Cliente mantiene nombre/correo bloqueados y sus permisos |
| Casos y cotizaciones | Dos chips: casos totales y resumen de etapas; KPI con mini gráficas, listado y badges originales. Detalle, cotización, venta, tarifas y configuración conservan todos sus campos | Mensaje para crear una solicitud o ajustar filtros; sin tablas falsas ni cambio de permisos |
| Dashboard | Chips de ventas/solicitudes que se actualizan con los datos; seis KPI con mini gráficas; gráficos completos, áreas suaves, barras redondeadas, donas con total y estrella amarilla en el mejor período | Estados vacíos originales, valores «—» donde corresponde y ninguna venta ficticia |
| Login | Tarjeta blanca con logo, fondo aurora sutil y botón amarillo; campos y recuperación existentes | Se mantienen los mensajes de ingreso y errores amables |

El menú oscuro conserva INICIO/GESTIÓN/ANÁLISIS, iconos, usuario y Cerrar sesión. El activo tiene barra amarilla y brillo morado; el texto queda blanco. El chip inferior recibe el mismo estado de conexión del encabezado. En Nueva solicitud indica la conexión del portal, sin afirmar que se haya guardado una solicitud.

Los chips del encabezado reciben las cifras por el canal local del componente de estado: **cero consultas adicionales y ningún rerun por segundo**. Si hay un fallo, se conserva el snapshot anterior junto al aviso de conexión existente.

## Mini gráficas y números

Cada mini gráfica usa hasta seis períodos del rango seleccionado. Las etiquetas y sus tooltips usan pesos chilenos, enteros o porcentajes según el KPI. En promedio/conversión, los períodos sin base quedan como huecos; no se dibuja un cero inventado.

En Hoy/Casos no existe una tabla de snapshots históricos del backlog. Sus mini gráficas muestran **pendientes/casos actuales agrupados por mes de ingreso**, con esa aclaración debajo. No representan cuántos pendientes había antes.

Los valores exactos de `st.metric` siguen disponibles para lectores de pantalla y pruebas. Tienen una entrada de 360 ms con `transform` y `opacity`. **No se interpolan cifras con `@property` ni JavaScript**: el conteo de texto exigiría animar otra propiedad y mostrar montos intermedios. Se prioriza la regla obligatoria de rendimiento y que el importe verdadero esté visible inmediatamente.

## Movimiento, contraste y rendimiento

- Solo dos animaciones infinitas propias: una capa aurora con tres manchas al 8% (36 s) y el brillo interno del encabezado (38 s). Se pausan durante los esqueletos de carga.
- En menos de 768 px ambas quedan estáticas, se reduce el blur de 38 a 16 px y se retira el blur de los chips. Con movimiento reducido no se animan entradas, hover, números, rayos ni confeti.
- Entradas de bloques: 240 ms, con diferencias de 60 ms; la tercera termina a los 360 ms. Rayos y esqueletos tienen ciclos finitos. No se anima color, blur, posición de fondo, sombra ni medidas.
- Plotly conserva sus interacciones y `uirevision`; no se interpolan sus trazados. El halo de las líneas es estático y se retira en celular. Las donas destacan una porción en hover usando solo `transform` en escritorio.
- El texto blanco del banner tiene una capa oscura de contraste. Menú blanco sobre azul marino; números con degradado azul marino/azul. Pares medidos: texto secundario/blanco 5,43:1; azul/blanco 4,62:1; azul marino/blanco 15,39:1. Los textos sobre colores de los gráficos llevan un halo blanco y relleno oscuro. En hover/pestañas lavanda se usa texto azul marino.
- Controles y botones de al menos 44 px, foco visible y selección de texto lavanda. SVG decorativos ocultos a tecnologías de asistencia; mini gráficas con descripciones de sus valores. Se conserva el contenido accesible de los KPI nativos.

Los efectos se degradan a colores planos y cifras reales si el navegador no admite backdrop-filter o texto con degradado. No hay imágenes externas nuevas, librerías de animación ni procesos de fondo. Se reutilizan las fuentes existentes y la marca en SVG inline.

## Momentos especiales

Tras confirmar una **venta nueva** (ambos flujos existentes) o una **solicitud de cliente enviada**, aparece un toast y confeti azul/morado/amarillo durante 2 s. Son 18 piezas en escritorio y ocho en celular. No aparece al abrir una página, al fallar una escritura, al editar una venta ni al recargar un comprobante. Con movimiento reducido queda el toast y el comprobante, sin confeti. No se habilita un nuevo formulario anónimo ni se cambia el flujo público/login existente.

## Pruebas y cómo ver el cambio

Al desplegar el commit de GitHub, abre tu enlace de Streamlit. Si tenías la pestaña abierta con una sesión antigua, recarga una vez para cargar los nuevos archivos. Esta entrega no requiere pegar SQL ni cambiar secretos.

| Prueba con datos ficticios | Resultado esperado |
|---|---|
| Abrir las cuatro páginas a 375 px, 768 px y 1440 px | Sin scroll horizontal del contenido. Una columna en celular; KPI reorganizados en tablet. A 375 y 768 los filtros del Dashboard quedan plegados en «Filtros», conservando los chips activos |
| Abrir el menú en celular y recorrerlo con teclado | Enlaces grandes y legibles; activo marcado con barra, icono y color, foco visible |
| Cambiar filtros y esperar un refresco | Cambian métricas, chips y mini gráficas del mismo rango. Los filtros y formularios se conservan como antes |
| Ver Dashboard con cero y una venta | Sin ejes vacíos; con una venta se ve el punto y la estrella. Todos los períodos en cero siguen presentes |
| Revisar Hoy sin pendientes | Mensaje «Todo al día» con ampolleta; las métricas no muestran pendientes ficticios |
| Enviar una solicitud de prueba como Cliente | Comprobante con código, plazo de contacto y toast; confeti breve una vez. Nombre/correo siguen bloqueados |
| Registrar una venta por cada flujo y luego recargar | Toast y confeti solo al confirmar. Se conservan la venta y Deshacer existentes; recargar no repite la celebración |
| Provocar un error de validación o escritura | Sin celebración ni confirmación falsa; se mantienen los avisos y lo escrito |
| Activar `prefers-reduced-motion: reduce` | Cero animaciones activas, sin confeti; todas las funciones siguen disponibles |

Verificación: recorridos de navegador local headless con datos ficticios en 12 combinaciones de página/ancho, revisión visual de capturas, comprobación de desbordamiento y presupuesto de movimiento; pruebas Python existentes y nuevas de formatos/escape/series; pruebas JS de actualización de chips y confeti. La emulación de tamaños no sustituye medir un teléfono físico de gama media.

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_en_vivo_js.mjs
node tests/test_celebracion.mjs
```

## Archivos completos

El ZIP de entrega incluye el código completo del repositorio y capturas ficticias. Los estilos están exclusivamente en `utils/estilos.py`, con variables en `:root` y comentarios sobre los selectores internos de Streamlit 1.65. `CSS_VIDRIO` se comparte entre la página y la raíz del componente nativo, sin duplicar su definición.

Componentes: `utils/componentes.py`; estado/chips: `utils/en_vivo.py` y `.js`; celebración: `utils/celebracion.js`; series de presentación: `utils/metricas_visuales.py`; gráficos: `utils/plotly_tema.py` y `utils/graficos_dashboard.py`. Las páginas solo pasan los datos ya cargados y activan la celebración después de sus confirmaciones existentes.
