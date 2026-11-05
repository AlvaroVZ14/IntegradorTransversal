"""Copiar un mensaje no lo envía ni lo registra como contacto realizado."""
import streamlit as st
from streamlit.components.v2 import component
from utils.estilos import CSS_COPIAR
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def _javascript():
    return Path(__file__).with_suffix('.js').read_text(encoding='utf-8')


def copiar_mensaje(texto,key,*,etiqueta='Copiar',confirmacion='Mensaje copiado.'):
    puente=component('mfy_copiar_hoy',html='<button type="button">Copiar</button>',css=CSS_COPIAR,js=_javascript())
    estado=puente(data={'text':texto,'confirmation':confirmacion,'label':etiqueta},default={'copiado':False,'fallo':False},on_copiado_change=lambda:None,on_fallo_change=lambda:None,key=key,height=50)
    if estado.copiado==texto:st.caption(confirmacion)
    if estado.fallo:
        st.session_state[key+'_manual']=texto
        st.text_area('Selecciona y copia este texto',key=key+'_manual',height=90)
        st.caption('Tu navegador no permitió copiar automáticamente. Mantén pulsado el texto y elige Copiar.')
