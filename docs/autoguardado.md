# Autoguardado, confirmaciones y sesión

## Ver la entrega

Abre **http://127.0.0.1:8502**, recarga con Ctrl+F5 e inicia sesión. Esta entrega es local; no se publicó en Community Cloud. El servidor se reinicia al terminar para evitar módulos de versiones anteriores en memoria.

No hay dependencias nuevas. El autoguardado funciona con el esquema actual. **Para activar Deshacer de una aceptación/venta recién registrada hay que ejecutar `supabase/migrations/202610220001_deshacer_aceptacion.sql` en SQL Editor**, después de la migración de permisos del 21/10. No se aplicó al proyecto vivo: esta sesión no tiene una conexión administrativa de SQL. Hasta aplicarla se conservan el registro y anulación ordinarios de ventas. Se conserva `requirements.txt`. Las claves siguen en `.streamlit/secrets.toml`, fuera del ZIP.

## Alcance comprobado en el proyecto

Se leyeron `app.py`, los formularios de `/paginas`, el repositorio y la caché de `/servicios`, las validaciones y las migraciones de Supabase. Los nombres reales son `mf_casos`, `mf_cotizaciones`, `mf_ventas`, `mf_tarifas` y `mf_perfiles`.

El editor existente se llama **Datos y seguimiento**; no existe otro formulario llamado “Completar datos”. El autoguardado se aplica a ese editor de casos ya registrados. Se conservan sus 14 campos, límites, selección de cliente, secciones, badges, pestañas y ayuda. También se mantiene una acción manual secundaria, ahora llamada **Guardar todo**. Nueva solicitud conserva su envío explícito y el consentimiento del cliente; no crea casos incompletos mientras se escribe.

No existe un campo RUT en `mf_casos` ni una tabla de historial definida en las migraciones. Se incluye una validación de RUT reutilizable y probada, sin inventar una columna. **No se afirma haber integrado un historial inexistente o desconocido.** Si el proyecto vivo tiene una tabla añadida manualmente, ejecuta `supabase/auditoria/02_historial_autoguardado.sql` (solo lectura) para obtener sus columnas, triggers y políticas antes de adaptar su escritura/compensación. No se borra ningún registro de auditoría.

## Autoguardado

Cada campo se envía al terminar de editarlo mediante `on_change`. Al escribir dentro de un cuadro de texto no se envía cada tecla a Supabase. Se muestra “Guardando…” mientras trabaja y “Guardado ✓ HH:MM” después de confirmar, usando hora de Chile.

Los errores aparecen junto al campo. Un correo inválido permanece escrito y no impide guardar el contacto, lugar u otro campo válido. Se validan texto, correo, teléfono, opciones, números y fechas. Las fechas pasadas que ya podían editarse en el detalle siguen permitidas; no se modificó esa regla de negocio.

El borrador y sus errores están en `st.session_state`, separados de los widgets para conservarlos al cambiar de página. La cola reintenta automáticamente con espera progresiva, hasta 30 segundos entre intentos. No muestra Guardado si la escritura falló.

Antes de guardar, se lee la versión actual del caso. Si otra sesión cambió el mismo campo, se conserva lo escrito, se muestra el conflicto y se ofrece **Guardar mi cambio**. Otros campos pueden seguir guardándose. Si Supabase guardó pero se perdió la respuesta, el reintento reconoce el valor confirmado sin repetir la escritura.

Las últimas lecturas del caso, propuestas, tarifas y ventas quedan respaldadas únicamente en la sesión administrativa. Ante un fallo temporal de consulta, se indica que se muestran datos de respaldo. Las escrituras nunca usan ese respaldo como prueba de versión: siempre consultan el registro real. Al confirmar una escritura se invalida la caché y se vuelve a intentar una lectura nueva.

### Corte de Internet y recuperación de texto

Se añade un respaldo en `sessionStorage` de **cliente, contacto, correo, teléfono, lugar y detalle**, antes de que el cambio pueda llegar al servidor. Está separado por usuario y caso, solo se activa dentro del editor administrativo y no contiene credenciales. Permite recuperar esos textos al reconectar o recargar la misma pestaña y volver a abrir el caso, después de autenticarse.

El texto se elimina del respaldo al reconocerse como guardado. Cerrar sesión explícitamente lo elimina también, incluso desde el Dashboard. Cerrar la pestaña normalmente termina ese almacenamiento; no se promete recuperación después de cerrar el navegador, borrar sus datos o usar un modo que deshabilite el almacenamiento.

