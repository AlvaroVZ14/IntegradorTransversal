"""Series de presentación a partir de filas ya cargadas, sin consultas nuevas."""
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo


def ingresos_seis_meses(filas, hoy=None):
    hoy=hoy or datetime.now(ZoneInfo('America/Santiago')).date()
    indice=hoy.year*12+hoy.month-1
    meses=[divmod(indice-i,12) for i in range(5,-1,-1)]
    claves=[(anio,mes+1) for anio,mes in meses]
    conteos=dict.fromkeys(claves,0)
    for fila in filas:
        valor=fila.get('created_at')
        if not valor:continue
        try:
            fecha=datetime.fromisoformat(str(valor).replace('Z','+00:00'))
            if fecha.tzinfo:fecha=fecha.astimezone(ZoneInfo('America/Santiago'))
            clave=(fecha.year,fecha.month)
            if clave in conteos:conteos[clave]+=1
        except (ValueError,TypeError):continue
    return list(conteos.values()),[f'{mes:02d}/{anio}' for anio,mes in claves]


def contexto_cohortes(data, ventas, hasta):
    """Desglosa los KPI existentes; no sustituye ni modifica sus cálculos."""
    periodos=data['series'].tail(6)
    convertidos={v['caso_id'] for v in ventas if not v.get('anulada') and
                 date.fromisoformat(str(v['fecha_venta'])[:10])<=hasta}
    solicitudes=[]
    for r in data['requests'].to_dict('records'):
        d=datetime.fromisoformat(str(r['created_at']).replace('Z','+00:00'))
        if not d.tzinfo:d=d.replace(tzinfo=timezone.utc)
        solicitudes.append((r['id'],d.astimezone(ZoneInfo('America/Santiago')).date()))
    pendientes=data['sales'][data['sales'].estado_pago!='Pagado'].to_dict('records')
    conversion=[];pagos=[]
    for p in periodos.itertuples():
        cohorte=[ident for ident,fecha in solicitudes if p.inicio<=fecha<=p.fin]
        conversion.append(100*sum(ident in convertidos for ident in cohorte)/len(cohorte) if cohorte else None)
        pagos.append(sum(float(v['monto_clp']) for v in pendientes if p.inicio<=date.fromisoformat(str(v['fecha_venta'])[:10])<=p.fin))
    return {'conversion':conversion,'pending_payment':pagos}
