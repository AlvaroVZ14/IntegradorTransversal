# Recarga, rutas y sesión administrativa

## Causa confirmada

El `app.py` anterior registraba únicamente Ingresar cuando faltaba
`auth_client`. Una recarga crea otra conexión y otro `st.session_state`, mientras
la barra de direcciones conserva `/dashboard`, `/casos`, etc. El registro por rol
también dejaba fuera las rutas privadas para clientes. Streamlit intentaba
resolver la URL antes de recuperar Auth y emitía el diálogo nativo.

Se reprodujo el patrón anterior con una intención de URL `/dashboard`: se emitía
`send_page_not_found`. Las pruebas nuevas espían ese mismo mensaje y verifican
cero emisiones en los recorridos corregidos. No se oculta ni traduce el diálogo.

Referencia oficial: [registro de páginas en la primera ejecución](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation).

## Cambios

- Las seis rutas Inicio (raíz), Hoy, Nueva solicitud, Casos y cotizaciones,
  Dashboard y Estado se registran siempre, antes de Auth, cookies o llamadas de
  red, en `st.navigation(..., position='hidden')`.
- El menú usa `st.page_link` y contiene únicamente los ítems permitidos.
  Estado sigue oculto del menú, disponible para Administración desde Configuración.
- El marco verifica `get_user` y consulta `mf_perfiles` antes de ejecutar una
  página. Los archivos de página tienen además su propia guardia de entrada.
  Registrar la URL no concede acceso a datos: RLS y RPC no se modifican.
- Sin sesión se dibuja el login en la ruta solicitada y se recuerda el destino.
  Administración regresa allí; Cliente que pidió una ruta privada termina en
  Nueva solicitud. Un ingreso normal a la raíz mantiene Hoy como inicio de
  Administración y Nueva solicitud para Cliente.
- Streamlit no ofrece catch-all nativo para URL inexistentes. En 1.65,
  `utils/navegacion.py::resolver_ruta_desconocida` normaliza la intención de ruta
  a Inicio **antes** de `st.navigation`. Usa la API interna acotada
  `ctx.pages_manager.set_script_intent`, sin interceptar mensajes ni cambiar
  autorizaciones. Esto cubre también rutas anidadas, que `st.Page` no admite.
  Por eso el requisito queda en **Streamlit >=1.65,<1.66**: antes de subir de
  versión hay que ejecutar las pruebas de rutas y revisar esta compatibilidad.

## Cookie de Administración

Se utiliza el componente **oficial de Streamlit v2**, con JavaScript propio
pequeño en `utils/sesion_cookie.js`, sin librerías externas ni claves nuevas.
No se agrega una dependencia. El único cambio de versiones es acotar Streamlit
a la rama menor comprobada.

Después de comprobar el rol admin, se guarda solo su refresh token opaco de
Supabase y el vencimiento en `mfy_admin_refresh_v1`: siete días, Path=/,
SameSite=Strict, sin Domain y Secure en HTTPS. HTTP se permite exclusivamente en
localhost/127.0.0.1 para desarrollo. No se guardan contraseña, rol ni access
token en la cookie; tampoco se usan URL, localStorage o archivos para tokens.

Al recargar, el servidor lee la cookie de `st.context.cookies`, renueva Auth y
vuelve a consultar el rol real. Un token de cliente nunca inicia sesión mediante
este mecanismo. Todo ingreso como Cliente limpia la cookie administrativa.
Antes de mostrar páginas, se espera la confirmación de escritura de la cookie
rotada con logo y pantalla de carga; no se dibuja un login fugaz durante una
restauración válida.

El cliente Supabase desactiva la rotación de fondo. `get_session()` renueva si
es necesario al ejecutar el marco y después se actualiza la cookie con el token
actual. Un fragmento liviano cada 30 segundos también comprueba el vencimiento
mientras la app está abierta; si renueva el token administrativo, vuelve al marco
para sincronizar la cookie. Así los fragmentos del Dashboard no quedan con un
JWT vencido por estar una hora sin cambiar de página. No consulta la base en cada
latido: `get_session()` usa su sesión en memoria mientras siga vigente.
Esto evita que una renovación invisible deje guardado un token anterior.
El vencimiento original no se prolonga con cada cambio de página. La cookie
vence a siete días; no reemplaza las reglas de expiración/revocación del servidor
Supabase. Si el servidor termina la sesión antes, se pide ingresar de nuevo.

