# Prompt 41 · Estados con colores comunes

Cambios de presentación sobre el tema del Prompt 30. No hay SQL, dependencias nuevas, transiciones de estado nuevas ni cambios de permisos. No se modificaron registros de Supabase ni se enviaron correos reales.

## Inventario: antes y después

| Lugar | Antes | Después |
|---|---|---|
| `ui/tema.py`, `utils/estados.py` | Etiquetas y colores en dos archivos distintos | Catálogo en `ui/estados.py`; adaptadores para las importaciones anteriores |
| Registro de Casos | Ya existía tabla HTML con chips, sin franja lateral ni íconos | Chip con ícono/texto y franja en fila; misma franja en las fichas móviles |
| Filtros de Casos | Pills nativas sin colores específicos ni conteos | Colores por etapa, íconos, conteos y activo con contorno; conserva subetapa En revisión |
| Detalle | Chip aislado | Banda lateral del color de la etapa y chip |
| Venta y aceptación | Pendiente / Abono recibido / Pagado en texto | Chip de pago y opciones con ícono; Abono recibido se muestra como Anticipo pagado |
| Hoy | Acciones y pendientes sin chips comunes de estado/antigüedad | Chips en tarjetas y pendientes; antigüedad verde, amarilla o roja con número de días |
| Historial del caso | Líneas de texto | Línea de tiempo con estado en hitos de aceptación, venta, rechazo, cierre y eventos que incluyan `estado_nuevo`; los eventos deshechos se indican y no se muestran como vigentes |
| Dashboard | Embudo usaba un diccionario de colores del tema | Orden y colores explícitos desde el catálogo; no usa la secuencia automática de Plotly para etapas |
| Versiones de cotización | Vigente / Vencida según fecha | Conserva vigencia y fechas; añade clasificación visual y Vence en N días |
| Editor de cotización | Aviso de borrador sin chip | Chip Borrador, sin convertirlo en versión emitida |
| Ficha PDF | No mostraba el estado | Banda con etiqueta y ayuda, fondo/texto/borde desde el mismo catálogo |
| Correo de nueva solicitud a Administración | Solo texto plano | Conserva texto y añade alternativa HTML con Solicitud y colores comunes |
| Correo explícito de cotización | Solo texto plano y adjuntos | Conserva texto/adjuntos y añade alternativa HTML con Enviada |
| Avisos de documentos | Mensaje genérico sin estado del caso | Se conservan: no se agregan datos internos al aviso para clientes |
| Reportes y CSV | Conteos y etiquetas sin formato de color | Conservados; CSV no admite colores. Las tablas que muestran Estado usan el componente común |
| Cotización Word/PDF | Sin estado interno del caso | Se conserva; el cambio solicitado del documento es en la ficha administrativa |
| Guía de estilo | Muestras de estados del caso | Añade pagos, cotizaciones, antigüedad y descarga JSON del catálogo |

Se revisaron las migraciones existentes: `mf_casos` conserva Solicitud, En revisión, Cotizado, Vendido, En ejecución, Finalizado y Cancelado; `mf_ventas.estado_pago` conserva Pendiente, Abono recibido y Pagado. Los eventos y envíos siguen en `mf_eventos_caso` y `mf_envios_cotizacion`. No se renombran columnas ni valores almacenados.

La tabla ya era HTML antes de este trabajo: se conserva porque permite chips y franja, mientras `st.dataframe` no renderiza ese HTML de forma nativa. No se cambia el orden de los registros ni se introduce o elimina paginación. Se mantiene el buscador, las opciones de filtro, la apertura de detalle y «Exportar listado CSV».

## Fuente única y reutilización

`ui/estados.py` contiene `CATALOGO`, un diccionario JSON compatible con cuatro grupos: caso, pago, cotizacion y antiguedad. Cada entrada define clave, etiqueta, fondo, texto, borde, sólido, ícono, orden y ayuda. Incluye funciones `color_estado`, `chip_estado`, `etiqueta_con_icono`, `mapa_colores`, antigüedad y clasificación visual de cotizaciones.

`utils/estados.py` y `ESTADOS_COLORES` son adaptadores derivados, sin colores propios. Los estilos del portal se generan en `ui/tema.py` a partir del catálogo. Los colores generales de la marca y de alertas no son definiciones de estados y permanecen en el tema. No hay otro mapa estado → código hexadecimal en el código de producción.

Para los futuros scripts de hoja de cálculo se puede importar `CATALOGO` sin cargar Streamlit ni consultar Supabase. Para copiarlo a Looker Studio: Mi cuenta → Guía de estilo → **Descargar catálogo de colores**. No se presupone que esos otros módulos estén implementados.

## Fechas, versiones y accesibilidad

