"""Prellenado y validación; los precios nunca se extrapolan sin revisión."""
from copy import deepcopy
from datetime import timedelta
from math import log
from mente_futuro.domain import today, money, quote_total
from utils.validaciones import rut_valido

SECCIONES={'descripcion':'Descripción','objetivos':'Objetivos','metodologia':'Metodología',
           'dirigido_a':'Dirigido a','incluye':'Qué incluye'}
EMISOR={'razon_social':'Razón social','rut':'RUT del emisor','giro':'Giro','direccion':'Dirección',
        'comuna':'Comuna','correo':'Correo del emisor','telefono':'Teléfono del emisor',
        'representante':'Representante','cuenta_bancaria':'Datos de transferencia'}
CONDICIONES='50% de anticipo para reservar la fecha y 50% al finalizar la actividad. Pago mediante transferencia. La fecha queda reservada una vez recibido el anticipo.'
CONFIG=dict(emisor={k:'' for k in EMISOR},vigencia_dias=30,condiciones=CONDICIONES,
            reserva_pct=50.0,remuneracion_pct=50.0,iva_default=0)


def configuracion(datos=None):
    datos=datos or {}
    return {**deepcopy(CONFIG),**datos,'emisor':{**CONFIG['emisor'],**datos.get('emisor',{})}}


def recomendar_tarifa(caso,tarifas):
    candidatas=[t for t in tarifas if t.get('activa',True) and t.get('servicio')==caso['servicio']]
    def distancia(t):
        return (0 if t.get('tematica')==caso['tematica'] else 1 if not t.get('tematica') else 2,
                abs(log(max(float(t['horas']),.5)/max(float(caso['horas']),.5)))+
                abs(log(max(int(t['participantes']),1)/max(int(caso['participantes']),1))),str(t['id']))
    return min(candidatas,key=distancia) if candidatas else None


def recomendar_plantilla(caso,plantillas):
    candidatas=[p for p in plantillas if p.get('activa',True) and p.get('servicio')==caso['servicio'] and p.get('tematica') in (None,'',caso['tematica'])]
    return min(candidatas,key=lambda p:(p.get('tematica')!=caso['tematica'],str(p['id']))) if candidatas else None


def textos_plantilla(caso,tarifa,plantilla):
    base=dict(descripcion=f"{caso['servicio']} sobre {caso['tematica']}.",objetivos=caso.get('detalle',''),
        metodologia='Metodología a acordar según los objetivos del servicio.',
        dirigido_a=f"{caso.get('cliente','')} · {caso['participantes']} participantes",
        incluye=(tarifa or {}).get('detalle',f"Actividad de {{horas}} horas para {{participantes}} personas."))
    base.update({k:v for k,v in (plantilla or {}).get('textos',{}).items() if k in SECCIONES})
    base['dirigido_a']=caso.get('dirigido_a') or f"{caso.get('cliente','')} · {caso['participantes']} participantes"
    sustituciones={k:str(caso.get(k,'')) for k in ('horas','participantes','cliente','servicio','tematica','modalidad')}
    sustituciones['horas']=f"{float(caso['horas']):g}".replace('.',',')
    for k,v in base.items():
        for variable,valor in sustituciones.items():v=v.replace('{'+variable+'}',valor)
        base[k]=v
    return base


def prellenar(caso,tarifas,plantillas,config):
    tarifa=recomendar_tarifa(caso,tarifas)
    plantilla=recomendar_plantilla(caso,plantillas)
    textos=textos_plantilla(caso,tarifa,plantilla)
    iva={'Exento':0,'IVA 19%':19}.get((tarifa or {}).get('tratamiento_iva'),config['iva_default'])
    return dict(tarifa_id=(tarifa or {}).get('id'),plantilla_id=(plantilla or {}).get('id'),
        base_clp=int((tarifa or {}).get('monto_clp',0)),descuento_pct=0.0,descuento_motivo='',iva_pct=iva,
        detalle=(tarifa or {}).get('detalle') or caso.get('detalle') or textos['descripcion'],
        condiciones=config['condiciones'],valida_hasta=(today()+timedelta(days=config['vigencia_dias'])).isoformat(),
        modalidad=caso['modalidad'],participantes=int(caso['participantes']),horas=float(caso['horas']),
        textos=textos,mostrar={k:True for k in SECCIONES},emisor=deepcopy(config['emisor']))


def faltantes(caso,borrador):
    falta=[]
    for k,label in [('cliente','Cliente'),('contacto','Contacto'),('email','Correo')]:
        if not caso.get(k):falta.append((label,'caso'))
    for k,label in EMISOR.items():
        if not str(borrador.get('emisor',{}).get(k,'')).strip():falta.append((label,'configuracion'))
    rut=borrador.get('emisor',{}).get('rut','')
    if rut and not rut_valido(rut):falta.append(('RUT del emisor válido','configuracion'))
    import re
    correo=borrador.get('emisor',{}).get('correo','')
    if correo and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',correo):falta.append(('Correo del emisor válido','configuracion'))
    if len(borrador.get('detalle','').strip())<2:falta.append(('Detalle del servicio','detalle'))
    for k,label in SECCIONES.items():
        if borrador.get('mostrar',{}).get(k,True) and len(borrador.get('textos',{}).get(k,'').strip())<2:
            falta.append((label,'programa'))
    if borrador.get('iva_pct') not in (0,19):falta.append(('Tratamiento de IVA','importes'))
    if borrador.get('descuento_pct',0)>0 and not borrador.get('descuento_motivo','').strip():falta.append(('Motivo del descuento','importes'))
    try:
        from datetime import date
        if date.fromisoformat(borrador['valida_hasta'])<today():falta.append(('Vigencia no vencida','condiciones'))
        quote_total(borrador['base_clp'],borrador['descuento_pct'],borrador['iva_pct'])
    except (ValueError,KeyError,TypeError):falta.append(('Importes y vigencia válidos','importes'))
    return falta


def datos_emision(borrador):
    campos=('tarifa_id','base_clp','descuento_pct','descuento_motivo','iva_pct','detalle','condiciones','valida_hasta')
    return {**{k:borrador[k] for k in campos},'documento':deepcopy(borrador)}


def mensaje_cliente(cotizacion):
    from mente_futuro.domain import code
    datos=cotizacion['snapshot']
    asunto=f"Propuesta {code(cotizacion,'COT')} · {datos.get('servicio','Mente y Futuro')}"
    texto=(f"Hola {datos.get('contacto','')},\n\nTe comparto nuestra propuesta de {datos.get('servicio','capacitación')} "
           f"para {datos.get('cliente','tu organización')}, por un total de {money(cotizacion['total_clp'])}.\n"
           f"La propuesta está vigente hasta {__import__('datetime').date.fromisoformat(cotizacion['valida_hasta']):%d/%m/%Y}.\n\n"
           'Quedo atenta a tus comentarios.\nMente y Futuro')
    return asunto,texto
