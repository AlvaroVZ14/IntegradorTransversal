# Documentos enviados por clientes — Prompt 29

## Activación en tu proyecto

1. En Supabase → SQL Editor → New query, pega **completo** `supabase/migrations/202611030002_documentos_cliente.sql` y ejecuta una vez. No reemplaces las migraciones anteriores ni desactives RLS. El script es transaccional y no borra archivos ni datos existentes.
2. Usa la versión actual de GitHub/Streamlit y recarga. Como cliente confirmado, abre **Mis documentos** y uno de tus casos: aparece **Enviar documentos**, incluso si Administración aún no ha subido nada.
3. Para avisos automáticos se reutiliza `[smtp]` de `st.secrets` y el `correo_contacto` ya guardado en `mf_configuracion`, registro `general`. El cliente nunca elige destinatario. Sin SMTP o sin ese correo, el archivo se guarda igualmente y Administración ve «Aviso por correo sin confirmar». No se añaden claves ni direcciones al repositorio.

Prerequisitos si instalas desde cero: migraciones generales y, en orden, `202611020002_documentos_caso.sql` (20), `202611020003_mis_documentos.sql` (21), `202611020004_redes_sociales.sql` (27), `202611030001_mi_perfil_cliente.sql` (28) y la nueva de arriba (29). En el proyecto publicado se verificaron señales de las anteriores; **solo queda aplicar la nueva**, salvo cambios posteriores en el proyecto. La app mantiene el resto de funciones aunque la nueva migración todavía no esté aplicada: no muestra el formulario de subida cliente hasta recibir su permiso en la consulta.

No hay dependencias nuevas. Se reutilizan pypdf, Pillow, docx, Supabase y el transporte SMTP TLS existente.

## Qué cambia

| Archivo completo | Cambio |
|---|---|
| `servicios/archivos_caso.py` | Tipos de cliente y conjunto común para reclasificación. Conserva la validación binaria ya existente. |
| `servicios/mis_documentos.py` | Subida verificada en el servidor, reserva recuperable, confirmación, eliminación en dos pasos y reserva de aviso. Mantiene descargas firmadas de 600 segundos consumidas por el servidor. |
| `servicios/documentos_caso.py` | Administración puede cambiar el tipo sin alterar la identidad del archivo. |
| `servicios/aviso_documento.py` | Aviso genérico a la socia, sin adjuntos, datos del caso, notas ni rutas. Un fallo no revierte la subida. |
| `paginas/mis_documentos.py` | Formulario por caso, lista de documentos propios, descarga y eliminación confirmada mientras el caso esté abierto. Sin nuevo ítem de menú. |
| `paginas/documentos_caso.py` | Etiqueta Enviado por el cliente, filtro por origen y cambio de tipo. Conserva carga, visibilidad, descargas, cotizaciones y eliminación anteriores. |
| `supabase/migrations/202611030002_documentos_cliente.sql` | Origen, tipos, rutas, cupos, RPC y políticas de Storage. |
| `tests/test_documentos_cliente.py`, `tests/test_documentos_cliente.mjs` | Pruebas ficticias de interfaz, binarios, reintentos, SMTP y permisos reales de PostgreSQL. |
| `README.md`, esta guía | Activación, archivos, pruebas y límites. |

El autor real sigue en `subido_por`, asignado desde Auth, nunca desde un dato elegido en pantalla. Los documentos anteriores conservan `origen='socia'` y sus rutas. Los nuevos del cliente usan `{caso_id}/cliente/{documento_id}.ext`. Tanto la ruta como el nombre descargable son identificadores opacos; no se guarda el nombre original. PDF, DOCX, XLSX, PNG, JPG/JPEG y WebP están admitidos; DOC/XLS antiguos, ejecutables, SVG, ZIP y formatos con macros no se admiten.

## Límites y permisos