- Antigüedad: 0–1 días verde; 2–5 amarillo; 6 o más rojo. Siempre muestra días, texto e ícono.
- Cotización: Borrador mientras se edita; Enviada solo con evidencia de envío; Sin respuesta después de 5 días; Vencida después de 30 días o al pasar su vigencia. Una aceptación o rechazo registrado tiene prioridad.
- Se consideran los eventos de la versión concreta, ignorando los deshechos y los de otras versiones. La fecha local usa America/Santiago.
- Una versión recién generada sin envío no se etiqueta falsamente Enviada: muestra «Generada · Sin envío registrado». No se crea un estado de base de datos por este texto.
- «Vence en N días» usa la fecha real `valida_hasta`. Los indicadores visuales no cambian fechas ni validaciones de aceptación/venta.
- El embudo conserva sus cinco etapas; Rechazada sigue fuera de él, con su chip separado, para no alterar el cálculo anterior. No se suman ni reordenan datos de negocio.
- Se prueba contraste de texto sobre fondo y de texto de gráficos sobre cada sólido (mínimo 4,5:1). Los chips llevan ícono y etiqueta; el filtro activo añade contorno.
- Las opciones del desplegable nativo conservan texto legible; el color de etapas está en los chips de filtro, ya que no se controla de forma portable cada opción del selector del navegador.
- La ficha PDF incluye etiqueta y frase además del color. Se renderizaron seis ejemplos ficticios y se revisaron visualmente las bandas.

## Archivos modificados

- `ui/estados.py`: catálogo y funciones puras, sin datos ni consultas.
- `ui/tema.py`: estilos derivados, chips, leyenda, franja de tabla y línea de tiempo. Se agrupan combinaciones de colores idénticas para evitar CSS repetido.
- `utils/estados.py`: compatibilidad con alias históricos.
- `utils/graficos_dashboard.py`: orden y colores del embudo.
- `paginas/gestion.py`: filtros y conteos, leyenda, detalle, pagos e historial de versiones. Comparte una lectura de eventos con la línea de tiempo para evitar consultarlos dos veces.
- `paginas/hoy.py`: chips de estado, pago y antigüedad; conserva las mismas acciones y umbrales de la pantalla.
- `paginas/cotizador.py`, `paginas/acciones_cotizacion.py`: borrador, opciones de pago y cronología.
- `paginas/guia_estilo.py`: muestras y descarga del catálogo.
- `servicios/ficha_caso.py`: banda de estado en PDF.
- `servicios/envio_cotizacion.py`, `scripts/avisos_solicitud.py`: alternativa HTML escapada; transporte, confirmación y destinatarios sin cambios.
- `tests/test_estados41.py`: límites de fechas, alias, decisiones deshechas, escape HTML, orden/color del gráfico y recorrido de registro/CSV.
- `tests/test_tema30.py`: presupuesto de 20 KiB (20 × 1024 bytes). El CSS emitido total es 20.384 bytes, frente a 19.944 anteriores: +440 bytes. Supera el límite decimal anterior de 20.000 en 384 bytes; se informa expresamente este pequeño incremento.
- `tests/generar_preview_dashboard.py`: conserva el CSS exclusivo de la previsualización estática, ahora separado del CSS que cargan las páginas; sigue definido en el tema único.

Los nombres legibles de variables y selectores se conservan en el código fuente. Para reducir transferencia, el CSS emitido usa variables abreviadas y clases nativas equivalentes, verificadas en el código instalado de Streamlit 1.65. No se agregan fuentes, librerías ni animaciones.

## Cómo probar y qué debería verse

1. Abre la app como Administración y entra en Casos y cotizaciones. Con un caso de cada etapa debes ver seis colores, íconos y franjas. «En revisión» conserva su opción, con apariencia de Solicitud y ayuda específica. No modifiques casos reales solo para esta prueba: usa datos ficticios o revisa las muestras de la Guía de estilo.
2. Pulsa un filtro de estado: se resalta con contorno y se filtra como antes. «Todos los estados» y cada etapa tienen conteo. Busca un nombre y descarga CSV: debe conservar datos y orden; el CSV contiene etiquetas, sin HTML ni colores.
3. Abre un caso. Debes ver banda y chip iguales a su fila. En Venta, un abono se presenta como Anticipo pagado; guardar sigue usando el valor histórico.
4. En Hoy, revisa solicitudes de 1, 2, 5 y 6 días: deben verse verde, amarillo, amarillo y rojo. Los botones mantienen sus destinos y no ejecutan acciones por mostrar el chip.
5. En Dashboard abre «¿Qué significa cada color?». El embudo mantiene cantidades y orden, con los mismos colores del registro. Rechazadas siguen indicadas fuera del embudo.
6. En Cotizaciones revisa una reciente, una de 6 días, otra vencida, una aceptada y una rechazada. Debes ver clasificación, vigencia y fecha; una versión sin evidencia de envío no aparece como Enviada. Un borrador no cuenta como versión.
7. Descarga la ficha PDF y comprueba que etiqueta/fondo/franja coinciden con el caso. Los correos reales solo se enviarán por las acciones ya existentes; las pruebas usan SMTP simulado.
8. Repite registro, detalle y Dashboard a 375 px y en computador: la tabla pasa a fichas, conserva chip y franja; no debe haber scroll horizontal de la página. A 768 px comprueba también que las leyendas y filtros se ajustan al ancho.
9. Entra como cliente y sin sesión: no deben aparecer páginas administrativas, cronologías ni montos internos nuevos.

Pruebas locales:

