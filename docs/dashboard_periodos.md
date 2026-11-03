# Dashboard: filtros simplificados y períodos — Prompt 23

La presentación se simplificó posteriormente en el [Prompt 24](dashboard_simple24.md). Esta guía conserva el contrato de filtros, calendario y comparación; el conjunto actual de gráficos y el modo de datos ficticios se describen en esa entrega.

## Cambios y uso

El Dashboard tiene únicamente **Agrupar por**, **Desde**, **Hasta** y **Limpiar**, más las flechas **Anterior / Siguiente**. Se retiran Rango rápido, Servicio, Temática y los chips redundantes. Los filtros se aplican a los gráficos y los cuatro KPI; se conserva la descarga del resumen y el panel independiente de reportes.

Inicialmente se abre el mes vigente completo, según la fecha de Chile. Cambiar Agrupar por carga automáticamente el período calendario vigente de ese tipo. Con fecha de referencia 03/11/2026:

| Agrupación | Desde / Hasta | Encabezado | Evolución |
|---|---|---|---|
| Mensual | 01/11/2026 – 30/11/2026 | Mes: noviembre 2026 · fechas exactas | Semanas ISO, lunes a domingo. |
| Trimestral | 01/10/2026 – 31/12/2026 | Trimestre 4 de 2026 · fechas exactas | Octubre, noviembre y diciembre. |
| Semestral | 01/07/2026 – 31/12/2026 | Semestre 2 de 2026 · fechas exactas | Julio a diciembre. |
| Anual | 01/01/2026 – 31/12/2026 | Año 2026 · fechas exactas | Enero a diciembre. |

El período vigente incluye su fecha final calendario aunque aún no haya llegado. **Siguiente** no permite entrar a un período cuyo inicio sea futuro. Desde un trimestre anterior sí permite volver al vigente. Las fechas manuales siguen siendo editables y no se acortan automáticamente a hoy.

Editar cualquiera de las fechas cambia el encabezado a **Rango personalizado · dd/mm/aaaa – dd/mm/aaaa**. Si Desde supera Hasta, se muestra un aviso claro y se conservan los KPI, gráficos, encabezado y rango aplicado anteriores. Los controles permiten corregir la fecha sin intercambiar extremos ni ampliar el rango por su cuenta.

**Limpiar** carga de nuevo el período vigente del tipo seleccionado; por ejemplo, si se eligió Semestral, no vuelve a Mensual. Navegar con las flechas vuelve a períodos completos de calendario, tomando como referencia el período que contiene Desde. El estado aplicado está separado de los widgets: se conserva entre reruns, refrescos automáticos y cambios de página dentro de la sesión, también cuando Streamlit retira widgets de una página no visible. No se añade persistencia en el navegador para los filtros al crear una sesión nueva.

En celular, los cuatro controles se apilan dentro del bloque Filtros abierto inicialmente. Se reutilizan los estilos y botones táctiles existentes; no se cambian paleta ni permisos.

## Rango, agrupación y comparación

Todos los KPI y distribuciones usan **exactamente Desde y Hasta, ambos inclusivos**. Se mantienen los cálculos comerciales existentes: ventas por fecha de venta, solicitudes por creación convertida a hora de Chile y exclusión de ventas anuladas. Retirar Servicio/Temática como filtros significa que el tablero abarca todos los servicios y temáticas del rango, sin restricciones antiguas escondidas en la sesión.

Las series por la agrupación elegida se conservan para el resumen/exportación. Si solo hay un grupo dentro del rango, las dos gráficas de evolución y los sparklines usan una serie adicional con unidad menor: semanas para Mensual; meses para Trimestral, Semestral y Anual. Si hay varios grupos, usan la agrupación elegida. En ambos casos se completan con ceros los grupos sin movimientos. La suma de la serie y la del desglose coinciden con el total del rango.

Las semanas de borde pueden abarcar días fuera del mes, pero **solo se cuentan movimientos dentro de Desde/Hasta**. Los subtítulos indican que representan semanas o meses del rango elegido. Sin ventas se mantiene el estado vacío amable, sin ejes vacíos.

La comparación de KPI usa el bloque inmediatamente anterior de **igual número de días inclusivos**, como pide el prompt; no se redondea a grupos completos. Esto es distinto de navegar por calendario:

- 01–30 noviembre 2026 compara con **02–31 octubre 2026**: 30 días contra 30.
- 01/10–31/12/2026 compara con **01/07–30/09/2026**: 92 días contra 92.
- Un rango de un día compara con el día inmediatamente anterior.
- Al comparar un año bisiesto se conservan sus 366 días, aunque el bloque anterior no coincida exactamente con otro año calendario.

