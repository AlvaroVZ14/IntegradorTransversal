# Un formulario, tres modos

Actualización de navegación del 26/10/2026: la entrada base muestra el login o recupera la sesión; `?vista=solicitud` muestra siempre el formulario público, incluso con una cuenta abierta. El enlace “Acceso del equipo y cuentas” abre `?vista=acceso`. Con sesión verificada de Administración, la raíz abre Hoy; con sesión cliente, abre el formulario de su cuenta, sin barra lateral. Consulta [las entradas y la sesión persistente vigentes](entradas_y_sesion.md); la comparación previa de esta guía documenta la unificación anterior.

No se toma el modo ni el rol desde la URL, el borrador o `user_metadata`. El rol se consulta en `mf_perfiles`. La cuenta administrativa existente se conserva; esta actualización no asigna administración a nadie.

## Comparación previa y decisiones

Se presentó esta comparación antes de sustituir los formularios. La fuente se revisó en `app.py`, `paginas/nueva_solicitud.py`, `paginas/solicitud_publica.py`, los servicios, borradores, estilos y migraciones existentes.

| Dato o elemento anterior | Público anterior | Nueva solicitud anterior | Decisión |
|---|---|---|---|
| Encabezado | Logo, “Cuéntanos qué necesita tu equipo” | Ampolleta, “Nueva solicitud” | Accidental: mismo título y ampolleta. Logo adicional público/cliente. |
| Ancho y pasos | Tarjeta 720 px, Contacto / Tu equipo / Enviar | Secciones en página larga | Accidental: tarjeta y pasos compartidos Contacto / Servicio / Detalles y envío. |
| Empresa | “Empresa o institución”; puede usar el nombre del contacto | “Nombre o empresa *” interno; “Empresa u organización (opcional)” cliente | Etiquetas accidentales. Regla intencional: público/cliente admiten nombre personal; interno puede guardar pendiente, sin inventar una empresa. |
| Contacto | “Nombre y apellido” editable | “Persona de contacto *”; bloqueado para cliente | Etiqueta accidental, bloqueo intencional. |
| Nombre de cuenta | No hay cuenta | Cliente mostraba el mismo nombre también en “Nombre de tu cuenta” | El mismo dato se conserva en la barra de cuenta y el campo de contacto bloqueado; no era un dato independiente. |
| Correo | “Correo electrónico” editable | “Correo de contacto *”; bloqueado para cliente | Etiqueta accidental, identidad de cuenta intencional. |
| RUT | Opcional, dígito verificador | Igual | Se conserva. |
| Cargo | Opcional | Igual | Se conserva. |
| Teléfono | “Teléfono (opcional)” | “Teléfono” | Etiqueta accidental; mismo formato y validación. |
| Servicio | Tarjetas | Selector | Accidental: mismas tarjetas en todos los modos. |
| Temática | Una principal, tarjetas | Una principal, selector | Control accidental. Se amplía a varias temáticas: la primera es principal y sigue alimentando los indicadores existentes. |
| Modalidad | Pastillas | Selector | Accidental: mismas opciones y pastillas. |
| Participantes | Paso 2 | Sección del servicio | Accidental: paso 3 en todos. Obligatorio fuera de interno; sus límites no cambian. |
| Horas | “Horas estimadas”, paso 2 | “Horas totales estimadas *” | Accidental: etiqueta única y paso 3, mismos límites. |
| Lugar | “Lugar (opcional)” | “Lugar o ciudad” | Accidental: “Lugar o ciudad (opcional)”. |
| Fecha | Fecha preferida opcional | Igual | Se conserva; no admite fecha pasada al guardar. |
| Comentarios | “Cuéntanos un poco más” | “¿Qué te gustaría lograr?” | Accidental: “Comentarios y objetivos (opcional)”. |
| Búsqueda y precarga | No | Solo interno | Intencional: se conserva solo en interno. |
| Vinculación manual y automática por correo | No | Solo interno | Intencional: se conserva; cliente se vincula en DB con su UID. Un visitante no se vincula por escribir el correo de otra persona. |
| Sugerencias, corregir correo y duplicados | No | Solo interno | Intencional: se conservan, editables y con apertura del caso duplicado. |
| Origen | Formulario web fijo | Selector interno | Intencional. Se conservan las ocho opciones anteriores, incluidas Otro, No informado y Formulario web. |
| Consentimiento | Obligatorio | Cliente obligatorio; interno no lo preguntaba | Intencional: obligatorio público/cliente; confirmación interna opcional. |
| Honeypot | Sí | No | Accidental entre público y cliente: ambos lo tienen, con comprobación en DB. |
| Resumen | Sí | No | Accidental: mismo resumen. |
| Enviar | Paso final | Al final de la página | Misma acción externa al final. Tras éxito queda deshabilitada, sin repetir el envío. |
| Guardar / cotizar / otra | No | Cotizar / registrar otra internos | Intencional: se conservan; se añade Guardar en cada paso interno. |
| Éxito | Check, código, 48 horas y otra | Cliente mensaje simple; interno abría el caso | Presentación compartida. Interno tiene Abrir caso, Cotizar y Registrar otra; externo 48 horas y Enviar otra. |
| Borrador | Por pestaña pública | Por cuenta | Intencional: un mecanismo compartido con espacios separados por persona y modo. |

