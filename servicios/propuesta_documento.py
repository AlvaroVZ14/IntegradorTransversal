"""Modelo común del documento v2; conserva los textos originales y no consulta ajustes."""
from copy import deepcopy
from datetime import date
from uuid import uuid4
from mente_futuro.domain import today,money,quote_total
from servicios.cotizacion_defaults import NUMERO_SECCION_INICIAL
from servicios.pago_cotizacion import pago_para_documento

MESES=('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')


def fecha_larga(valor):
    f=date.fromisoformat(str(valor)[:10])
    return f'{f.day} de {MESES[f.month-1]} {f.year}'


def folio(q):
    fecha=(q.get('documento') or {}).get('fecha_emision') or q.get('fecha_emision') or today().isoformat()
    return f"MF-{str(fecha)[:4]}-{int(q.get('numero') or 0):04d}"


def ampliar_borrador(d,caso,plantilla=None):
    """Solo añade campos ausentes. No transforma ni sobrescribe versiones emitidas."""
    p=(plantilla or {}).get('textos') or {}
    inicial={
        'formato_version':2,'fecha_emision':today().isoformat(),
        'objetivos_especificos':p.get('objetivos_especificos',[]),
        'momentos':p.get('momentos',[]),
        'jornadas_duracion':d.get('detalle_modalidad') or f"{d.get('horas') or caso.get('horas') or ''} horas en total",
        'item_descripcion':d.get('detalle') or d.get('servicio') or caso.get('servicio',''),
        'descuento_periodo':'','mostrar_condiciones':True,
    }
    for k,v in inicial.items():d.setdefault(k,deepcopy(v))
    for nombre in ('objetivos_especificos','momentos'):
        if not isinstance(d[nombre],list):d[nombre]=[]
        for i,item in enumerate(d[nombre]):
            if not isinstance(item,dict):item={'texto':str(item)} if nombre=='objetivos_especificos' else {'etiqueta':'','descripcion':str(item)}
            d[nombre][i]={'id':str(uuid4()),**item}
    return d


def modelo(q):
    d=deepcopy(q.get('documento') or {});t=d.get('textos') or {};s={**q['snapshot'],**d}
    mostrar=d.get('mostrar') or {}
    modalidad=str(s.get('modalidad') or '').strip()
    duracion=str(d.get('jornadas_duracion') or d.get('detalle_modalidad') or '').strip()
    # Los borradores antiguos podían tener el nombre de la modalidad en el detalle.
    if modalidad and duracion.lower().startswith(modalidad.lower()):duracion=duracion[len(modalidad):].lstrip(' ·,-:')
    modalidad=' · '.join(x for x in (modalidad if modalidad!='Por definir' else '',duracion if duracion!='Por definir' else '') if x) or 'Por definir'
    neto=quote_total(q['base_clp'],q['descuento_pct'],0);total=quote_total(q['base_clp'],q['descuento_pct'],q['iva_pct'])
    objetivos=[i.get('texto','') if isinstance(i,dict) else str(i) for i in d.get('objetivos_especificos',[])]
    momentos=[i if isinstance(i,dict) else {'descripcion':str(i)} for i in d.get('momentos',[])]
    secciones=[]
    pago=pago_para_documento(d)
    for clave,titulo in [('objetivos','Objetivos'),('metodologia','Metodología'),('detalle','Detalle del servicio'),('valor','Valor del servicio'),('condiciones','Condiciones generales')]:
        if clave in ('objetivos','metodologia') and not mostrar.get(clave,True):continue
        if clave=='condiciones' and not d.get('mostrar_condiciones',True):continue
        secciones.append((clave,NUMERO_SECCION_INICIAL+len(secciones),titulo))
    if pago:secciones.append(('pago',NUMERO_SECCION_INICIAL+len(secciones),'Datos para el pago'))
    return dict(folio=folio(q),fecha=fecha_larga(d.get('fecha_emision') or q['fecha_emision']),
        cliente=s.get('cliente',''),servicio=s.get('servicio',''),modalidad=modalidad,
        participantes=str(s.get('participantes') or '-'),dirigido_a=(t.get('dirigido_a') or '-') if mostrar.get('dirigido_a',True) else '-',
        descripcion=t.get('descripcion','') if mostrar.get('descripcion',True) else '',
        objetivo_general=t.get('objetivos',''),especificos=[x for x in objetivos if x.strip()],
        introduccion=t.get('metodologia',''),momentos=[x for x in momentos if x.get('etiqueta') or x.get('descripcion')],
        item=d.get('item_descripcion') or q.get('detalle') or s.get('servicio',''),
        incluye=t.get('incluye','') if mostrar.get('incluye',True) else '',
        base=money(q['base_clp'])+'.-',neto=money(neto),iva=money(total-neto),total=money(total),
        descuento=float(q['descuento_pct']),motivo=q.get('descuento_motivo') or d.get('descuento_motivo',''),
        periodo=d.get('descuento_periodo',''),exento=q['iva_pct']==0,
        condiciones=[x.lstrip('• ').strip() for x in q.get('condiciones','').splitlines() if x.strip()],
        pago=pago,secciones=secciones,version=q.get('version_cotizacion',1))
