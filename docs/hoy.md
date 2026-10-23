# Hoy y próximos pasos

## Activar y abrir

1. Ejecuta completo `supabase/migrations/202610220004_hoy.sql` en SQL Editor de Supabase, **después de `202610220003_cotizador_asistido.sql` y sus requisitos**. No repitas migraciones ya aplicadas. Esta sesión no tiene conexión administrativa a SQL: la migración nueva no se ejecutó en el proyecto vivo.
2. Abre http://127.0.0.1:8502, recarga e ingresa como Administración. Hoy es el inicio predeterminado y el destino después de un nuevo login, incluso si se llegó desde una dirección antigua del Dashboard. Las demás páginas siguen accesibles.
3. En Casos y cotizaciones → Configuración → Hoy · Avisos y mensajes ajusta los plazos y las tres plantillas. No hay dependencias nuevas respecto de la entrega del cotizador.

La entrega está implementada localmente y en `output/mente-futuro-hoy.zip`. **No se publicó en Streamlit Cloud**. Si falta la migración, Hoy muestra qué activar y conserva la navegación a las otras páginas.

Cliente sigue recibiendo únicamente Nueva solicitud. Hoy no se registra como página para ese rol y también verifica Administración antes de cargar datos. Los RPC nuevos comprueban `es_admin()` en PostgreSQL. No se amplían permisos de clientes ni se añaden claves de servidor a la aplicación.

## Qué muestra cada categoría

| Tarjeta | Regla y orden | Acción explícita |
| --- | --- | --- |
| Solicitudes sin cotizar | Casos Solicitud/En revisión sin ninguna cotización, ordenados por creación real, más antiguos primero. Días de espera en Chile. | Cotizar abre ese caso en Cotizaciones, conservando el editor y sus campos. |
| Cotizaciones sin respuesta | Última cotización de un caso Cotizada sin venta activa, emitida hace cinco días o más por defecto. Se excluyen contactos recientes de esa misma cotización durante la pausa configurada. | Hacer seguimiento abre un mensaje editable. |
| Faltan datos | Contacto/cliente/correo/servicio/temática/horas/personas inválidos o faltantes; modalidad por definir; RUT/teléfono proporcionados pero inválidos. También recuerda confirmar jornada de un caso pagado y registrar/revisar una venta de un caso aceptado. | Completar abre Datos y seguimiento, o Venta cuando lo pendiente es registrar/revisar la venta. Son avisos; no se endurecen validaciones de otras páginas. |
| Ventas con pago pendiente o anticipo | Ventas no anuladas con estado Pendiente o Abono recibido. | Registrar pago abre la pestaña Venta del caso. Preparar recordatorio abre otro mensaje editable. |
| Casos que se pueden cerrar | Caso Aceptada/En seguimiento, venta activa Pagado y fecha efectiva de realización confirmada no futura. Orden por jornada realizada. | Cerrar caso guarda el cierre y ofrece Deshacer durante diez segundos. |
| Correos por revisar | Intentos de correo del cotizador con error o resultado incierto; o preparados sin confirmación después del umbral de minutos. También se muestran si su caso ya está cerrado. | Revisar envío abre el caso. Marcar revisado registra la revisión y retira ese intento en ese estado, sin reenviar ni afirmar entrega. |

Un caso puede necesitar más de una acción, por eso Acciones pendientes cuenta tarjetas, no clientes distintos. Con cero tareas se muestra **Todo al día. Buen trabajo**. Consultar Hoy no cambia estados ni crea contactos, ventas o envíos.

Los avisos se recalculan cada 30 segundos con lecturas en caché de hasta 60 segundos, aisladas por sesión. Las escrituras usan la invalidación existente y reflejan el cambio en la siguiente navegación de esa misma sesión. No se afirma sincronización instantánea entre dispositivos ni se usa Supabase Realtime.

## Jornada realizada y cierre

El esquema anterior solo tenía `mf_casos.fecha_preferida`, que no prueba que se haya realizado una actividad. Se añade **`fecha_realizacion`**, opcional, y el control **Jornada realizada el** en Datos y seguimiento, con el autoguardado existente. No se copia automáticamente desde Fecha preferida y no admite una fecha futura. La solicitud de Cliente no puede fijar ese dato a través del RPC público.

Cerrar caso exige además Pagado y una venta no anulada. La función SQL bloquea caso/venta, comprueba ambas versiones y cambia el estado interno a Finalizado, mostrado como Cerrada. No crea ventas, altera montos, marca pagos ni envía mensajes. La operación es idempotente para reintentos de una respuesta perdida.

Deshacer verifica autor, reloj de PostgreSQL, plazo de diez segundos y versiones del caso y de la venta. Si algo cambió, conserva esos cambios e informa que no pudo revertir. Vuelve al estado anterior y marca el evento como deshecho; no elimina cotizaciones, ventas ni el historial.

Después del cierre aparece una tarjeta para **Guardar como plantilla** cuando los textos del programa no coinciden con una plantilla existente, reutilizando la acción del cotizador. También ofrece **Preparar agradecimiento**. Ambas acciones son opcionales y no se ejecutan por cerrar el caso.

## Mensajes e historial

Hay plantillas editables para seguimiento, recordatorio de pago y agradecimiento. Admiten `{contacto}`, `{cliente}`, `{servicio}`, `{cotizacion}`, `{monto}` y `{fecha_jornada}`. Se sustituyen como texto, sin ejecutar código. La configuración conserva los datos del emisor, reparto, IVA y condiciones existentes; guardar una de las secciones no borra la otra.

