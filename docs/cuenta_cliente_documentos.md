# Cuenta de cliente y Mis documentos — Prompt 21

## Activar

1. Aplicar primero `supabase/migrations/202611020002_documentos_caso.sql` si todavía no se aplicó el Prompt 20.
2. Ejecutar **completo** `supabase/migrations/202611020003_mis_documentos.sql` en Supabase → SQL Editor con el administrador del proyecto. Ejecutarlo una sola vez, después de las migraciones existentes.
3. Reiniciar la app local o esperar el despliegue del commit en Community Cloud. No hay dependencias nuevas ni secretos nuevos.
4. En Supabase Auth conservar la confirmación de correo activada y las URLs de redirección válidas. Se reutilizan el registro, login, roles y recuperación de sesión existentes.

No se ejecutó SQL en el proyecto publicado ni se usaron cuentas o archivos reales. La migración se verificó en PostgreSQL efímero; Storage y correo se simularon en las pruebas Python.

## Qué cambia

- Administración conserva sus cinco secciones y Estado. En el detalle del caso se agrega **Correos adicionales con acceso a los documentos**, con autoguardado, validación, normalización y límite de 20 correos. La cuenta vinculada identifica al solicitante; por sí sola no concede acceso a documentos si no coincide el correo confirmado.
- Cliente tiene **Solicitar servicio** y **Mis documentos**, además de cerrar sesión. Solicitar servicio reutiliza el formulario, nombre y correo bloqueados, consentimiento y guardado existentes. Al ingresar desde la raíz llega al formulario; una ruta administrativa o inexistente lo lleva a Mis documentos.
- Sin cuenta, la raíz y `?vista=solicitud` muestran el formulario y el botón **Iniciar sesión**. `?vista=acceso` conserva el login y Crear cuenta de cliente. Enviar sin cuenta no crea usuario ni sesión.
- Mis documentos muestra únicamente empresa, código, servicio, fecha y documentos visibles con tipo, fecha y descarga. No ofrece fichas internas de casos ni consulta ventas, cotizaciones, tarifas o configuración.
- La fecha de agrupación es la de creación del caso, presentada en Chile; no se inventa una fecha de jornada cuando no existe.

## Acceso a datos

La fuente de identidad es `auth.users`: ID del JWT, correo actual y `email_confirmed_at`. No se confía en el correo de perfil, el navegador ni `user_metadata`. Una cuenta con rol cliente recibe los casos cuyo correo de contacto coincide, sin distinguir cuándo se creó la cuenta, o cuyo correo adicional coincide. Un `cliente_id` antiguo que contradiga el correo ya no decide este permiso. Cambiar el correo del contacto o eliminar uno adicional puede revocar el acceso anterior.

Se mantienen cerradas las tablas de gestión, incluida `mf_casos`: conceder al cliente SELECT de una fila completa expondría estados y datos internos. En su lugar, `mf_mis_documentos` devuelve solo una proyección autorizada con las seis claves de caso y cinco claves de documento necesarias. No devuelve notas, pagos, rutas ni metadatos del aviso. Las lecturas directas de `mf_documentos` también quedan limitadas por RLS a Administración. Las RPC verifican la misma pertenencia confirmada y no permiten escrituras. No hay permisos anónimos nuevos.

El descriptor `mf_documento_cliente` solo autoriza un documento disponible, visible y propio. Python lo utiliza para crear un enlace firmado de 600 segundos y consumirlo en el servidor. Streamlit entrega los bytes mediante un botón de descarga diferida: la página no contiene rutas de Storage ni tokens firmados. No se precargan todos los archivos ni se usa caché compartida. Un archivo descargado ya no puede revocarse; tampoco debe compartirse un enlace firmado durante su vigencia.

Las políticas de Storage siguen protegiendo el bucket privado incluso si existe otra política permisiva. Los permisos administrativos de carga, visibilidad y eliminación permanecen. Los avisos por correo siguen destinados al contacto principal; agregar un correo adicional concede acceso a documentos, no una suscripción automática a avisos.

