# Corrección del módulo de cotizaciones

## Diagnóstico previo

Se revisaron `app.py`, `paginas/gestion.py`, `paginas/cotizador.py`,
`servicios/cotizacion_asistida.py`, `servicios/repositorio.py`, los generadores
Word/PDF y las migraciones SQL relacionadas. No se consultaron datos privados
de la base publicada con una sesión de Administración.

| Dato | Origen y causa anterior |
| --- | --- |
| Razón social, RUT, giro, dirección, comuna, correo, teléfono, representante y datos de transferencia | `EMISOR` y `faltantes()` en `servicios/cotizacion_asistida.py` exigen los nueve datos para emitir. También validan RUT y correo. |
| Emisor de un borrador antiguo | `editor_cotizacion()` conservaba el JSON del borrador por encima del prellenado. Un emisor vacío seguía vacío después de completar Configuración. Requería el botón manual «Actualizar datos del emisor desde Configuración». |
| Vigencia, condiciones, IVA y porcentajes de reparto | `CONFIG` contenía valores iniciales en Python. La migración `202610220003_cotizador_asistido.sql` crea la fila `mf_configuracion`, pero con `datos = {}`. Solo guardar Configuración persistía esos valores. |
| Tarifa de referencia | Se recomienda desde `mf_tarifas` según servicio, temática, horas y participantes. Si no existe coincidencia, se permite propuesta personalizada y monto manual; no se obliga a crear una tarifa. |
| Programa | Se recomienda desde `mf_plantillas_programa`; si falta, `textos_plantilla()` propone textos editables desde el caso. |
| Cliente, contacto y correo; contenido de la propuesta, descuento e importes | Son datos propios del caso/cotización y mantienen las validaciones existentes. Los casos marcados incompletos siguen teniendo su aviso anterior en `paginas/gestion.py`. |

La sesión guarda borradores en `st.session_state.cotizadores`; la copia del
emisor también estaba en `mf_borradores_cotizacion.datos`. Por eso el problema
podía continuar incluso después de recargar. No se identificó un fallo de permisos.

La parte «en vivo» retirada es la pestaña **Vista previa**, el indicador
**Total previsto** de esa pestaña y **Total de la propuesta (CLP)** de Importes.
Se conservan el autoguardado del borrador, los documentos descargables y los
totales definitivos de las versiones emitidas. La actualización de Casos/Hoy/
Dashboard no cambia.

## Cambios

- `servicios/cotizacion_asistida.py`: `cargar_configuracion()` completa una sola
  vez las claves iniciales que faltan en la fila existente `mf_configuracion`
  mediante el guardado con control de versión. Conserva los valores ya guardados
  y las claves de otros módulos. Si hay conflicto, relee sin sobrescribir.
- Se mantienen los valores iniciales anteriores: vigencia 30 días, IVA 0,
  reparto 50/50 y las condiciones comerciales existentes. No se crean precios,
  tarifas, programas ni identidades de empresa ficticias en producción.
- `actualizar_emisor()` toma el emisor actual de Configuración para los
  borradores; conserva los textos, montos, descuentos y condiciones específicas
  editados. Nunca modifica versiones emitidas.
- `paginas/cotizador.py`: aplica esa carga automática, separa los avisos de
  configuración de los datos de la propuesta y ofrece **Ir a Ajustes
  (Configuración)**. Si faltan datos del emisor, el borrador se guarda; la emisión
  final conserva las validaciones previas. Elimina el refresco manual del emisor
  y la vista/cálculos en vivo. Una sesión que estaba en la pestaña eliminada
  vuelve a Programa.
- `tests/test_cotizador.py`: agrega regresiones con datos exclusivamente ficticios.

No hay migración SQL nueva, tablas ni permisos nuevos, ni dependencias nuevas.
El único guardado adicional es completar los valores iniciales en la tabla de
configuración existente, anunciado antes de implementar. Los datos legales
reales que falten deben completarse una vez en Configuración; no se inventan.

El total sigue calculándose al generar y al guardar: `quote_total()` valida
el documento y `mf_cotizaciones.total_clp` es una columna generada en PostgreSQL.
El RPC `mf_emitir_cotizacion` permanece intacto.

## Pruebas y cómo repetirlas

Desde la raíz del proyecto, con las dependencias de desarrollo disponibles:

```powershell
python -m unittest discover -s tests -p test_cotizador.py -v
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_cotizador.mjs
```

La prueba SQL necesita la instalación de PGlite ya usada por el proyecto en
`tmp/db-test/node_modules`. Es una base local desechable, no Supabase publicado.
Las pruebas Python usan `AppTest` y un repositorio simulado; Word/PDF se generan
realmente. El servidor SMTP está simulado y no se envían mensajes.

Resultado de esta entrega: **182 pruebas Python aprobadas** en la suite completa
y prueba SQL local de cotizaciones aprobada. Las advertencias de ejecución
`ScriptRunContext` corresponden al entorno de pruebas de Streamlit.

| Prueba | Resultado esperado y comprobado localmente |
| --- | --- |
| Administración, cliente nuevo, tarifa existente, sin abrir Ajustes | Recomienda la tarifa, genera y ofrece Word/PDF; total ficticio $1.250.000. No solicita completar el emisor si ya está configurado. |
| Cliente existente y borrador guardado | Recupera la edición y lee automáticamente el emisor vigente, aunque el borrador almacenara uno vacío. |
| Recarga simulada con una instancia nueva de AppTest | Mantiene textos, condiciones, montos, descuento e IVA desde el borrador. No depende de la sesión de edición anterior. |
| Descuento 10% e IVA 19% sobre $1.250.000 | Total guardado $1.338.750. |
| Configuración incompleta | Aviso dirigido a Administración y botón a Configuración. Se puede editar y guardar el borrador; no se emite un documento incompleto. |
| Inicialización de valores | Se guardan una vez; una segunda lectura no vuelve a guardar. Se respetan condiciones y reparto personalizados. |
| Fallo de guardado de valores iniciales | No se pisan valores existentes; el servicio entrega los valores iniciales y señala que no logró persistirlos. |
| Contenido y versiones emitidas | Una actualización del emisor no altera snapshots emitidos; RLS y cálculo SQL conservan sus pruebas. |
| Pantalla simplificada | Sin pestaña Vista previa, sin los dos totales en vivo ni botón de actualización manual del emisor. |

Para comprobarlo en la aplicación publicada: ingresar como Administración,
abrir Casos y cotizaciones → detalle → Cotizaciones y generar una propuesta de
prueba autorizada. Recargar antes de generar y verificar que la edición se
conserva. Este paso en producción queda pendiente: las pruebas automatizadas
no usan la cuenta real ni insertan casos/cotizaciones reales.
