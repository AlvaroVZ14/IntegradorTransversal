"""Agenda calculada sobre datos reales. Consultar nunca cambia estados ni envía."""
from copy import deepcopy
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo
from mente_futuro.domain import code,money
from utils.validaciones import validar_campo

CHILE=ZoneInfo('America/Santiago')
CONFIG_HOY=dict(dias_sin_respuesta=5,dias_entre_seguimientos=3,minutos_correo_pendiente=15,
    seguimiento='Hola {contacto}, ¿cómo estás? Quisiera saber si pudiste revisar la propuesta {cotizacion} para {servicio}. Quedo atenta a tus comentarios. Mente y Futuro',
    pago='Hola {contacto}, te escribo por el pago de {servicio}, asociado a {cotizacion}. El total del servicio es {monto}. ¿Podrías confirmar el estado del pago o compartir el comprobante? Gracias. Mente y Futuro',
    agradecimiento='Hola {contacto}, muchas gracias por participar en {servicio} el {fecha_jornada}. Fue un gusto trabajar con {cliente}. Quedo atenta a tus comentarios. Mente y Futuro')


def configuracion_hoy(datos=None):
    resultado={**deepcopy(CONFIG_HOY),**(datos or {}).get('hoy',{})}
    for campo,limite in [('dias_sin_respuesta',365),('dias_entre_seguimientos',365),('minutos_correo_pendiente',1440)]:
        try:resultado[campo]=max(1,min(limite,int(resultado[campo])))
        except (ValueError,TypeError):resultado[campo]=CONFIG_HOY[campo]
    for campo in ('seguimiento','pago','agradecimiento'):
        if not isinstance(resultado[campo],str) or not resultado[campo].strip():resultado[campo]=CONFIG_HOY[campo]
    return resultado


def instante(valor):
    if not valor:return None
    try:
        dt=datetime.fromisoformat(str(valor).replace('Z','+00:00'))
        return (dt if dt.tzinfo else dt.replace(tzinfo=CHILE)).astimezone(CHILE)
    except (ValueError,TypeError):return None


def fecha(valor):
    if not valor:return None
    try:return date.fromisoformat(str(valor)[:10])
    except ValueError:return None


def saludo(hora):
    return 'Buenos días' if 5<=hora<12 else 'Buenas tardes' if 12<=hora<20 else 'Buenas noches'


