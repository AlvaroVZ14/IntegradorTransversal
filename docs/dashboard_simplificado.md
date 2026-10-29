# Simplificación del Dashboard

## Análisis previo, comunicado antes de modificar

Los cálculos están en `mente_futuro/domain.py:dashboard_data` y
`servicios/dashboard.py`. Se mantienen intactos. El Dashboard respeta los
filtros de servicio y temática; usa fecha de venta para ventas y fecha de
creación convertida a America/Santiago para solicitudes.

| Indicador anterior | Definición exacta | Ubicación anterior |
| --- | --- | --- |
| Ventas del período | Suma de `monto_clp` de las ventas no anuladas con fecha dentro del rango, vinculadas a los casos que cumplen servicio y temática. | Tarjeta y chip de encabezado en Dashboard. |
| Ventas cerradas | Número de filas de esas mismas ventas. No corresponde al estado Cerrada del caso. | Tarjeta en Dashboard, gráfico Solicitudes vs ventas y exportación. |
| Nuevas solicitudes | Número de casos cuya fecha de creación en Chile está dentro del rango y cumplen servicio y temática. | Tarjeta y chip de encabezado en Dashboard. |
| Venta promedio | Media aritmética de los montos de las ventas anteriores convertida a entero con `int`, como antes. Sin ventas se muestra —. | Dashboard. |
| Solicitudes que se vendieron | 100 × solicitudes del rango cuyo ID aparece en una venta no anulada con fecha menor o igual al final del rango ÷ solicitudes del rango. Sin solicitudes se muestra —. La venta no necesita estar dentro del rango inferior. | Dashboard. |
| Ventas con pago pendiente | Suma del monto completo de las ventas filtradas cuyo estado de pago es distinto de Pagado. Incluye Abono recibido. No calcula el saldo restante de cada venta. | Dashboard. |

Las variaciones se mantienen: `(actual - anterior) / abs(anterior) × 100`.
El bloque anterior tiene igual número de períodos completos de la agrupación
elegida y termina antes del primer período actual. Si ambos valores son cero,
la variación es 0%; si el anterior es cero y el actual positivo, se informa
Sin comparación previa. Los valores no disponibles permanecen sin porcentaje.

### Gráficos y otros indicadores

| Elemento | Cálculo / definición |
| --- | --- |
| Ventas por período | Suma por semana/mes/trimestre/semestre/año, incluidos períodos en cero. Promedio: suma de los períodos dividida por su cantidad; mejor período: máximo. |
| Solicitudes vs ventas | Conteos separados por fecha de creación y fecha de venta, respectivamente. |
| Temáticas | Conteo de solicitudes filtradas por temática; cinco principales y suma del resto como Otras. Porcentajes sobre todas las solicitudes agrupadas. |
| Embudo | Conteo del estado actual de solicitudes creadas en el rango. Las etiquetas oficiales agrupan sus equivalentes internos. Porcentaje sobre las cinco etapas del embudo, no sobre estados externos al embudo. |
| Origen | Conteo y porcentaje por origen de las solicitudes filtradas; incluye Referido por colega aunque sea cero. |
| Canal | Conteo por canal del enlace de las solicitudes filtradas, usando la normalización existente. |
| Modalidad | Conteo y porcentaje por modalidad de solicitudes filtradas; conserva modalidades no informadas y otras existentes. |
| Reserva vs remuneración | Sumas de los montos de reparto efectivamente guardados de las ventas filtradas. Si faltan datos de reparto, no se inventan porcentajes. |
| Tipo de servicio | Conteo y porcentaje de solicitudes filtradas por servicio. |
| Dato destacado | Mejor período por monto cuando hay ventas; de lo contrario, temática con más solicitudes y su porcentaje. |

### Hoy y Casos: no son exactamente Nuevas solicitudes

La etiqueta literal Nuevas solicitudes solo estaba en Dashboard. Se revisaron
las otras pantallas para evitar equiparar números con definiciones distintas:

- **Hoy / Por cotizar:** casos activos en Solicitud o En revisión sin cotización.
- **Hoy / Pagos por registrar:** ventas no anuladas Pendiente o Abono recibido
  de casos no cerrados/rechazados.
- **Hoy / Acciones pendientes:** suma de las seis listas (solicitudes,
  seguimientos, datos, pagos, cierres y correos). Un caso puede aportar varias
  acciones. Las reglas y umbrales no se modifican.
- **Casos / Casos registrados:** todos los casos cargados, antes de filtrar.
- **Casos / Por revisar:** estados Solicitud y En revisión, independientemente
  de que exista una cotización.
