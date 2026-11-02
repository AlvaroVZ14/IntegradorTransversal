# Tu propuesta a medida

Implementación del Prompt 19. La generación no depende de Configuración. No se modifican roles ni otros módulos.

## Referencia y resultado

Se revisaron visualmente las dos páginas del PDF de referencia aportado anteriormente, disponible en Descargas. No había una carpeta `referencias/` en este proyecto. Se conservaron únicamente su estructura y criterios gráficos; sus clientes, importes y textos particulares no se copiaron al código ni al repositorio.

La referencia tiene marco rectangular, logo pequeño superior izquierdo, línea gris, título Times New Roman azul oscuro centrado, objetivos/metodología en la primera página y tablas/condiciones en la segunda. La referencia original es tamaño carta; la salida nueva es A4 por instrucción del prompt. El PDF usa Times y Helvetica estándar, sin descargar fuentes ni depender de las instaladas en el servidor. Por estas adaptaciones, no se promete igualdad píxel a píxel con el original.

PDF principal: ReportLab. Word editable: python-docx. Ambos se construyen con el mismo modelo de contenido. Para propuestas normales se separa el programa y el detalle en dos páginas. Los textos extensos continúan automáticamente; las tablas repiten el encabezado cuando corresponde. Al desactivar objetivos y metodología, no se fuerza una primera página vacía.

## Editor

- Programa: objetivo general, lista de objetivos específicos; introducción y lista de momentos con etiqueta/descripción; descripción y dirigido a. Las listas permiten agregar, quitar, subir y bajar. Se conservan los campos anteriores, incluidos el detalle libre y observaciones de modalidad.
- Modalidad de la propuesta admite Presencial, Online, Híbrida y Por definir. Jornadas y duración es texto libre. El documento combina modalidad y duración sin duplicar el nombre ni Por definir. Esto no cambia el catálogo del formulario ni las restricciones de los casos: los datos específicos de la propuesta se guardan en su JSON.
- Plantillas: se precargan por servicio/temática. Cargar y Restablecer recuperan también las listas estructuradas; Guardar como plantilla las conserva sin identificadores temporales.
- Importes: valor base e IVA, descripción del ítem 1, Qué incluye, descuento con motivo y período. Se muestra el total inmediato usando el cálculo existente. El IVA parte exento. Cambiar IVA actualiza solo la primera condición si aún contiene el texto inicial; respeta condiciones personalizadas.
- Condiciones: una viñeta por línea, textos iniciales del Prompt 18, fecha de validez y nombre del archivo. Son editables solo para esta cotización. Incluye interruptor de condiciones generales.
- Fecha de emisión editable, hoy inicialmente. La vigencia automática usa emisión + 30 días y deja de reemplazar la fecha cuando se modifica manualmente.
- Vista previa: visor PDF oficial de Streamlit, con el mismo generador que la descarga. Cambia al actualizar los campos. El folio de borrador termina en 0000; el definitivo se asigna al generar.
- Generar guarda una versión y cambia el caso a Cotizada mediante la operación atómica existente. Mantiene historial y descarga de cada versión. No se escriben cotizaciones por mostrar la vista previa.

Las versiones nuevas guardan `formato_version=2`. Los documentos históricos sin esa marca usan sus generadores anteriores; no se reescriben snapshots. Borradores existentes reciben los campos nuevos sin borrar su texto. Todo se guarda en `mf_borradores_cotizacion.datos` y `mf_cotizaciones.documento`, ambos JSONB existentes.

`NUMERO_SECCION_INICIAL` en `servicios/cotizacion_defaults.py` controla el número de partida. La numeración se calcula con las secciones activas. La descripción opcional se omite sin quitar la tabla necesaria de modalidad/participantes/dirigido a. Dirigido a vacío se representa con `-`.

Nombres nuevos: `Cotizacion_MF-2026-0004_NombreCliente.pdf` y `.docx`. Se usa el número global que ya asigna la base; no se agregó ni reinicia un contador anual. El nombre sigue siendo editable y se sanea para impedir rutas/caracteres inválidos.

## Correos y WhatsApp

Junto a las descargas aparecen Redactar correo (`mailto`, destinatario/asunto/mensaje) y Mensaje para WhatsApp, con copia y enlace. No envían automáticamente ni adjuntan archivos: se adjunta a mano. Se conserva la acción anterior Enviar al cliente con su confirmación, sin agregar envíos automáticos.

## Activación en Supabase

**Ejecutar una vez** `supabase/migrations/202611020001_fecha_propuesta.sql` en SQL Editor del proyecto, después de las migraciones existentes del cotizador asistido. No necesita secretos en el código ni datos de empresa.

La migración actualiza `mf_emitir_cotizacion` para insertar `fecha_emision` desde la propuesta, con hoy en Chile como respaldo. Conserva firma, permisos de administración, concurrencia, idempotencia, versiones, snapshot, totales y cambio de estado. No altera tablas ni datos existentes.

