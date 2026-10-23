# Cotizador asistido

## Activación

La entrega está implementada en el proyecto local. **No se publicó en Streamlit Cloud ni se ejecutaron migraciones en Supabase vivo**, porque esta sesión no dispone de conexión administrativa a SQL. Los ensayos utilizan cuentas, repositorios y PostgreSQL ficticios.

1. Instala las dependencias con `python -m pip install -r requirements.txt`. Se añaden **docxtpl** y **reportlab**; python-docx llega como dependencia de docxtpl. Se requiere **Streamlit 1.65 o posterior** por las pestañas con estado. Word y PDF se generan sin Office, LibreOffice ni servicios de conversión en producción.
2. En Supabase → SQL Editor ejecuta completo `supabase/migrations/202610220003_cotizador_asistido.sql`, después de las migraciones anteriores `202610210001`, `202610220001` y `202610220002`. **No repitas las anteriores si ya están aplicadas.** El script nuevo es una transacción y no está pensado para ejecutarse dos veces.
3. Abre http://127.0.0.1:8502 e ingresa como Administración. Ve a **Casos y cotizaciones → Configuración**, completa el emisor y revisa IVA, vigencia, condiciones y reparto iniciales.
4. Abre un caso completo → Cotizaciones. Revisa el prellenado, pulsa **Generar cotización** y luego **Descargar Word** o **Descargar PDF**. Ese recorrido requiere dos clics después de abrir el caso cuando la configuración y el caso ya están completos. No se presenta como un tiempo cronometrado con usuarios.

Mientras no se aplique el SQL nuevo, se conserva el cotizador anterior y su descarga HTML, con un aviso de activación. Un fallo de conexión no se interpreta como ausencia de esquema ni como un guardado exitoso.

## Qué existía y qué se añadió

Se revisaron `app.py`, las páginas, el repositorio autenticado, los componentes y las migraciones. El proyecto real tenía `mf_casos`, `mf_cotizaciones`, `mf_ventas` y `mf_tarifas`, un editor básico, cotización HTML, registro de venta y anulación confirmada. No tenía docxtpl, PDF descargable directo, plantillas de programa, configuración de emisor ni historial/envíos. Se incorporaron esas piezas sin retirar el editor manual, descuentos, IVA, condiciones, historial HTML ni formularios de venta anteriores.

Tablas nuevas, todas con RLS y acceso exclusivo a Administración:

- `mf_configuracion`: emisor, vigencia, IVA por defecto, condiciones y reparto.
- `mf_plantillas_programa`: tipo de servicio, temática opcional, cinco secciones y disponibilidad.
- `mf_borradores_cotizacion`: un borrador por caso, versión de concurrencia y autor de la edición.
- `mf_eventos_caso`: decisiones, reversión y registro de envíos, separados de las versiones de cotización.
- `mf_envios_cotizacion`: reserva de un intento, canal, destinatario y estado para evitar reenvíos automáticos.

Se añaden temática opcional a tarifas; documento, motivo de descuento y versión de cotización a `mf_cotizaciones`; cotización aceptada y motivo de rechazo al caso; y porcentajes, montos de reparto y número de documento a ventas. Los registros históricos se conservan: no se inventa un reparto para ventas antiguas. Su descarga HTML sigue disponible. Las versiones antiguas no tenían numeración propia; la columna nueva parte de 1 en ellas y las emisiones nuevas siguen la secuencia por caso.

Los valores internos de estados se conservan: Cotizado se presenta como Cotizada; Vendido como Aceptada; En ejecución como En seguimiento; Cancelado como Rechazada. No se cambian permisos de Cliente ni se le añaden páginas privadas.

## Prellenado y edición

La tarifa Recomendada prioriza la misma temática, luego referencias generales y finalmente cercanía proporcional de horas/personas dentro del mismo tipo de servicio. **No multiplica ni extrapola el precio**. Si horas o participantes difieren, conserva la advertencia para revisar monto y alcance. El tarifario permite indicar temática de referencia opcional sin retirar sus campos anteriores.

La plantilla se elige por servicio y temática, con respaldo en una plantilla general de ese servicio. Si no hay plantillas guardadas, prepara textos iniciales editables a partir del caso y de la tarifa; no afirma que exista un programa aprobado. Dirigido a se precarga desde el cliente/personas del caso. Se sustituyen `{horas}`, `{participantes}`, `{cliente}`, `{servicio}`, `{tematica}` y `{modalidad}` sin ejecutar texto como código. Si falta un objetivo o una sección habilitada, pide completarlo.

El editor contiene Programa, Importes, Condiciones y Vista previa. Todos los textos siguen editables; cada sección puede incluirse o excluirse sin borrar su contenido. Restablecer al texto de la plantilla actúa solo sobre esa sección. Cambiar una selección de plantilla requiere pulsar Cargar textos, para no pisar la edición por navegar entre opciones. Elegir otra tarifa actualiza monto, detalle e IVA conocido de esa referencia, conservando el resto.

