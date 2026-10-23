"""Borrador por cuenta. Nunca contiene Auth; consentimiento no se restaura."""
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import streamlit as st
from streamlit.components.v2 import component
from mente_futuro.domain import SERVICES, TOPICS, MODALITIES
from servicios.solicitud_rapida import TEXTOS, ORIGENES

DEFAULTS = dict(cliente='',rut='',contacto='',cargo='',email='',telefono='',servicio=SERVICES[0],
                tematica=TOPICS[0],participantes=1,horas=1.0,modalidad=MODALITIES[2],
                lugar='',fecha_preferida=None,detalle='',cliente_id=None,origen=ORIGENES[0])


def iniciar(repo):
    if st.session_state.get('solicitud_usuario') != repo.user.id:
        st.session_state.solicitud_usuario=repo.user.id
        st.session_state.solicitud_borrador=None
    if not st.session_state.get('solicitud_borrador'):
        valores={**DEFAULTS,'origen':st.session_state.get('solicitud_ultimo_origen',ORIGENES[0])}
        if not repo.is_owner:
            valores.update(email=repo.user.email,contacto=repo.profile.get('nombre',''),origen='Formulario web')
        st.session_state.solicitud_borrador=dict(id=str(uuid4()),values=valores)
    st.session_state.request_id=st.session_state.solicitud_borrador['id']
    return st.session_state.solicitud_borrador


def recuperar(repo,borrador):
    puente=component('mfy_solicitud_borrador',html="<span aria-hidden='true'></span>",
                     js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    resultado=puente(data=dict(user=repo.user.id,id=borrador['id'],values=borrador['values'],texts=list(TEXTOS),
        discard=st.session_state.get('solicitud_descartados',[]),ack=st.session_state.get('solicitud_recuperada_id'),
        ackValues=st.session_state.get('solicitud_ack',{})),
        default={'recovered':None},on_recovered_change=lambda:None,key='request_backup',height=0)
    entrada=resultado.recovered
    if not isinstance(entrada,dict) or entrada==st.session_state.get('solicitud_recuperacion_ack'):return
    st.session_state.solicitud_recuperacion_ack=entrada
    try: UUID(str(entrada.get('id')))
    except (ValueError,TypeError,AttributeError):return
    if entrada['id'] in st.session_state.get('solicitud_descartados',[]):return
    valores=entrada.get('values')
    if not isinstance(valores,dict):return
    borrador['id']=entrada['id']
    for campo,valor in valores.items():
        if campo not in DEFAULTS:continue
        if not repo.is_owner and campo in ('contacto','email','cliente_id','origen'):continue
        if campo in TEXTOS and (not isinstance(valor,str) or len(valor)>10000):continue
        if campo in ('horas','participantes'):
            from utils.validaciones import validar_campo
            if validar_campo(campo,valor):continue
            valor=float(valor) if campo=='horas' else int(valor)
        opciones={'servicio':SERVICES,'tematica':TOPICS,'modalidad':MODALITIES,'origen':ORIGENES}
        if campo in opciones and valor not in opciones[campo]:continue
        if campo=='fecha_preferida' and valor:
            try: date.fromisoformat(valor)
            except (TypeError,ValueError):continue
        if campo=='cliente_id' and valor is not None and not isinstance(valor,str):continue
        borrador['values'][campo]=valor
        st.session_state.pop('request_'+campo,None)
    st.session_state.solicitud_ack=dict(borrador['values'])
    st.session_state.solicitud_recuperada_id=borrador['id']
    st.session_state.request_id=borrador['id']


def limpiar(borrador):
    st.session_state.setdefault('solicitud_descartados',[]).append(borrador['id'])
    st.session_state.solicitud_ultimo_origen=borrador['values']['origen']
    st.session_state.solicitud_borrador=None
    for key in list(st.session_state):
        if key.startswith('request_') and key not in ('request_receipt',):
            del st.session_state[key]
    for key in ('solicitud_recuperada_id','solicitud_recuperacion_ack','solicitud_ack','solicitud_manual_correo','solicitud_busqueda','solicitud_duplicado'):
        st.session_state.pop(key,None)
