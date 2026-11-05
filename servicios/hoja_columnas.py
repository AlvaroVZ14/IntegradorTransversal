"""Contrato único de columnas de Sheets; nunca contiene credenciales ni filas."""
COLUMNAS={
 'Casos':('codigo','fecha_solicitud','año','mes','trimestre','semestre','empresa','tipo_servicio','tematica','modalidad','participantes','horas','origen_pedido','canal_captacion','registrado_por','estado','fecha_ultimo_cambio','dias_en_estado','motivo_rechazo','faltan_datos','monto_cotizado','tiene_venta','monto_vendido','estado_pago','monto_pendiente'),
 'Cotizaciones':('numero','version','codigo_caso','fecha_emision','año','mes','trimestre','semestre','empresa','servicio','tematica','monto_bruto','descuento_pct','monto_total','exento_iva','fecha_envio','dias_sin_respuesta','estado_cotizacion'),
 'Ventas':('id_venta','codigo_caso','fecha_venta','año','mes','trimestre','semestre','empresa','tipo_servicio','tematica','modalidad','participantes','monto_vendido','pct_reserva','monto_reserva','pct_remuneracion','monto_remuneracion','estado_pago','monto_pendiente'),
 'Registro':('fecha','hoja','filas_escritas','resultado','error'),
 'Leyenda':('hoja','columna','significado','color'),
 'Resumen':('Mes','Total vendido','','Trimestre','Total vendido','','Temática','Total vendido','','Mes de solicitudes','Solicitudes'),
}
CLAVES={'Casos':('codigo',),'Cotizaciones':('numero','version'),'Ventas':('id_venta',)}
FECHAS={'fecha_solicitud','fecha_ultimo_cambio','fecha_emision','fecha_envio','fecha_venta','fecha'}
MONEDAS={'monto_cotizado','monto_vendido','monto_pendiente','monto_bruto','monto_total','monto_reserva','monto_remuneracion'}

AYUDAS={
 'empresa':'Empresa declarada; si coincide con la persona de contacto se reemplaza por Cliente particular.',
 'fecha_solicitud':'Día en que se recibió la solicitud, según la hora de Chile.',
 'fecha_ultimo_cambio':'Último cambio conocido de estado; inicialmente se usa la última fecha disponible.',
 'dias_en_estado':'Días calendario desde el último cambio conocido de estado.',
 'monto_pendiente':'Monto completo de ventas sin pago total. La app no registra el valor del abono; no representa el saldo exacto.',
 'monto_bruto':'Valor base de la cotización, antes de descuento e IVA.',
 'motivo_rechazo':'Solo categoría de rechazo; nunca incluye la nota libre.',
 'dias_sin_respuesta':'Días desde la emisión, siguiendo la clasificación actual de la app; cero si hubo decisión.',
 'canal_captacion':'Canal del enlace de una solicitud enviada; no cuenta visitas.',
 'faltan_datos':'SI si hay datos por completar; NO en caso contrario.',
 'monto_vendido':'Monto de la venta no anulada; las ventas anuladas se retiran de esta copia.',
 'registrado_por':'Cliente o Administración; nunca el nombre de una persona.',
 'estado_cotizacion':'Clasificación actual de la propuesta; Generada si no hay evidencia de envío.',
 'estado_pago':'Pendiente, Anticipo pagado o Pagado.',
}

def leyenda():
    from ui.estados import CATALOGO
    filas=[[hoja,c,AYUDAS.get(c,c.replace('_',' ').capitalize()),''] for hoja in CLAVES for c in COLUMNAS[hoja]]
    for grupo in ('caso','pago','cotizacion'):
        filas.extend([grupo,e['etiqueta'],e['ayuda'],e['fondo']] for e in CATALOGO[grupo].values())
    return filas