El botón amarillo Generar cotización queda fijo mientras se usa el editor. Se conserva Emitir y guardar cotización como alternativa manual. El banner muestra los datos que faltan y ofrece ir a la pestaña correspondiente, a Datos del caso o a Configuración. Un descuento mayor que cero requiere motivo. Los datos incompletos no producen una versión definitiva.

Las condiciones iniciales y el reparto 50/50 son valores de partida editables, **no información atribuida a la empresa**. Antes de generar hay que completar sus nueve datos reales. IVA se determina por la tarifa o por la configuración que Administración revisa y guarda.

## Borradores y versiones

Al editar un control se guarda el borrador en Supabase. Los textos se capturan además tras una pausa de aproximadamente 700 ms mientras se escribe. Se muestra Borrador guardado ✓ solamente después de confirmar el guardado. Hay respaldo de texto en sessionStorage por usuario/caso y limpieza al cerrar sesión, incluso desde otra página.

Si falla la conexión, conserva la edición de la sesión y reintenta. Un conflicto de versión de borrador no sobrescribe automáticamente otra sesión: ofrece Guardar mi borrador sobre el actual. El respaldo del navegador no contiene tokens ni contraseñas, pero sí texto del caso; usa un equipo de confianza y cierra sesión. No es un modo offline completo: selectores/números/fechas deben haber llegado al servidor, y el almacenamiento del navegador puede no estar disponible.

Un borrador no altera el estado del caso ni cuenta como cotización. **Generar** crea una fila en `mf_cotizaciones` con el programa, interruptores, emisor e importes copiados en esa versión y pasa el caso a Cotizada. La operación usa un UUID estable: reintentar una respuesta perdida no duplica la versión. Si se editaron datos después de un resultado incierto, se informa al recuperar la versión anterior y se conserva la nueva edición en el borrador.

Word usa docxtpl con escape de XML; PDF usa ReportLab. Ambos parten del mismo snapshot, respetan las secciones habilitadas y usan montos y fechas de Chile. **Los binarios se regeneran desde la versión guardada; no se implementó un bucket de archivos ni se promete identidad de bytes entre futuras versiones del motor de documentos.** El contenido de emisor/programa/configuración sí queda fijado en la cotización. El aspecto paginado de Word puede variar entre visores. La descarga HTML anterior se mantiene como alternativa.

Después de generar aparece un aviso con las dos descargas y Enviar al cliente. Si no hay una plantilla con los textos actuales, Guardar como plantilla la crea sin interrumpir las descargas ni modificar el documento emitido.

## Correo y WhatsApp

Configura únicamente en `.streamlit/secrets.toml` o Secrets de Community Cloud, sin subir credenciales al repositorio:

```toml
[smtp]
host = "smtp.tu-proveedor.cl"
puerto = 587
usuario = "tu-cuenta"
password = "TU_CLAVE_SMTP"
remitente = "contacto@tu-dominio.cl"
ssl = false
```

Con `ssl = false` se exige STARTTLS; para TLS implícito se usa `ssl = true` y el puerto del proveedor, habitualmente 465. El proveedor puede exigir una contraseña de aplicación y límites propios de envío. La app no configura DNS ni valida la llegada al buzón.

Enviar al cliente abre una vista previa con destinatario, asunto, saludo al contacto, resumen y adjuntos elegibles Word/PDF. Se pueden editar. **Abrir la ventana no envía nada.** Debe marcarse Confirmo enviar este correo y pulsar Enviar. No se hicieron envíos reales durante el desarrollo.

Antes de contactar SMTP se reserva un intento en la base de datos. Una respuesta perdida o un intento incierto no se reenvía automáticamente. Si SMTP acepta pero falla el registro, ofrece Reintentar solo registro del correo. Preparar otro intento de correo genera otro identificador y requiere volver a confirmar; revisa antes el correo anterior para evitar duplicados. La aceptación SMTP no garantiza entrega, y SMTP no ofrece una transacción atómica con PostgreSQL.

WhatsApp permite copiar el texto y abrir un enlace wa.me al teléfono normalizado. No adjunta documentos ni manda mensajes automáticamente: descarga el archivo y adjúntalo en WhatsApp. Solo después de marcar Ya envié esta cotización por WhatsApp y pulsar Registrar envío se añade la fecha al historial. Copiar o abrir el enlace por sí solos no registran un envío ficticio.

En Historial del caso y envíos aparece Cotización enviada el dd/mm/aaaa por correo/WhatsApp. El texto distingue registro de envío de prueba de entrega efectiva.

## Aceptar, vender, rechazar y deshacer

Marcar como aceptada abre un único diálogo con monto de la cotización, fecha de hoy, reparto de configuración, pago y número de documento opcional. Aceptar y registrar venta valida suma de 100%, vigencia y concurrencia; crea la venta y deja el caso En seguimiento de forma atómica. El importe de venta puede editarse sin alterar la cotización emitida. Los CLP de reserva se redondean y remuneración recibe el resto, de modo que ambos sumen exactamente la venta.

