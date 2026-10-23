"""Captura de texto con pausa breve; recuperación administrativa por usuario/caso."""
from pathlib import Path
import streamlit as st
from streamlit.components.v2 import component
from servicios.cotizacion_asistida import SECCIONES

TEXTOS=['detalle','condiciones','descuento_motivo',*SECCIONES]


def capturar(repo,caso_id,draft):
    repo.owner_only()
    puente=component('mfy_cotizacion_texto',html="<span aria-hidden='true'></span>",js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    saved={f:draft['datos']['textos'].get(f,'') if f in SECCIONES else draft['datos'].get(f,'') for f in TEXTOS}
    resultado=puente(data=dict(user=repo.user.id,id=caso_id,fields=TEXTOS,saved=saved if not draft['pendiente'] else draft.get('confirmado',{}),ack=draft.get('ack',{}),reset=draft.get('reset_local',{})),
        default={'patch':{}},on_patch_change=lambda:None,key='cottext_'+caso_id,height=0)
    patch=resultado.patch
    if not isinstance(patch,dict) or patch==draft.get('ack'):return
    draft['ack']=dict(patch)
    for campo,valor in patch.items():
        if campo not in TEXTOS or not isinstance(valor,str) or len(valor)>5000:continue
        destino=draft['datos']['textos'] if campo in SECCIONES else draft['datos']
        destino[campo]=valor;draft['pendiente']=True
        st.session_state[f'cotedit_{caso_id}_{campo}']=valor
