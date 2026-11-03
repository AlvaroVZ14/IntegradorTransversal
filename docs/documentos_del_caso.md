# Documentos del caso

Prompt 20. Nueva pestaña administrativa Documentos en el detalle del caso, junto a Datos y seguimiento, Cotizaciones y Venta. La pantalla de cliente Mis documentos corresponde al Prompt 21 y no se incorpora aquí.

Actualización posterior: [Cuenta de cliente y Mis documentos](cuenta_cliente_documentos.md) implementa el Prompt 21. Después de aplicar su migración, el cliente usa las RPC limitadas; SELECT directo de `mf_documentos` devuelve cero filas para impedir que reciba notas o rutas internas.

## Activación

1. Ejecutar completo `supabase/migrations/202611020002_documentos_caso.sql` en Supabase → SQL Editor con la cuenta que administra el proyecto, después de las migraciones existentes. La migración crea el bucket privado y las políticas; no hace falta crearlo público ni cambiar permisos desde Storage.
2. Instalar dependencias con `python -m pip install -r requirements.txt`. Se añade `pypdf>=6.4,<7` para comprobar archivos PDF. Pillow y las demás dependencias ya se usaban en el proyecto.
3. Abrir un caso como Administración → Documentos. Sin la migración se muestra el archivo SQL que falta; las otras pestañas y la generación de cotizaciones siguen funcionando.
4. Los avisos reutilizan `[smtp]` de `st.secrets` y el transporte TLS del envío existente. Si SMTP no está habilitado, la subida se conserva y se avisa del fallo. Los valores reales no se guardan en el código.

No se ejecutó SQL ni se subieron archivos en Supabase publicado desde esta sesión: no hay conexión administrativa disponible. Las pruebas se hicieron en PostgreSQL efímero y con Storage/SMTP simulados.

## Datos y visibilidad

La tabla real se llama **mf_documentos**, siguiendo el prefijo del proyecto. Incluye todos los campos solicitados: id, caso_id, tipo, nombre, archivo_path, tamano, tipo_mime, visible_cliente, subido_por, fecha_subida y nota.

| Tipo | Visibilidad inicial |
|---|---|
| Lista de asistencia, Informe, Certificado, Material | Visible para el cliente |
| Cotización, Otro | Solo Administración |

Al subir se puede dejar Según el tipo o elegir una visibilidad explícita. Cada documento disponible tiene su interruptor Visible para el cliente. El valor inicial también se aplica en el trigger SQL; no depende únicamente del formulario.

Se añaden tres campos técnicos para mantener consistencia:

- `estado_archivo`: pendiente, disponible, eliminando o eliminado. Un archivo pendiente o en eliminación nunca se devuelve a clientes.
- `cotizacion_id`: vínculo único con la versión de cotización, para no duplicar sus PDF automáticos.
- `aviso_estado`: reserva única y resultado de correo, para no reenviar automáticamente un aviso incierto.

El archivo se elimina mediante la API de Storage. Queda una marca de metadatos con estado eliminado, oculta del listado y del cliente, sin nota ni archivo; evita que una cotización eliminada reaparezca al sincronizar. No borrar filas de `storage.objects` manualmente por SQL: eso no es el procedimiento de eliminación física del archivo.

Las cotizaciones nuevas generan automáticamente una copia PDF privada en Documentos, con visibilidad apagada. Las versiones anteriores se incorporan al abrir la pestaña. Un fallo de esta copia no duplica ni invalida la cotización: su descarga original sigue en Cotizaciones. Las copias pendientes se reintentan al abrir Documentos. Eliminar esa copia no elimina la versión original ni su historial.

## Seguridad

Bucket **documentos-casos**, `public=false`, límite de 10 MiB por archivo y lista de MIME permitidos. Rutas `UUID-del-caso/UUID-del-documento.ext`. El nombre original se utiliza solo para identificar el formato y nunca se conserva en la tabla, ruta, descarga, correo ni repositorio. El servidor SQL también fuerza un nombre genérico con UUID.

