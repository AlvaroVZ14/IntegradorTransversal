# Google Sheets: copia de informes (Prompt 38)

## Qué se encontró y qué cambia

Los prompts 37 y 41 ya estaban implementados: canales en `mf_casos.canal_captacion` y catálogo en `ui/estados.py`. No había librerías ni conexión con Google. La app usa Supabase con su clave pública en secretos y el JWT de cada usuario; no se reutiliza esa sesión para exportar ni se amplían sus permisos.

Se añaden `gspread` y `google-auth` para Sheets y `psycopg[binary]` para leer un esquema PostgreSQL privado. Preferimos un rol limitado (`mfy_hoja`) a una clave `service_role`: solo permite leer las tres vistas sanitizadas y ejecutar las funciones acotadas de la cola. No permite leer tablas comerciales ni escribir casos. Las credenciales solo se abren en `servicios/hoja_sync.py`, del lado servidor.

Las escrituras comerciales siguen confirmándose en Supabase. Sus triggers dejan una tarea en la misma transacción. Un trabajador independiente agrupa cambios durante siete segundos y actualiza la copia; Google nunca participa en el guardado. Al iniciar Administración se atiende lo pendiente y se revisa periódicamente. El candado de PostgreSQL también excluye otras instancias y el proceso nocturno. Los rangos son absolutos, con claves estables; repetir envíos o reconstrucciones no duplica filas. Un cambio posterior al lote sigue pendiente hasta su siguiente envío. Borrar una cotización o anular una venta retira la fila de la copia.

Las tres pestañas de datos son de lectura para las personas: una reconstrucción reemplaza sus cambios manuales. Resumen conserva sus fórmulas; Leyenda se regenera desde el contrato. Registro conserva un máximo de 500 entradas. Los errores se registran también en PostgreSQL, aunque Google no esté disponible.

## Activación por el equipo técnico (una vez)

1. **Google Cloud:** abre https://console.cloud.google.com/, crea un proyecto llamado Mente y Futuro y activa **Google Sheets API** en APIs y servicios → Biblioteca. No hace falta activar facturación para esta integración. Deberías ver la API habilitada.
2. En **IAM y administración → Cuentas de servicio**, crea una cuenta para informes, sin asignarle roles generales del proyecto. En sus claves crea una llave JSON y guárdala en un lugar privado. No la subas al repositorio ni la envíes por chat. Deberías ver un correo terminado en `iam.gserviceaccount.com`.
3. Abre la hoja **Mente y Futuro · Datos**, ya creada con Casos, Cotizaciones, Ventas, Resumen, Leyenda y Registro. Compártela como Editor con ese correo y con la socia. Mantén **Acceso general: Restringido**; no publiques la hoja. Si usas otra cuenta de Drive, crea una hoja vacía con ese nombre en esa cuenta.
4. En Supabase, ejecuta `supabase/migrations/202611050004_hoja_reportes.sql` **después de las migraciones anteriores**. Comprueba que `reportes` NO figura en los esquemas expuestos de la API. La migración no modifica los datos comerciales existentes. Después, solo en el editor SQL privado, habilita el inicio de sesión del rol con `ALTER ROLE mfy_hoja LOGIN PASSWORD 'UNA_CONTRASEÑA_NUEVA_GENERADA_POR_TI';`. Sustituye el ejemplo por una contraseña fuerte; no guardes la sentencia real en archivos. Copia la conexión de **Session pooler, puerto 5432**, usando como usuario `mfy_hoja.REFERENCIA_DEL_PROYECTO`. Codifica los caracteres especiales de la contraseña en la URL. No uses la contraseña de postgres ni `service_role`.
5. En **Streamlit → Manage app → Settings → Secrets**, conserva los secretos actuales y agrega el bloque `[hoja]` del `secrets.toml.example`: `activada=true`, conexión limitada, ID y URL de la hoja. Dentro de `[hoja.google]` copia los valores del JSON. `private_key` debe conservar sus saltos de línea. No pegues secretos en el código. Deberías ver la app iniciando normalmente; si faltan credenciales la app sigue guardando y la copia queda pendiente.
6. En **GitHub → Settings → Secrets and variables → Actions**, crea los secretos `HOJA_DATABASE_URL`, `HOJA_ID`, `HOJA_URL`, `HOJA_GOOGLE_JSON` (JSON completo) y la **variable** `HOJA_SYNC_ENABLED=true`. En **Actions → Sincronizar hoja de informes → Run workflow**, ejecútalo una vez. Debe finalizar en verde y aparecer datos, formatos, leyenda y fórmulas en la hoja. También puedes ejecutar `python scripts/preparar_hoja.py` en un equipo técnico con esas variables de entorno: prepara y copia los datos; repetirlo es seguro.
7. En Administración, abre **Mi cuenta → Estado de la hoja**: debe mostrar **Al día**, Abrir hoja y Sincronizar ahora. La reconstrucción completa requiere marcar la confirmación. Guarda un caso ficticio: debería aparecer en menos de un minuto en condiciones normales. No borres ni vuelvas a crear las cuentas de servicio o sus claves después de activarlas; para rotar una llave, actualiza ambos destinos antes de revocar la anterior.

La hoja ya está creada, pero la sincronización NO queda activada hasta completar Cloud, SQL y secretos. La conexión de Drive usada para crearla no equivale a una cuenta de servicio para la app.

## Formato, privacidad y significado de los datos

`servicios/hoja_columnas.py` es el contrato exacto de columnas. Las vistas tienen listas explícitas; el procesador rechaza columnas adicionales. No se exportan JSON de cotizaciones, RUT, correo, teléfono, contacto, redes, notas, datos bancarios ni documentos. Empresa conserva la razón social declarada; si coincide con la persona de contacto o está vacía, se sustituye por Cliente particular. Revisa la calidad del campo empresa si allí se ingresaron datos personales incorrectamente.

