# Compartir el formulario y conocer su canal

Se agregó **Compartir**, solo para Administración, en el grupo **GESTIÓN**. Hoy conserva todas sus tareas y agrega la tarjeta “Comparte tu formulario”. Se revisaron las páginas, componentes, configuración y migraciones existentes: no había un botón “Copiar enlace del formulario” ni un generador QR que reutilizar. Sí existía `copiar_mensaje`, que ahora también copia enlaces y textos, conservando sus usos anteriores.

## Activación

El código está preparado para Streamlit 1.65. La única dependencia nueva de producción es `qrcode[pil]>=8.2,<9`, declarada en `requirements.txt`. Streamlit Cloud la instala al desplegar; en local:

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

1. Si todavía no ejecutaste [el SQL del formulario unificado](../supabase/migrations/202610240001_formulario_unificado.sql), ejecútalo primero. Si ya lo ejecutaste, no lo repitas.
2. En **Supabase → SQL Editor → New query**, pega completo y ejecuta [202610240002_compartir_canales.sql](../supabase/migrations/202610240002_compartir_canales.sql). No lo pegues en medio de otra consulta. Requiere las migraciones previas del proyecto; se prueba junto al esquema real versionado.
3. En la app, entra como Administración y abre **Casos y cotizaciones → Configuración → Formulario: contacto, redes y privacidad**. Completa **URL pública de la aplicación**, con la dirección publicada de Streamlit. Se guarda como `mf_configuracion.datos.url_publica` en la fila `general`.
4. Abre **GESTIÓN → Compartir**. Si no hay URL guardada, se intenta detectar con `st.context.url`; se muestra un aviso y un botón para confirmarla y guardarla. Las direcciones locales/privadas se advierten y no se ofrecen como enlaces para clientes. Nunca se deduce la URL de `sitio_web`, porque ese dato corresponde al sitio de la empresa y podría ser otra página.
5. Revisa los textos, ajústalos y pulsa **Guardar textos para compartir**. Las cinco plantillas viven en `mf_configuracion.datos.compartir`. Las actualizaciones conservan el resto de la configuración y verifican su versión para evitar sobrescribir cambios de otra sesión.

No se puede aplicar DDL en Supabase desde la clave pública que utiliza la aplicación. El SQL debe ejecutarse con una cuenta autorizada en el panel; no se guardaron claves administrativas ni se ejecutaron envíos reales durante estas pruebas.

## Qué contiene

- Seis tarjetas: Instagram, Facebook, WhatsApp, Sitio web, Código QR y Directo. Cada una muestra el enlace, su uso, **Copiar** con confirmación y **Abrir** en otra pestaña. Copiar o abrir nunca publica nada automáticamente.
- Un selector de canal para ver y descargar su QR. PNG de alta resolución, 300 dpi, módulos azul marino `#0B2545`, fondo blanco, margen de cuatro módulos y corrección de errores H. SVG vectorial con los mismos módulos y colores. No se envía la URL a un servicio QR externo ni se superpone el logo al código.
- Textos para Instagram (biografía y publicación), Facebook, WhatsApp y sitio web. El editor conserva `{enlace}`; la vista previa y **Copiar texto** lo reemplazan por el enlace de su canal. No se evalúan otras llaves ni expresiones.
- Cuatro pasos breves en “Cómo publicarlo”.
- En Hoy, **Copiar enlace** usa Directo y **Ir a Compartir** abre la página. La tarjeta utiliza la configuración ya presente en la lectura de Hoy; no agrega otra consulta periódica.

La tarjeta PDF A5 es opcional y no se agregó en esta entrega. El SVG descargable permite imprimir el QR sin pérdida de resolución.

## Canales y compatibilidad

| Parámetro `canal` | Etiqueta guardada/mostrada |
|---|---|
| `instagram` | Instagram |
| `facebook` | Facebook |
| `whatsapp` | WhatsApp |
| `sitio_web` | Sitio web |
| `qr` | Código QR |
| `directo` o parámetro ausente | Directo en nuevas solicitudes externas |
| Cualquier otro valor | Otro |
| Casos anteriores y registros internos | Sin canal registrado (NULL) |

La columna nueva es **`mf_casos.canal_captacion`**. Es independiente del campo existente **`origen`**: un formulario público sigue teniendo origen “Formulario web”; una llamada o referido interno conserva su origen anterior. No se atribuye un canal inventado a los casos históricos ni se reemplazan estados o reglas comerciales.

El canal corresponde al primer enlace con que se inició el borrador. Se conserva entre pasos, cambios de página y recarga de la misma pestaña, si el navegador permite `sessionStorage`. Cambiar el parámetro mientras ya se está completando una solicitud no cambia su canal a mitad del envío. Al terminar, una solicitud nueva puede usar el enlace actual. No identifica automáticamente la aplicación desde la cual se abrió: reenviar un enlace de Instagram por WhatsApp mantiene Instagram.

La validación de Python y la función privada SQL usan la misma lista cerrada. Tanto `registrar_solicitud_publica` como `registrar_solicitud` pasan por el helper de inserción actualizado; el cliente autenticado mantiene su identidad forzada en DB. No se toma el modo ni el rol desde el canal. Los parámetros desconocidos, números o estructuras manipuladas no se guardan como etiquetas arbitrarias. Los enlaces generados eliminan parámetros y fragmentos de la URL base y solo incluyen `vista=solicitud` y `canal`, sin nombres, correos ni tokens.

