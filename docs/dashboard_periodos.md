# Dashboard: filtros, períodos e indicadores

Entrega del 22/10/2026. Archivos completos en `paginas/dashboard.py`, `servicios/dashboard.py`, `utils/responsive.py` y `utils/estados.py`. No hay dependencias nuevas ni cambios SQL por este dashboard.

## Revisión del proyecto

Los archivos dashboard.py indicados en el pedido no existían. La interfaz estaba en `paginas/gestion.py` y los cálculos en `mente_futuro/domain.py`. El nuevo servicio reutiliza `dashboard_data`: conserva ventas por `mf_ventas.fecha_venta`, exclusión de ventas anuladas, solicitudes por `mf_casos.created_at` en America/Santiago, conversión de la cohorte y pagos pendientes. Se mantuvo el adaptador `paginas.gestion.dashboard_page` para no romper importaciones.

Se revisaron las migraciones versionadas, que definen `fecha_venta` como DATE y `created_at` como TIMESTAMPTZ. No se contó con conexión administrativa para volver a inspeccionar el catálogo remoto. El dashboard continúa consultando las tablas mediante el repositorio autenticado y exige rol admin al inicio.

## Filtros

La fila superior contiene Agrupar por, Rango rápido, Desde, Hasta, Servicio, Temática y Limpiar. No está en la barra lateral. El valor inicial es Mensual y Últimos 6 meses. Limpiar restablece esos valores y ambos filtros a Todos/Todas.

Los rangos rápidos incluyen el período actual parcial:

- Últimas 8 semanas: lunes de hace siete semanas hasta hoy.
- Últimos 6 meses: primer día del mes de hace cinco meses hasta hoy.
- Este año: 1 de enero hasta hoy.
- Año anterior: 1 de enero a 31 de diciembre del año anterior.
- Personalizado: las fechas seleccionadas por la usuaria.

Cambiar Desde o Hasta activa Personalizado. Si las fechas están invertidas, se ordenan. Para permitir una comparación visible se exigen al menos 4 semanas o 2 períodos de cualquier otra agrupación. Son períodos de calendario visibles, incluidos los parciales, no una duración mínima en días. Si faltan períodos, se amplía Desde hacia atrás, se mantiene Hasta, aparece un aviso y el rango pasa a Personalizado. Por ejemplo, Anual con Este año se amplía al año anterior para mostrar dos años.

En pantallas menores de 768 px, los controles pasan a un expander Filtros y se muestran chips con agrupación, fechas, servicio y temática. Un componente nativo de Streamlit comunica únicamente si el ancho está por debajo del límite, sin librerías externas. Los valores de filtros se conservan al cambiar de ancho.

## Qué aparece en cada agrupación

| Agrupación | Cada barra representa | Ejemplo de etiqueta | Mínimo visible |
|---|---|---|---|
| Semanal | Semana ISO de lunes a domingo | Sem 42 · 12–18 oct | 4 semanas |
| Mensual | Mes calendario | oct 2026 | 2 meses |
| Trimestral | Ene–mar, abr–jun, jul–sep u oct–dic | T4 · 2026 | 2 trimestres |
| Semestral | Ene–jun o jul–dic | S2 · 2026 | 2 semestres |
| Anual | Año calendario | 2026 | 2 años |

No existe agrupación diaria. Las barras de períodos parcialmente incluidos suman solo movimientos dentro de Desde/Hasta. Las fechas completas de inicio y fin del período aparecen al pasar el mouse. Los ejes usan una clave interna de fecha para que etiquetas de semanas de distintos años no se mezclen.

`agrupar_por_periodo(df, agrupacion, desde=None, hasta=None)` devuelve inicio, fin, periodo, total y cantidad. Siempre devuelve todos los períodos, incluidos ceros. Para usar exactamente dos argumentos se pueden establecer `df.attrs['desde']` y `df.attrs['hasta']`; un DataFrame vacío necesita esos límites. Para solicitudes detecta `created_at` y aplica la hora chilena; para ventas usa `fecha_venta` y elimina anuladas.

## Indicadores y comparación