Fechas PostgreSQL reales → fechas numéricas de Sheets, formato `dd/mm/yyyy`, región Chile y zona America/Santiago. Montos son números, no cadenas con `$`. Los textos se escriben con `RAW`: un valor que comienza con `=` no ejecuta una fórmula. Años, meses, trimestres y semestres siguen el calendario chileno. Los colores de estado vienen de `ui/estados.py`; los nombres de estados se traducen sin cambiar los almacenados en el sistema.

- `monto_pendiente` sigue el indicador actual: monto completo de una venta que no está Pagada. La app no almacena el importe del abono, por lo que NO es el saldo exacto.
- `fecha_ultimo_cambio` comienza con `updated_at` disponible de cada caso existente. Desde la instalación se registra cada cambio de estado; no se inventa historia anterior. `dias_en_estado` se recalcula desde esa fecha.
- `fecha_envio` solo aparece cuando existe evidencia de envío; no se supone que descargar equivale a enviar.
- Cotizaciones usan base antes de descuento/IVA, porcentaje y total ya calculados por la app. No se cambia el cálculo comercial. Las anulaciones de ventas se excluyen.
- `registrado_por` solo indica Cliente o Administración. Motivo de rechazo exporta la categoría, nunca la nota libre.
- Leyenda explica cada columna, estado y color. Resumen incluye ventas por mes, trimestre y temática, y conteo de solicitudes por mes. Inicializa fórmulas solo si Resumen está vacío: nunca reemplaza uno ya personalizado.

## Cuotas, programación y límites reales

Según la [documentación de Sheets](https://developers.google.com/workspace/sheets/api/limits), el límite es de 60 lecturas y 60 escrituras por minuto por usuario/proyecto, y 300 por proyecto. Se agrupan rangos, se limita el tamaño de cada envío a menos de 900 KB y se espacian las escrituras grandes. Los errores 429 esperan al menos un minuto; errores temporales usan espera creciente. Errores permanentes quedan pendientes y se reintentan después, sin imprimir respuestas de proveedores o secretos.

El control nocturno corre a las **07:17 UTC** (03:17 o 04:17 en Chile) y puede iniciarse manualmente. [GitHub advierte](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) que los cron pueden retrasarse, solo ejecutan en la rama predeterminada y se desactivan en repositorios públicos con 60 días sin actividad. Revisa Actions mensualmente; si aparece desactivado, pulsa **Enable workflow** y ejecútalo. Esto no garantiza que Streamlit permanezca despierto ni que Supabase nunca se pause. Mientras la app está detenida, el control nocturno recupera cambios cuando pueda conectarse; no se promete sincronización en un minuto en ese escenario.

Hoy muestra un aviso si la integración está activa y lleva más de 24 horas sin éxito. Los registros previos permanecen en Supabase; Sheets no es el respaldo principal ni reemplaza la base.

El esquema privado no debe añadirse a la [lista de esquemas expuestos](https://supabase.com/docs/guides/api/using-custom-schemas). El SQL revoca permisos para anon/authenticated/service_role y usa RLS sin políticas en cola y estado. El rol dedicado solo obtiene las tres vistas y funciones concretas; no se concede acceso al navegador.

## Pruebas y qué debería verse

Pruebas automatizadas locales, con datos ficticios y PostgreSQL efímero:

| Prueba | Resultado esperado |
|---|---|
| Crear y editar caso | Una fila por código, valores nuevos reemplazan anteriores. |
| Generar cotización y registrar venta | Las pestañas correspondientes contienen importes numéricos y fechas reales. |
| Repetir envío y reconstruir dos veces | Mismas filas, sin duplicados; Resumen intacto. |
| Eliminar cotización o anular venta | Desaparece de su copia; la fila del caso se actualiza. |
| Google caído / conexión rechazada | Mensaje amable, cola pendiente, guardado comercial conservado. |
| Cuota 429 | Espera creciente, no pierde el lote ni expone el error original. |
| Cambio mientras otro lote se envía | Sigue pendiente para el próximo lote, sin reconocerlo antes de tiempo. |
| Cliente o anónimo intenta leer reportes | Error de permisos en vistas, cola y estado. |
| Rol de informes intenta leer mf_casos | Error de permisos. Solo lee vistas sanitizadas. |
| Formato y fórmulas | Fechas/moneda, encabezados protegidos y congelados; Resumen no se sobrescribe. |

Comandos: `python -m unittest discover -s tests -p test_hoja38.py` y `node tests/test_hoja38.mjs`. El segundo requiere el PGlite temporal utilizado por las otras pruebas SQL del proyecto. No se conecta a Supabase real.

**Pendientes de activación real:** ejecutar el workflow con la cuenta de servicio y una hoja de prueba; guardar/editar/anular desde la app; revocar temporalmente acceso a esa hoja y restituirlo; verificar reintento, fórmulas regionales y tiempo real menor a un minuto. Las pruebas locales usan un doble de Sheets; no son una certificación de red ni de credenciales reales. La hoja vacía creada en Drive no tiene datos de clientes.

## Detener o revertir

Desactiva `activada` en Streamlit y `HOJA_SYNC_ENABLED` en GitHub. Si necesitas detener también los triggers, ejecuta `supabase/rollback/202611050004_hoja_reportes.sql`: conserva todas las tablas comerciales y la cola, deshabilita el acceso del rol y los triggers nuevos. No publica datos ni elimina la copia de Google. Para reactivar después del rollback, el equipo técnico debe recrear los cuatro triggers de la migración, restaurar los permisos explícitos del rol y reactivar su LOGIN; no se debe repetir la migración entera porque el esquema ya existe.
