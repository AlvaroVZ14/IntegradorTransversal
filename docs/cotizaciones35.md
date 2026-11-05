# Prompt 35: casos y cotizaciones

## Diagnóstico previo

Se revisaron `paginas/gestion.py`, `cotizador.py`, `acciones_cotizacion.py`,
`listas_propuesta.py`, los servicios de borrador/documentos/pago/repositorio,
los estilos de `ui/tema.py` y las migraciones existentes.
Los prompts 30 y 41 están implementados: sistema de diseño y catálogo único
de estados. Se reutilizan; los nombres almacenados de los estados no cambian.

Ya existían: prellenado de tarifa y programa, cinco secciones de texto,
interruptores, descuento, IVA, datos de pago por versión, borrador en
`mf_borradores_cotizacion`, detección de conflicto entre sesiones, correo con
confirmación, WhatsApp, aceptación con venta y Deshacer por 10 segundos,
caducidad y seguimiento en Hoy. No se reemplazaron esos mecanismos.

Fricciones detectadas por código: tres pestañas largas; el registro completo
se repetía antes del detalle; PDF del borrador generado aun con el expander
cerrado; descargas preparadas al renderizar el historial; versiones sin
comparación; filtros limitados; listado sin paginar; envío disperso.

### Clics antes y después

Son mínimos del recorrido programado, **no mediciones de una persona**.
No incluyen escribir, seleccionar cada campo ni descargar/adjuntar archivos.
No se dispone del navegador automatizado: el host devuelve
`The browser access host is unavailable`. Los scrolls y el objetivo de dos
minutos quedan pendientes de medición real.

| Tramo y punto de partida | Antes | Ahora | Scrolls antes/después |
|---|---:|---:|---|
| Registro → detalle → Cotizaciones | 2 selecciones | 2: abrir acciones rápidas y Cotizar; Ver abre detalle | Por medir |
| Caso completo, tarifa/programa sugeridos → generar | 1 clic (ya era posible) | 1 clic directo; atajo guiado: abrir Atajos, Cotización rápida, Generar = 3 | Por medir |
| Revisar contenido personalizado | 3 pestañas sin secuencia | 5 pasos, Atrás/Siguiente y acceso directo a cada paso | Por medir |
| Versión → redacción de correo | 1 acceso directo o Enviar al cliente | 2: Enviar → Redactar correo, o Enviar correo desde la app; confirmación SMTP conservada | Por medir |
| Versión → texto WhatsApp | Expander + abrir/copiar | Enviar + abrir/copiar; registro manual posterior conservado | Por medir |
| Versión → aceptación y venta con valores listos | 2 botones | 2 botones; importe precargado y Deshacer conservados | Por medir |
| Versión → rechazo con motivo | 3 acciones como mínimo | 3 acciones como mínimo, incorpora Sin presupuesto | Por medir |

No se promete reducir todos los clics: el menú de envío añade orden, y el
asistente añade orientación. No se retiró la emisión directa de un clic.

Prioridad por impacto: (1) no generar documentos al editar, (2) recuperar
borrador, (3) detalle sin lista previa y con siguiente paso, (4) asistente y
atajos, (5) filtros/paginación, (6) versiones y envío unificados.
No se añadieron automatismos de envío ni cambios de estado por navegar.

## Cambios

- Registro: buscador y chips existentes, filtros plegables de temática,
  modalidad, origen, canal y fechas inclusivas; orden por fecha/antigüedad
  o monto; 20 casos por página; CSV de todo el resultado filtrado.
  Monto = venta no anulada o, en su ausencia, última cotización; casos sin
  importe al final. Una lectura agrupada reutiliza el snapshot de Hoy.
  Acciones rápidas por caso dentro de un expander: Ver, Cotizar y Contactar.
  Contactar prepara texto y no registra falsamente un envío.
