"""Un borrador por persona y modo; la identidad cliente nunca se restaura del navegador."""
from datetime import date
from pathlib import Path
from uuid import UUID,uuid4
import streamlit as st
from streamlit.components.v2 import component
from utils.formulario_config import valores_iniciales,CAMPOS,TEXTOS,OPCIONES,BLOQUEADOS
from utils.validaciones import validar_campo

def contexto(modo,repo=None):return modo+':'+(str(repo.user.id) if repo else 'visitante')
def prefijo(modo):return 'publico_' if modo=='publico' else 'request_'

def iniciar(modo,repo,catalogo):
    scope=contexto(modo,repo)
    almacen=st.session_state.setdefault('formularios',{})
    if scope not in almacen:
        valores=valores_iniciales()
        antiguo=st.session_state.get('publico_borrador') if modo=='publico' else st.session_state.get('solicitud_borrador') if st.session_state.get('solicitud_usuario')==getattr(getattr(repo,'user',None),'id',None) else None
        if antiguo:valores.update({k:v for k,v in antiguo.get('values',{}).items() if k in valores})
        if not valores['servicio']:valores['servicio']=next(iter(catalogo['servicios']),None)
        if not valores['tematicas']:valores['tematicas']=[valores.get('tematica') or catalogo['tematicas'][0]] if catalogo['tematicas'] else []
        valores['origen']=st.session_state.get('solicitud_ultimo_origen',valores['origen'])
        almacen[scope]=dict(id=(antiguo or {}).get('id',str(uuid4())),token=(antiguo or {}).get('token',str(uuid4())),step=1,values=valores,tocados=[],ack={},scope=scope)
    borrador=almacen[scope]
    borrador['values']['tematica']=next(iter(borrador['values']['tematicas']),None)
    if modo=='cliente':
        borrador['values'].update(contacto=repo.profile.get('nombre',''),email=repo.user.email or '',cliente_id=None,origen='Formulario web',referido_por='')
    st.session_state.request_id=borrador['id']
    return borrador

def recuperar(borrador,modo,repo,catalogo):
    bridge=component('mfy_formulario_borrador',html='<span aria-hidden="true"></span>',
        js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    legacy='mfy-public-draft-v1' if modo=='publico' else 'mfy-solicitud:'+str(repo.user.id)
    respuesta=bridge(data={**{k:borrador[k] for k in ('id','token','step','values','ack')},'texts':[k for k in TEXTOS if modo in CAMPOS[k].modos and k not in BLOQUEADOS[modo]],
        'prefix':prefijo(modo),'storageKey':'mfy-formulario:'+borrador['scope'],'legacyKey':legacy,
        'focus':borrador.pop('focus',None),'discard':st.session_state.get('formularios_descartados',[])},
        default={'recovered':None},on_recovered_change=lambda:None,key='ff_backup_'+modo,height=0)
    entrada=respuesta.recovered
    if not isinstance(entrada,dict) or entrada==borrador.get('recuperado'):return
    borrador['recuperado']=entrada
    try:UUID(entrada['id']);UUID(entrada.get('token',borrador['token']))
    except (ValueError,TypeError,KeyError,AttributeError):return
    if entrada['id'] in st.session_state.get('formularios_descartados',[]):return
    valores=entrada.get('values')
    if not isinstance(valores,dict):return
    opciones={'servicio':catalogo['servicios'],'modalidad':OPCIONES['modalidad'],'origen':OPCIONES['origen']}
    for campo,valor in valores.items():
        if campo not in borrador['values'] or campo in BLOQUEADOS[modo]:continue
        if modo!='interno' and campo in ('cliente_id','origen','referido_por'):continue
        if campo in TEXTOS and (not isinstance(valor,str) or len(valor)>CAMPOS[campo].limite):continue
        if campo in opciones and valor is not None and valor not in opciones[campo]:continue
        if campo=='tematicas' and (not isinstance(valor,list) or len(valor)>6 or any(t not in catalogo['tematicas'] for t in valor)):continue
        if campo in ('horas','participantes'):
            if valor is not None and (isinstance(valor,bool) or validar_campo(campo,valor)):continue
            valor=(float(valor) if campo=='horas' else int(valor)) if valor is not None else None
        if campo=='fecha_preferida' and valor:
            try:date.fromisoformat(valor)
            except (ValueError,TypeError):continue
        if campo=='cliente_id' and valor is not None:
            try:UUID(valor)
            except (ValueError,TypeError,AttributeError):continue
        borrador['values'][campo]=valor
        st.session_state.pop(prefijo(modo)+campo,None)
    if 'tematicas' not in valores and valores.get('tematica') in catalogo['tematicas']:borrador['values']['tematicas']=[valores['tematica']]
    borrador.update(id=entrada['id'],token=entrada.get('token',borrador['token']))
    paso=entrada.get('step',1)
    if type(paso) is int and 1<=paso<=3:borrador['step']=paso
    borrador['ack']=dict(borrador['values'])

def limpiar(borrador,modo,repo):
    st.session_state.setdefault('formularios_descartados',[]).append(borrador['id'])
    if modo=='interno':st.session_state.solicitud_ultimo_origen=borrador['values']['origen']
    st.session_state.get('formularios',{}).pop(contexto(modo,repo),None)
    for k in list(st.session_state):
        if k.startswith(prefijo(modo)) or k in ('solicitud_busqueda','solicitud_manual_correo','solicitud_duplicado','solicitud_duplicado_firma'):
            del st.session_state[k]
    st.session_state.pop('publico_borrador',None);st.session_state.pop('solicitud_borrador',None)
