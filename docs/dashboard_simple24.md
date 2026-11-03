# Dashboard simple — Prompt 24

## Qué se revisó y qué se retiró

| Bloque anterior | Decisión y motivo |
|---|---|
| Ventas del período / Ventas cerradas | Un único KPI monetario **Total vendido**. El conteo sigue disponible, plegado y con el nombre Cantidad de ventas; no se presenta como otro monto equivalente. |
| Venta promedio | Se conserva, con ayuda: total vendido dividido por casos vendidos. |
| Solicitudes que se vendieron | Se conserva el cálculo; etiqueta breve **Conversión**, con definición en su ayuda. |
| Ventas con pago pendiente | Se conserva el cálculo; etiqueta **Pago pendiente**. La ayuda aclara que es el monto completo de ventas no pagadas totalmente, no el saldo después de los abonos. |
| Minigráficos y explicaciones bajo cada KPI | Se retiran: duplicaban la evolución y las definiciones que ya tienen ayuda. Solo Total vendido muestra variación; sin base anterior, texto neutro. |
| Detalle con los cuatro valores de las tarjetas | Se retiran esas filas duplicadas. El detalle conserva solo Cantidad de ventas y Solicitudes recibidas. |
| Solicitudes vs ventas | Se retira del Dashboard simplificado: repetía las series de evolución y conteos. |
| Temáticas más solicitadas y solicitudes por servicio | Se sustituyen por **Ventas por temática** y **Ventas por tipo de servicio**: ahora muestran CLP, no cantidades de solicitudes. |
| Dato destacado | Se retira para evitar repetir total, promedio o mejor período ya presentes en KPI/evolución. |
| Modalidad, Reserva vs remuneración y Solicitudes por canal | Se retiran de esta presentación para mantener los cinco gráficos solicitados. Son dimensiones diferentes, no se califican como duplicados: sus campos y datos siguen en los casos/ventas. No se borran registros ni se elimina su lógica reutilizable. |
| Solicitudes del período y descarga | Se conservan plegadas/exportables para no perder acceso al detalle. |
| Reportes por período | Se conserva como sección independiente y plegada; no se modifica su módulo. En demostración se oculta para no mezclar datos reales con ficticios y reaparece al desactivar el modo. |

## Resultado visible

Cuatro KPI: **Total vendido**, **Venta promedio**, **Conversión** y **Pago pendiente**. Cada uno tiene ayuda nativa de Streamlit. Se ubican en una fila en computador y dos por fila en celular, con tarjetas más bajas, sin minigráficos ni párrafos repetidos. La tableta conserva la adaptación existente de dos columnas. El encabezado baja de 288 a 132 px en computador y a 112 px en celular; se mantiene marca y paleta. Los controles de filtros se conservan; en celular el bloque Filtros comienza plegado para dar prioridad a los indicadores.

Los gráficos son tarjetas de dos columnas en computador y una en celular:

1. Ventas por período: evolución de montos, ceros dentro de un rango con ventas, promedio amarillo y mejor período resaltado. Conserva el desglose automático semanal/mensual del Prompt 23.
2. Ventas por temática: suma de ventas del rango atribuida a la **temática principal** de cada caso.
3. Ventas por tipo de servicio: suma de ventas por servicio.
4. Embudo de casos por estado: cantidades de solicitudes creadas en el rango, con sus estados actuales. Rechazada y otras subetapas se conservan fuera del embudo en badges; no desaparecen del dato.
5. Origen de las solicitudes: cantidades por origen, en morado.

Los montos por temática/servicio se calculan sobre las ventas **ya filtradas por fecha**, no solo sobre casos nuevos del rango. Así, una venta de un caso creado antes también se incluye. Cada venta se cuenta una sola vez: no se duplica entre todas las temáticas. Si falta el caso o la clasificación, se conserva el monto bajo Sin información. Sus sumas coinciden con Total vendido. Ventas anuladas siguen excluidas.

No se cambian fórmulas de los KPI, filtros, comparación de igual duración, zona horaria, permisos ni consultas a Supabase. El cambio monetario de los dos gráficos es explícito: los anteriores medían demanda, los nuevos miden ventas. Azul para ventas, morado para solicitudes y amarillo para promedio/resaltes. Sin datos, cada tarjeta muestra un ícono y un mensaje; no dibuja ejes vacíos ni una curva plana de ceros.