- Detalle: cabecera adherente bajo la barra superior; cliente, código,
  estado, acción contextual, siguiente paso y cinco hitos horizontales.
  Cambiar de caso conserva el selector anterior en un expander compacto,
  y Volver al listado conserva filtros y número de página.
  Las fechas solo aparecen si se pueden demostrar con registros existentes;
  no se inventan fechas de estados intermedios. Pestañas con símbolos y
  marcas de pendientes. La lista queda accesible con Volver al listado.
- Editor: Programa / Detalle / Importes / Condiciones y pago / Revisar y
  generar; progreso, avance con validación por paso y vuelta sin perder datos.
  Se conservan todos los campos e interruptores anteriores.
- Atajos: rápida usa la tarifa/programa ya recomendados y lleva a revisión;
  biblioteca lleva a Programa; duplicar copia una versión sin modificarla,
  conservando las fechas vigentes del borrador actual.
- Borrador: guardado existente con versión y reintento, indicador en minutos.
  Fragmento del editor evita recalcular toda la página al editar. Catálogos
  y versiones para duplicar se conservan 60 segundos por sesión, usuario y
  revisión. El total visible se recalcula al cambiar importes, descuento o IVA.
- Resumen lateral con contenido ampliable, debajo en celular mediante las
  columnas responsive existentes. No es una reproducción del PDF: permite
  revisar los datos sin ejecutar generadores. Total fijo al pie.
- Versiones: expanders compactos, valores/condiciones plegables, diferencia
  de monto y alcance frente a la versión anterior. Estado, vigencia y fecha
  de envío real reutilizan el catálogo e historial existentes.
- Enviar reúne correo confirmado, WhatsApp, copia y registro posterior.
  Abrir WhatsApp no significa que el mensaje salió.
- Nuevos motivos de rechazo: Precio, Fecha, Eligió a otro proveedor, Sin
  presupuesto y Otro; nota opcional. Se conservan los motivos históricos.

No se modificaron generadores, plantillas de documentos, archivos de pago,
roles, políticas ni tablas. Sin nuevas dependencias de producción.
El CSS nuevo vive solo en `ui/tema.py` y se carga solo en Casos.

### Generación y versiones anteriores

El botón Generar verifica los dos formatos y emite la versión como antes;
prepara además su caché de descarga. Editar o renderizar el historial ya no
ejecuta esos generadores. Se usa la descarga diferida nativa de Streamlit
1.65. Para una versión histórica sin archivo en memoria, pulsar Descargar
reconstruye el archivo desde su snapshot una vez y lo conserva en caché.
No se eliminó la recuperación de copias faltantes en Documentos.

## Activar los motivos nuevos una vez

1. En Supabase abre **SQL Editor → New query**.
2. Copia completo `supabase/migrations/202611050002_cotizaciones_fluidas.sql`
   y pulsa **Run**. Debe salir **Success. No rows returned**.
3. En la app, rechaza una cotización ficticia con **Sin presupuesto**.
   Debes ver el caso como Rechazada y conservar el motivo en sus datos.

No se ejecutó esta migración contra el proyecto real: no hay conexión DDL
autorizada disponible en el entorno. Fue probada en PostgreSQL efímero.
No crea columnas ni borra datos. Reemplaza únicamente la función
`mf_decidir_cotizacion`, conservando guardia de administración,
idempotencia, validación de versión, venta, reparto y Deshacer.
Rollback: ejecutar `supabase/rollback/202611050002_cotizaciones_fluidas.sql`.
Los motivos ya registrados permanecen, aunque la lista vuelva a la anterior.
Mientras no se active, usar los motivos anteriores; los nuevos serán
rechazados por la base con el aviso amable existente.

Los motivos quedan en `mf_casos.motivo_rechazo` y en
`mf_eventos_caso.datos.motivo`. No se añade integración con una hoja de
cálculo ni gráfico de rechazos: los prompts 38/39 no forman parte de esta
entrega y podrán consumir estos datos.

## Pruebas y resultado esperado

Todas las pruebas usan datos ficticios, repositorio aislado o PostgreSQL
efímero. No se envían mensajes reales ni se crean casos reales.