- Cliente con correo **confirmado en Auth**, rol cliente y coincidencia con el correo del caso o con un correo adicional autorizado por Administración. El correo escrito en un parámetro nunca concede acceso.
- Máximo **10 MiB** por archivo (10 × 1024² bytes), **20 archivos activos por caso**, sumando ambos orígenes y las cotizaciones incorporadas. Los pendientes y los que están eliminándose ocupan cupo hasta finalizar su borrado; los casos antiguos con más de 20 archivos se conservan, pero no admiten nuevos mientras no se libere espacio.
- Máximo **20 reservas nuevas por cuenta en los últimos 60 minutos**, contando también las eliminadas y las subidas pendientes. Reintentar el mismo ID no consume otro cupo. Bloqueo del caso y bloqueo por cuenta serializan las comprobaciones en PostgreSQL.
- Cerrada corresponde al valor histórico `Finalizado` en la base. El cliente sigue descargando archivos disponibles, pero no puede subir ni eliminar. Administración conserva su gestión de documentos. No se modifican estados ni permisos de otros módulos.
- El cliente no obtiene SELECT/UPDATE/DELETE directos de `mf_documentos` ni de las tablas de gestión: usa RPC con controles explícitos y datos mínimos. La consulta omite rutas, notas internas, montos y estados internos; devuelve solo un permiso booleano para enviar documentos.
- Puede consultar documentos visibles de sus casos y los que él envió, aunque estos últimos no estén marcados como visibles. Otro contacto del mismo caso no ve su archivo privado salvo que Administración active su visibilidad. No puede eliminar archivos ajenos.
- Storage permanece privado con políticas restrictivas, incluso ante políticas permisivas ajenas. No se permite sobreescribir archivos del cliente. Las descargas verifican permisos al pulsar, firman por 600 segundos y entregan los bytes a través de Streamlit: la pantalla no muestra rutas ni enlaces firmados. Un archivo ya descargado no puede retirarse del computador del destinatario; un enlace firmado emitido sigue siendo válido hasta vencer.
- Borrado recuperable: primero marca `eliminando`, después elimina el objeto de Storage y finalmente conserva un registro `eliminado`. No se libera cupo si todavía existe el objeto. Si el caso se cierra durante una operación, Administración puede terminarla.
- La selección se conserva en la página ante un fallo de conexión y el reintento reconoce una subida ya completada. El archivo seleccionado no se respalda en localStorage ni en el repositorio; si se cierra o recarga la pestaña antes de completar la subida, hay que volver a seleccionarlo.
- Administración ve los archivos al abrir la pestaña Documentos del caso. No se fuerza un refresco del detalle durante una edición, para respetar el comportamiento anterior.

## Antivirus: alcance real

Se valida extensión, firma/formato de los bytes, tamaño, integridad de imágenes y estructura OOXML en el **servidor de la app**, antes de reservar o subir. Los documentos nunca se ejecutan ni se previsualizan. Se rechazan archivos vacíos, formatos falseados, macros VBA detectadas en OOXML, archivos dañados y paquetes con expansión excesiva.

