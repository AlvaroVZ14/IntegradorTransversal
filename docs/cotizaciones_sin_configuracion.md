# Cotizaciones sin dependencia de Configuración

Corrección del 02/11/2026. No requiere SQL, nuevas dependencias ni completar datos de empresa.

## Diagnóstico anterior

| Lectura o dependencia | Ubicación anterior | Efecto |
|---|---|---|
| `mf_configuracion`, fila `general`, JSON `datos` | `Repository.quote_settings()` | Fuente de ajustes generales. |
| `cargar_configuracion`, `configuracion`, `CONFIG` | `servicios/cotizacion_asistida.py` | Leían y eventualmente escribían valores iniciales antes de cotizar. |
| `emisor`: razón social, RUT, giro, dirección, comuna, correo, teléfono, representante, cuenta bancaria | `prellenar`, `actualizar_emisor`, `faltantes` | Nueve campos y validaciones de RUT/correo podían impedir generar. |
| `vigencia_dias`, `condiciones`, `iva_default` | `prellenar` | Fechas, condiciones e IVA iniciales dependían de ajustes. |
| `nombre`, `sitio_web`, `correo_contacto`, `logo_base64` | `prellenar`, `documento_descarga` | Datos de marca se copiaban desde ajustes al documento o al descargar históricos. |
| `reserva_pct`, `remuneracion_pct` | `dialogo_aceptar` | Reparto inicial de la venta leído desde ajustes. |
| `repo.quote_settings()` como detector de compatibilidad | `gestion.issue_quote`, `quote_history`, `tariffs_content` | Abrir el editor, acciones o tarifas provocaba lecturas ajenas a la propuesta. |
| `cotizadores[caso_id].datos.emisor` en sesión y borradores | `editor_cotizacion`, `actualizar_emisor` | El emisor se sincronizaba desde ajustes aunque el borrador ya existiera. |
| Pestaña Configuración, formulario `config_cotizador_*` | `configuracion_cotizador` | Pedía datos de empresa, vigencia, condiciones, IVA y reparto. |

También bloqueaban contacto/correo, detalle libre, secciones de programa habilitadas y motivo de descuento vacío. Se eliminaron estos bloqueos de contenido opcional.

## Resultado

`servicios/cotizacion_defaults.py` es la única fuente de valores comerciales iniciales públicos:

- Exento de IVA; selector editable en Importes.
- Vigencia de 30 días desde emisión. Mientras no se edite manualmente, la fecha se renueva al abrir el borrador en otro día. Se preservan fechas manuales válidas; una vencida se renueva con aviso.
- Forma de pago: **Contado – Crédito 30 días**.
- Reserva: **50% 48 horas previo a la jornada y 50% al finalizar**.
- Lista inicial: reunión diagnóstica, materiales, ejecución de `{horas}` horas, diplomas, material práctico y reunión de cierre.
- Archivo: `Cotizacion_{folio}_{cliente}`; se reemplazan los marcadores y se sanea el nombre al descargar.
- Reparto inicial de la venta: 50% reserva y 50% remuneración.

Condiciones muestra la fecha, condiciones comerciales, Qué incluye y nombre del archivo. Las ediciones se guardan en el borrador y afectan solo a esa propuesta. Las plantillas de programa existentes siguen siendo una fuente opcional de textos, incluida su sección Qué incluye.

Solo se requiere cliente, servicio, detalle de la modalidad y un ítem con valor positivo. El modelo existente tiene un servicio principal y un valor base global: no se agregó una tabla de ítems. Los avisos indican el campo y permiten abrir su pestaña/ir a su ancla. Objetivos, descripción, metodología, dirigido a y condiciones pueden quedar vacíos. El detalle libre vacío o demasiado corto se sustituye por servicio y modalidad para cumplir la restricción SQL existente. Un descuento sin motivo recibe un texto genérico público, manteniendo el motivo manual editable.

Se conservan las restricciones de integridad: montos y descuentos válidos, IVA permitido, fecha válida, permisos, concurrencia, idempotencia y estados que admiten nuevas propuestas. No se exige completar ajustes para guardar el borrador ni generar documentos.

