# Prompt 37: Compartir compacto y atribución por enlace

## Revisión y alcance

Ya existían `canal_captacion`, su chip en el detalle, el filtro del registro,
QR PNG/SVG con qrcode y corrección alta, borrador con canal y copia con
respaldo manual. Se reutilizaron. No se crearon columnas duplicadas,
contadores de visitas ni mecanismos nuevos de autenticación.

Compartir ahora tiene una tarjeta con enlace, copia, acceso al formulario,
QR de 160 px, descarga PNG y botones de WhatsApp, Instagram, Facebook,
LinkedIn y Correo. Instagram copia el enlace y muestra dónde pegarlo;
no intenta publicar automáticamente. Los otros botones abren la herramienta
de compartir o redactar con su propio enlace. Abrirlos no envía solicitudes.

Tres textos editables aparecen en pestañas dentro de «Textos listos».
Se conservan los textos anteriores restantes, la descarga SVG, la elección
del canal del QR y el acceso a enlaces/contacto en «Más textos y opciones».
«Cómo publicarlo» queda plegado. El diseño normal se comprueba con estos
bloques cerrados; expandir los editores puede requerir desplazarse.

Si hay solicitudes atribuidas en los últimos 90 días, aparece su resumen y
un acceso al Dashboard. Se cuenta el día actual y los 89 anteriores, según
la fecha de Chile; no se incluyen registros futuros ni casos sin canal.
Sin datos se omite la línea. Se utiliza una lectura agrupada y con caché,
no una consulta por canal. La tarjeta de Hoy no añade consultas.

## Fuente única del enlace

`servicios/marca.py`, constante `URL_PUBLICA`, es la única dirección publicada
usada por Compartir, sus QR y el botón de copia de Hoy. No se repite el dominio
en otros archivos nuevos. Si cambia el despliegue, se cambia esa constante.
La función antigua `resolver_url` se conserva por compatibilidad, pero no
decide los enlaces nuevos. La configuración guardada no se borra: su antiguo
campo `url_publica` ya no determina estos enlaces.

Todos los enlaces nuevos incluyen `vista=solicitud` y el código corto `c`.
El enlace principal sin parámetros conserva su comportamiento previo para
Administración y cuentas; no se convierte en un enlace público por accidente.
Una URL con `c`, incluso sin `vista`, abre el formulario público, sin usar
sesión ni conceder permisos. El enlace público explícito continúa mostrando
el formulario aunque Administración tenga una sesión abierta.

| Código | Valor almacenado | Etiqueta visible |
|---|---|---|
| ig | instagram | Instagram |
| fb | facebook | Facebook |
| wa | whatsapp | WhatsApp |
| li | linkedin | LinkedIn |
| mail | correo | Correo |
| qr | qr | Código QR |
| web | sitio_web | Sitio web |
| directo, ausencia o desconocido | directo | Directo |

Los enlaces anteriores con `canal=instagram`, etc., continúan funcionando.
Si hay ambos parámetros, manda `c`. Los desconocidos se normalizan a Directo;
no se almacena su texto libre. Los valores históricos `otro` y NULL se
conservan sin inventar una atribución distinta.

El canal queda en el borrador durante los pasos y recargas. Un canal
explícito en el enlace tiene prioridad sobre el recuperado de un borrador
antiguo. Se mantiene separado de `origen`, identidad, correo y permisos.
No se guarda información del visitante para contar visitas.

## Dashboard y hoja de cálculo

Se añadió «Solicitudes por canal» usando las solicitudes que ya filtró el
Dashboard por fechas, el componente de tarjeta y el tema de gráficos
existentes. No cambia KPI ni cálculos anteriores. Sin solicitudes no se
presenta un gráfico vacío. El filtro y chip de los casos se reutilizan;
incluyen LinkedIn y Correo.

El campo está disponible para la futura exportación del Prompt 38. Este
trabajo no crea una hoja ni inicia una integración con Google por su cuenta.

## SQL: activar una vez

La columna ya existe por la migración de Compartir anterior. El SQL nuevo
amplía su restricción para LinkedIn y Correo y actualiza el normalizador
privado. No actualiza filas ni cambia las políticas o permisos existentes.

1. En Supabase, abre **SQL Editor → New query**.
2. Copia completo `supabase/migrations/202611050003_compartir_compacto.sql`
   y pulsa **Run**. Debe aparecer **Success. No rows returned**.
3. Envía una solicitud ficticia desde el enlace de LinkedIn o Correo.
   En el caso debe aparecer su canal y el origen «Formulario web».

Requiere el SQL anterior `202610240002_compartir_canales.sql`. No se ejecutó
en el proyecto real porque este entorno no dispone de acceso DDL al proyecto.
Debe aplicarse antes de usar los canales nuevos: la función anterior podría
clasificarlos como Otro.