Antes de activar este SQL, los envíos completos heredados sin canal explícito siguen funcionando. Los enlaces que sí contienen `canal` conservan el borrador y avisan si la actualización aún no está lista, para no perder silenciosamente su atribución. Después de ejecutar el SQL, el catálogo anuncia la versión 3; el caché puede tardar hasta 60 segundos en renovarse.

## Seguridad y Dashboard

La página comprueba `require_admin` al comienzo; también se registra siempre como ruta válida, pero el menú solo la ofrece a Administración. `mf_configuracion_compartir()` vuelve a comprobar `es_admin()` en DB y utiliza `SECURITY INVOKER`, respetando la RLS existente. Anónimos y clientes no pueden obtener ni editar esa configuración. No se amplió ninguna política de casos, tarifas, ventas o perfiles.

El detalle del caso muestra un chip **Canal · Instagram**, etc. Dashboard agrega **Solicitudes por canal**, con conteos enteros y porcentajes, dentro de una tarjeta del mismo estilo. Se usan los IDs de las solicitudes ya filtradas por fechas de creación en Chile, servicio y temática; no se modifican los indicadores ni se hace una consulta adicional. Los registros históricos e internos se incluyen como “Sin canal registrado” para que la suma siga coincidiendo con las nuevas solicitudes del período. Sin datos, aparece el estado vacío habitual.

## Pruebas y resultado esperado

Utiliza exclusivamente personas, empresas y correos ficticios en un entorno de prueba.

| Prueba | Qué debería verse |
|---|---|
| Administración entra | Compartir aparece en GESTIÓN; Hoy muestra “Comparte tu formulario”. Las páginas y funciones anteriores siguen disponibles. |
| Cliente abre `/compartir` o fuerza `?pagina=Compartir` | Llega a Nueva solicitud, sin herramientas de compartir, configuración ni descargas QR. |
| Visitante abre `/compartir` | Ve el login, sin datos administrativos ni diálogo Page not found. Los enlaces generados con `?vista=solicitud` sí abren el formulario público. |
| URL no configurada | Aviso de dirección detectada y opción para guardarla; si es local o no se detecta, se pide completar Configuración. |
| Copiar cada uno de los seis enlaces | Confirmación “Enlace copiado ✓”. Abrirlo en una ventana privada muestra el formulario público sin login, con su parámetro de canal. |
| Enviar desde cada canal | El caso muestra su canal; tras el refresco de Dashboard, el gráfico incorpora esa solicitud en el rango correspondiente. Origen sigue “Formulario web”. |
| `?canal=hola` o `?canal=admin&modo=interno` | El formulario sigue siendo público/cliente según sesión; el caso queda “Otro”, sin campos ni permisos internos. |
| Enlace sin `canal` | Nueva solicitud externa queda Directo. Un caso anterior sigue Sin canal registrado. |
| Pasar pasos, volver y recargar | Conserva datos y canal del borrador en la misma pestaña; no duplica un envío al reintentar con el mismo UUID/token. |
| Seleccionar cada canal del QR | Cambia la vista previa; PNG y SVG contienen el enlace exacto de ese canal. Un lector debe abrir el formulario sin login. |
| Editar un texto | La vista previa reemplaza `{enlace}` con el canal correcto. Copiar usa el texto editado; Guardar lo conserva al volver y no borra el emisor ni otras configuraciones. |
| Cambiar fechas, servicio o temática | El gráfico de canales refleja exactamente las solicitudes del mismo filtro, incluyendo Sin canal registrado. Si no hay solicitudes aparece un mensaje vacío, sin ejes. |
| Cortar red o conflicto de versión al guardar configuración | Mensaje amable, sin falsa confirmación; el texto escrito permanece en los widgets para reintentar. |

Comandos automáticos:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_compartir_sql.mjs
node tests/test_formulario_borrador.mjs
```

La prueba SQL utiliza PostgreSQL efímero PGlite (`tmp/db-test/node_modules/@electric-sql/pglite`), prueba seis canales más Otro, idempotencia, RLS, usuarios cliente y administrador, identidad, preservación de origen, lectura en vivo y reversión. No toca la base real. El lector independiente opcional de QA se instala con `python -m pip install --target tmp/qr-decoder zxing-cpp`; solo se usa para decodificar los seis PNG originales y a tamaño de vista previa. No es dependencia de producción.

Se revisan 375, 768 y 1440 px con Edge local y datos ficticios, más los botones reales del portapapeles. Esto no sustituye escanear con un celular físico: esa prueba y los navegadores internos de redes sociales quedan para la validación en dispositivo real.

## Reversión sin perder datos

Vuelve al código previo y ejecuta [202610240002_compartir_canales.sql de rollback](../supabase/rollback/202610240002_compartir_canales.sql). Restaura las funciones guardadas antes de esta actualización y elimina la RPC privada nueva. Conserva la columna de canal con todos sus datos, los textos, URL y demás configuración. No repitas la migración sobre los objetos preservados sin revisarlos.

Referencias verificadas: [context.url de Streamlit](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.context) y [qrcode: PNG, SVG, margen y corrección de errores](https://pypi.org/project/qrcode/).