“Dirigido a” en la solicitud, “Referido por”, los registros incompletos y los avisos de nuevas solicitudes no estaban implementados en ese flujo; son adiciones explícitas. Ningún estado comercial se reemplaza: “Faltan datos” es una marca con lista de pendientes.

## Archivos y fuentes de verdad

- `paginas/formulario.py`: única interfaz. `nueva_solicitud.py` decide el modo desde el perfil y la llama; `solicitud_publica.py` es solo un adaptador.
- `utils/formulario_config.py`: campos, etiquetas, ayudas, pasos, tipos, opciones fijas, obligatoriedad y diferencias intencionales.
- `servicios/formulario.py`: normalización, validación y guardado; fuerza identidad y decide el canal según la sesión.
- `utils/formulario_borrador.py/.js`: borrador compartido y recuperación de los borradores anteriores.
- `public.mf_catalogo_formulario` y RPC `mf_catalogo_solicitudes()`: servicio y temáticas se leen de DB, sin exponer tarifas ni programas. Se inicializa con las opciones admitidas por el esquema existente. Incorporar categorías nuevas requiere migrar también las restricciones y filtros del resto del sistema; no basta con inventar un nombre en el navegador.
- `mf_configuracion`, fila `general`, JSON `datos`: sitio, redes, correo y `politica_privacidad`. No hay contactos reales escritos en el código. `correo_avisos` es privado; si falta, el worker utiliza `correo_contacto`.

Antes de activar el SQL se mantienen las opciones y el guardado completo heredados. Los campos nuevos con contenido, múltiples temáticas y el guardado incompleto no se descartan silenciosamente: se conserva el borrador y se pide activar la actualización. Tras activarlo se usa el catálogo de DB.

## 1. Activar el SQL

1. En el proyecto Supabase correcto abre **SQL Editor → New query**.
2. Copia y ejecuta completo [202610240001_formulario_unificado.sql](../supabase/migrations/202610240001_formulario_unificado.sql), una vez.
3. Requiere las migraciones existentes hasta `202610230001_lectura_en_vivo.sql`. **Funciona aunque no hayas ejecutado `202610230002_formulario_publico.sql`**; no necesitas ejecutar esa migración anterior ahora.
4. La transacción preserva perfiles, roles y casos existentes. Si falla, no deja cambios parciales. Guarda antes un respaldo como en el procedimiento de mantenimiento del proyecto.
5. En la app, como Administración: **Casos y cotizaciones → Configuración** y abre “Formulario: contacto, redes y privacidad”. Completa los enlaces y correos reales. Si una clave está vacía se omite su enlace; no se inventa una política de privacidad.

