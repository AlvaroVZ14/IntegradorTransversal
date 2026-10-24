"""Borrador público por pestaña, sin credenciales ni consentimiento persistente."""
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

import streamlit as st
from streamlit.components.v2 import component
from mente_futuro.domain import SERVICES, TOPICS, MODALITIES
from servicios.formulario_publico import CAMPOS
from utils.solicitud_borrador import DEFAULTS
from utils.validaciones import validar_campo

TEXTOS = ('cliente','contacto','rut','cargo','email','telefono','lugar','detalle')


def iniciar():
    if not st.session_state.get('publico_borrador'):
        st.session_state.publico_borrador = dict(id=str(uuid4()), token=str(uuid4()), step=1,
            values={k:DEFAULTS[k] for k in CAMPOS})
    return st.session_state.publico_borrador


def puente(borrador):
    bridge=component('mfy_publico_borrador',html='<span aria-hidden="true"></span>',
        js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    resultado=bridge(data={**borrador,'texts':list(TEXTOS),'focus':st.session_state.pop('publico_focus',None),
        'ack':st.session_state.get('publico_ack',{}),
        'discard':st.session_state.get('publico_descartados',[])},
        default={'recovered':None},on_recovered_change=lambda:None,key='publico_backup',height=0)
    entrada=resultado.recovered
    if not isinstance(entrada,dict) or entrada==st.session_state.get('publico_recuperado'):return
    st.session_state.publico_recuperado=entrada
    try:
        UUID(entrada['id']); UUID(entrada['token'])
    except (ValueError,TypeError,KeyError,AttributeError):return
    if entrada['id'] in st.session_state.get('publico_descartados',[]):return
    valores=entrada.get('values')
    if not isinstance(valores,dict):return
    opciones={'servicio':SERVICES,'tematica':TOPICS,'modalidad':MODALITIES}
    for campo,valor in valores.items():
        if campo not in CAMPOS:continue
        if campo in TEXTOS and (not isinstance(valor,str) or len(valor)>10000):continue
        if campo in opciones and valor not in opciones[campo]:continue
        if campo in ('participantes','horas'):
            if isinstance(valor,bool) or validar_campo(campo,valor):continue
            valor=int(valor) if campo=='participantes' else float(valor)
        if campo=='fecha_preferida' and valor is not None:
            try:date.fromisoformat(valor)
            except (ValueError,TypeError):continue
        borrador['values'][campo]=valor
        st.session_state.pop('publico_'+campo,None)
    borrador['id'],borrador['token']=entrada['id'],entrada['token']
    paso=entrada.get('step')
    if type(paso) is int and 1<=paso<=3:borrador['step']=paso
    st.session_state.publico_ack=dict(borrador['values'])


def descartar(borrador):
    st.session_state.setdefault('publico_descartados',[]).append(borrador['id'])
    st.session_state.publico_borrador=None
    for key in list(st.session_state):
        if key.startswith('publico_') and key not in ('publico_descartados','publico_recibo'):
            del st.session_state[key]