**Comparado con …** muestra siempre las fechas efectivamente usadas. Si no hay ventas en la base anterior, no aparece +0,0% verde ni flecha: aparece **Sin datos del período anterior** como texto neutro. Las solicitudes pueden seguir comparándose en el detalle si sí existían solicitudes previas, independientemente de que hubieran generado ventas. No se divide por cero ni se inventa una variación.

## Archivos completos

| Archivo | Cambio |
|---|---|
| `servicios/periodos.py` | Calendario puro, conversión a fecha de Chile, inicio/fin, navegación, comparación, validación, etiquetas y elección del desglose. |
| `servicios/dashboard.py` | Reutiliza el calendario, conserva la agregación comercial y añade el desglose; comparación de igual duración y sin porcentaje con base cero. Reexporta utilidades usadas por reportes. |
| `paginas/dashboard.py` | Cuatro controles, flechas, encabezado exacto, último rango válido, conservación de estado, sin chips ni restricciones por servicio/temática y comparación neutra. |
| `tests/test_periodos.py` | Pruebas nuevas de calendario, límites, sumas, anulaciones, ceros, zona horaria y comportamiento de interfaz. |
| `tests/test_dashboard.py` | Conserva las verificaciones de totales y actualiza el contrato de comparación; retira pruebas de controles eliminados. |
| `tests/test_dashboard_simplificado.py` | Verifica valores históricos conservados y el nuevo mensaje sin datos anteriores. |
| `tests/test_en_vivo_ui.py`, `tests/test_app.py` | Pruebas de refresco y limpieza con los controles actuales. |
| `README.md`, esta guía | Uso, entrega y pruebas. |

No se cambian tablas, RLS, consultas a Supabase, sesiones de autenticación ni otros módulos. **No hay SQL que ejecutar ni dependencias nuevas**. El panel de reportes conserva sus filtros y exportaciones propios; no queda ligado al rango del Dashboard.

## Pruebas y resultado esperado

Las pruebas usan AppTest, funciones puras y datos ficticios; no crean ventas ni casos reales. No se tomaron capturas de dispositivos físicos.

| Prueba | Qué debería verse / comprobarse |
|---|---|
| Noviembre 2026, cambiar las cuatro agrupaciones | Fechas y encabezados de la tabla inicial; Siguiente desactivado en el período vigente. |
| Anterior desde enero o primer trimestre | Diciembre o cuarto trimestre del año anterior; Siguiente vuelve al período de partida. |
| Febrero 2024 / febrero 2026 | Último día 29 / 28, respectivamente; sin fechas inexistentes. |
| 31 de marzo y 1 de abril | Pertenecen a T1 y T2, respectivamente. Lo mismo se prueba en junio/julio, septiembre/octubre y diciembre/enero. |
| Ventas el primer y último día del rango | Ambas se incluyen; las del día anterior y posterior no. Anuladas excluidas. |
| Un solo grupo / rango de varios grupos | Desglose menor / agrupación elegida; se conservan ceros y la suma coincide con los KPI. |
| Cambiar una fecha | Encabezado Rango personalizado; se agrupa según la opción elegida. |
| Desde posterior a Hasta | Aviso y último rango válido intacto; no se corrigen fechas de forma silenciosa. |
| Limpiar con Trimestral seleccionado | Toma el trimestre vigente, conserva Trimestral y elimina el error. |
| No hay ventas anteriores | Sin datos del período anterior, sin indicador verde de +0,0%. |
| Esperar refresco o ir a Hoy y volver | Se conservan agrupación, fechas y rango aplicado dentro de la sesión. |
| Pantalla móvil en AppTest | Filtros en bloque móvil; se conservan controles y acciones. La inspección visual física de anchos concretos sigue siendo manual. |

```powershell
python -m unittest discover -s tests -p test_periodos.py -v
python -m unittest discover -s tests -p test_dashboard*.py -v
python -m unittest discover -s tests
```

La entrega incluye además la ejecución de la suite de regresión de toda la aplicación. Los tests de reportes comprueban que su calendario y sus totales no cambian al reutilizar las funciones extraídas.

Resultados: **245/245** en la suite completa; comprobación final de **10/10** pruebas de períodos (incluidas dos comprobaciones adicionales), **20/20** de Dashboard y **9/9** de reportes.
