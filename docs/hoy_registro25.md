# Hoy y Registro sin repeticiones — Prompt 25

## Bloques eliminados, sustituidos o limitados

| Bloque | Cambio y motivo |
|---|---|
| Contadores del encabezado de Hoy | Se desactivan explícitamente; repetían las tarjetas. El encabezado conserva saludo y fecha. |
| Tarjeta Acciones pendientes | Se retira: sumaba las categorías, incluyendo casos con más de una tarea. No aportaba una acción distinta ni un total de casos únicos. La suma queda solo para decidir si mostrar Todo al día, sin imprimirse. |
| KPI y minigráficos anteriores de Hoy | Se sustituyen por tres tarjetas accionables completas: Por cotizar, Pagos por registrar y Cotizaciones sin respuesta. El número aparece una vez en cada tarjeta. |
| Conteos en los títulos de las listas | Se retiran para no repetir las cifras de las tarjetas. Los títulos identifican la acción y las filas mantienen los datos útiles de cada caso. |
| Solicitudes sin cotizar | Sigue únicamente como lista de trabajo en Hoy, ordenada por antigüedad y limitada a cinco. Cada fila conserva Cotizar; Ver todas lleva al registro completo filtrado. |
| Todo al día | Se retira el aviso de éxito duplicado; se conserva una sola tarjeta ilustrada con el mensaje. |
| Comparte tu formulario | Se compacta a título, Copiar enlace e Ir a Compartir, reutilizando la URL del snapshot existente. Si falta una URL válida, Copiar enlace queda desactivado con una indicación breve. |
| Nuevas solicitudes en Casos y cotizaciones | Ya no existía un bloque o KPI de ese tipo en el código actual; se verificó y no se añadió otro. El registro conserva todos los casos, sin volver a convertirse en agenda. |
| Leyenda estática del listado de casos | Se sustituye por chips nativos de estado clicables, sincronizados con el selector. Los badges de estado de la tabla y del detalle se conservan. |

No se borran casos, datos ni funciones de cotización, pagos, documentos o seguimiento. Las listas de Faltan datos, pagos, casos que se pueden cerrar y correos por revisar siguen en Hoy, con sus acciones explícitas. Los diálogos, cierre/Deshacer y sugerencias posteriores al cierre también se conservan.

## Qué abre cada tarjeta

Toda la superficie de cada tarjeta es un botón nativo, operable con teclado y foco visible. Al pulsarlo se abre **Casos y cotizaciones → Registro de casos**, se limpia la búsqueda anterior y cualquier detalle abierto, y se aplica el filtro correspondiente.

| Tarjeta/filtro | Regla compartida por Hoy y Registro |
|---|---|
| Por cotizar | Casos abiertos en Solicitud o En revisión, sin ninguna cotización emitida. Incluye ambos estados, no solo Solicitud. |
| Pagos por registrar | Casos abiertos con venta no anulada y pago Pendiente o Abono recibido. No equivale a un único estado del caso. |
| Cotizaciones sin respuesta | Caso Cotizada sin venta, cuya última cotización supera el plazo configurado y que no está en pausa por un seguimiento reciente. |

El plazo de respuesta se interpreta **estrictamente como más de** los días configurados, conforme a este prompt. Por defecto son cinco: una cotización de exactamente cinco días no entra; a los seis días sí. Se mantiene la configuración existente y la pausa después de un seguimiento. La interfaz explica el umbral actual en la ayuda de la tarjeta, sin añadir un módulo de ajustes.

Los tres filtros de pendientes aparecen además entre las opciones del selector del registro, junto a los estados normales. Los chips representan los estados normales y Todos los estados. Al elegir un grupo de pendientes no se marca un estado único que pueda ser engañoso; al elegir un chip, se vuelve al filtrado por estado. El buscador se combina con ambos tipos de filtro y se conserva al cambiar el estado dentro del registro.

