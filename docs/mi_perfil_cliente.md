# Mi perfil dentro de Mis documentos — Prompt 28

## Activar

1. Si aún falta, aplicar primero `supabase/migrations/202611020004_redes_sociales.sql` (Prompt 27), después de las migraciones anteriores.
2. Ejecutar completo y una sola vez `supabase/migrations/202611030001_mi_perfil_cliente.sql` en Supabase → SQL Editor, con la cuenta administradora del proyecto.
3. Usar la versión actual de la app, recargar e ingresar con una cuenta **cliente** confirmada. Abrir Mis documentos → Mi perfil. El catálogo público pasa a versión 5; su caché puede tardar hasta 60 segundos en renovarse.

No hay dependencias ni secretos nuevos. No se ejecutó esta migración en Supabase publicado desde esta entrega: no hay acceso administrativo disponible. Las pruebas usan PostgreSQL efímero, cuentas ficticias y repositorios simulados.

## Qué aparece

El menú sigue teniendo solo **Solicitar servicio** y **Mis documentos**. No se registra una ruta adicional. Mi perfil es una tarjeta plegable al principio de Mis documentos, también cuando todavía no hay archivos. En celular se mantiene plegada inicialmente; al abrirla, los campos se apilan y Guardar cambios ocupa el ancho completo.

Empresa, Nombre de contacto y Correo son de solo lectura. El nombre viene del perfil de cuenta existente y el correo de Auth; se muestra «Es el correo de tu cuenta». La empresa se obtiene del registro vinculado o de la solicitud de ese correo. El RUT no aparece ni se recibe como dato editable.

Solo se editan teléfono, cargo y las cinco redes. Se reutilizan las validaciones del Prompt 27: normalización de Instagram, HTTP/HTTPS, límite de 200 caracteres y Otra red como texto libre si no es un enlace. Teléfono usa la misma validación y formato chileno del formulario; cargo tiene un máximo de 160 caracteres. Vacíos son válidos. Un solo botón **Guardar cambios** confirma con **Listo, actualizamos tus datos**.

Si nunca hubo una solicitud, empresa y los campos editables aparecen vacíos; nombre y correo siguen siendo los conocidos de la cuenta. Guardar crea el registro sin crear un caso ni una cuenta nueva. La primera solicitud con empresa reutiliza ese registro vacío. No se permite editar la empresa desde Mi perfil; se establece al solicitar un servicio o al registrarlo Administración.

## Una fuente de verdad

Se reutiliza `mf_empresas_redes` del Prompt 27, agregando **telefono**, **cargo** y **version**. No se crea otra tabla de clientes ni un duplicado en `mf_perfiles`. Las nuevas columnas se inicializan con los datos de contacto disponibles; RUT, estados y cotizaciones no se alteran.

Los cambios confirmados de teléfono, cargo y redes se sincronizan con los casos del mismo correo de contacto y empresa. Las ediciones administrativas de esos datos y las solicitudes con sesión actualizan el mismo registro. Las cotizaciones emitidas mantienen su snapshot histórico. Las escrituras conservan el control de versiones del caso: una edición concurrente puede pedir revisar el dato antes de sobrescribirlo.

También se admite sincronizar esos campos opcionales a casos incompletos. La excepción del trigger de integridad exige una cuenta confirmada, pertenencia por correo, igualdad exacta con el registro canónico y que ninguna otra columna comercial cambie. No da al cliente permiso de actualizar la tabla de casos.

Como en el Prompt 27, un envío público no confirmado no puede sobrescribir un perfil confirmado. Sus datos entrantes se conservan en su solicitud para revisión; no se convierten automáticamente en cambios autorizados del perfil de otra persona.

Si un correo corresponde a varias empresas, Mi perfil muestra la empresa de la solicitud más reciente. No mezcla empresas distintas. El formulario conserva la consulta por empresa al cambiar ese campo. El cliente puede editar sus registros por la RPC únicamente cuando pertenecen a su propio correo confirmado, sin cambiar su empresa o identidad.

Solicitar servicio se precarga con teléfono, cargo y redes actuales. Si ya había un borrador, se actualizan solo sus campos que la persona no editó; se conservan servicio, detalles y cambios manuales. El respaldo de la pestaña recibe la misma actualización sin sustituir texto local pendiente de enviar.

