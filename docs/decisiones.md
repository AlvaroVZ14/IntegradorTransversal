# Decisiones de implementación

- Se mantiene Streamlit y Supabase, respetando el proyecto existente.
- Se conservan tres secciones principales. El tarifario forma parte de Casos y cotizaciones para evitar más navegación.
- Cada cliente tiene una cuenta propia. Ocultar botones se complementa con permisos reales en PostgreSQL.
- Se crean tablas con prefijo `mf_` porque no se dispone del esquema administrativo de la antigua tabla `casos`. No se borra ni transforma información anterior automáticamente.
- Las tarifas se extraen de los documentos proporcionados como referencias, sin asumir una regla lineal de precio por hora o participante. La dueña puede ajustar cada propuesta.
- Los descuentos de aniversario no se reutilizan automáticamente. El tratamiento de IVA de coaching requiere selección explícita.
- Las cotizaciones guardan una copia inmutable de los datos y se descargan como HTML imprimible. No se envían correos comerciales automáticamente.
- La venta se registra tras confirmar la aceptación; no se deduce únicamente del estado del caso. Los pagos tienen estados, sin contabilidad ni cálculo de saldos parciales.
- El dashboard usa los datos consultados en Supabase, con fecha local de Chile para solicitudes, fecha de aceptación para ventas y exportaciones CSV protegidas contra fórmulas.
- No se implementa marketing, publicidad, captación, facturación tributaria ni integración contable.

Pendiente de activación en el entorno real: aplicar la migración, identificar y asignar la cuenta de la dueña, comprobar permisos con cuentas distintas y revisar/importar datos antiguos si corresponde. Los precios y condiciones deben ser validados por Mente y Futuro antes de uso comercial.
