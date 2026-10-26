# Dos entradas y sesión persistente · 26/10/2026

Este cambio reorganiza la entrada y la navegación. No modifica diseño, campos, estados, cálculos, escrituras comerciales ni políticas SQL. No requiere dependencias nuevas ni una migración SQL nueva. Los requisitos previos del formulario público y de canales siguen siendo los de las entregas anteriores.

## Comportamiento vigente

| Entrada | Sin sesión | Administración válida | Cliente válido |
|---|---|---|---|
| Raíz, sin parámetros | Login | Hoy | Nueva solicitud, identidad bloqueada |
| `?vista=acceso` | Login | Login y Volver a la app | Login y Volver a la app |
| `?vista=solicitud` | Formulario público | Formulario público y Volver a la app | Formulario público y Volver a la app |
| URL administrativa directa | Login | Página solicitada | Nueva solicitud |
| URL inexistente | Login | Hoy | Nueva solicitud |

El login conserva Crear cuenta de cliente y agrega la acción solicitada **Enviar solicitud sin cuenta**, que fija explícitamente `vista=solicitud`. Crear una cuenta sigue siendo opcional, con el flujo de confirmación existente y rol decidido en DB. Enviar una solicitud pública nunca crea una cuenta ni una sesión.

La rama pública se ejecuta antes de recuperar Auth, no construye un repositorio de usuario, no asigna `_repo_actual` y pasa `repo=None` al componente compartido. Por eso una sesión administrativa no precarga datos ni habilita herramientas internas en el formulario compartido. El botón Volver a la app abandona el parámetro público y el marco verifica la sesión y el rol antes de elegir Hoy o Nueva solicitud. Un token inválido no impide abrir el formulario público.

Compartir ya generaba enlaces explícitos `?vista=solicitud&canal=...`; se conservó esa función y se verificó de nuevo. No se cambió el contenido de los QR, los canales, la captura del borrador, las validaciones, el consentimiento ni el guardado.

## Autorización y URLs estables

`st.navigation(position='hidden')` reconoce todas las URLs conocidas desde la primera ejecución. Reducir ese registro mientras aún no se restauró Auth volvería a producir el diálogo Page not found. El registro de una URL no otorga autorización.

El marco construye aparte `rutas_para_perfil`: un diccionario de destinos ejecutables del rol verificado. Para Cliente contiene solamente Nueva solicitud. Para Administración incluye sus páginas y Estado. Tanto las redirecciones como el menú usan ese diccionario. Antes de `actual.run()` se aplica `guard_route`; cada archivo protegido mantiene además `proteger_pagina` y sus verificaciones `require_admin` existentes. No es una ocultación mediante CSS.

## Cookie y cierre de sesión

- Cookie nueva `mfy_session_refresh_v2`, host actual y `Path=/`, sin `Domain` compartido. Guarda solo refresh token y vencimiento; no guarda contraseña, rol ni datos del negocio.
- Plazo de hasta siete días desde el ingreso explícito, sin extender ese plazo por cada recarga. Se conserva al cerrar/reabrir pestañas si el navegador permite cookies persistentes.
- Al recuperar se llama a Supabase Auth, se vuelve a obtener el usuario y su perfil y solo se admiten los roles ya existentes admin/cliente. Una cookie no puede asignarse Administración.
- Se reconoce la cookie administrativa anterior y se elimina al confirmar el guardado de la nueva. No se expulsa a una administradora únicamente por el cambio de nombre.
- La rotación del refresh token actualiza la cookie, también para clientes. La renovación del cliente no consulta páginas de negocio.
- Cerrar sesión intenta revocar la sesión local en Supabase, limpia el estado de Streamlit y ordena eliminar las cookies nueva y anterior. Un listener del botón las elimina también antes de la respuesta del servidor.
- Una cookie malformada, vencida, revocada o con perfil inválido se elimina y vuelve al login sin trazas técnicas. Un fallo transitorio de red durante la recuperación conserva el token y ofrece reintentar; no se interpreta como una contraseña inválida.

**Límites y riesgos:** el componente oficial v2 usa `document.cookie`; la cookie no puede ser HttpOnly y, por tanto, una vulnerabilidad XSS podría exponer el token. Se utiliza `Secure` con HTTPS y `SameSite=Strict`; HTTP solo permite persistencia en loopback para desarrollo. Si el navegador bloquea cookies aparece el aviso y se puede usar la sesión actual, pero no se promete recuperarla al recargar. No se guarda el token en `localStorage`.

El plazo local de siete días no sustituye las políticas de sesión/revocación configuradas en Supabase. Un usuario que controle su navegador puede alterar una fecha local, pero el token siempre debe ser aceptado por Auth y no le concede otro rol. La revocación remota necesita red; los JWT ya emitidos pueden seguir válidos hasta su expiración. Para un límite absoluto impuesto por el servidor o cookies HttpOnly haría falta configuración/backend adicional, fuera del cambio de navegación solicitado. En equipos compartidos se debe cerrar sesión.

## Revisión de permisos del formulario público

Se revisaron las migraciones existentes y se ejecutaron en PostgreSQL efímero. No se modificaron políticas, grants ni funciones SQL de producción.

- `anon` no puede leer casos, perfiles, cotizaciones, ventas, tarifas ni la tabla de configuración, ni insertar directamente en casos.
- La escritura se realiza mediante `registrar_solicitud_publica`, que valida el formulario y devuelve únicamente su código. No escribe en `auth.users`. Los avisos y recibos internos son parte de la misma transacción existente.
- Se conservan **dos lecturas públicas intencionales**: `mf_catalogo_solicitudes` entrega etiquetas de servicios/temáticas y versión; `mf_configuracion_publica` entrega únicamente sitio web, redes, correo público y política de privacidad. Son proyecciones limitadas, sin acceso a tablas ni datos de clientes. Si “no leer datos” significa también prohibir estos metadatos públicos, ese punto no se cumple literalmente: habría que sustituir el catálogo/enlaces por contenido estático o una proyección aprobada. No se cambió por instrucción del usuario.