El respaldo automático/manual ya incluía esta tabla: las columnas nuevas entran en el CSV sin agregar secretos ni otro formato de respaldo.

## Seguridad

- `mf_mi_perfil()` verifica rol cliente y correo confirmado en `auth.users`. No recibe el correo del navegador como autoridad. Devuelve solo identidad visible, campos permitidos e ID/versión para controlar concurrencia.
- `mf_guardar_mi_perfil(p_datos,p_id,p_version)` acepta únicamente teléfono, cargo y cinco redes; rechaza claves desconocidas, tipos incorrectos y valores inválidos. Verifica que el registro pertenezca al correo confirmado y que la versión no haya cambiado.
- Anónimos y cuentas sin confirmar no pueden leer ni guardar. Administración conserva su acceso de gestión, pero no usa estas RPC como si fuera cliente.
- La tabla canónica y las tablas de gestión siguen cerradas a la lectura/escritura directa de clientes por sus permisos y RLS. Las RPC son la única vía de perfil; no se habilita SELECT de filas completas de casos.
- No se cambian RUT, empresa, nombre, correo, roles, estados, montos, notas ni permisos de documentos desde el guardado del perfil.

## Archivos

| Archivo | Cambio |
|---|---|
| paginas/mi_perfil.py | Tarjeta plegable, lectura protegida, validación, guardado y actualización de precarga del borrador. |
| servicios/perfil_cliente.py | Contrato de campos, RPC con JWT personal y conservación de ediciones pendientes. |
| paginas/mis_documentos.py | Incluye la tarjeta antes del listado sin crear otro menú o ruta. |
| utils/formulario_borrador.py | Precarga teléfono/cargo/redes y reconoce cambios recuperados como ediciones manuales. |
| paginas/formulario.py | Cambiar empresa precarga también teléfono/cargo si no se editaron a mano. |
| supabase/migrations/202611030001_mi_perfil_cliente.sql | Columnas del registro existente, RPC, validación, versiones y sincronización acotada. |
| tests/test_mi_perfil.py, tests/test_mi_perfil.mjs | Datos ficticios, interfaz, aislamiento, restricciones y sincronización. |
| tests/test_app.py, tests/test_entradas.py | Respuesta de perfil ficticia y contexto completo del callback del formulario compartido. |

## Pruebas y qué debería verse

| Prueba | Resultado esperado |
|---|---|
| Cliente A abre Mis documentos | Mi perfil y documentos propios; dos opciones en el menú. |
| A edita teléfono y @usuario | Guarda normalizados; aparece el mensaje exacto y se precargan en Solicitar servicio. |
| A intenta usar el ID del registro de B | RPC devuelve permiso denegado y los datos de B no cambian. |
| B consulta su cuenta | Solo su propia empresa/contacto; nunca el perfil de A. |
| Cuenta con correo sin confirmar | No puede leer ni guardar, incluso con JWT simulado en SQL. |
| Cliente sin solicitud previa | Campos editables vacíos; Guardar crea el registro sin crear casos. La primera solicitud reutiliza el ID. |
| Se envían rut, estado, rol, empresa, nombre o correo en p_datos | La operación completa se rechaza; no hay cambios parciales. |
| URL peligrosa, teléfono inválido o cargo largo | Error claro junto al campo; no se guarda y se conserva el texto. |
| Perfil editado en otra sesión | Se avisa del conflicto; se conserva lo escrito y se exige revisar antes de volver a guardar. |
| Administración abre casos existentes | Ve teléfono/cargo/redes actualizados, incluidos casos incompletos. RUT y estados permanecen iguales. |
| Cotización ya emitida | Su snapshot histórico no cambia tras editar el perfil. |
| Se vuelve al formulario con un borrador | Se conservan sus cambios manuales; los campos no editados usan los datos recién guardados. |

```powershell
python -m unittest discover -s tests -p test_mi_perfil.py
python -m unittest discover -s tests
node tests/test_mi_perfil.mjs
node tests/test_formulario_unificado_sql.mjs
node tests/test_publico_sql.mjs
```

La prueba SQL usa PGlite en `tmp/db-test/node_modules`, como las demás pruebas del proyecto; no es una dependencia de Streamlit. Queda pendiente aplicar el SQL real y revisar la tarjeta desde un teléfono físico.