**Límite importante:** números, fechas y selectores que ya llegaron al servidor se conservan en el borrador de sesión. Si Internet se corta antes de entregar esos eventos y se recarga inmediatamente, no tienen el respaldo local adicional de los campos de texto. No se promete un modo offline completo para todos los controles. Mientras el servidor no pueda verificar Auth, puede pedir reintentar el acceso; eso no significa que el borrador de la sesión se haya confirmado como guardado.

Este respaldo contiene datos de contacto del caso. Cualquier script del mismo origen y una persona con acceso al navegador podría leerlos. No lo uses en un equipo compartido sin cerrar sesión; no equivale a una sesión autenticada ni permite entrar a la app. Los clientes no reciben este componente ni autoguardado administrativo.

## Estados y confirmaciones

Cambiar un estado no destructivo del editor lo guarda sin botón ni confirmación extra. Aparece un aviso flotante con **Deshacer**, disponible durante 10 segundos. Es un componente con botón nativo, porque [`st.toast`](https://docs.streamlit.io/develop/api-reference/status/st.toast) no es un contenedor de widgets.

Deshacer comprueba también la versión del caso y el plazo en el servidor: no pisa un cambio posterior, aunque se pulse un botón antiguo. Un fallo de red conserva la opción mientras siga dentro del plazo. El estado cancelado no se guarda automáticamente: requiere **Confirmo anular el caso** y **Anular caso**.

Se mantiene la casilla **Venta anulada** y se añade confirmación obligatoria para aplicar una nueva anulación de venta. Se conserva también la casilla de aceptación de cotización como apoyo opcional; pulsar **Registrar venta** ya confirma esa aceptación y no exige marcarla.

**Aceptada sigue siendo una venta real.** En el esquema, `Vendido` se establece mediante `mf_registrar_venta`, con cotización, fecha, importe y pago. No se permite generar esa aceptación mediante un simple cambio de texto del estado. Se conserva la pestaña Venta y todos sus campos. Pulsar Registrar venta es el clic que registra esa aceptación.

Después de aplicar el SQL nuevo, ese clic también ofrece Deshacer durante diez segundos: `mf_deshacer_aceptacion` revierte atómicamente la venta recién creada y el estado del caso, conservando la cotización. Verifica Administración, autor original, plazo en el reloj de PostgreSQL, versión de venta y versión del caso capturada en el momento de aceptar. No permite borrar ventas antiguas ni revertir casos que cambiaron después. La anulación ordinaria sigue siendo distinta y requiere confirmación. La migración solo añade metadatos para ventas futuras y una función restringida; no modifica importes ni ventas previas. Su reversión está en `supabase/rollback/202610220001_deshacer_aceptacion.sql`.

El aviso también cubre cambios reversibles del editor, por ejemplo Aceptada → En seguimiento, sin requerir ese SQL. No inventa una nota de historial, importación o envío de correos: esos flujos no existen en el código actual.

Las propuestas que se están preparando ya no pierden sus valores cuando el contacto del caso se autoguarda y aumenta la versión del caso. Los snapshots de cotizaciones emitidas siguen siendo inmutables.

## Dashboard actualizado

La invalidación se realiza dentro del repositorio después de confirmar cada escritura: caso, solicitud, tarifa, cotización y venta. No depende de haber pulsado un botón de interfaz. Casos vuelve a leer sus datos y Dashboard obtiene datos nuevos al navegar desde la misma sesión.

El Dashboard conserva Actualizar y añade **Actualizado hace X min**, calculado desde la consulta real, no desde cada render. Se actualiza automáticamente cada 30 segundos, respetando la caché de 60 segundos. En otra pestaña o sesión, los cambios pueden tardar hasta ese ciclo de consulta; no se afirma que exista Supabase Realtime ni sincronización instantánea entre dispositivos.

## Persistencia de sesión: evaluación, sin activarla

La sesión actual sigue usando el cliente Supabase en memoria. Un refresco completo puede pedir iniciar sesión otra vez. **No se añadió persistencia de autenticación para Administración ni para Cliente**, dado que esta parte solicita evaluar la alternativa.

Supabase rota los refresh tokens; una cookie con siete días de vencimiento no impone por sí sola siete días de vida a la sesión del servidor. La rotación, la revocación y la comprobación mediante `getUser()` importan. Los controles avanzados de tiempo máximo del servicio requieren planes Pro según su [documentación de sesiones](https://supabase.com/docs/guides/auth/sessions); no se usaron como supuesto en el plan gratuito.

No recomiendo guardar directamente el refresh token administrativo en una cookie manejada por un componente JavaScript. `HttpOnly` impide leer la cookie desde JavaScript y requiere control del encabezado HTTP del servidor; un componente del navegador no puede ofrecer esa protección por sí solo. Cifrar o firmar una cookie no elimina el riesgo de robo y reutilización del valor. Ver [atributos de cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).

Mi recomendación para una fase posterior es **Recordarme solo para Administración, opcional y solo en equipo propio**, con una sesión opaca emitida por un backend del mismo origen: cookie Secure, HttpOnly y SameSite apropiado, vencimiento absoluto de siete días comprobado en el servidor, inactividad más corta, almacenamiento cifrado de tokens en el servidor, rotación sincronizada y revocación al cerrar sesión. En cada restauración habría que verificar el usuario y su rol real; la cookie nunca otorgaría el rol. Esto requiere un backend/proxy y almacenamiento de sesión adicionales, no solo instalar un componente.

Supabase también documenta un modelo de cliente JavaScript que necesita acceso a sus tokens; no se confunde con esta recomendación para el Auth Python de la app. Ver su [guía avanzada](https://supabase.com/docs/guides/auth/server-side/advanced-guide). Para Cliente conservaría el ingreso actual, sin Recordarme.

## Archivos y pruebas

Resultado de esta entrega: **73 pruebas Python aprobadas**, más las simulaciones JavaScript de recuperación local, los diez escenarios del menú móvil y las pruebas SQL de Deshacer aceptación. Los cálculos del Dashboard, los permisos por rol y las dependencias se conservaron sin cambios respecto de la entrega anterior.

La entrega completa está en `output/mente-futuro-autoguardado.zip`. Incluye `paginas/edicion_caso.py`, `servicios/autoguardado.py`, `servicios/lecturas_locales.py`, `utils/validaciones.py`, `utils/borrador_local.py`, los archivos actualizados y las pruebas. No contiene secretos ni datos reales.

```powershell
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
node tests/test_borrador_local.mjs
node tests/test_menu_movil.mjs
node tests/test_deshacer_aceptacion.mjs
```

Las pruebas Python usan repositorios ficticios: validación independiente, pérdida de conexión y de respuesta, concurrencia, vencimiento de Deshacer, confirmación de anulación, borrador de cotización conservado, persistencia al iniciar una sesión nueva, invalidación de caché y los recorridos anteriores. Las pruebas JavaScript simulan captura offline, recuperación tras remontar el componente, eliminación de texto confirmado y cierre de sesión. El SQL se prueba en PostgreSQL efímero con PGlite (la dependencia de pruebas existente en `tmp/db-test`, no una dependencia de la app): permisos, reversión atómica, vencimiento, concurrencia y rollback. No se escriben pruebas en Supabase real.

### Qué debe verse en las cuatro pruebas manuales

| Prueba | Pasos con datos ficticios | Resultado esperado |
| --- | --- | --- |
| Editar y recargar | En Datos y seguimiento cambia Contacto y sal del campo. Espera Guardado y recarga. | El nuevo contacto vuelve desde Supabase; puede ser necesario ingresar otra vez. No debes pulsar Guardar todo. |
| Cortar Internet | Con el editor cargado, desactiva Internet y modifica un texto, por ejemplo Lugar. Reconecta la misma pestaña. | El texto local se conserva y se recupera al reconectar. Si el servidor recibió el cambio pero falló Supabase, aparece el aviso de pendiente y se reintenta. Solo muestra Guardado después de confirmar. No uses recarga inmediata con selectores/números desconectados como garantía de modo offline completo. |
| Estado y Deshacer | Cambia Solicitud → En revisión o Aceptada → En seguimiento. Pulsa Deshacer antes de diez segundos. | Se guarda el cambio y luego vuelve al estado anterior. Si otra edición aumentó la versión, se informa y no se sobrescribe. Para anular un caso o venta sí se exige confirmación. |
| Dashboard | Modifica un campo que afecte sus filtros o registra una venta ficticia y abre Dashboard en la misma sesión. | Datos nuevos sin pulsar Actualizar. Se conserva el botón y se ve la edad real de la lectura. En otra sesión se aplica el ciclo automático y el TTL descritos. |

La inspección visual y el corte físico de red en un navegador real quedan pendientes: la herramienta de navegador de esta sesión no tiene superficies disponibles. Las simulaciones automáticas no se presentan como comprobación física de Internet ni como una revisión visual a 375 px.
