"""Catálogo serializable. Presentación, nunca transiciones ni permisos.

CATALOGO puede exportarse con json.dumps para hojas de cálculo/Looker Studio.
"""
from datetime import date,datetime
from html import escape
from zoneinfo import ZoneInfo

TEXTO_GRAFICOS='#000000'


def _estado(clave,etiqueta,fondo,texto,borde,solido,icono,orden,ayuda):
    return dict(clave=clave,etiqueta=etiqueta,fondo=fondo,texto=texto,borde=borde,
                solido=solido,icono=icono,orden=orden,ayuda=ayuda)


CATALOGO={
 'caso':{
  'solicitud':_estado('solicitud','Solicitud','#EAF1FF','#244FAF','#6699FF','#6699FF','✉',0,'Llegó y falta cotizar.'),
  'cotizada':_estado('cotizada','Cotizada','#F1ECFF','#6533A8','#9966FF','#9966FF','◆',1,'Esperando respuesta del cliente.'),
  'aceptada':_estado('aceptada','Aceptada','#E7F5ED','#216342','#32956B','#32956B','✓',2,'Aceptada; falta registrar la venta.'),
  'seguimiento':_estado('seguimiento','En seguimiento','#FFF6D1','#705800','#C69A00','#FFCC00','◷',3,'Servicio en curso o por cerrar.'),
  'cerrada':_estado('cerrada','Cerrada','#EDF0F4','#4D5C71','#8793A5','#8793A5','■',4,'Servicio terminado.'),
  'rechazada':_estado('rechazada','Rechazada','#FCECEE','#963D47','#E99A9F','#E99A9F','×',5,'No se concretó.')},
 'pago':{
  'pendiente':_estado('pendiente','Pendiente','#FFF6D1','#705800','#C69A00','#FFCC00','◷',0,'El pago está pendiente.'),
  'anticipo':_estado('anticipo','Anticipo pagado','#EAF1FF','#244FAF','#6699FF','#6699FF','◐',1,'Se recibió un anticipo; falta completar el pago.'),
  'pagado':_estado('pagado','Pagado','#E7F5ED','#216342','#32956B','#32956B','✓',2,'Pago completo.')},
 'cotizacion':{
  'borrador':_estado('borrador','Borrador','#EDF0F4','#4D5C71','#8793A5','#8793A5','✎',0,'Propuesta en preparación.'),
  'enviada':_estado('enviada','Enviada','#F1ECFF','#6533A8','#9966FF','#9966FF','↗',1,'Enviada al cliente.'),
  'sin_respuesta':_estado('sin_respuesta','Sin respuesta','#FFF0E0','#8A4800','#D68A37','#E9A45D','◷',2,'Más de 5 días sin respuesta.'),
  'vencida':_estado('vencida','Vencida','#FCECEE','#963D47','#E99A9F','#E99A9F','!',3,'Pasó la vigencia o más de 30 días desde la emisión.'),
  'aceptada':_estado('aceptada','Aceptada','#E7F5ED','#216342','#32956B','#32956B','✓',4,'Propuesta aceptada.'),
  'rechazada':_estado('rechazada','Rechazada','#FCECEE','#963D47','#E99A9F','#E99A9F','×',5,'Propuesta rechazada.')},
 'antiguedad':{
  'reciente':_estado('reciente','Menos de 2 días','#E7F5ED','#216342','#32956B','#32956B','✓',0,'Recibida recientemente.'),
  'atencion':_estado('atencion','De 2 a 5 días','#FFF6D1','#705800','#C69A00','#FFCC00','◷',1,'Conviene revisarla pronto.'),
  'demorada':_estado('demorada','Más de 5 días','#FCECEE','#963D47','#E99A9F','#E99A9F','!',2,'Lleva más de 5 días esperando.')}
}
ALIAS_CASO={'En revisión':'solicitud','Cotizado':'cotizada','Vendido':'aceptada',
            'En ejecución':'seguimiento','Finalizado':'cerrada','Cancelado':'rechazada'}
ETIQUETAS={k:CATALOGO['caso'][v]['etiqueta'] for k,v in ALIAS_CASO.items()}
ETIQUETAS.update({e['etiqueta']:e['etiqueta'] for e in CATALOGO['caso'].values()})
ETIQUETAS['En revisión']='En revisión'


def color_estado(estado,tipo='caso'):
    clave=(ALIAS_CASO.get(estado,estado) if tipo=='caso' else
           'anticipo' if tipo=='pago' and estado=='Abono recibido' else estado)
    for e in CATALOGO[tipo].values():
        if clave in (e['clave'],e['etiqueta']):return dict(e)
    return dict(CATALOGO['caso']['cerrada'],clave='desconocido',etiqueta=str(estado or 'Sin estado'),ayuda='Estado no reconocido.')


