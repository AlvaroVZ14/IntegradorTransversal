# Arquitectura implementada

Streamlit mantiene un cliente Supabase independiente en cada sesión. Supabase Auth verifica al usuario; PostgreSQL aplica permisos mediante Row Level Security. No hay clientes de conexión compartidos ni cachés globales de información personal.

## Modelo

- `mf_perfiles`: usuario de Auth, nombre, correo y rol `cliente` o `duena`. El registro público siempre crea un cliente. Solo SQL administrativo cambia roles.
- `mf_casos`: solicitud y seguimiento, con creador, cuenta de cliente vinculada, datos de contacto, servicio, temática, alcance y fechas.
- `mf_tarifas`: referencias editables por la dueña, con fuente y estado activo.
- `mf_cotizaciones`: documentos inmutables con copia de datos del caso, importes, descuento, IVA, vigencia y condiciones. El total se calcula también en PostgreSQL.
- `mf_ventas`: una venta por caso, vinculada a una cotización de ese caso, con monto, fecha de aceptación, estado de pago y anulación.

## Escrituras

El formulario inserta solicitudes con un UUID estable para poder reintentar. Las funciones `mf_emitir_cotizacion` y `mf_registrar_venta` verifican el rol, bloquean el caso durante la operación y realizan sus escrituras en una sola transacción. Las cotizaciones usan un identificador de operación y las ventas una restricción única por caso para evitar duplicados.

Las ediciones de casos, tarifas y pagos utilizan un número de versión para detectar cambios simultáneos. Las consultas están paginadas para no limitar el dashboard a los primeros 1.000 registros.

## Accesos

Sin sesión no se accede a las tablas nuevas. El cliente ve sus casos y las cotizaciones asociadas; no puede alterar sus estados, emitir propuestas, gestionar ventas, ver tarifas internas ni asignarse un rol. La dueña ve todos los casos, perfiles, tarifas, cotizaciones y ventas. Las cotizaciones no se actualizan ni borran desde la API: una revisión se emite como otro documento.

Las claves publicables se mantienen fuera de Git. No se utiliza una clave administrativa para las operaciones del portal. La configuración de producción, la migración y la asignación del primer rol están descritas en el README.