Formatos: PDF, DOCX, XLSX, PNG, JPG/JPEG y WebP. No se aceptan SVG, HTML, archivos con macros ni formatos antiguos DOC/XLS. Se comprueba contenido además de extensión: lector PDF, estructura OOXML y comprobación de imagen con Pillow. Los ZIP de Office tienen límites de entradas/descompresión y las imágenes un máximo de 20 millones de píxeles para limitar memoria. El contenido se procesa en memoria; la app no escribe archivos subidos en el disco del repositorio.

Administración puede leer y escribir todos los documentos. Un cliente solo puede leer metadatos y objetos disponibles, visibles y correspondientes a sus casos. La pertenencia se verifica con `mf_casos.cliente_id=auth.uid()` o, si el caso aún no tiene cliente_id, con el correo **verificado en auth.users**, además del rol cliente. Un correo en el perfil editable, un parámetro de URL o user_metadata no concede acceso. Un caso vinculado explícitamente a otra cuenta no se recupera por coincidencia de correo.

No se abren las políticas de las tablas de casos, cotizaciones, ventas ni tarifas. Las funciones auxiliares leen únicamente la pertenencia necesaria; la consulta de destinatarios requiere Administración. El cliente no puede subir, cambiar visibilidad ni eliminar. Las políticas restrictivas del bucket evitan que otra política permisiva general de Storage exponga este bucket; no cambian el acceso de otros buckets.

Los enlaces se firman con el JWT de la persona, duran **600 segundos** y se generan al pulsar Preparar descarga. Nunca se usa service_role ni `get_public_url`. En la interfaz se retira el enlace tras unos nueve minutos al volver a renderizar, dejando margen para regenerarlo.