Al cerrar sesión se borra la cookie y se solicita revocar la sesión actual a
Supabase. Si no hay red, el navegador puede borrarla, pero no se puede confirmar
la revocación remota. Una falla de red durante restauración conserva la cookie
para reintentar, sin mostrar páginas privadas. Una cookie vencida, alterada o
revocada lleva al login. Si el navegador bloquea cookies, aparece un aviso y se
puede usar la sesión actual sin persistencia tras recargar.

**Riesgo:** una cookie creada con JavaScript no puede ser HttpOnly. Un XSS o una
extensión maliciosa podría robar el refresh token y reutilizar la sesión.
Secure y SameSite reducen otros riesgos, pero no solucionan XSS. Usar solo en el
equipo de confianza de Administración y cerrar sesión en equipos compartidos.
No es una cookie de servidor HttpOnly ni una garantía de acceso durante siete días
si Supabase revoca la sesión o el navegador elimina sus cookies.

Referencias: [sesiones y rotación de Supabase](https://supabase.com/docs/guides/auth/sessions),
[refresh_session en Python](https://supabase.com/docs/reference/python/auth-refreshsession),
[componentes oficiales v2](https://docs.streamlit.io/develop/concepts/custom-components/components-v2/communicate).

## Enlace `?vista=solicitud`: diferencia encontrada

En la versión de este proyecto recibida, **no había un formulario anónimo ni una
función de guardado público**: `app.py` enviaba cualquier visita sin Auth al
login, y `registrar_solicitud` exige una cuenta autenticada. Esto difiere del
contexto de la solicitud. Esta corrección conserva el flujo autenticado existente.

El enlace mantiene sus parámetros y ya no causa un diálogo. Con el flujo
existente se ingresa y se continúa en Nueva solicitud, en lugar de Hoy. **Esto no
equivale a enviar sin cuenta.** Implementar un guardado realmente anónimo es una
ampliación del formulario y su backend; no se abrieron permisos anónimos de tablas
ni se inventó una RPC pública en este cambio de recarga.

## Pruebas con datos ficticios

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_sesion_cookie.mjs
node tests/test_menu_movil.mjs
```

`test_recarga.py` reproduce el patrón antiguo y simula la intención de URL que
envía un navegador nuevo. Espía el mensaje interno `send_page_not_found`, además
de comprobar destino, menú y ausencia de datos privados. `test_sesion.py` usa
tokens ficticios para expiración y rol. La prueba JS ejecuta el componente en un
documento simulado: Secure, SameSite, límite de siete días, cierre y bloqueo de
HTTP externo. No se usaron credenciales reales en estas pruebas.

| Prueba manual | Resultado esperado |
| --- | --- |
| Administración ingresa y recarga Hoy, Nueva solicitud, Casos, Dashboard o Estado | Logo durante recuperación; vuelve a la misma página, con menú administrativo; sin login fugaz ni diálogo inglés |
| Cliente recarga Nueva solicitud | Debe ingresar otra vez: deliberadamente no hay cookie persistente para clientes; vuelve a Nueva solicitud |
| Cliente abre `/hoy`, `/casos`, `/dashboard` o `/estado` con sesión | Redirección a Nueva solicitud; menú de un solo ítem y ningún dato privado |
| Sin sesión abre una URL válida | Login, sin diálogo; al ingresar como Administración vuelve a esa URL; como Cliente va a Nueva solicitud si era privada |
| Abre `/no-existe` o `/ruta/anidada` | Sin diálogo; Administración va a Hoy, Cliente a Nueva solicitud; sin sesión aparece el login antes de resolver según el rol |
| Borra la cookie o espera su vencimiento | Login normal; no se restauran datos privados por un nombre de ruta |
| Se revoca o baja el rol de la cuenta en Supabase | No se recupera Administración mediante la cookie antigua |
| Cierra sesión y recarga | Permanece en login; la cookie no restaura la sesión cerrada |
| Falla la red al recuperar la sesión | Logo y aviso para reintentar; no se borra la cookie válida ni se muestran datos privados |
| `?vista=solicitud` sin cuenta | Sin diálogo, mantiene el flujo de login actual; el envío anónimo está pendiente de aclaración, como se detalla arriba |

La inspección física en navegador y la política de cookies de Community Cloud
deben verificarse tras publicar: las pruebas de Python/JS no equivalen a una
prueba visual ni a pulsar F5 en un navegador real conectado a producción.

Validación local de esta entrega: **126 pruebas Python aprobadas**, incluida la
reproducción del fallo anterior, y pruebas JavaScript de cookie y cierre de menú
móvil aprobadas. No se requieren migraciones SQL ni secretos nuevos.
