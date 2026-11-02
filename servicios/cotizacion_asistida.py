"""Prellenado y validación; los precios nunca se extrapolan sin revisión."""
from copy import deepcopy
from datetime import timedelta
from math import log
from mente_futuro.domain import today, money, quote_total
from servicios.cotizacion_defaults import (NOMBRE_EMPRESA,IVA_DEFAULT,VIGENCIA_DIAS_DEFAULT,
    CONDICIONES_DEFAULT,INCLUYE_VALOR_DEFAULT,NOMBRE_ARCHIVO_DEFAULT,DESCUENTO_MOTIVO_DEFAULT)

SECCIONES={'descripcion':'Descripción','objetivos':'Objetivos','metodologia':'Metodología',
           'dirigido_a':'Dirigido a','incluye':'Qué incluye'}
EMISOR={'razon_social':'Razón social','rut':'RUT del emisor','giro':'Giro','direccion':'Dirección',
        'comuna':'Comuna','correo':'Correo del emisor','telefono':'Teléfono del emisor',
        'representante':'Representante','cuenta_bancaria':'Datos de transferencia'}


def recomendar_tarifa(caso,tarifas):
    candidatas=[t for t in tarifas if t.get('activa',True) and t.get('servicio')==caso['servicio']]
    def distancia(t):
        return (0 if t.get('tematica')==caso['tematica'] else 1 if not t.get('tematica') else 2,
                abs(log(max(float(t['horas']),.5)/max(float(caso.get('horas') or .5),.5)))+
                abs(log(max(int(t['participantes']),1)/max(int(caso.get('participantes') or 1),1))),str(t['id']))
    return min(candidatas,key=distancia) if candidatas else None


def recomendar_plantilla(caso,plantillas):
    candidatas=[p for p in plantillas if p.get('activa',True) and p.get('servicio')==caso['servicio'] and p.get('tematica') in (None,'',caso['tematica'])]
    return min(candidatas,key=lambda p:(p.get('tematica')!=caso['tematica'],str(p['id']))) if candidatas else None


def textos_plantilla(caso,tarifa,plantilla):
    base=dict(descripcion=f"{caso.get('servicio') or ''} sobre {caso.get('tematica') or ''}.",objetivos=caso.get('detalle','') or '',
        metodologia='Metodología a acordar según los objetivos del servicio.',
        dirigido_a=f"{caso.get('cliente') or ''} · {caso.get('participantes') or 1} participantes",
        incluye='\n'.join(INCLUYE_VALOR_DEFAULT))
    base.update({k:v for k,v in (plantilla or {}).get('textos',{}).items() if k in SECCIONES})
    base['dirigido_a']=caso.get('dirigido_a') or f"{caso.get('cliente') or ''} · {caso.get('participantes') or 1} participantes"
    sustituciones={k:str(caso.get(k,'')) for k in ('horas','participantes','cliente','servicio','tematica','modalidad')}
    sustituciones['horas']=f"{float(caso.get('horas') or .5):g}".replace('.',',')
    for k,v in base.items():
        for variable,valor in sustituciones.items():v=v.replace('{'+variable+'}',valor)
        base[k]=v
    return base


def prellenar(caso,tarifas,plantillas):
    tarifa=recomendar_tarifa(caso,tarifas)
    plantilla=recomendar_plantilla(caso,plantillas)
    textos=textos_plantilla(caso,tarifa,plantilla)
    modalidad=caso.get('modalidad') or 'Por definir'
    return dict(tarifa_id=(tarifa or {}).get('id'),plantilla_id=(plantilla or {}).get('id'),
        base_clp=int((tarifa or {}).get('monto_clp',0)),descuento_pct=0.0,descuento_motivo='',iva_pct=IVA_DEFAULT,
        detalle=(tarifa or {}).get('detalle') or caso.get('detalle') or textos['descripcion'],
        condiciones=CONDICIONES_DEFAULT,valida_hasta=(today()+timedelta(days=VIGENCIA_DIAS_DEFAULT)).isoformat(),vigencia_automatica=True,
        modalidad=modalidad,detalle_modalidad='' if modalidad=='Por definir' else
            f"{modalidad} · {float(caso.get('horas') or .5):g} horas · {caso.get('participantes') or 1} participantes",
        cliente=caso.get('cliente') or '',servicio=caso.get('servicio') or '',
        participantes=int(caso.get('participantes') or 1),horas=float(caso.get('horas') or .5),
        textos=textos,mostrar={k:True for k in SECCIONES},emisor={},marca={'nombre':NOMBRE_EMPRESA},
        nombre_archivo=NOMBRE_ARCHIVO_DEFAULT)


def faltantes(caso,borrador):
    falta=[]
    for k,label in [('cliente','Cliente'),('servicio','Servicio')]:
        if not str(borrador.get(k,caso.get(k)) or '').strip():falta.append((label,k))
    if not str(borrador.get('detalle_modalidad') or '').strip():falta.append(('Detalle de la modalidad','detalle_modalidad'))
    if borrador.get('base_clp',0)<=0:falta.append(('Un ítem con valor mayor a cero','importes'))
    if borrador.get('iva_pct') not in (0,19):falta.append(('Tratamiento de IVA','importes'))
    try:
        from datetime import date
        emision=date.fromisoformat(borrador.get('fecha_emision') or today().isoformat())
        if date.fromisoformat(borrador['valida_hasta'])<emision:falta.append(('Vigencia posterior a la emisión','condiciones'))
        quote_total(borrador['base_clp'],borrador['descuento_pct'],borrador['iva_pct'])
    except (ValueError,KeyError,TypeError):falta.append(('Importes y vigencia válidos','importes'))
    return falta


def datos_emision(borrador):
    campos=('tarifa_id','base_clp','descuento_pct','descuento_motivo','iva_pct','detalle','condiciones','valida_hasta')
    documento=deepcopy(borrador)
    detalle=documento.get('detalle','').strip()
    documento['detalle']=detalle if len(detalle)>=2 else f"{documento.get('servicio','Servicio')} · {documento.get('detalle_modalidad','')}"
    if documento.get('descuento_pct',0)>0 and not documento.get('descuento_motivo','').strip():
        documento['descuento_motivo']=DESCUENTO_MOTIVO_DEFAULT
    return {**{k:documento[k] for k in campos},'fecha_emision':documento.get('fecha_emision') or today().isoformat(),'documento':documento}


def mensaje_cliente(cotizacion):
    from mente_futuro.domain import code
    from servicios.propuesta_documento import folio
    datos=cotizacion['snapshot']
    codigo=folio(cotizacion) if (cotizacion.get('documento') or {}).get('formato_version')==2 else code(cotizacion,'COT')
    asunto=f"Propuesta {codigo} · {datos.get('servicio','Mente y Futuro')}"
    texto=(f"Hola {datos.get('contacto','')},\n\nTe comparto nuestra propuesta de {datos.get('servicio','capacitación')} "
           f"para {datos.get('cliente','tu organización')}, por un total de {money(cotizacion['total_clp'])}.\n"
           f"La propuesta está vigente hasta {__import__('datetime').date.fromisoformat(cotizacion['valida_hasta']):%d/%m/%Y}.\n\n"
           'Quedo atenta a tus comentarios.\nMente y Futuro')
    return asunto,texto