Las reglas viven en `servicios/hoy.py`: `casos_por_accion` reutiliza `pendientes`, no una segunda versión de los cálculos. Cuando se aplica un filtro de pendientes, Registro utiliza el snapshot completo de Hoy, que ya incluye casos, cotizaciones, ventas y eventos. No hace una consulta adicional por caso. Al usar un estado normal, conserva su lectura habitual de casos. Se mantienen caché, recuperación ante fallos y temporizadores existentes; consultar no cambia datos ni envía mensajes.

## Archivos completos

| Archivo | Cambio |
|---|---|
| `paginas/hoy.py` | Encabezado sin contadores, tres accesos filtrados, límite de cinco solicitudes, Ver todas y mensaje vacío único. |
| `servicios/hoy.py` | Filtros de acciones reutilizables; umbral estrictamente mayor que el plazo configurado. |
| `paginas/gestion.py` | Filtros de pendientes exactos, chips de estado sincronizados y registro completo sin KPI duplicados. |
| `paginas/compartir.py` | Tarjeta compacta en Hoy y Copiar enlace desactivado si falta URL válida. La página Compartir mantiene sus herramientas. |
| `utils/componentes.py` | Componente reutilizable de tarjeta de acción con botón nativo. |
| `utils/estilos.py` | Estilos centralizados de tarjetas, compartir compacto, enlace Ver todas y altura táctil de chips. |
| `tests/test_hoy.py` | Actualiza la expectativa del mensaje vacío único; conserva las pruebas anteriores de acciones. |
| `tests/test_hoy_registro25.py` | Pruebas nuevas de tarjetas, navegación, grupos exactos, chips, límites, umbral y enlace público. |
| `README.md`, esta guía | Entrega y uso. |

**Sin migraciones SQL, dependencias ni secretos nuevos.** No cambia permisos: Hoy y Registro siguen verificando Administración en el servidor, y la navegación conserva la protección de clientes y visitantes.

## Pruebas y qué debería verse

Las pruebas usan datos ficticios, AppTest y repositorios simulados; no envían correos ni modifican la base publicada. No se realizaron pruebas visuales en dispositivos físicos.

Resultado de la entrega: **257 pruebas aprobadas** en la suite completa; las seis pruebas nuevas de esta corrección también pasan en su comprobación final específica.

| Prueba | Resultado esperado |
|---|---|
| Abrir Hoy con pendientes | Tres tarjetas con números una sola vez, sin chips numéricos en el encabezado y sin Acciones pendientes. |
| Pulsar cada tarjeta | Abre Registro, con su filtro aplicado, sin búsqueda o detalle anterior que oculte los resultados. Solo aparecen los casos que integraban ese grupo de tareas. |
| Ocho solicitudes sin cotizar | Hoy muestra cinco, empezando por la más antigua; Ver todas muestra las ocho en el registro filtrado. |
| Cotizar una fila de Hoy | Abre el caso elegido en Cotizaciones, como antes. |
| Pulsar chip Cotizada | Selector y listado cambian a Cotizada. El buscador sigue funcionando. Cambiar el selector sincroniza el chip. |
| Entrar al registro completo | Buscador, selector, chips, exportación y detalle; ningún KPI de nuevas solicitudes ni lista de tareas para cotizar. |
| Cotización emitida hace cinco/seis días | Con plazo de cinco, solo la de seis días entra en Sin respuesta. Una llamada reciente de seguimiento puede pausarla según las reglas anteriores. |
| Sin tareas | Una sola tarjeta Todo al día; los tres accesos siguen disponibles con cero. |
| Copiar enlace | Reutiliza la URL guardada/detectada válida, con `?vista=solicitud&canal=directo`; no consulta clientes ni guarda datos. |
| Cliente intenta abrir Hoy o Registro | Se mantiene la redirección de permisos existente. |

```powershell
python -m unittest discover -s tests -p test_hoy_registro25.py -v
python -m unittest discover -s tests -p test_hoy.py -v
python -m unittest discover -s tests
```
