"""Valores iniciales públicos. Se copian a cada cotización y nunca leen Supabase."""
NOMBRE_EMPRESA='Mente y Futuro'
IVA_DEFAULT=0
CONDICION_IVA_AFECTA_DEFAULT='Valor neto más IVA 19%.'
VIGENCIA_DIAS_DEFAULT=30
FORMA_PAGO_DEFAULT='Contado – Crédito 30 días'
RESERVA_CONDICION_DEFAULT='50% 48 horas previo a la jornada y 50% al finalizar'
CONDICIONES_DEFAULT=(
    'Valor exento de IVA.\n'
    f'Validez de la propuesta: {VIGENCIA_DIAS_DEFAULT} días desde la fecha de emisión.\n'
    f'Forma de pago: {FORMA_PAGO_DEFAULT}.\n'
    f'Reserva: {RESERVA_CONDICION_DEFAULT}.')
INCLUYE_VALOR_DEFAULT=(
    'Reunión diagnóstica.',
    'Materiales para la jornada.',
    'Ejecución de {horas} horas de actividad.',
    'Diplomas de reconocimiento.',
    'Material práctico.',
    'Reunión de cierre posterior a la jornada.')
NOMBRE_ARCHIVO_DEFAULT='Cotizacion_{folio}_{cliente}'
NUMERO_SECCION_INICIAL=1
RESERVA_PCT_DEFAULT=50.0
REMUNERACION_PCT_DEFAULT=50.0
DESCUENTO_MOTIVO_DEFAULT='Descuento aplicado a esta cotización'