**Esto no es un antivirus ni certifica que un PDF o documento sea inocuo.** No se instaló un motor ClamAV ni un servicio externo de análisis. La documentación consultada no ofrece una garantía de análisis antivirus incluido con el plan gratuito; tampoco debe suponerse que cambiar a un plan de pago lo añade automáticamente. La [discusión de Supabase sobre análisis de archivos](https://github.com/orgs/supabase/discussions/23645) propone un escáner adicional; [ClamAV](https://docs.clamav.net/manual/Usage/Scanning.html) necesita motor y firmas actualizadas.

Storage controla MIME declarado, tamaño, rutas y permisos, pero PostgreSQL no inspecciona el contenido binario del objeto. Alguien que use directamente la API con su JWT podría saltarse la inspección de bytes de la interfaz; los permisos y cupos siguen aplicándose. Para una garantía también frente a ese flujo hace falta una cuarentena y un proceso de validación/escaneo de confianza, con credenciales de servidor, antes de habilitar la descarga. No se afirma tener esa garantía en esta entrega.

Mitigaciones actuales: cuentas confirmadas, lista cerrada de formatos, cupos en base de datos, bucket privado, nombres opacos, no ejecución/previsualización y enlaces breves. Recomendación: abrir descargas con antivirus del equipo y vista protegida de Office. No enviar nóminas ni documentos privados a analizadores públicos de archivos. Una ampliación puede incorporar cuarentena y ClamAV en infraestructura propia; requiere evaluar recursos y mantenimiento, no prometerlo gratis en Community Cloud.

## Espacio de Supabase

La [documentación oficial de Storage Size](https://supabase.com/docs/guides/platform/manage-your-usage/storage-size), consultada para esta entrega, indica **1 GB** incluido en Free. En Supabase abre **Usage de la organización → Storage Size**, y filtra por proyecto. Es una cuota compartida, no 1 GB por caso. Veinte archivos de 10 MiB pueden sumar 200 MiB en un solo caso; los límites por caso/cuenta no sustituyen el control del total.

Para consultar tamaños agregados, ejecuta como administradora en SQL Editor (solo lectura):

```sql
select bucket_id, count(*) as archivos,
       round(coalesce(sum((metadata->>'size')::bigint),0)/1048576.0,2) as mib
from storage.objects
group by bucket_id
order by mib desc;
```

Elimina archivos que ya no necesites desde la app, tras respaldarlos de forma privada si corresponde. No borres filas directamente en `storage.objects`: la eliminación del archivo debe pasar por Storage. Los respaldos CSV de tablas de gestión no equivalen a un respaldo de los bytes de Storage.

## Pruebas ejecutadas y qué deberías ver

Las pruebas automáticas usan cuentas y documentos ficticios, repositorios simulados, AppTest de Streamlit y PostgreSQL efímero con RLS. Storage se modela mediante sus tablas y un servicio simulado; no se enviaron correos ni se crearon archivos en el proyecto real. No son pruebas visuales en dispositivos físicos.

Resultado de esta entrega: **239 pruebas Python aprobadas**; también aprobadas las seis suites SQL indicadas abajo (el formulario unificado se ejecuta con y sin su migración pública anterior). Incluyen los prompts 20, 21, 27 y 28 y la regresión de módulos anteriores.

| Prueba | Resultado comprobado / qué ver al repetirla |
|---|---|
| A sube PDF a su caso, aunque no tenga documentos previos | Se guarda como cliente, con su autor real y nombre opaco; aparece «Recibimos tu documento. La socia comunitaria lo verá en tu caso.» y Documentos que enviaste. |
| Administración abre Documentos | Ve el archivo, etiqueta Enviado por el cliente; puede filtrar, reclasificar y eliminar con confirmación. |
| Archivo mayor de 10 MB | La validación del servidor lo rechaza antes de reservar o subir; PostgreSQL también rechaza una reserva fuera del máximo. |
| EXE o contenido que no es PDF con extensión .pdf | Error claro; no se sube ni reserva. MIME/extensión incompatibles también se rechazan en RPC. |
| B consulta, firma, confirma, borra o intenta subir al caso de A | Permiso denegado o sin resultados; no ve documentos ni casos de A. |
| Correo sin confirmar | No lista casos ni puede reservar/subir, aun con JWT simulado. |
| Sin sesión | RPC denegada y Storage sin objetos accesibles, incluso con una política permisiva adicional de prueba. |
| Documento oculto de la socia | No aparece en la consulta ni tiene descriptor de descarga para el cliente. |
| Documento que A envió y no está marcado visible | A puede descargarlo; B no. La visibilidad no revoca al autor el acceso a su propio envío. |
| Caso Cerrada | Desaparecen subida y eliminación; descarga sigue disponible. RPC también bloquea cambios. |
| 21.º archivo del caso / 21.ª reserva por hora | Rechazo con aviso de cupo; el resto de la app continúa disponible. |
| Se pierde la respuesta tras subir | Reintentar el mismo lote confirma el objeto existente sin duplicarlo. |
| Falla el borrado de Storage | Queda eliminando y puede completarse; no libera cupo antes de borrar el objeto. |
| SMTP falla | Documento disponible y aviso incierto; no se reenvía automáticamente para evitar duplicados. |

```powershell
python -m unittest discover -s tests -p test_documentos_cliente.py -v
python -m unittest discover -s tests
node tests/test_documentos_cliente.mjs
node tests/test_documentos_caso.mjs
node tests/test_mi_perfil.mjs
node tests/test_formulario_unificado_sql.mjs
node tests/test_publico_sql.mjs
node tests/test_en_vivo_sql.mjs
```

Las pruebas SQL necesitan el entorno PGlite de pruebas ya utilizado en el proyecto (`tmp/db-test/node_modules/@electric-sql/pglite`); no es una dependencia de producción.

## Verificación de los prompts anteriores

| Función previa | Comprobación |
|---|---|
| 20: documentos de Administración | Código presente, pestaña conservada, validación/subida/avisos/cotización privada y pruebas de RLS anteriores pasan. La tabla existe en Supabase publicado. |
| 21: Solicitar servicio y Mis documentos | Rutas y guardias se conservan; aislamiento por correo confirmado, alta posterior, contactos adicionales y visibilidad cubiertos por SQL y AppTest. La RPC publicada existe y rechaza anónimos (42501). |
| 27: redes sociales y ficha | Formulario compartido, edición del caso y ficha PDF presentes; sus pruebas se incluyen en la suite Python. El catálogo público publicado responde versión 5, posterior a esta migración. |
| 28: Mi perfil | Tarjeta dentro de Mis documentos conservada, sin tercera sección; lectura, escritura acotada, sincronización y A/B cubiertos por sus pruebas. Su RPC publicada existe y rechaza anónimos (42501). |
| Cotizaciones, datos de pago, Hoy, Dashboard, reportes, compartir, entradas y sesión | Se conservan sus módulos y se ejecuta la suite de regresión Python; no se modifican cálculos, permisos ni campos de esos módulos. |
| 29 en Supabase publicado antes de activar | La consulta sin filas de la columna origen devolvió 42703: aún falta esta migración. No se aplicó DDL desde esta sesión porque solo hay una clave pública, sin acceso administrativo. |

La comprobación remota fue de solo lectura: catálogo público versión 5 y enlaces de acceso/formulario HTTP 200. Esto confirma disponibilidad y señales de esquema, **no equivale a probar todos los flujos con usuarios reales en producción**. Tras ejecutar el SQL, repite el recorrido A → subir PDF → Administración → Documentos, y el intento de B con datos ficticios en la app publicada.