Resultados ejecutados:

- Suite general: **283 pruebas**, inicialmente 281 correctas y 2 regresiones
  detectadas (selector para cambiar de caso y etiqueta de vista previa).
  Ambas corregidas; no se ocultan ni se eliminan las pruebas anteriores.
- Reejecución de `test_pago_cotizacion.py`: **4/4 correctas** después de corregir
  el selector. Confirma precarga, independencia y snapshots de pago intactos.
- Reejecución de `test_propuesta_documento.py`: **4/4 correctas** después de
  restaurar la etiqueta de vista previa y el enlace de redacción de correo.
- `test_cotizaciones35.py`: **5/5 correctas** tras los últimos ajustes; incluye
  tres recorridos de interfaz con varias comprobaciones, además de lógica pura.
- `test_cotiz*.py`: **15/15 correctas** en la ejecución dirigida inicial.
- `test_cotizaciones35.mjs`: **correcta**, todas las migraciones cargadas en
  PostgreSQL efímero, seis motivos incluidos los históricos, nota, permisos
  administración/cliente/visitante, reintento idempotente y rollback sin pérdidas.
- Compilación de los módulos modificados y `git diff --check`: correctos.

No se repitió la suite completa de 283 tras las dos correcciones; se
verificaron específicamente los grupos afectados y el flujo nuevo.

| Prueba | Qué debe verse |
|---|---|
| Caso nuevo completo → cotizar | Cinco pasos, prellenado y total; Generar disponible sin abrir ajustes |
| Atajos → Cotización rápida → Generar | Revisión en el paso 5; una versión, PDF y Word descargables |
| Editar y pasar de paso | El valor permanece; no se crean versiones ni PDF/Word al editar |
| Cortar conexión tras abrir editor | Lo escrito se conserva en la sesión; aviso y reintento sin borrar el borrador |
| Volver la conexión | Se confirma el guardado; otra sesión recupera la edición confirmada |
| Duplicar anterior | Copia editable, versión anterior intacta y fechas actuales conservadas |
| Enviar | Un menú; correo requiere confirmación; WhatsApp requiere registro después del envío real |
| Aceptar y registrar venta | Monto precargado, reparto validado, caso En seguimiento y Deshacer 10 s |
| Rechazar | Se conserva motivo y nota; cliente/visitante no pueden ejecutar la decisión |
| 23 casos | Primera página 20, segunda 3; CSV contiene el resultado completo |
| Filtros y fecha de borde | Se filtran según día de Chile; Desde/Hasta inclusivos y rango invertido se avisa |

Limitación del borrador: si se cierra la pestaña **sin conexión y antes de que
el servidor confirme el guardado**, no se puede garantizar recuperar las
últimas teclas; el puente existente usa almacenamiento de sesión del
navegador. No se cambió por almacenamiento permanente de datos de pago.
Con conexión, una vez confirmado el borrador se recupera desde la base.

### Revisión visual pendiente (no se presenta como aprobada)

En 375×812, 768×1024 y 1440×900: abrir Registro, detalle, cada paso,
versiones y Enviar. Comprobar ausencia de scroll horizontal de página,
tarjetas apiladas, vista previa debajo, total sin tapar botones, cabecera
sin superposición, acciones de al menos 44 px y línea de hitos con su propio
desplazamiento. Probar también teclado abierto y zoom de texto.
Medir una propuesta sencilla con cronómetro y contar desplazamientos.

## Archivos completos

`paginas/gestion.py`, `paginas/cotizador.py`,
`paginas/acciones_cotizacion.py`, `servicios/flujo_cotizaciones.py`,
`ui/tema.py`, migración y rollback indicados, pruebas
`tests/test_cotizaciones35.py` y `tests/test_cotizaciones35.mjs`, este informe.

Ejecución: `python -m unittest discover -s tests` y
`node tests/test_cotizaciones35.mjs` (usa PGlite de las herramientas locales
de pruebas; no es dependencia de la aplicación).