**Alcance exacto del enlace firmado:** sin sesión y sin enlace válido, no se autoriza descargar. Quien tenga un enlace firmado válido puede descargar durante su vigencia, incluso sin sesión; es el funcionamiento de un enlace temporal. Apagar la visibilidad impide nuevas lecturas y firmas, pero no revoca inmediatamente un enlace ya emitido. Consulte [descargas de Supabase](https://supabase.com/docs/guides/storage/serving/downloads), [buckets privados](https://supabase.com/docs/guides/storage/buckets/fundamentals) y [control de acceso](https://supabase.com/docs/guides/storage/security/access-control).

## Reintentos y correo

Primero se registra una fila pendiente, luego el archivo y finalmente se confirma su tamaño/MIME contra Storage. No se publica al cliente antes de confirmar el archivo completo. Un reintento del mismo envío reconoce la fila y el objeto existentes sin sobrescribir ni crear otra copia.

Para eliminar, se marca primero eliminando y se oculta; después se elimina el objeto y se confirma la marca final. Si se interrumpe tras iniciar ese proceso, queda oculto y se puede completar la eliminación con confirmación. Si no se logró contactar al servidor para iniciarlo, la interfaz no afirma que ya fue eliminado u ocultado: pide revisar su estado.

Avisar al cliente por correo parte activado. Al pulsar Subir documentos, cada archivo visible puede enviar un aviso breve, sin adjuntos, nombre de archivo, nota, datos del caso ni enlace firmado. Se reutiliza el transporte SMTP existente con TLS. La reserva de un intento evita reenvíos automáticos: un resultado incierto se conserva para revisión. SMTP aceptado no prueba entrega al buzón. No se envía correo al incorporar automáticamente cotizaciones privadas ni por cambiar el interruptor de visibilidad.

La subida indica si ya hay una cuenta cliente verificada o si el destinatario debe crearla con ese correo. Es un estado de disponibilidad de permisos. La interfaz lo aclara: **Mis documentos se incorpora en el Prompt 21**; en esta entrega la navegación del cliente sigue siendo Nueva solicitud. El acceso por API ya está limitado y preparado para esa pantalla.

## Pruebas realizadas

Resultado: **214 pruebas Python aprobadas**, más la prueba SQL de documentos y Storage. Las siete pruebas específicas del módulo también pasaron por separado.

`tests/test_documentos_caso.py` usa archivos ficticios y Storage/SMTP simulados. Comprueba:

- Tipos reales, archivos vacíos, tamaño, PDF falso, Office con estructura incorrecta e imagen con extensión incorrecta.
- Subida interrumpida después de guardar el objeto: reintento sin duplicado ni sobrescritura.
- Nombres y rutas sin nombre/apellido del archivo de entrada.
- Lista de asistencia visible inicialmente, cambio de visibilidad y firma de 600 segundos.
- Eliminación con fallo y reintento, manteniendo el documento oculto tras iniciarse la operación.
- PDF de cotización privado, único por versión y sin reaparecer al eliminar su copia.
- Correo genérico sin adjuntos; fallo SMTP que conserva el archivo; reserva que impide repetir el aviso.
- Formulario administrativo, cuenta pendiente y guardia de rol de la pestaña.

`tests/test_documentos_caso.mjs` ejecuta SQL real en PostgreSQL efímero, con un modelo local de las tablas de Storage. Verifica admin, cliente propio, otro cliente, correo no confirmado, cuenta confirmada después, caso vinculado a otra persona, documento oculto y acceso anónimo. También verifica que una política permisiva ajena no exponga los objetos del bucket, que otros buckets conserven su acceso, que un cliente no pueda escribir, que los casos sigan bloqueados y que los avisos y la eliminación sean idempotentes.

Esta prueba valida RLS de metadatos/objetos; **no sustituye una prueba HTTP contra el Storage publicado** ni prueba su reloj real de expiración. No se enviaron correos ni archivos reales.

```powershell
python -m unittest discover -s tests -p 'test_documentos_caso.py' -q
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_documentos_caso.mjs
```

La prueba SQL usa la instalación local de PGlite en `tmp/db-test/node_modules`, como las pruebas SQL existentes; no es dependencia del despliegue.

## Prueba manual en el proyecto publicado

1. Aplicar la migración y entrar como Administración. Abrir un caso ficticio → Documentos.
2. Subir una lista PDF sin datos reales, tipo Lista de asistencia y visibilidad Según el tipo. Debe aparecer disponible, con interruptor activado y nombre genérico. Si falla SMTP, el documento debe seguir ahí.
3. Preparar descarga: el enlace debe descargar el archivo. Esperar más de diez minutos: el enlace anterior debe dejar de servir y Preparar descarga debe generar otro.
4. En una ventana privada sin sesión, probar la ruta pública `/storage/v1/object/public/documentos-casos/<ruta>` y la ruta autenticada sin cabecera JWT: deben devolver error de autorización/no encontrado, sin archivo. No usar como prueba anónima un enlace firmado todavía válido: ese enlace sí concede acceso temporal.
5. Con Prompt 21 aplicado, entrar como cliente confirmado a Mis documentos: debe aparecer su archivo visible y poder descargarlo. SELECT directo de `mf_documentos` devuelve cero filas. Otro cliente o una cuenta sin confirmar no deben ver ni descargar ese archivo.
6. Apagar visibilidad: la nueva consulta/firma del cliente debe quedar bloqueada. Una firma anterior puede durar el tiempo que le reste.
7. Confirmar y eliminar: desaparece de la lista y el archivo se elimina de Storage. Reabrir no debe regenerar una cotización cuya copia se eliminó.
8. Generar una cotización: debe aparecer en Documentos como Cotización, con visibilidad apagada y su descarga original conservada en Cotizaciones.

## Archivos completos

`supabase/migrations/202611020002_documentos_caso.sql`, `servicios/archivos_caso.py`, `servicios/documentos_caso.py`, `servicios/aviso_documento.py`, `servicios/envio_cotizacion.py`, `paginas/documentos_caso.py`, `paginas/gestion.py`, `paginas/cotizador.py`, `requirements.txt`, `tests/test_documentos_caso.py`, `tests/test_documentos_caso.mjs` y esta guía.