Referencias: [funciones seguras de Supabase](https://supabase.com/docs/guides/database/functions), [buckets privados y enlaces temporales](https://supabase.com/docs/guides/storage/buckets/fundamentals).

## Archivos

| Archivo | Cambio |
|---|---|
| app.py | Raíz pública sin sesión, entradas de cliente y redirección segura. |
| utils/permisos.py | Dos destinos de cliente, destino seguro Mis documentos y guardia por página. |
| utils/navegacion_portal.py | Dos rutas estables nuevas y menú según rol; se elimina el enlace duplicado del antiguo menú de un solo destino. |
| paginas/solicitar_servicio.py | Adaptador al formulario existente. |
| paginas/mis_documentos.py | Vista mínima por caso y descargas diferidas. |
| servicios/mis_documentos.py | Lectura paginada con JWT y descarga autorizada sin mostrar rutas. |
| paginas/formulario.py | Acceso al login con la etiqueta Iniciar sesión. |
| mente_futuro/ui.py | Explica el acceso a documentos al crear una cuenta. |
| paginas/edicion_caso.py, servicios/autoguardado.py, utils/validaciones.py | Campo de correos adicionales y validación independiente. |
| servicios/documentos_caso.py | Guardia administrativa en sus consultas internas; cliente usa el servicio mínimo. |
| paginas/documentos_caso.py | Aviso de disponibilidad actualizado. |
| supabase/migrations/202611020003_mis_documentos.sql | Columna nueva, validación, autorización, RPC y políticas documentales/Storage. No borra tablas ni casos. |
| tests/test_mis_documentos.py, tests/test_documentos_caso.mjs | Pruebas nuevas del portal y aislamiento en SQL. |
| tests/test_app.py, test_recarga.py, test_entradas.py, test_formulario_unificado.py, test_hoy.py, test_arranque_cloud.py, test_navegacion_superior.py, test_compartir.py | Expectativas de menú y destinos actualizadas. |
| tests/storage_fixture.mjs, test_formulario_unificado_sql.mjs, test_publico_sql.mjs, test_en_vivo_sql.mjs | Modelo local mínimo de Storage para ejecutar todas las migraciones en pruebas SQL anteriores. |

## Pruebas y resultado esperado

Usar dos correos **ficticios** distintos en pruebas automatizadas. Para probar correo real de confirmación en producción, utilizar cuentas de prueba bajo control del equipo, sin datos de clientes.

| Prueba | Qué debería verse |
|---|---|
| A confirmado, documento visible en caso con correo A | Empresa, código, servicio, fecha y botón Descargar. |
| B confirmado entra a Mis documentos | No ve casos ni archivos de A. Si no tiene propios, aparece el mensaje cálido de espera. |
| Correo sin confirmar, incluso con JWT simulado | RPC devuelve cero casos; no puede firmar ni descargar. Auth normalmente impide ingresar hasta confirmar. |
| Solicitud pública/interna anterior al registro | Al confirmar una cuenta con el mismo correo aparece el caso sin vinculación manual. |
| Documento no visible, pendiente o eliminado | No aparece ni se autoriza su descarga. |
| Documento antes visible, ahora oculto | Al volver a cargar desaparece. Una nueva descarga comprueba el permiso y se rechaza. |
| Correo adicional B guardado por Administración | B ve únicamente los documentos visibles de ese caso; al quitarlo pierde acceso a nuevas descargas. |
| Cliente abre /hoy, /casos, /dashboard, /compartir o /estado | Redirección a Mis documentos, sin contenido administrativo ni Page not found. |
| Cliente recarga /solicitar-servicio o /mis-documentos | Se conserva la ruta permitida y el menú de dos opciones tras restaurar sesión. |
| Administración ingresa y recarga sus páginas | Acceso y funciones habituales conservados. |
| Sin sesión abre raíz o enlace público | Formulario sin menú privado, acceso a Iniciar sesión; enviar no crea cuenta ni sesión. |
| Cliente consulta mf_casos, mf_documentos o tablas de gestión directamente | Cero filas o permiso denegado; consulta mínima solo por RPC autorizada. |
| Celular 375 px | Tarjetas apiladas, descargas de ancho completo y menú existente con dos opciones. Requiere revisión visual en un teléfono real. |

```powershell
python -m unittest discover -s tests -p test_mis_documentos.py
python -m unittest discover -s tests
node tests/test_documentos_caso.mjs
```

La prueba SQL usa PGlite local ya instalado en `tmp/db-test/node_modules`; en una copia nueva instalarlo con `npm install --prefix tmp/db-test @electric-sql/pglite`. No es dependencia de la app.

Pendiente al entregar: aplicar la migración en Supabase y probar una descarga HTTP y la confirmación por correo reales. Las pruebas locales no verifican el reloj de expiración del Storage publicado ni sustituyen la revisión en un celular físico.
