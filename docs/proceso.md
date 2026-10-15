# Flujo de gestión

1. El cliente crea una cuenta, confirma su correo e inicia sesión.
2. Envía los datos de una solicitud. Se guarda en Supabase y obtiene un número de caso.
3. La dueña revisa el caso. Puede registrar solicitudes recibidas por otros medios y vincularlas a una cuenta existente.
4. Selecciona una tarifa de referencia o un valor personalizado. Ajusta detalle, descuento, IVA, fecha de vigencia y condiciones. Revisa el total y emite la cotización.
5. El cliente puede consultar y descargar las propuestas de sus casos. La aceptación se coordina con la dueña; el portal no simula una aceptación automática.
6. La dueña registra la venta confirmada usando la cotización aceptada y su fecha. No se permite duplicar ventas de un caso ni usar una cotización ajena.
7. Actualiza el seguimiento del servicio y el estado de pago. Una anulación conserva el registro y lo excluye de los indicadores.
8. Consulta el dashboard por fechas y servicio, revisa demanda, ventas y conversión, y descarga los datos cuando los necesita.

La confirmación de solicitud, cotización o venta se muestra únicamente después de que Supabase confirma la escritura. Si una conexión falla, la aplicación informa el problema y permite reintentar.