Agrega `mf_emitir_propuesta_v2`, entrada versionada que delega en esa función. Solo authenticated puede invocarla y la función delegada exige Administración. El repositorio usa esa entrada para propuestas v2. Si falta la migración y la fecha es hoy, puede usar el RPC anterior, que ya emite con hoy en Chile, conservando los campos nuevos en JSON. Para cualquier otra fecha, falla antes de insertar y muestra qué actualización aplicar; el borrador se conserva. Solo se permite ese respaldo ante función inexistente (PGRST202), nunca ante errores de permiso, concurrencia o guardado. Así un servidor anterior no ignora silenciosamente una fecha histórica elegida.

No se aplicó SQL en Supabase de producción desde esta sesión: no hay conexión administrativa disponible. **La fecha editable distinta de hoy requiere este paso.** Las cotizaciones con la fecha habitual de hoy mantienen compatibilidad con la migración anterior.

## Dependencias

Se cambia `streamlit` a `streamlit[pdf]>=1.65,<1.66` en requirements para incluir el visor oficial (`streamlit-pdf`). ReportLab y python-docx ya estaban disponibles mediante las dependencias existentes. La app no requiere Word ni LibreOffice.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Pruebas

Resultado: **202 pruebas Python aprobadas en la batería general**, más pruebas SQL del cotizador, fecha editable/roles y recuperación del borrador. La comprobación final específica del módulo tuvo **4 pruebas aprobadas**, incluida la compatibilidad con el RPC anterior solo para hoy y sin reintentar errores de permisos/concurrencia.

`tests/test_propuesta_documento.py` comprueba:

- Documento normal de dos páginas, orden de secciones, fecha larga, modalidad y duración, folio, formato CLP y nombre seguro.
- Documento con 45 objetivos y 35 condiciones: cuatro páginas y marcador final presente, sin perder texto; descuento de 15%, neto $850.000, IVA $161.500, total $1.011.500 sobre base $1.000.000.
- Sin objetivos, metodología ni descripción: una página y numeración consecutiva desde Detalle del servicio.
- Word válido con tablas y contenido correspondiente, sin marcadores sin resolver; generación sin mutar el snapshot.
- Editor: total inmediato e IVA, fecha editable, agregar/reordenar/quitar listas, persistencia entre sesiones, generar versión y acceso a descargas/mensajes.

`tests/test_cotizacion_sin_configuracion.mjs` aplica la migración en PostgreSQL efímero: emisión sin fila de ajustes, fecha elegida persistida, rechazo de vigencia anterior a emisión sin crear versión, reparto/Deshacer y rechazo al usuario sin rol admin. No consulta datos reales. Las pruebas del cotizador SQL y del puente de borrador también se conservan.

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_cotizacion_sin_configuracion.mjs
node tests/test_cotizador.mjs
node tests/test_cotizacion_borrador.mjs
```

Se generaron tres muestras ficticias en `output/propuesta19/`, fuera del repositorio. Se renderizaron y revisaron visualmente todas las páginas PDF, comparando marco, orden, tipografías, márgenes y tablas con la referencia. La revisión visual de Word queda pendiente: el renderizador indicó que falta LibreOffice, y Word instalado se bloqueó al abrir la muestra. Se cerraron únicamente los procesos ocultos de esa prueba. Su estructura y contenido sí se verificaron automáticamente; no se afirma fidelidad visual comprobada en Word.

Tampoco se comprobó en un teléfono físico ni se insertaron casos de prueba en producción. Revisión manual recomendada: abrir PDF en celular y usar zoom; abrir Word y comprobar saltos de página con las fuentes de ese equipo.

## Recorrido manual esperado

1. Administración → Casos y cotizaciones → abrir caso → Cotizaciones. Elegir tarifa; revisar Programa, Importes y Condiciones.
2. Agregar dos objetivos y tres momentos; cambiar orden y recargar. Deben mantenerse los valores guardados en el borrador.
3. Abrir Vista previa; cambiar monto/IVA/condiciones. Debe cambiar el PDF sin crear versiones en el historial.
4. Generar cotización: debe aparecer una versión y el caso Cotizada, con Descargar PDF y Descargar Word. Descargar y comparar con la referencia.
5. Desactivar objetivos y metodología, generar otra versión: la numeración se ajusta, la anterior conserva su contenido y formato.
6. Redactar correo o abrir WhatsApp: debe abrir el programa correspondiente con el texto listo. No se envía nada desde esos botones. Adjuntar el archivo manualmente.

## Archivos completos modificados

`paginas/cotizador.py`, `paginas/listas_propuesta.py`, `paginas/acciones_cotizacion.py`, `servicios/propuesta_documento.py`, `servicios/documentos_propuesta.py`, `servicios/documentos_cotizacion.py`, `servicios/cotizacion_asistida.py`, `servicios/cotizacion_defaults.py`, `servicios/repositorio.py`, `utils/cotizacion_borrador.py`, `requirements.txt`, `supabase/migrations/202611020001_fecha_propuesta.sql`, `tests/test_propuesta_documento.py`, `tests/test_cotizacion_sin_configuracion.mjs`, `tests/test_cotizacion_sin_configuracion.py`, `tests/test_cotizador.py`, `tests/test_app.py` y este documento.
