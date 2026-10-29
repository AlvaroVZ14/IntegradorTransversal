"""Reportes aditivos por calendario; no cambia estados, precios ni permisos."""
from datetime import date,datetime,timedelta
import re

import pandas as pd

from servicios.dashboard import inicio_periodo,periodos_del_rango,etiqueta_periodo,mover_periodo

AGRUPACIONES=('Mensual','Trimestral','Semestral','Anual')
INDICADORES=('Solicitudes','Cotizaciones emitidas','Ventas cerradas','Total vendido (CLP)',
             'Ventas con pago pendiente (CLP)')


def fecha_chile(valor):
    """DATE conserva su día; timestamps se interpretan en UTC y convierten a Chile."""
    if valor is None or valor=='':return None
    if isinstance(valor,date) and not isinstance(valor,datetime):return valor
    if isinstance(valor,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',valor):
        return date.fromisoformat(valor)
    fecha=pd.Timestamp(valor)
    if pd.isna(fecha):return None
    fecha=fecha.tz_localize('UTC') if fecha.tzinfo is None else fecha
    return fecha.tz_convert('America/Santiago').date()


def validar_rango(desde,hasta,agrupacion):
    if agrupacion not in AGRUPACIONES:raise ValueError('Selecciona una agrupación válida.')
    if not isinstance(desde,date) or not isinstance(hasta,date):raise ValueError('Elige Desde y Hasta para generar el reporte.')
    if desde>hasta:raise ValueError('Desde no puede ser posterior a Hasta. Revisa las fechas del reporte.')


def reporte_periodos(casos,cotizaciones,ventas,desde,hasta,agrupacion='Mensual'):
    validar_rango(desde,hasta,agrupacion)
    periodos=periodos_del_rango(desde,hasta,agrupacion)
    filas={inicio:{'Período':etiqueta_periodo(inicio,agrupacion),
                   'Desde':max(desde,inicio),
                   'Hasta':min(hasta,mover_periodo(inicio,1,agrupacion)-timedelta(days=1)),
                   **{k:0 for k in INDICADORES}} for inicio in periodos}
    def fila(valor):
        fecha=fecha_chile(valor)
        return filas[inicio_periodo(fecha,agrupacion)] if fecha and desde<=fecha<=hasta else None
    for caso in casos:
        destino=fila(caso.get('created_at'))
        if destino is not None:destino['Solicitudes']+=1
    for cotizacion in cotizaciones:
        destino=fila(cotizacion.get('fecha_emision') or cotizacion.get('created_at'))
        if destino is not None:destino['Cotizaciones emitidas']+=1
    ids={c['id'] for c in casos}
    for venta in ventas:
        if venta.get('anulada',False) or venta.get('caso_id') not in ids:continue
        destino=fila(venta.get('fecha_venta'))
        if destino is not None:
            monto=int(venta['monto_clp'])
            destino['Ventas cerradas']+=1
            destino['Total vendido (CLP)']+=monto
            if venta.get('estado_pago')!='Pagado':destino['Ventas con pago pendiente (CLP)']+=monto
    return pd.DataFrame(filas.values())


def totales_reporte(frame):
    return {k:int(frame[k].sum()) for k in INDICADORES}


def exportar_reporte(frame):
    """CSV UTF-8 con BOM y punto y coma; montos numéricos para operar en Excel."""
    from mente_futuro.domain import csv_bytes
    copia=frame.copy()
    for columna in ('Desde','Hasta'):copia[columna]=copia[columna].map(lambda f:f.strftime('%d/%m/%Y'))
    return csv_bytes(copia)
