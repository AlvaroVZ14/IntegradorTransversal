"""Preparación visual de Hoy sobre su snapshot; sin lecturas ni escrituras."""
from datetime import datetime
from servicios.hoy import CHILE,instante

DIAS=('lunes','martes','miércoles','jueves','viernes','sábado','domingo')
MESES=('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')


def fecha_larga(ahora):
    local=ahora.astimezone(CHILE) if ahora.tzinfo else ahora
    return f'{DIAS[local.weekday()]} {local.day} de {MESES[local.month-1]}'


def para_hacer_ahora(grupos,limite=5):
    lista=[dict(item,accion=accion) for clave,accion in (('solicitudes','cotizar'),('seguimientos','seguimiento'))
           for item in grupos[clave]]
    lista.sort(key=lambda i:(-i['dias'],str(i['caso'].get('created_at','')),i['caso']['id']))
    return lista if limite is None else lista[:limite]


def hace_cuanto(fecha,ahora):
    ahora=instante(ahora)
    dt=instante(fecha)
    if not dt:return 'Fecha no disponible'
    if len(str(fecha))==10:
        dias=max(0,(ahora.date()-dt.date()).days)
        return 'Hoy' if not dias else f'Hace {dias} '+('día' if dias==1 else 'días')
    segundos=max(0,int((ahora-dt).total_seconds()))
    if segundos<60:return 'Ahora'
    n,unidad=(segundos//60,'minuto') if segundos<3600 else (segundos//3600,'hora') if segundos<86400 else (segundos//86400,'día')
    return f'Hace {n} {unidad}'+('s' if n!=1 else '')


def actividad_reciente(datos,ahora=None,limite=5):
    ahora=instante(ahora) if ahora else datetime.now(CHILE)
    casos={c['id']:c for c in datos['casos']}
    eventos={}
    def agregar(clave,caso_id,fecha,texto,estado=None,icono='•'):
        cuando=instante(fecha)
        if not cuando or cuando>ahora:return
        caso=casos.get(caso_id,{})
        eventos[clave]=dict(id=clave,caso_id=caso_id,fecha=cuando,texto=texto,
            cliente=caso.get('cliente') or 'Cliente',estado=estado,icono=icono,
            relativo=hace_cuanto(fecha,ahora))
    for c in casos.values():agregar('solicitud:'+c['id'],c['id'],c.get('created_at'),'Solicitud recibida','Solicitud','✉')
    for q in datos['cotizaciones']:
        agregar('cotizacion:'+q['id'],q['caso_id'],q.get('created_at') or q.get('fecha_emision'),'Cotización emitida','Cotizada','◆')
    # Ventas y su evento representan una sola acción. El evento da la hora exacta.
    for v in datos['ventas']:
        if not v.get('anulada'):
            agregar('venta:'+v['caso_id'],v['caso_id'],v.get('created_at') or v.get('fecha_venta'),'Venta registrada','En seguimiento','✓')
    for e in sorted(datos['eventos'],key=lambda e:str(e.get('created_at',''))):
        if e.get('deshecho_en'):continue
        tipo=e.get('tipo')
        if tipo in ('aceptar','rechazar','vender','cierre'):
            etiqueta,estado={'aceptar':('Propuesta aceptada','Aceptada'),'rechazar':('Propuesta rechazada','Rechazada'),
                'vender':('Venta registrada','En seguimiento'),'cierre':('Caso cerrado','Cerrada')}[tipo]
            clave='venta:'+e['caso_id'] if tipo=='vender' else 'evento:'+e['id']
            agregar(clave,e['caso_id'],e.get('created_at'),etiqueta,estado,'✓' if tipo!='rechazar' else '×')
    for d in datos.get('documentos',[]):
        if d.get('origen')=='cliente' and d.get('estado_archivo','disponible')=='disponible':
            agregar('documento:'+d['id'],d['caso_id'],d.get('fecha_subida'),'Documento enviado por el cliente',None,'↑')
    return sorted(eventos.values(),key=lambda e:(e['fecha'],e['id']),reverse=True)[:limite]


def avisos_automatizacion(datos,ahora=None):
    """Contrato preparado para Prompt 38. Ausencia de integración = ningún aviso."""
    ahora=instante(ahora) if ahora else datetime.now(CHILE)
    hoja=(datos.get('automatizaciones') or {}).get('hoja_calculo') or {}
    if hoja.get('integrada') is not True:return []
    avisos=[];ultimo=instante(hoja.get('ultima_sincronizacion'))
    if ultimo is None or (ahora-ultimo).total_seconds()>86400:
        avisos.append('La hoja de cálculo está esperando una actualización. Tus datos siguen guardados en la app.')
    if hoja.get('estado_correo') in ('error','fallido','incierto'):
        avisos.append('No pudimos confirmar el correo de aviso. Puedes seguir trabajando y revisar el envío más tarde.')
    return avisos