Rollback: `supabase/rollback/202611050003_compartir_compacto.sql` restaura
la normalización anterior. Conserva la restricción ampliada para no invalidar
ni borrar casos de LinkedIn/Correo que ya hayan llegado.

## QR y copia

Se conserva qrcode, ya instalado; no hay dependencias nuevas de producción.
PNG de alta resolución, azul marino sobre blanco, margen y corrección H;
SVG sigue disponible en las opciones. Se genera por enlace y se conserva
en la caché existente de diez minutos, con máximo de 24 entradas.
No se superpone el logo: se prioriza la lectura del QR pequeño.

La copia usa Clipboard API y el respaldo existente; solo confirma
«Enlace copiado» si tuvo éxito. Cuando el navegador bloquea ambas opciones,
ofrece el texto para copiar manualmente. No se promete compatibilidad con
todos los navegadores internos sin probarlos físicamente.

## Pruebas ejecutadas

- `test_compartir.py`: 9 pruebas correctas, incluyendo generación PNG/SVG,
  lector independiente, enlaces, guardado de textos y permisos por rol.
- `test_compartir37.py`: 5 pruebas correctas. Códigos nuevos y anteriores,
  desconocido y ausencia, URL de cada botón, límites de 90 días en Chile,
  caché, lectura QR a 160 px, entrada pública y conservación durante pasos
  y recarga; el gráfico aparece y desaparece según el rango del Dashboard.
- `test_dashboard_sim*.py`: 5 pruebas correctas después de actualizar las
  expectativas a seis gráficos; indicadores y valores se conservan.
- Suite general: 291 pruebas ejecutadas; 289 correctas y dos expectativas
  antiguas de cinco gráficos. Ambas se actualizaron para el nuevo gráfico
  solicitado y se verificaron de nuevo en su grupo. La prueba extra del
  rango del gráfico se añadió y aprobó después de esa ejecución general.
  No se repitió la suite completa tras esos ajustes de pruebas.
- PostgreSQL efímero, `test_compartir37.mjs`: migraciones completas, todos
  los códigos, desconocido/sin canal, escritura pública e idempotencia,
  origen intacto, acceso denegado a gestión, fila histórica idéntica y
  rollback sin pérdida. Todos correctos; no se usan datos ni Supabase reales.
- `test_copiar34.mjs`: copia normal, respaldo y bloqueo correctos, sin
  confirmaciones falsas. Es una simulación de las APIs del navegador.
- Comprobación adicional local: los QR reales generados para QR y Directo
  se decodificaron a 160 px con zxing-cpp, sin visitar la app ni escribir datos.
  El lector de QA ya estaba instalado en las herramientas locales y no se
  agregó a los requisitos de producción.

## Comprobaciones físicas pendientes

El navegador automatizado devuelve «The browser access host is unavailable».
No se tomaron capturas. No se da por cumplido sin medir el requisito de cero
scroll en computador; depende también de la altura y del zoom, no solo del
ancho de 1280 px. Tampoco se afirma haber escaneado con un teléfono físico.

| Prueba manual | Qué debería verse |
|---|---|
| Administración → Compartir, 1280×900, bloques cerrados | Una tarjeta compacta y las opciones plegadas; revisar que no necesite scroll |
| Compartir, 375 px | Enlace completo o envuelto, botones táctiles, QR sin recortes y sin scroll horizontal |
| Copiar y pegar en una ventana privada | Formulario público sin login; confirmación de copia solo si funcionó |
| Botones por canal | URL propia; Instagram copia y pide pegar en biografía/historia; los demás preparan compartir/redactar |
| Enviar desde cada enlace | Chip del canal correspondiente; origen Formulario web; sin crear cuenta |
| Sin canal y con c desconocido | Caso Directo, sin almacenar el texto desconocido |
| Recargar a medio completar | Borrador y canal conservados; sin cambio de permisos |
| Descargar QR y escanear con celular | Abre el formulario, código de canal correcto, sin login |
| Datos del período en Dashboard | Gráfico por canal con sus conteos; cambiar fechas cambia los datos |
| Cliente o visitante intenta Compartir | No puede ver ni usar las herramientas administrativas |

## Entrega completa

Código: `app.py`, `paginas/compartir.py`, `paginas/dashboard.py`,
`servicios/compartir.py`, `servicios/marca.py`, `utils/canales.py`,
`utils/formulario_borrador.py` y `ui/tema.py`.
SQL y rollback indicados arriba. Pruebas nuevas y actualización de pruebas
anteriores de Compartir, Hoy y cantidad de gráficos. Este informe acompaña
el ZIP con los archivos completos del commit.