- Ventas del período: monto de ventas confirmadas, con impuestos definidos en cada cotización.
- Ventas cerradas: cantidad de ventas, no cantidad de solicitudes creadas.
- Nuevas solicitudes: casos creados en las fechas seleccionadas.
- Venta promedio: total vendido dividido por casos vendidos. Sin ventas muestra —.
- Solicitudes que se vendieron: porcentaje de solicitudes creadas en el rango que tienen venta no anulada hasta Hasta. Incluye la frase De cada 10 solicitudes, X terminaron en venta. Sin solicitudes muestra —.
- Ventas con pago pendiente: valor completo de ventas que no están totalmente pagadas, incluidas las que tienen abono. No es el saldo exacto por cobrar.

Cada indicador tiene variación relativa `(actual-anterior)/anterior × 100`, con la flecha de Streamlit. Una base cero con actividad actual se marca Sin base anterior, nunca un 100% inventado; cero contra cero muestra 0%. Si el indicador no existe por falta de ventas/solicitudes, no hay variación.

El bloque anterior tiene la misma cantidad de períodos de calendario que toca el rango actual y termina antes del primer período actual. Se muestran sus fechas. Ejemplo: julio–diciembre en Mensual o Trimestral compara con enero–junio; en Anual, cualquier rango dentro de 2026 compara con 2025. El bloque anterior es completo y el actual puede ser parcial: la ayuda junto a las fechas lo aclara. Servicio y Temática se aplican igual a ambos bloques.

La clasificación por servicio y temática utiliza el caso actual, como antes. Los estados muestran el estado actual, no una reconstrucción histórica.

## Estados y errores de gráficos

Las etiquetas compartidas en todas las vistas son Cotizada, Aceptada, En seguimiento, Cerrada y Rechazada. Se conservan los valores antiguos en PostgreSQL y la lógica de cotizaciones/ventas: no se cambian restricciones ni registros para corregir un texto. El estado adicional En revisión que ya existía también se mantiene.

Los gráficos de estados y solicitudes usan ticks enteros. Si no hay ventas no se crea un gráfico con ejes vacíos: aparece Aún no hay ventas en este rango. El resumen CSV sigue incluyendo todos los períodos con cero. Con una sola venta se muestra una barra con el monto y el resto de los períodos en cero.

## Cómo probar

Desde la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py" -v
python -m streamlit run app.py
```

Para acceder al tablero usa una cuenta de Administración. La migración de permisos de la entrega anterior sigue siendo necesaria para el rol admin; este dashboard no agrega una migración nueva. Los cambios permanecen locales hasta publicarse en GitHub/Streamlit.

Las pruebas de servicio usan casos y ventas ficticios e incluyen un rango vacío, una sola venta de $1.250.000, semanas ISO que cruzan de año, cierres de trimestre/semestre, períodos cero, zona horaria chilena, anulaciones, filtros combinados y variación contra el bloque anterior. Las pruebas AppTest recorren las cinco agrupaciones, los rangos rápidos, las fechas manuales, Limpiar, la vista móvil y los indicadores sin actividad; también conservan el recorrido administrativo completo.

Comprobación manual:

1. En un rango sin ventas: no debe aparecer Venta promedio $0 ni ejes 0.000000; debe verse — y un mensaje amigable.
2. Con una venta ficticia de $1.250.000: Ventas del período y Venta promedio deben indicar $1.250.000, Ventas cerradas 1; los demás períodos deben seguir presentes.
3. Cambia las cinco agrupaciones: se conservan los totales para las mismas fechas; cambia la distribución de barras. Si el rango necesita ampliarse, revisa el aviso y las nuevas fechas.
4. Cambia un rango rápido y luego una fecha: primero se actualizan ambas fechas; después aparece Personalizado.
5. Filtra servicio/temática y pulsa Limpiar: deben restablecerse los valores iniciales.
6. En 375 px: se ve Filtros plegado y chips; al abrirlo se pueden editar todos los controles. En escritorio deben quedar en una fila.
7. Con una solicitud Cotizada: el gráfico y el listado deben usar Cotizada y conteos 0, 1, 2… sin fracciones.

La revisión visual real del navegador a 375 px queda pendiente; AppTest verifica la estructura y la rama móvil, pero no dibuja una pantalla física.

Referencia de la detección de pantalla: [componentes nativos de Streamlit](https://docs.streamlit.io/develop/concepts/custom-components/components-v2/register).