Esto verifica el esquema versionado, no audita automáticamente cambios manuales que pudieran existir en la instancia real. No se usaron cuentas reales ni se enviaron solicitudes/correos a producción.

## Archivos modificados y propósito

| Archivo | Cambio |
|---|---|
| `app.py` | Prioridad de la entrada pública, login por defecto, rutas autorizadas por rol y restauración para ambas cuentas. |
| `mente_futuro/ui.py` | Botón Enviar solicitud sin cuenta e ingreso explícito que abandona el login y reinicia su plazo de sesión. |
| `paginas/formulario.py` | Enlace discreto Volver a la app y descarte de eventos tardíos de widgets ya desmontados al cerrar sesión; conserva el mismo formulario. |
| `servicios/acceso.py` | La confirmación de correo usa el mismo establecimiento de sesión que el login. |
| `servicios/sesion.py` | Nombre de cookie, compatibilidad, validación de identidad/rol y recuperación de clientes. |
| `utils/sesion_cookie.py` | Persistencia, sincronización y renovación para ambos roles; eliminación de cookie anterior. |
| `utils/sesion_cookie.js` | Escritura de cookie nueva y eliminación de ambas al cerrar sesión. |
| `utils/navegacion.py` | Diccionario de destinos ejecutables según el rol, separado del registro estable. |
| `utils/permisos.py` | Página protegida sin sesión muestra login, salvo entrada pública explícita. |
| `tests/test_entradas.py` | Pruebas dedicadas de los recorridos y ausencia de Auth al enviar el formulario público. |
| `tests/test_recarga.py` | Login anónimo y restauración cliente al recargar rutas. |
| `tests/test_sesion.py` | Recuperación y rotación de los dos roles. |
| `tests/test_sesion_cookie.mjs` | Cookie de siete días, HTTPS, migración y eliminación de ambas cookies. |
| `tests/test_app.py` | Logout vuelve al login. |
| `tests/test_formulario_unificado.py` | Formulario público explícito, manteniendo las pruebas de campos y etiquetas. |
| `tests/test_compartir.py` | Visitante privado al login y enlace explícito público con cuenta abierta. |
| `tests/test_formulario_unificado_sql.mjs` | SELECT/INSERT directo denegados a anon y envío sin crear usuarios Auth. |
| `README.md`, `docs/formulario_unificado.md`, `docs/compartir.md` | Referencias actualizadas al nuevo comportamiento. |
| `docs/recarga_y_sesion.md` | Aviso de documento histórico y enlace al comportamiento vigente. |
| `docs/estado_proyecto.md` | Registro del cambio de entrada y persistencia de ambas cuentas. |
| `docs/entradas_y_sesion.md` | Este informe y sus límites. |

## Resultados de pruebas

Regresión completa: **174 pruebas Python aprobadas**. Pruebas de cookie y borrador en JavaScript aprobadas. SQL del formulario probado con y sin la migración pública anterior, incluyendo denegación de lectura/escritura directa y conservación de `auth.users`.

| Prueba pedida | Resultado esperado y comprobación |
|---|---|
| 1. Principal sin sesión, recarga | Login, Crear cuenta de cliente y Enviar solicitud sin cuenta. Probado automáticamente y en navegador local. |
| 2. Principal Administración, recarga/reabrir pestaña | Hoy, sin flash de login, con cookie válida. Comprobación con Auth ficticia, incluyendo pestaña nueva. |
| 3. Principal Cliente, recarga | Solo Nueva solicitud, nombre/correo bloqueados, sin menú ni datos administrativos. Recuperación con rol cliente probado. |
| 4. Público sin sesión, con admin y cliente, recarga | Siempre formulario anónimo, sin precarga de identidad ni lateral. Con cuenta abierta ofrece Volver a la app. Auth no es consultado en esta rama. |
| 5. Cliente abre URL administrativa | Redirige a Nueva solicitud antes de ejecutar consultas administrativas. |
| 6. Envío público sin cuenta | Se llama una sola vez a la RPC anónima, se obtiene código y no se crea sesión. PostgreSQL confirma que no aumenta `auth.users`. |
| 7. Ningún Page not found | Registro estable y prueba del envío del diálogo en cada ruta; también rutas desconocidas y anidadas. |

Las cuentas, tokens, base PostgreSQL y escrituras de QA son ficticios. Las capturas y resultados de navegador están en `output/dos-entradas`, excluido del repositorio. Se debe validar adicionalmente la configuración Auth/cookies de producción y los navegadores físicos donde se usará la app.

La matriz de Edge local completó **14 recorridos**, incluyendo reapertura de pestaña de ambos roles, público con ambas cuentas, logout, envío anónimo, URL inexistente, cookie inválida y migración de cookie anterior. Los 14 quedaron OK y sin Page not found. Se corrigió un evento tardío del formulario al salir: ahora ignora borradores desmontados y, para el mismo UUID vigente, actualiza la referencia activa sin perder campos.

Comandos utilizados:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_sesion_cookie.mjs
node tests/test_formulario_borrador.mjs
node tests/test_formulario_unificado_sql.mjs
```

Las pruebas del cotizador usan la dependencia de desarrollo `pypdf`, ya disponible en el Python de pruebas; no se añadió a las dependencias de producción. Para ejecutar esa suite dentro de otro entorno hay que instalarla como dependencia de pruebas.

Referencias: [sesiones de Supabase](https://supabase.com/docs/guides/auth/sessions) y [registro de páginas de Streamlit](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation).
