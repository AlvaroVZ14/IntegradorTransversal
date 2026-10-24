# Datos en vivo

Streamlit instalado: **1.65.0**, con `st.fragment(run_every=...)` y componentes nativos v2. No hay dependencias nuevas ni claves nuevas. Se conservan gráficos, indicadores, filtros, exportaciones, acciones y permisos.

## Activación en Supabase (una vez)

1. Abre el **SQL Editor** del mismo proyecto Supabase que utiliza la app.
2. Crea una consulta nueva, pega **todo** [202610230001_lectura_en_vivo.sql](../supabase/migrations/202610230001_lectura_en_vivo.sql) y pulsa **Run**. Deben estar aplicadas las migraciones anteriores, incluida `202610220005_mantenimiento.sql`.
3. `Success. No rows returned` es el resultado esperado. Abre Dashboard: la píldora debe pasar de «Actualización pendiente» a «En vivo» en su siguiente ciclo.

Esta función SQL es una lectura `STABLE SECURITY INVOKER`. Comprueba `es_admin()`, respeta las RLS existentes y no modifica datos. Devuelve un único JSON con las tablas necesarias para cada pantalla, sin el truncamiento REST a 1.000 filas. No agrega acceso para clientes ni usuarios anónimos.

Si todavía no aplicaste el SQL, la primera carga intenta las lecturas anteriores una sola vez por pantalla/sesión para conservar acceso a la información. Los ciclos siguientes solo reintentan la nueva RPC; nunca repiten varias consultas de compatibilidad por ciclo. La píldora indica «Actualización pendiente», sin declarar que la lectura está en vivo.

Para revertir: restaura primero la versión anterior de los archivos Python/JS y ejecuta [el rollback](../supabase/rollback/202610230001_lectura_en_vivo.sql). Solo elimina la función nueva; no elimina tablas, filas ni políticas.

## Comportamiento

| Pantalla | Ciclo | Se conserva |
|---|---|---|
| Dashboard | 60 s | Filtros fuera del fragmento, pestañas, gráficos y exportación |
| Hoy | 30 s | Acciones, mensajes y sugerencias. Se pausa mientras está abierto un mensaje o las sugerencias tras cerrar un caso |
| Registro de casos | 60 s | Búsqueda y filtro de estado; el temporizador solo pertenece al listado |
| Detalle de un caso | Sin refresco periódico del listado | Todos los editores, autoguardado y Deshacer existentes |

En Casos, elige **Abrir detalle** para editar; no se abre automáticamente el primer caso. **Volver al listado** cierra el detalle y reanuda el refresco. Los accesos desde Hoy o desde una solicitud recién registrada siguen abriendo directamente su caso. Las pestañas de Casos y las del detalle recuerdan su selección.

La píldora del encabezado tiene un reloj local en JavaScript: no hace consultas ni reruns cada segundo. Respeta movimiento reducido. Si estás editando, indica la pausa. Si falla una lectura, conserva el snapshot anterior y su fecha; cambia a amarillo y reintenta en el próximo ciclo. Al volver internet, puede tardar hasta 30/60 s en confirmar la recuperación. No se muestran excepciones ni datos inventados como si fueran una lectura nueva.

Solo la primera carga muestra esqueletos/spinner. Los ciclos siguientes reemplazan los datos dentro de su fragmento, sin recrear el marco ni los filtros. Plotly conserva la interacción con `uirevision` y no repite la animación de entrada.

Una RPC por pantalla/ciclo, con caché de 60 s aislado por sesión. Las escrituras confirmadas invalidan la revisión compartida de Hoy/Casos/Dashboard; la próxima lectura de la sesión recibe los cambios inmediatamente, sin esperar al timer. Las escrituras de otras sesiones se detectan en el siguiente ciclo. Los borradores de cotización no emitidos siguen sin contar como ventas ni versiones.

Esto funciona mientras la app está abierta y conectada. No es un servicio en segundo plano, no evita que los planes gratuitos se duerman ni garantiza recepción durante una caída. «Sin conexión» puede aparecer por internet o por un fallo del servidor; no supone que se hayan perdido datos.

## Pruebas manuales con datos ficticios

| Prueba | Qué deberías ver |
|---|---|
| Deja Dashboard abierto. En otra pestaña crea una solicitud de «Empresa Ficticia Horizonte», con una temática incluida en los filtros | En hasta 60 s sube Nuevas solicitudes y se actualizan los gráficos que corresponden. Los gráficos de ventas no cambian hasta registrar una venta |
| Cambia agrupación, fechas, servicio y temática; espera dos ciclos | Los controles mantienen exactamente tu selección y los cálculos siguen aplicando esos filtros |
| Desplázate hacia los gráficos inferiores y espera | La página permanece en ese lugar; no reaparece un spinner ni se reconstruye el menú. Si cambia la altura del contenido por datos nuevos, el navegador puede ajustar el espacio disponible |
| Deja Hoy abierto y registra un caso desde otra pestaña | Aparece en los pendientes que correspondan en hasta 30 s, sin cambiar estados ni enviar mensajes |
| Deja Registro de casos abierto y crea otra solicitud en otra pestaña | El listado y sus KPI cambian en hasta 60 s; la búsqueda y estado elegido se mantienen |
| Abre un caso, elige Cotizaciones o Venta y escribe en un formulario; espera más de un minuto | Ningún temporizador del listado reconstruye el detalle. La pestaña permanece seleccionada y los editores/autoguardado siguen funcionando. Volver al listado reanuda la actualización |
| En Hoy abre Hacer seguimiento y edita el mensaje durante un minuto | El texto no se reinicia, no se envía ni se registra por sí solo. Al cerrar la ventana se reanuda el ciclo |
| Tras una lectura correcta, corta internet un minuto y vuelve a conectarlo | Los últimos datos siguen visibles. La píldora se vuelve amarilla; al confirmar la siguiente lectura vuelve a verde y avanza la fecha real |
| Guarda un cambio de caso/cotización/venta y abre Dashboard en esa misma sesión | Ves el resultado confirmado sin pulsar Actualizar. Los formularios y confirmaciones existentes se conservan |
| Entra como Cliente | Solo Nueva solicitud; no se ejecuta la nueva RPC desde esa pantalla y la base de datos rechaza invocarla con ese JWT |

## Verificación automatizada

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_en_vivo_js.mjs
node tests/test_en_vivo_sql.mjs
```

La prueba SQL usa PostgreSQL efímero con `@electric-sql/pglite` (herramienta de desarrollo ya usada en el proyecto, ubicada en `tmp/db-test/node_modules`), no Supabase real. Cubre 1.001 casos ficticios, vistas, permisos y rollback. Las pruebas Python cubren caché, una llamada por ciclo, invalidación, fallos/recuperación y recorridos de UI con filtros. El test JS verifica reloj local, offline y limpieza de listeners. Las pruebas físicas de scroll, tamaños de pantalla y red del navegador se comprueban con la matriz manual; AppTest no simula esa interacción visual.

Los archivos completos están en el repositorio y en el ZIP de esta entrega. No se incluyen secretos, datos reales ni archivos de caché.