El editor, historial, descarga Word/PDF y aceptación ya no consultan ajustes. Nuevas propuestas no incluyen datos fiscales/contacto de un emisor obtenidos de Configuración. El nombre público y logo local siguen disponibles. Los snapshots históricos conservan sus datos originales; no se borran ni se reemplazan con ajustes actuales.

Se eliminó la pestaña Configuración y su editor comercial. Tarifas siguen en Tarifas y servicios. Allí se conserva un panel plegable **Enlaces, avisos y respaldos**, cargado solo al abrirlo, para no perder funciones del formulario público, Compartir, Hoy y mantenimiento. Compartir lleva a este panel mediante “Editar enlaces y contacto”. Estas opciones no intervienen en una cotización.

En Venta aparecen Reserva (%) y Remuneración (%), con valores visibles 50/50 y validación de suma 100%. Se usa la operación SQL atómica ya existente `mf_decidir_cotizacion`, también usada por Aceptar y vender, para persistir los porcentajes y sus montos. Al registrar venta el caso queda En seguimiento y conserva Deshacer de 10 segundos. No se cambió el esquema ni la función SQL.

## Datos que quedan sin uso para este flujo

En `mf_configuracion.datos`, las claves `emisor`, `vigencia_dias`, `condiciones`, `iva_default`, `reserva_pct` y `remuneracion_pct` ya no alimentan cotizaciones nuevas. Las claves de marca tampoco se consultan al emitir o descargar cotizaciones. No se borró ninguna clave ni columna.

**Ninguna tabla completa queda obsoleta:** `mf_configuracion` sigue atendiendo enlaces, formularios, avisos y respaldos; `mf_cotizaciones.documento`, sus condiciones/fechas, los borradores, plantillas, tarifas y las columnas de reparto de `mf_ventas` conservan su función. No ejecutar DROP ni DELETE en producción.

## Verificación con datos ficticios

Resultado final: **199 pruebas Python aprobadas**, además de las tres verificaciones Node indicadas abajo (SQL sin configuración, cotizador SQL existente y recuperación de borradores). Sin cambios en permisos ni migraciones.

Pruebas nuevas en `tests/test_cotizacion_sin_configuracion.py`:

1. Valores iniciales locales, copias independientes, condiciones/programa vacíos y mínimos precisos.
2. Nombre de descarga y PDF con cliente/modalidad propios de la propuesta.
3. Caso nuevo con ajustes vacíos y métodos de lectura/escritura de ajustes que fallan si se llaman: genera $250.000, conserva borrador entre sesiones y descarga Word/PDF válidos. No se invoca ninguno de esos métodos.
4. Reparto 30/60 bloqueado; 30/70 registra $60.000/$140.000 sobre venta de $200.000. Deshacer retira la venta.

Prueba SQL local aislada en `tests/test_cotizacion_sin_configuracion.mjs`: se elimina la fila general **solo en la base efímera**, se emite por $250.000 sin emisor ni programa ni condiciones, se vende con reparto 30/70 ($75.000/$175.000) y se deshace. No accede a Supabase publicado.

Comandos desde la raíz (entorno con dependencias del proyecto y `pypdf` de verificación ya disponible):

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_cotizacion_sin_configuracion.mjs
node tests/test_cotizador.mjs
node tests/test_cotizacion_borrador.mjs
```

Los tests SQL usan la instalación local de PGlite en `tmp/db-test/node_modules`, igual que las pruebas SQL existentes; no es una dependencia de producción.

Prueba manual: Administración → Nueva solicitud con datos ficticios → Guardar y cotizar ahora. En Programa revisa cliente, servicio y detalle de modalidad; en Importes ingresa un valor positivo. En Condiciones deben estar los textos anteriores ya escritos y editables. Borra objetivos/metodología/condiciones si deseas comprobar que son opcionales. Genera y descarga. Reabre el caso para comprobar el borrador y la versión. En Venta prueba los porcentajes y Deshacer. No debe aparecer ningún aviso que pida Configuración.

No se insertaron clientes ni cotizaciones de prueba en producción. La verificación publicada con una cuenta de Administración queda como comprobación manual; las pruebas automáticas utilizan repositorio ficticio y PostgreSQL local.