## Ver datos de prueba

1. Ingresar como Administración y abrir Dashboard.
2. Activar **Ver datos de prueba**.
3. Aparece un aviso visible: **Datos de prueba ficticios. No son ventas reales y no se guardan en Supabase.**
4. Se generan en memoria 12 solicitudes y 8 ventas para el rango elegido, más 6 solicitudes/4 ventas del rango anterior. Los filtros y flechas funcionan sobre el ejemplo sin tocar datos reales.
5. Apagar el interruptor para volver a la lectura real y a Reportes por período.

El ejemplo es determinista: Total vendido **$4.080.000**, Venta promedio **$510.000**, Conversión **66,7%** y Pago pendiente **$2.040.000**. Hay distintos estados, temáticas, servicios, orígenes y pagos, para mostrar los cinco gráficos. Cambiar el rango redistribuye las fechas del ejemplo; no representa una serie histórica real. El CSV de demostración se llama **DEMO-resumen-por-periodo.csv** para distinguirlo. El interruptor empieza apagado y solo está disponible para Administración. No se crea ningún caso, cliente, venta, correo o cuenta en Supabase.

## Archivos completos

- `paginas/dashboard.py`: cuatro KPI, cinco gráficos, lectura real/demostración separadas y detalle sin duplicaciones.
- `servicios/dashboard.py`: agregación monetaria por temática principal/servicio con conservación del total.
- `servicios/dashboard_demo.py`: datos ficticios generados en memoria para los rangos actual y anterior.
- `utils/graficos_dashboard.py`: barras monetarias azules con CLP y porcentajes, sin hover de conteos.
- `utils/estilos.py`: encabezado compacto y grid de KPI acotados al Dashboard; otras páginas conservan sus estilos.
- `tests/test_dashboard_simple24.py`: pruebas nuevas de demostración, distribución, retorno a datos reales, estructura y vacíos.
- `tests/test_dashboard_simplificado.py`, `tests/test_app.py`: contrato visual actualizado con los mismos valores históricos.
- `tests/generar_preview_dashboard.py`: vista HTML actualizada con los cinco gráficos y datos ficticios.
- `README.md`, esta guía: entrega y uso.

Sin dependencias nuevas y **sin SQL que ejecutar**. No se insertan datos de prueba en producción.

## Pruebas

Resultado: **251 pruebas aprobadas** en la suite completa, incluidas las cuatro nuevas de esta entrega. Se usan datos ficticios, funciones puras y AppTest; no se envían correos ni se insertan filas de prueba en producción.

| Prueba | Resultado esperado |
|---|---|
| Datos históricos de prueba anteriores | Mismos total, promedio, conversión y pago pendiente; etiquetas nuevas y cinco gráficos. |
| Activar demostración | Cuatro KPI con ayuda y cinco gráficos; aviso ficticio. No se consulta de nuevo ni se escribe el repositorio real para generar el ejemplo. |
| Desactivar demostración | Se recuperan datos reales y panel de reportes; las filas reales no cambian. |
| Ventas por temática y servicio | Cada suma coincide con Total vendido; no se cuentan solicitudes ni se duplican temáticas. |
| Caso antiguo con venta actual | Se clasifica y cuenta la venta aunque la creación del caso quede fuera del rango. |
| Venta anulada / caso sin clasificación | Anulada excluida / monto conservado bajo Sin información. |
| Sin datos | Cuatro KPI con valores vacíos/ceros apropiados y mensajes en las tarjetas; ningún gráfico vacío. |
| Filtros y períodos | Se mantienen las pruebas de meses, trimestres, semestres, años, fechas inválidas y comparación del Prompt 23. |
| Celular | Reglas CSS de dos KPI por fila y gráficos apilados, conservando controles táctiles. AppTest valida estructura, no sustituye la inspección visual en un teléfono físico. |

```powershell
python -m unittest discover -s tests -p test_dashboard_simple24.py -v
python -m unittest discover -s tests
python tests/generar_preview_dashboard.py
```

La vista previa se guarda en `output/dashboard-vista-ficticia.html`, contiene solo datos ficticios y los gráficos interactivos. Es una referencia exportable; la app real usa componentes Streamlit y sus permisos habituales.