Hacer seguimiento abre una vista previa con asunto y cuerpo editables, Copiar, Abrir en WhatsApp y Abrir en correo. WhatsApp necesita un teléfono utilizable y mailto un correo válido. Copiar tiene una alternativa manual si el navegador bloquea el portapapeles. Los enlaces requieren la aplicación correspondiente en el dispositivo.

**Copiar o abrir no confirma que se haya realizado el contacto.** Después de contactar, pulsa Registrar seguimiento realizado. Se guarda en `mf_eventos_caso` como contacto de esa cotización y aparece **Seguimiento realizado el dd/mm/aaaa** en el historial del caso. La tarjeta se retira durante tres días calendario de Chile por defecto. El mismo registro no duplica eventos al reintentar. No se modifica el estado ni la versión del caso por registrar un contacto.

Recordatorios y agradecimientos tienen acciones equivalentes de registro. Registrar un recordatorio no hace desaparecer una deuda: la tarjeta de pago permanece hasta actualizar el estado de pago. El importe del mensaje es el total de la venta; no se inventa un saldo después de un abono, porque el esquema actual no almacena su importe. Cuando una venta corresponde a una versión anterior de cotización, el recordatorio y la sugerencia post-cierre usan esa versión vendida.

Los plazos iniciales son cinco días sin respuesta, tres días de pausa tras seguimiento y quince minutos para revisar un correo preparado. Se guardan dentro de `mf_configuracion.datos.hoy`; no en una tabla inventada llamada configuracion. Las lecturas usan esos valores, con respaldo en los iniciales si aún no se han configurado.

## Cambios de esquema y capas

- `paginas/hoy.py`: saludo, tarjetas, accesos, diálogo y configuración.
- `servicios/hoy.py`: reglas puras, días de espera y textos.
- `servicios/repositorio.py`: lecturas administrativas y RPC con el JWT del usuario.
- `utils/mensaje_listo.py`: copia de texto; usa estilos compartidos y botón de al menos 44 px.
- `utils/navegacion.py` y `utils/permisos.py`: agregan Hoy solo a Administración.
- `202610220004_hoy.sql`: fecha efectiva y funciones `mf_registrar_contacto_hoy`, `mf_cerrar_caso_hoy` y `mf_deshacer_cierre_hoy`.

Se reutilizan `mf_eventos_caso`, `mf_envios_cotizacion` y `mf_configuracion` del cotizador. Los valores internos de estado se conservan: Cotizado/Cotizada, Vendido/Aceptada, En ejecución/En seguimiento, Finalizado/Cerrada y Cancelado/Rechazada. No se retiran campos, botones ni páginas anteriores.

## Qué probar con datos ficticios

Resultado de la entrega: **106 pruebas Python aprobadas**, además de las pruebas SQL de Hoy/cotizador y las simulaciones JavaScript de navegación y borradores. No se realizaron contactos ni envíos reales durante las pruebas.

| Prueba | Preparación y acción | Qué debe verse |
| --- | --- | --- |
| Solicitudes | Dos casos sin cotizar, de 10 y 20 días. Pulsa Cotizar en el primero mostrado. | El de 20 días aparece antes y abre su propia pestaña Cotizaciones. |
| Seguimiento | Caso Cotizada, propuesta de hace seis días, sin venta ni contacto reciente. | Mensaje con contacto, servicio y código. Abrirlo no registra nada. Tras Registrar seguimiento realizado desaparece hasta vencer la pausa configurada. |
| Datos | Caso con modalidad por definir o correo inválido. | Faltan datos identifica el dato y Completar abre ese caso sin modificarlo. |
| Pago | Venta con Abono recibido. Pulsa Registrar pago. | Abre Venta con el control de pago existente. No se marca Pagado automáticamente. |
| Cierre | Venta Pagado, caso En seguimiento y Jornada realizada el confirmada. | Cerrar caso lo deja Cerrada y ofrece plantilla/agradecimiento. Deshacer vuelve al estado anterior y mantiene venta/cotización. |
| Fecha solicitada | Fecha preferida pasada pero sin fecha efectiva de realización. | No ofrece cerrar; pide confirmar la jornada cuando corresponda. |
| Fallo de correo | Intento incierto o error. | Aparece Correos por revisar. Marcar revisado lo retira sin reenviarlo ni cambiar su estado original. |
| Todo al día | Sin tareas, ventas pendientes ni correos por revisar. | Mensaje Todo al día. Buen trabajo. |
| Cliente | Entrar con cuenta Cliente e intentar la ruta de Hoy. | Solo Nueva solicitud; sin lecturas de tareas ni acciones privadas. |

Pruebas:

```powershell
python -m pip install -r requirements-dev.txt
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
node tests/test_hoy.mjs
```

PGlite es solo dependencia de pruebas: `npm install --prefix tmp/db-test @electric-sql/pglite` si no existe esa carpeta. Los ensayos SQL se ejecutan en PostgreSQL efímero, no Supabase real. Las pruebas cubren las seis categorías, el acceso inicial, permisos, configuración preservada, contactos explícitos, idempotencia, fecha efectiva, pago, plazo y concurrencia. La revisión física de la interfaz a 375 px queda pendiente; AppTest no se presenta como inspección visual en un teléfono.

## Resumen diario opcional

Se dejó **documentado, sin implementar ni activar**, conforme a la alternativa solicitada. No hay ningún workflow nuevo ni se solicitaron claves de servidor para esta entrega. Los correos que muestra Hoy provienen del registro de intentos del cotizador, no de un aviso diario inexistente. La propuesta para una fase posterior está en [Resumen diario opcional](resumen_diario_opcional.md).