```powershell
python -m unittest discover -s tests
```

La suite usa datos ficticios. La revisión visual de las seis fichas PDF sí se realizó. El recorrido responsive de la app en navegador y la comprobación del despliegue público están pendientes; las pruebas AppTest no validan píxeles ni el comportamiento real de CSS en móvil. No se presentan capturas de navegador como si se hubieran tomado.

## Estado → colores → lugares

Tabla generada desde el catálogo; en producción los códigos viven únicamente en `ui/estados.py`.

| Grupo / estado | Fondo / texto | Borde / sólido | Dónde se muestra |
|---|---|---|---|
| caso / Solicitud | #EAF1FF / #244FAF | #6699FF / #6699FF | Registro, detalle, Hoy, leyendas, embudo; ficha PDF. Solicitud también en aviso a Administración. |
| caso / Cotizada | #F1ECFF / #6533A8 | #9966FF / #9966FF | Registro, detalle, Hoy, leyendas, embudo; ficha PDF. Solicitud también en aviso a Administración. |
| caso / Aceptada | #E7F5ED / #216342 | #32956B / #32956B | Registro, detalle, Hoy, leyendas, embudo; ficha PDF. Solicitud también en aviso a Administración. |
| caso / En seguimiento | #FFF6D1 / #705800 | #C69A00 / #FFCC00 | Registro, detalle, Hoy, leyendas, embudo; ficha PDF. Solicitud también en aviso a Administración. |
| caso / Cerrada | #EDF0F4 / #4D5C71 | #8793A5 / #8793A5 | Registro, detalle, Hoy, leyendas, embudo; ficha PDF. Solicitud también en aviso a Administración. |
| caso / Rechazada | #FCECEE / #963D47 | #E99A9F / #E99A9F | Registro, detalle, Hoy, leyendas, embudo; ficha PDF. Solicitud también en aviso a Administración. |
| pago / Pendiente | #FFF6D1 / #705800 | #C69A00 / #FFCC00 | Venta, diálogo de aceptación, pendientes de Hoy y guía. |
| pago / Anticipo pagado | #EAF1FF / #244FAF | #6699FF / #6699FF | Venta, diálogo de aceptación, pendientes de Hoy y guía. |
| pago / Pagado | #E7F5ED / #216342 | #32956B / #32956B | Venta, diálogo de aceptación, pendientes de Hoy y guía. |
| cotizacion / Borrador | #EDF0F4 / #4D5C71 | #8793A5 / #8793A5 | Editor o historial de versiones y guía. Enviada también en el correo de cotización. |
| cotizacion / Enviada | #F1ECFF / #6533A8 | #9966FF / #9966FF | Editor o historial de versiones y guía. Enviada también en el correo de cotización. |
| cotizacion / Sin respuesta | #FFF0E0 / #8A4800 | #D68A37 / #E9A45D | Editor o historial de versiones y guía. Enviada también en el correo de cotización. |
| cotizacion / Vencida | #FCECEE / #963D47 | #E99A9F / #E99A9F | Editor o historial de versiones y guía. Enviada también en el correo de cotización. |
| cotizacion / Aceptada | #E7F5ED / #216342 | #32956B / #32956B | Editor o historial de versiones y guía. Enviada también en el correo de cotización. |
| cotizacion / Rechazada | #FCECEE / #963D47 | #E99A9F / #E99A9F | Editor o historial de versiones y guía. Enviada también en el correo de cotización. |
| antiguedad / Menos de 2 días | #E7F5ED / #216342 | #32956B / #32956B | Lista de pendientes de Hoy y guía. |
| antiguedad / De 2 a 5 días | #FFF6D1 / #705800 | #C69A00 / #FFCC00 | Lista de pendientes de Hoy y guía. |
| antiguedad / Más de 5 días | #FCECEE / #963D47 | #E99A9F / #E99A9F | Lista de pendientes de Hoy y guía. |

## Resultado de pruebas

| Prueba | Resultado |
|---|---|
| Suite completa | 271 pruebas en 157,497 s: OK. Incluye recorridos de cotización, roles, recarga y SMTP simulado. |
| Catálogo y contraste | 18 entradas, serialización JSON y contraste ≥4,5:1 verificados. |
| Alias y escape HTML | Valores históricos conservados; contenido no confiable escapado. |
| Antigüedad | Días 0, 1, 2, 5 y 6 verificados. |
| Cotizaciones | Límites 5/6 y 30/31 días, fecha de vencimiento, aceptación, rechazo, eventos deshechos y versiones ajenas verificados. |
| Registro y CSV | Siete valores históricos, seis apariencias, mismo orden y exportación disponible; sin mutar registros. |
| Embudo | Orden y colores explícitos, valores conservados y estado vacío comprobados. |
| Ficha PDF | Seis PDF ficticios renderizados y bandas revisadas visualmente; comparación en output/pdf/estados41/comparacion.png. |
| 375 px / 768 px / computador | Pendiente revisión visual en navegador. Se conservan los breakpoints y fichas móviles del tema. |
| Aplicación publicada | Código subido a GitHub; despliegue público no comprobado en navegador. |