def etiqueta_estado(estado):return ETIQUETAS.get(estado,estado)
def estado_visual(estado):return color_estado(estado)['etiqueta']
def etiqueta_opcion_estado(estado):
    return 'Solicitud · en revisión' if estado=='En revisión' else etiqueta_estado(estado)


def etiqueta_con_icono(estado,tipo='caso'):
    e=color_estado(estado,tipo)
    return e['icono']+' '+e['etiqueta']


def clase_estado(estado,tipo='caso'):
    # Clases por combinación visual: evita repetir CSS para pago/caso/cotización.
    paletas=list(dict.fromkeys(tuple(e[k] for k in ('fondo','texto','borde','solido'))
        for grupo in CATALOGO.values() for e in grupo.values()))
    e=color_estado(estado,tipo)
    return 'mfy-estado-'+str(paletas.index(tuple(e[k] for k in ('fondo','texto','borde','solido'))))


def chip_estado(estado,tipo='caso',cantidad=None):
    e=color_estado(estado,tipo)
    texto=e['etiqueta']+(f' · {int(cantidad)}' if cantidad is not None else '')
    ayuda='Solicitud en revisión' if tipo=='caso' and estado=='En revisión' else e['ayuda']
    return (f'<span class="mfy-badge {clase_estado(estado,tipo)}" title="{escape(ayuda,quote=True)}">'
            f'<span aria-hidden="true">{e["icono"]}</span> <span>{escape(texto)}</span></span>')


def mapa_colores(tipo='caso'):
    return {e['etiqueta']:e['solido'] for e in sorted(CATALOGO[tipo].values(),key=lambda e:e['orden'])}


def chip_antiguedad(dias):
    dias=max(0,int(dias));clave='reciente' if dias<2 else 'atencion' if dias<=5 else 'demorada'
    return chip_estado(clave,'antiguedad').replace(CATALOGO['antiguedad'][clave]['etiqueta'],f'{dias} '+('día' if dias==1 else 'días'))


def _fecha(valor):
    if not valor:return None
    if isinstance(valor,datetime):f=valor
    elif isinstance(valor,date):return valor
    else:
        try:f=datetime.fromisoformat(str(valor).replace('Z','+00:00'))
        except ValueError:return None
    return f.astimezone(ZoneInfo('America/Santiago')).date() if f.tzinfo else f.date()


def estado_cotizacion(cotizacion,caso=None,eventos=(),hoy=None):
    """Clasificación visual, sin escrituras; decisiones/envíos requieren evidencia."""
    q=cotizacion;caso=caso or {};hoy=hoy or datetime.now(ZoneInfo('America/Santiago')).date()
    activos=sorted((e for e in eventos if e.get('cotizacion_id')==q.get('id') and not e.get('deshecho_en')),
                   key=lambda e:str(e.get('created_at','')),reverse=True)
    decision=next((e['tipo'] for e in activos if e.get('tipo') in ('aceptar','vender','rechazar')),None)
    if decision:return 'rechazada' if decision=='rechazar' else 'aceptada'
    if q.get('id') and caso.get('cotizacion_aceptada_id')==q['id']:return 'aceptada'
    if q.get('estado') in ('Borrador','borrador'):return 'borrador'
    emision=_fecha(q.get('fecha_emision'));vence=_fecha(q.get('valida_hasta'));dias=(hoy-emision).days if emision else 0
    if (vence and vence<hoy) or dias>30:return 'vencida'
    if dias>5:return 'sin_respuesta'
    if q.get('enviado_en') or any(e.get('tipo')=='envio' for e in activos):return 'enviada'
    # Generada sin evidencia de envío no se etiqueta falsamente Enviada.
    return None


def vigencia_cotizacion(cotizacion,hoy=None):
    hoy=hoy or datetime.now(ZoneInfo('America/Santiago')).date();fin=_fecha(cotizacion.get('valida_hasta'))
    if fin is None:return 'Sin fecha de vigencia'
    dias=(fin-hoy).days
    return f'Vence en {dias} días' if dias>0 else 'Vence hoy' if dias==0 else f'Venció hace {-dias} días'


def html_correo(cuerpo,estado,tipo='caso'):
    """Alternativa HTML escapada; el correo conserva también su texto plano."""
    e=color_estado(estado,tipo)
    chip=(f'<p style="background:{e["fondo"]};color:{e["texto"]};border:1px solid {e["borde"]};padding:10px">'
          +escape(e['icono']+' '+e['etiqueta'])+'</p>')
    return '<!doctype html><html lang="es"><body>'+chip+'<p>'+escape(cuerpo).replace('\n','<br/>')+'</p></body></html>'