- **Casos / En desarrollo:** estados internos Vendido y En ejecución,
  presentados como Aceptada y En seguimiento.
- El encabezado de Casos repetía el total y mostraba el número de etapas con
  casos, o el conteo del estado seleccionado.

Otros duplicados propuestos, sin modificarlos: los tres chips del encabezado
de Hoy repiten sus tres tarjetas. También hay cifras presentes en gráficos
y tarjetas, pero conservan su contexto analítico y no se retiran.

## Presentación resultante

- Dashboard: cuatro tarjetas, sin chips repetidos en el encabezado.
- **Total vendido** conserva el monto y añade la cantidad de ventas debajo,
  incluida su comparación anterior cuando existe. La ayuda explica monto
  frente a cantidad y evita confundir venta registrada con caso Cerrada.
- **Venta promedio**, **Solicitudes que se vendieron** y **Ventas con pago
  pendiente** conservan sus valores, ayudas, tendencias y variaciones.
- **Ver detalle de indicadores** contiene los seis indicadores originales,
  valor anterior y variación. El conteo histórico de solicitudes se presenta
  como Solicitudes recibidas en el período; no como otra tarjeta de tareas.
- Se conservan todos los gráficos, filtros, solicitudes del período y CSV.
- Casos: sin tarjetas ni chips de resumen. Permanecen lista con sus filtros,
  número de registros, estados, exportación y acceso al detalle/acciones.
- Hoy no cambia: concentra el resumen y las tareas diarias.

## Comparación antes / después

Muestra ficticia: 01/05/2026 a 21/10/2026, agrupación Mensual, todos los servicios
y temáticas. Se capturó el Dashboard anterior antes de modificarlo y se comparó
con el posterior. Los archivos de comprobación quedan en `tmp/`, ignorado por Git.

| Indicador anterior | Antes | Después | Dónde queda |
| --- | --- | --- | --- |
| Ventas del período | $7.460.000 | $7.460.000 | Tarjeta Total vendido y detalle. |
| Ventas cerradas | 6 | 6 | Texto dentro de Total vendido, detalle, gráfico y CSV. |
| Nuevas solicitudes | 12 | 12 | Detalle como Solicitudes recibidas en el período, gráficos, listado y CSV. |
| Venta promedio | $1.243.333 | $1.243.333 | Tarjeta y detalle. |
| Solicitudes que se vendieron | 50,0% | 50,0% | Tarjeta y detalle. |
| Ventas con pago pendiente | $2.160.000 | $2.160.000 | Tarjeta y detalle. |

Se compararon también las variaciones y todos los puntos de las series:
idénticos. La prueba AppTest repite los valores con Administración en una
instancia nueva, recuperando la sesión de prueba y volviendo al Dashboard.
Esto comprueba la reconstrucción de pantalla, no una recarga física del navegador
ni la cuenta real de producción.

La comparación automática de los seis valores, sus variaciones y las series
previas/posteriores pasó. La suite ejecutó 186 pruebas: la única expectativa
desactualizada era el número de tarjetas (esperaba seis). Tras ajustarla a cuatro,
se repitieron y aprobaron los 33 recorridos de `test_app.py`; la nueva prueba de
valores y sesión nueva también pasó. No se insertaron datos en producción.

## Archivos y cómo probar

- `paginas/dashboard.py`: reubicación de indicadores y cuatro tarjetas.
- `paginas/gestion.py`: listado sin resúmenes repetidos.
- `utils/componentes.py`: opción para omitir métricas de encabezado; por defecto
  conserva el comportamiento de las demás páginas.
- `tests/test_app.py`, `tests/test_en_vivo_ui.py`: comprobaciones actualizadas
  para las nuevas ubicaciones, manteniendo cobertura de estados y refresco.
- `tests/test_dashboard_simplificado.py`: valores previos, sesión nueva,
  cuatro tarjetas, nueve gráficos y exportación.
- Este informe.

Sin cambios de colores, CSS, permisos, base de datos o servicios de cálculo.

```powershell
python -m unittest discover -s tests -p test_dashboard_simplificado.py -v
python -m unittest discover -s tests -p 'test_*.py' -q
```

Manualmente: entrar como Administración, elegir el mismo rango/filtros que
antes, comprobar el monto y la cantidad bajo Total vendido y abrir Ver detalle
de indicadores. Recargar y repetir con esos mismos filtros. En Casos deben
aparecer primero búsqueda, filtro de estado y listado; Hoy mantiene sus tareas.
