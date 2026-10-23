# Cliente con acceso exclusivo a Nueva solicitud

Entrega del 21/10/2026. El cambio está implementado en los archivos del proyecto; la migración debe aplicarse al Supabase real antes de publicar este código. No se han modificado los permisos de producción desde esta sesión.

## Esquema revisado y alcance

Se revisó el esquema versionado `202610150001_gestion_mente_futuro.sql` y el código existente. Sus nombres reales son `mf_perfiles(id,rol,nombre,email)`, `mf_casos`, `mf_cotizaciones`, `mf_tarifas` y `mf_ventas`. El rol anterior es `duena`, no `admin`. Sus políticas dejaban leer casos propios y cotizaciones, aunque no concedían acceso total a todos los autenticados.

No hay conexión administrativa a Supabase en esta sesión, por lo que no se pudo contrastar su catálogo actual en vivo. La consulta de auditoría incluida permite comprobar cualquier cambio realizado directamente en el panel antes de aplicar la migración. No se requieren claves administrativas dentro de la app.

Se mantienen los nombres y relaciones. `duena` se convierte en `admin` para todas las cuentas que ya tengan ese rol. No se crea otra tabla de perfiles ni se decide el rol mediante el correo, la URL o `user_metadata`. El disparador de registro existente sigue creando `cliente`, incluso si se intenta enviar `rol=admin` en los metadatos.

Los estados reales son Solicitud, En revisión, Cotizado, Vendido, En ejecución, Finalizado y Cancelado. Este cambio de permisos conserva ese flujo para no alterar cotizaciones y ventas existentes; los nombres distintos del texto de contexto no se aplicaron como una migración de estados.

## Archivos completos y capas

- `app.py`: sesión y guardia de rutas. Cliente solo tiene Nueva solicitud; cualquier parámetro de URL se limpia. Un valor de navegación privado en la sesión se reemplaza por Nueva solicitud.
- `paginas/nueva_solicitud.py`: identidad de cuenta bloqueada, consentimiento obligatorio y pantalla de comprobante sin listado. Administración conserva su formulario interno.
- `paginas/gestion.py`: casos, cotizaciones, tarifas y dashboard. Cada punto de entrada privado valida el rol antes de consultar datos.
- `servicios/repositorio.py`: operaciones Supabase. Para cliente solo usa `registrar_solicitud`; todos los métodos de consulta de tablas de negocio exigen Administración.
- `utils/permisos.py`: única interpretación del rol y selección de rutas en Python.
- `mente_futuro/ui.py`: textos nuevos de acceso.
- `mente_futuro/presentation.py`: diseño existente con columnas apiladas en pantallas de hasta 480 px, incluidas las de 375 px.
- Los módulos anteriores `mente_futuro/pages.py` y `repository.py` quedan como adaptadores de compatibilidad.

No hay dependencias Python nuevas. `requirements.txt` sigue siendo suficiente. PGlite se utiliza solo en pruebas locales de SQL, fuera de las dependencias de la aplicación.

## SQL por partes y activación

1. En SQL Editor ejecuta **solo lectura**: `supabase/auditoria/00_inspeccionar_accesos.sql`. Compara columnas, políticas y funciones con el esquema versionado. Si hay funciones adicionales que devuelven datos de negocio con SECURITY DEFINER, deben revisarse antes de habilitar el acceso a clientes: las políticas RLS no sustituyen la autorización dentro de esas funciones.
2. Ejecuta **todo** `supabase/migrations/202610210001_cliente_solo_solicitud.sql` una vez. No ejecutes otra vez la migración inicial en un proyecto ya creado. La nueva está separada en cuatro partes comentadas dentro de una única transacción:
   - Parte 1: respaldo privado de las políticas y permisos reales encontrados.
   - Parte 2: migración `duena → admin`, función `es_admin()` SECURITY DEFINER con search_path fijo y alias para las funciones existentes.
   - Parte 3: columnas de origen, autor y consentimiento; función `registrar_solicitud(uuid,jsonb)`.
   - Parte 4: reemplazo de políticas y revocación de permisos públicos/por columna antiguos; acceso de negocio solo para Administración.
3. Publica el código de esta entrega en Streamlit. Durante este paso, el código anterior puede dejar de funcionar para las cuentas administrativas hasta que se actualice; el acceso del cliente ya estará cerrado por la base de datos.
4. Cierra las sesiones abiertas y vuelve a ingresar con las cuentas de prueba. La aplicación consulta el perfil al procesar cada interacción.

La migración inspecciona las tablas públicas `mf_*` y los nombres heredados `casos`, `cotizaciones`, `tarifas`, `programas`, `ventas`, `historial` y `configuracion`, si existen. No inventa tablas de programas, historial o configuración. El respaldo incluye políticas no versionadas, permisos por tabla/columna y estado de RLS. Una política RESTRICTIVE impide que otra política permisiva accidental reabra estas tablas para clientes.

El cliente conserva SELECT de su propio perfil. No tiene INSERT/UPDATE/DELETE de perfiles. Las operaciones administrativas de perfiles y roles siguen siendo exclusivamente SQL; el panel de la app no asigna roles. En las tablas de negocio la cuenta admin conserva la gestión completa.

## Contrato del formulario

La función `registrar_solicitud` verifica cuenta confirmada, rol cliente, consentimiento booleano verdadero y campos del servicio. Nombre y correo se obtienen del perfil y de Auth; cualquier identidad, rol, estado, origen o autor recibido en el JSON se ignora. El servidor fija:

```text
cliente_id = auth.uid()
creado_por = auth.uid()
contacto = mf_perfiles.nombre
email = auth.users.email
origen = Formulario web
registrado_por = Cliente
estado = Solicitud
consentimiento = true
consentimiento_fecha = hora del servidor
consentimiento_version = 2026-10-21
```

