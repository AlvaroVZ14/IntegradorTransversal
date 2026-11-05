"""Consultas de presentación del registro y asistente; no modifica documentos."""
from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

PASOS=('Programa','Detalle','Importes','Condiciones y pago','Revisar y generar')
MOTIVOS_RECHAZO=('Precio','Fecha','Eligió a otro proveedor','Sin presupuesto','Otro')

def fecha_local(valor):
    texto=str(valor)
    if len(texto)==10:return datetime.fromisoformat(texto).date()
    fecha=datetime.fromisoformat(texto.replace('Z','+00:00'))
    if fecha.tzinfo is None:fecha=fecha.replace(tzinfo=ZoneInfo('UTC'))
    return fecha.astimezone(ZoneInfo('America/Santiago')).date()

def filtrar_registro(casos, filtros, desde=None, hasta=None, orden='Más recientes'):
    datos=[c for c in casos if all(not v or c.get(k) in v for k,v in filtros.items())
           and (not desde or fecha_local(c['created_at'])>=desde)
           and (not hasta or fecha_local(c['created_at'])<=hasta)]
    campo=(lambda c:float(c.get('importe_registro') or 0)) if orden.startswith('Monto') else lambda c:c['created_at']
    ordenados=sorted(datos,key=lambda c:(campo(c),str(c['id'])),reverse=orden not in ('Más antiguos','Monto menor'))
    if orden.startswith('Monto'):
        ordenados=[c for c in ordenados if c.get('importe_registro') is not None]+[c for c in ordenados if c.get('importe_registro') is None]
    return ordenados

def duplicar_borrador(actual, cotizacion):
    """Copia el contenido editable, conservando emisión/vigencia actuales."""
    datos=deepcopy(actual)
    documento=cotizacion.get('documento') or {}
    for k in datos:
        if k in documento and k not in ('fecha_emision','valida_hasta','vigencia_automatica'):
            datos[k]=deepcopy(documento[k])
    for k in ('base_clp','descuento_pct','descuento_motivo','iva_pct','detalle','condiciones','tarifa_id'):
        if k in cotizacion:datos[k]=deepcopy(cotizacion[k])
    return datos

def comparar_versiones(actual, anterior):
    diferencia=int(actual['total_clp'])-int(anterior['total_clp'])
    a=actual.get('documento') or {};b=anterior.get('documento') or {}
    campos=('servicio','item_descripcion','participantes','horas','detalle_modalidad','detalle')
    return diferencia,[k for k in campos if a.get(k,actual.get(k))!=b.get(k,anterior.get(k))]

def siguiente_paso(estado):
    return {
        'Solicitud':('Cotizar','Cotizaciones','Prepara una propuesta con la tarifa y el programa sugeridos.'),
        'En revisión':('Cotizar','Cotizaciones','Completa lo necesario y prepara la propuesta.'),
        'Cotizado':('Registrar respuesta','Cotizaciones','Esperando la respuesta del cliente. Si pasan 5 días te avisamos en Hoy.'),
        'Vendido':('Registrar venta','Venta','Registra la venta con el monto de la cotización aceptada.'),
        'En ejecución':('Subir documento','Documentos','Comparte los documentos del servicio con tu cliente.'),
    }.get(estado,('Ver documentos','Documentos','Puedes consultar los antecedentes y documentos del caso.'))