La clave publicable de la app no puede ejecutar DDL ni configurar Supabase Auth. Por eso el SQL y la configuración SMTP se activan desde sus paneles, no mediante un botón que eluda permisos.

## 2. Cuentas y correo de confirmación

Se recomienda **SMTP propio y mantener Confirm Email habilitado**. Así el correo bloqueado de una cuenta cliente está verificado. No se deshabilitó la confirmación para saltarse el problema de entrega.

Según la [documentación SMTP de Supabase](https://supabase.com/docs/guides/auth/auth-smtp), el proveedor integrado solo entrega a direcciones del equipo del proyecto y tiene un límite de dos mensajes por hora. Es para pruebas, no para registros de clientes externos. Con SMTP propio se deben revisar también los límites de [Supabase Auth](https://supabase.com/docs/guides/auth/rate-limits) y del proveedor contratado.

Configuración que debe realizar la persona con acceso al proyecto y al correo:

1. Obtén del proveedor SMTP el host, puerto, usuario, contraseña y remitente autorizado. No los pegues en el chat ni en archivos del repositorio.
2. En Supabase, **Authentication → Emails → SMTP Settings**, habilita SMTP propio e ingresa esos valores. Mantén **Confirm Email** activado en el proveedor Email. Usa un remitente/dominio verificado y configura los registros DNS que indique ese proveedor. Desactiva su seguimiento de enlaces para no alterar los enlaces de confirmación.
3. En **URL Configuration**, conserva la URL base publicada de esta app como Site URL. Los contactos comerciales siguen viniendo de `mf_configuracion`; esta es una configuración de autenticación distinta.
4. En **Email Templates → Confirm sign up**, pega [confirmacion.html](../supabase/templates/confirmacion.html). Usa `{{ .SiteURL }}` y `{{ .TokenHash }}`: no contiene una URL real codificada.
5. El usuario crea su cuenta, abre el correo y pulsa Confirmar correo y continuar. La app borra el token de la URL, Supabase lo verifica y se abre el formulario cliente con nombre/correo bloqueados. El botón adicional evita consumir el enlace con una simple vista previa del correo. [Referencia de plantillas y verificación](https://supabase.com/docs/guides/auth/auth-email-templates).

Si no llega la confirmación, la app ofrece solicitar otro correo o enviar la solicitud sin cuenta. Un fallo SMTP no crea una sesión confirmada ficticia. Según la configuración Auth, Supabase puede ocultar si una dirección ya existe; el mensaje ofrece iniciar sesión sin consultar un listado de usuarios. [Comportamiento de sign_up en Python](https://supabase.com/docs/reference/python/auth-signup).

El registro incluye honeypot y límites de intentos en la interfaz, además de los límites de Auth en servidor. La restricción local se puede eludir: no se presenta como protección completa. Supabase admite [hCaptcha y Turnstile](https://supabase.com/docs/guides/auth/auth-captcha), pero no se activó CAPTCHA sin sus claves y componente de verificación. No habilitarlo en el panel hasta integrar el frontend correspondiente.

Desde el 26/10/2026, Administración y Cliente conservan una cookie de sesión de hasta siete días, con rol revalidado en Supabase. Una sesión inválida vuelve al login. El enlace público no utiliza esa sesión. Los borradores no contienen contraseñas ni tokens Auth, y no restauran el consentimiento. Detalle y límites en [la guía de sesión](entradas_y_sesion.md).

## 3. Avisos a la dueña: independientes de Auth

Guardar una solicitud externa inserta, dentro de la misma transacción, un aviso en `mf_avisos_solicitud`. No se encolan casos anteriores ni registros internos. El fallo de correo nunca deshace una solicitud ya guardada.

El worker [avisos_solicitud.py](../scripts/avisos_solicitud.py) se ejecuta desde [GitHub Actions](../.github/workflows/avisos-solicitudes.yml). Usa SMTP con TLS y la clave de servidor exclusivamente en secretos de GitHub; la aplicación sigue rechazando claves de servidor. No imprime datos personales, guarda CSV ni publica artefactos con solicitudes.

En **GitHub → Settings → Secrets and variables → Actions**:

| Tipo | Nombre | Valor |
|---|---|---|
| Secret | `SUPABASE_URL` | URL del proyecto existente |
| Secret | `SUPABASE_SERVER_KEY` | Clave de servidor/service_role del proyecto; nunca la de la app pública |
| Secret | `SMTP_HOST` | Host de tu proveedor |
| Secret | `SMTP_PORT` | 587 para STARTTLS o 465 para TLS implícito |
| Secret | `SMTP_USER` | Usuario SMTP |
| Secret | `SMTP_PASSWORD` | Contraseña SMTP |
| Secret | `SMTP_FROM` | Remitente autorizado |
| Variable | `AVISOS_SOLICITUDES_ACTIVOS` | `true` para habilitar; `false` para desactivar |

Supabase Auth y el worker requieren configuraciones separadas aunque usen el mismo proveedor. Antes de activar el worker, completa `correo_avisos` o `correo_contacto` en la app. **No está activado ni se enviaron correos reales durante estas pruebas.**

El cron está previsto cada cinco minutos; GitHub puede retrasarlo y no garantiza entrega inmediata. Un fallo anterior al envío se reintenta, hasta cinco intentos con espera creciente. Si se pierde la respuesta después de comenzar el envío, se marca incierto para evitar duplicados. “Enviado” significa aceptado por SMTP, no entregado a la bandeja de entrada. Administración puede ver los contadores en **Estado del sistema → Avisos de nuevas solicitudes**. Un aviso incierto se revisa antes de reenviar; no se reinicia ciegamente.

## Seguridad y casos incompletos

- El trigger de `auth.users` escribe explícitamente `rol='cliente'`, aunque los metadatos digan admin o cambie el default. El administrador se asigna solo mediante SQL por una persona autorizada.
- `registrar_solicitud` valida campos según el rol real. Para clientes rechaza origen, referido, vinculación, autoría, indicadores internos y confirmación interna. Fuerza nombre, correo confirmado, UID, origen Formulario web y registrado por Cliente.
- El canal anónimo sigue siendo una RPC limitada con token aleatorio de reintento, honeypot y límites de envío; solo devuelve el código. No utiliza la sesión administrativa para guardar un formulario anónimo.
- Catálogo y configuración pública son proyecciones explícitas; no conceden lectura de las tablas. Los clientes solo leen su perfil. No pueden leer casos, tarifas, ventas, programas, historial, configuración, catálogos privados ni avisos.
- Los datos presentes se validan igual que antes. Solo Administración puede guardar campos obligatorios pendientes como NULL; no se generan correos ni nombres de relleno. Una marca derivada por trigger enumera lo pendiente y se elimina al completarlo. Un caso incompleto no puede pasar a Cotizada ni venderse.
- Todas las funciones de reserva/confirmación del worker están reservadas a `service_role`. Ni un visitante ni un cliente pueden marcar un aviso como enviado.

## Pruebas y qué debería verse

Las pruebas automáticas usan repositorio, SMTP y PostgreSQL efímero con datos ficticios. No escriben en Supabase real ni envían correos. No hay dependencias nuevas de producción.

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_formulario_borrador.mjs
node tests/test_formulario_unificado_sql.mjs
```

PGlite es solo de pruebas, bajo `tmp/db-test/node_modules`; si falta, instalar `@electric-sql/pglite` temporalmente en esa carpeta. Se comprueba el SQL con y sin la migración pública anterior y su reversión sin borrar casos.

| Prueba solicitada | Resultado esperado |
|---|---|
| (a) Raíz desde celular sin sesión | Login. Enviar solicitud sin cuenta abre `?vista=solicitud`: formulario sin barra lateral, tres pasos y enlace discreto de acceso al pie. |
| (b) Crear cuenta | Texto “Tus datos quedan listos…”. Tras confirmar el correo, nombre y correo bloqueados, empresa editable, sin listados. Si falla SMTP no se simula ingreso y se ofrece continuar sin cuenta. |
| (c) Entrar como cliente | Barra mínima con logo, nombre y Cerrar sesión; únicamente formulario. Guardar vincula con su UID real. Enviar otra conserva su identidad y limpia el resto. |
| (c) Entrar como administración | Raíz abre Hoy, menú completo. Nueva solicitud usa el mismo componente y muestra ayudas internas y saltos entre pasos. |
| (d) Metadatos `rol='admin'` | El perfil nuevo queda cliente; no recibe menú ni datos administrativos. La prueba SQL incluye otros indicadores falsos de administración. |
| (e) Recargar cada ruta | Ningún diálogo Page not found. Ambas cuentas restauran su sesión cuando la cookie es válida. Sin sesión se muestra login; `?vista=solicitud` sigue siendo público. |
| (f) Correo ya registrado | Mensaje amable que ofrece iniciar sesión; no muestra listados de correos ni concede una sesión por una respuesta ambigua. |
| (g) Tres modos lado a lado | Mismos campos comunes, etiquetas, controles, ancho y pasos. Solo cambian identidad bloqueada, logo, navegación y herramientas internas declaradas. Una prueba compara el contrato y otra los widgets realmente renderizados. |
| (h) Cliente existente interno | Buscador precarga datos; vinculación por correo y selector manual siguen disponibles. Se puede corregir cualquier dato y aplicar o ignorar sugerencias. |
| (h) Incompleto interno | Guardar funciona; muestra código, Faltan datos y pendientes. Abrir caso permite completarlo. Cotizar queda bloqueado hasta completarlo. |
| (h) Referido por colega | Aparece Referido por; se guarda su texto. Guardar y registrar otra mantiene el último origen. |
| (h) RUT inválido | `12.345.678-9` produce un mensaje junto al campo y no se guarda. `12.345.678-5` sí pasa. Los tres formatos de teléfono se normalizan a `+56 9 1234 5678`. |
| (h) Sin consentimiento externo | No se escribe nada. Tras consentir se recibe código y mensaje de 48 horas hábiles; el botón de envío queda deshabilitado. |
| URL `?modo=interno`, `?vista=hoy`, `/dashboard` sin permisos | Login sin sesión o formulario cliente con sesión; nunca campos internos, tablas o Dashboard. La entrada pública explícita conserva únicamente el formulario anónimo. |
| Recarga a mitad del formulario | En la misma pestaña se recuperan campos y paso, sujeto al almacenamiento permitido por el navegador. La cookie válida recupera la sesión cliente; si venció, se pide ingresar nuevamente antes de retomar su borrador. |
| Corte de red al guardar | Se conserva el borrador; el reintento utiliza el mismo UUID. Un envío confirmado no crea dos casos. |
| Fallo del aviso a la dueña | El caso existe igualmente. Estado muestra pendiente/error/incierto según lo ocurrido; no se repiten correos inciertos automáticamente. |

Se revisaron 375, 768 y 1440 px en Edge con capturas ficticias, sin scroll horizontal y con movimiento reducido. Quedan pendientes las pruebas en **Instagram/Facebook reales, Chrome Android y Safari iOS**, particularmente sus teclados y la conservación de pestañas. La emulación no demuestra compatibilidad completa con esos dispositivos. La limitación del marco externo de Community Cloud explicada en la guía anterior sigue vigente: la app oculta sus controles internos, pero no garantiza quitar la marca del alojamiento.

## Revertir

Desactiva primero `AVISOS_SOLICITUDES_ACTIVOS`, completa los casos con datos pendientes y vuelve al código anterior. Luego ejecuta [rollback](../supabase/rollback/202610240001_formulario_unificado.sql). Restaura las funciones anteriores respaldadas y desactiva las nuevas entradas; conserva casos, campos nuevos, catálogo y avisos. El rollback se niega a continuar si hay casos incompletos que el código anterior no sabe manejar. No repitas la migración sin revisar los objetos preservados.