Empresa/organización es opcional y no sustituye la identidad de la cuenta. Se permite reintentar un mismo UUID sin duplicar el caso. Se devuelve únicamente `{"codigo":"MF-2026-0001"}`; nunca una fila de casos. El código es un comprobante, no un enlace de consulta.

Después del envío se ve el código y **“Te contactaremos dentro de las próximas 48 horas hábiles”**. Solo aparece el botón para enviar otra solicitud, que abre un formulario nuevo con el consentimiento desmarcado.

## Pruebas manuales y resultado esperado

Usa cuentas ficticias confirmadas, por ejemplo `cliente.uno@example.test`, `cliente.dos@example.test` y `administracion@example.test`, en un proyecto de pruebas. Para estas direcciones sin buzón, crea las cuentas de prueba ya confirmadas desde administración y completa `mf_perfiles.nombre`. No cambies la configuración de confirmación de todas las cuentas para hacer las pruebas.

| Prueba | Resultado esperado |
|---|---|
| Cliente inicia sesión | Solo Nueva solicitud. No hay pestañas Registro de casos/Tarifas ni Dashboard. |
| Cliente intenta elegir Casos, Dashboard o Tarifas por menú | Las opciones no existen. |
| Cliente abre `/?pagina=Casos%20y%20cotizaciones` | Se limpia la URL y vuelve a Nueva solicitud; no consulta ni muestra datos privados. |
| Cliente abre `/?pagina=Dashboard` o `/?pagina=Tarifas%20y%20servicios` | Mismo resultado. Tampoco funciona `?page=Dashboard` ni `?rol=admin`. |
| Se intenta cambiar la ruta en una sesión antigua que mostraba casos | El siguiente procesamiento del servidor la fuerza a Nueva solicitud. |
| Se llama directamente a una función de página privada | PermissionError antes de cargar tablas. No existen archivos de multipágina de Streamlit en `/pages` ni se usa `st.switch_page`. |
| Nombre/correo de cuenta en formulario | Precargados y bloqueados. No hay vinculación, origen ni campos internos. |
| Enviar sin consentimiento | Error visible, sin escritura. Una llamada RPC directa también falla. |
| Enviar con consentimiento | Solo comprobante con código y mensaje de 48 horas hábiles. No hay listado ni cotización. |
| Reintentar el mismo envío por conexión interrumpida | Mismo código; un caso, sin duplicados. |
| Enviar JSON con contacto/correo/cliente_id/autor/origen/estado falsificados | Se guardan la identidad y los valores internos fijados en el servidor. |
| Cliente consulta cada tabla con su JWT | 0 filas o error 42501; ni siquiera lee su caso recién enviado. |
| Cliente consulta perfiles | Solo su perfil; no puede cambiarse a admin. |
| Administración inicia sesión | Mantiene Nueva solicitud, Casos y cotizaciones (dos pestañas) y Dashboard. |
| Administración consulta/gestiona datos | Ve todas las solicitudes, tarifas, propuestas y ventas; puede cotizar, registrar ventas y gestionar seguimiento. |
| Anónimo llama al RPC o consulta tablas | Acceso denegado. |
| Ventana de 375 px | Campos en una columna, textos y consentimiento legibles, botón completo sin desplazamiento horizontal. |

Para comprobar tablas con JWT real desde la raíz:

```powershell
python tests/probar_sesion_cliente.py
```

Introduce una cuenta ficticia de cliente y su contraseña cuando los solicite. No se imprimen tokens y no modifica registros. Para probar las políticas dentro de SQL Editor usa `supabase/auditoria/01_probar_cliente.sql`, reemplazando el UUID por el de esa cuenta ficticia. El script cambia temporalmente al rol authenticated, comprueba cada tabla y termina con ROLLBACK. Ejecutar SELECT como postgres no sirve para comprobar las restricciones de un cliente.

## Pruebas automatizadas reproducibles

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
npm install --prefix tmp/db-test --no-audit --no-fund @electric-sql/pglite
node tests/test_database.mjs
```

AppTest comprueba rutas, identidad bloqueada, consentimiento, éxito sin listado, textos de login y el recorrido administrativo de solicitud/cotización/venta/dashboard. PostgreSQL efímero aplica el esquema inicial, incluye tablas adicionales ficticias y una política abierta, aplica la migración, prueba clientes/admin/anónimo, restaura el esquema de acceso anterior y vuelve a aplicar la migración. Todas las pruebas usan datos ficticios y no conectan a producción.

Resultado de esta entrega: 20 pruebas Python y 110 comprobaciones SQL correctas. También se comprobó que la migración aborta ante vistas de negocio o funciones SECURITY DEFINER adicionales accesibles a clientes que requieren revisión. La prueba visual manual a 375 px y las pruebas con sesiones del Supabase real quedan para después de la activación; AppTest no reproduce un navegador con ese ancho.

## Revertir

1. Ejecuta `supabase/rollback/202610210001_cliente_solo_solicitud.sql` con postgres.
2. Publica la versión anterior del código, por ejemplo el commit `1282020` de este repositorio.
3. Cierra y vuelve a abrir las sesiones. Los roles admin vuelven a duena.

La reversión restaura las políticas originales, los permisos por tabla/columna y los estados previos de RLS desde `mf_seguridad.respaldos`, incluido cualquier permiso amplio anterior. Conserva las solicitudes nuevas y sus columnas de consentimiento para no perder trazabilidad. Si el respaldo no existe, aborta. Después de revertir se puede volver a aplicar la migración.

Referencia técnica: [RLS de Supabase](https://supabase.com/docs/guides/database/postgres/row-level-security) y [seguridad de funciones SQL](https://supabase.com/docs/guides/database/functions).