Solo marcar aceptada deja el caso en Aceptada sin crear venta. Después puede registrarse con el diálogo nuevo o con el formulario manual anterior, que conserva su comportamiento. No se cuentan aceptaciones sin venta como ingresos.

Deshacer dura diez segundos, comprobados por PostgreSQL. Revierte la decisión y, si corresponde, solo la venta recién creada. Conserva la cotización y marca el evento como deshecho. Si pasó el plazo, cambió el caso o se modificó la venta, no sobrescribe esos cambios. La anulación ordinaria sigue requiriendo su confirmación.

Marcar como rechazada permite motivo opcional Precio, Fecha, Eligió otra empresa u Otro y detalle libre. Guarda el motivo para análisis posterior; no se añadió un nuevo gráfico de rechazo. Los gráficos y cálculos anteriores del Dashboard se conservan. Las ventas históricas sin reparto siguen sin tener un reparto inventado.

## Pruebas y resultados esperados

| Paso | Acción con datos ficticios | Qué debe verse |
| --- | --- | --- |
| Preparación | Completar Configuración y abrir un caso completo. | Lista 9/9 y banner Prellenado automáticamente. Revisa y genera; tarifa Recomendada y textos editables. |
| Cotizar en un clic | Pulsar Generar cotización. | Una versión emitida, caso Cotizada y aviso de descargas. Pulsar varias veces por un reintento no duplica la misma operación. |
| Descargar | Elegir Word o PDF. | Archivo real del formato elegido, mismo código, programa, descuento, IVA y total; la descarga HTML sigue disponible. |
| Editar y volver | Editar Objetivos, esperar Borrador guardado, salir y volver al caso o iniciar otra sesión. | Recupera el borrador desde Supabase sin crear una versión adicional. |
| Enviar | Abrir Enviar al cliente y revisar correo/adjuntos. | Antes de confirmar no sale nada. Con SMTP de pruebas y confirmación explícita se acepta el mensaje y registra el canal/fecha. |
| Alternativa WhatsApp | Copiar texto, abrir wa.me y luego confirmar manualmente que se envió. | Texto listo; el historial se actualiza únicamente tras Registrar envío. |
| Aceptar y vender | Abrir el diálogo, cambiar el reparto y pulsar Aceptar y registrar venta. | Con suma incorrecta no crea venta; con 100% crea una sola venta y pasa a En seguimiento. |
| Deshacer | Pulsar antes de diez segundos. | Elimina esa venta reciente y vuelve al estado anterior, conservando la cotización. Tras el plazo o un cambio posterior, informa que no pudo deshacer. |
| Solo aceptar | Elegir Solo marcar aceptada. | Aceptada, sin ingreso ni venta hasta registrarla posteriormente. |
| Rechazar | Seleccionar un motivo opcional y confirmar rechazo. | Rechazada con el motivo almacenado. |
| Cliente | Ingresar con cuenta Cliente e intentar URL privada. | Solo Nueva solicitud. Sin configuración, borradores de cotizaciones, descargas privadas ni decisiones. |

Pruebas automatizadas:

```powershell
python -m pip install -r requirements-dev.txt
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
node tests/test_cotizador.mjs
node tests/test_cotizacion_borrador.mjs
```

Las pruebas SQL usan la dependencia de desarrollo PGlite ya existente en `tmp/db-test/node_modules`. En una copia limpia: `npm install --prefix tmp/db-test @electric-sql/pglite`. No hace falta para ejecutar la app.

Se aprobaron **93 pruebas Python** y las pruebas JavaScript/SQL de borrador, idempotencia, permisos, reparto, plazo y concurrencia de Deshacer. SMTP se simuló: no se mandaron correos a destinatarios reales. Se generó una cotización ficticia de dos páginas en cada formato y se inspeccionaron sus cuatro páginas renderizadas. El renderizador empaquetado produjo PDF con LibreOffice aislado; ante la ausencia de Poppler, se rasterizó ese PDF con MuPDF. Estas herramientas son de QA, no dependencias del despliegue. No se presenta AppTest como revisión física de la interfaz a 375 px.

Para regenerar el ejemplo de revisión: `python -m tests.datos_cotizacion_ficticios` si el entorno admite ese módulo, o `$env:PYTHONPATH=(Get-Location).Path; python tests/datos_cotizacion_ficticios.py`. Produce archivos ficticios en `output/cotizador/`.

La entrega completa está en `output/mente-futuro-cotizador-asistido.zip`, con todos los archivos de código, SQL, dependencias y pruebas; sin secretos, binarios de herramientas ni datos reales.

Referencias técnicas: [docxtpl y escape de contenido](https://docxtpl.readthedocs.io/en/stable/), [smtplib y envío con TLS](https://docs.python.org/3.12/library/smtplib.html). Los parámetros comerciales y tributarios los configura Administración; los ejemplos no constituyen tarifas ni datos reales de la consultora.