def pendientes(casos,cotizaciones,ventas,eventos,envios,config,ahora=None):
    ahora=ahora or datetime.now(CHILE)
    ahora=(ahora if ahora.tzinfo else ahora.replace(tzinfo=CHILE)).astimezone(CHILE)
    hoy=ahora.date()
    grupos={k:[] for k in ('solicitudes','seguimientos','datos','pagos','cierres','correos')}
    ultimas={}
    for q in sorted(cotizaciones,key=lambda q:(q.get('fecha_emision',''),q.get('created_at',''),q.get('numero',0)),reverse=True):
        ultimas.setdefault(q['caso_id'],q)
    ventas_caso={v['caso_id']:v for v in ventas if not v.get('anulada',False)}
    for caso in casos:
        if caso['estado'] in ('Finalizado','Cancelado'):continue
        q=ultimas.get(caso['id']);v=ventas_caso.get(caso['id'])
        creado=instante(caso.get('created_at'))
        dias=max(0,(hoy-creado.date()).days) if creado else 0
        q_venta=next((x for x in cotizaciones if v and x['id']==v.get('cotizacion_id')),None)
        item=dict(caso=caso,cotizacion=q_venta or q,venta=v,dias=dias)
        if not q and caso['estado'] in ('Solicitud','En revisión'):grupos['solicitudes'].append(item)
        emitida=fecha((q or {}).get('fecha_emision'))
        if q and not v and caso['estado']=='Cotizado' and emitida and (hoy-emitida).days>=config['dias_sin_respuesta']:
            contactos=[instante(e.get('created_at')) for e in eventos if e['caso_id']==caso['id'] and
                e.get('tipo')=='seguimiento' and e.get('cotizacion_id')==q['id'] and e.get('datos',{}).get('tipo_mensaje')=='seguimiento']
            reciente=max((d for d in contactos if d),default=None)
            if not reciente or (hoy-reciente.date()).days>=config['dias_entre_seguimientos']:
                grupos['seguimientos'].append({**item,'dias':(hoy-emitida).days})
        falta=[]
        for campo,label in [('cliente','Cliente'),('contacto','Contacto'),('email','Correo'),('servicio','Servicio'),('tematica','Temática'),('participantes','Participantes'),('horas','Horas')]:
            if validar_campo(campo,caso.get(campo)):falta.append(label)
        if caso.get('modalidad') in (None,'','Por definir'):falta.append('Modalidad por definir')
        for campo,label in (('rut','RUT'),('telefono','Teléfono')):
            if caso.get(campo) and validar_campo(campo,caso[campo]):falta.append(label)
        if caso['estado'] in ('Vendido','En ejecución') and not v:
            falta.append('Revisar venta anulada' if any(s['caso_id']==caso['id'] and s.get('anulada') for s in ventas) else 'Venta por registrar')
        if v and v.get('estado_pago')=='Pagado' and not fecha(caso.get('fecha_realizacion')):
            falta.append('Confirmar jornada realizada cuando corresponda')
        if falta:grupos['datos'].append({**item,'faltantes':falta,'completar_venta':caso['estado'] in ('Vendido','En ejecución') and not v})
        if v and v.get('estado_pago') in ('Pendiente','Abono recibido'):grupos['pagos'].append(item)
        realizada=fecha(caso.get('fecha_realizacion'))
        if v and v.get('estado_pago')=='Pagado' and realizada and realizada<=hoy and caso['estado'] in ('Vendido','En ejecución'):
            grupos['cierres'].append(item)
    for clave in ('solicitudes','datos','pagos'):grupos[clave].sort(key=lambda t:(instante(t['caso'].get('created_at')) or ahora,t['caso']['id']))
    grupos['seguimientos'].sort(key=lambda t:(-t['dias'],t['caso']['id']))
    grupos['cierres'].sort(key=lambda t:(t['caso']['fecha_realizacion'],t['caso']['id']))
    casos_por_id={c['id']:c for c in casos}
    for envio in envios:
        if envio.get('canal')!='correo':continue
        estado=envio.get('estado');creado=instante(envio.get('created_at'))
        revisar=estado in ('error','incierto') or (estado=='preparado' and creado and ahora-creado>=timedelta(minutes=config['minutos_correo_pendiente']))
        revisado=any(e.get('tipo')=='correo_revisado' and e.get('datos',{}).get('envio_id')==envio['id'] and e.get('datos',{}).get('estado')==estado for e in eventos)
        caso=casos_por_id.get(envio['caso_id'])
        if revisar and not revisado and caso:grupos['correos'].append(dict(caso=caso,envio=envio,cotizacion=next((q for q in cotizaciones if q['id']==envio['cotizacion_id']),None)))
    return grupos


def mensaje_listo(tipo,caso,cotizacion,venta,config):
    variables=dict(contacto=caso.get('contacto',''),servicio=caso.get('servicio',''),cliente=caso.get('cliente',''),
        cotizacion=code(cotizacion,'COT') if cotizacion else 'la propuesta',
        monto=money((venta or {}).get('monto_clp',(cotizacion or {}).get('total_clp',0))),
        fecha_jornada=fecha(caso.get('fecha_realizacion')).strftime('%d/%m/%Y') if fecha(caso.get('fecha_realizacion')) else 'la jornada realizada')
    texto=config[tipo]
    for k,v in variables.items():texto=texto.replace('{'+k+'}',str(v))
    asunto={'seguimiento':'Seguimiento de propuesta','pago':'Recordatorio de pago','agradecimiento':'Gracias por la jornada'}[tipo]
    return asunto+' · '+variables['cotizacion'],texto
