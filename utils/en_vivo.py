"""Reloj local del navegador; no genera reruns ni consultas por segundo."""
from pathlib import Path
import streamlit as st
from streamlit.components.v2 import component
from servicios.en_vivo import estado
from utils.estilos import CSS_EN_VIVO


def guardar_metricas(vista, metricas):
    st.session_state['mfy_metricas_'+vista]=[(str(label),str(valor)) for label,valor in metricas]


def _componente():
    return component('mfy_en_vivo', html='<span class="live" role="status"></span><div class="mfy-glass-chips"></div>',
                     css=CSS_EN_VIVO,js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))


def metricas_cabecera(vista):
    predeterminadas={'hoy':['Por cotizar','Pagos por registrar','Acciones pendientes'],
                     'dashboard':['Ventas del período','Nuevas solicitudes'],
                     'casos':['Casos totales','Por etapa']}
    metricas=st.session_state.get('mfy_metricas_'+vista,[(s,'—') for s in predeterminadas[vista]])
    _componente()(data=dict(vista=vista,modo='metricas',metricas=metricas),key='mfy_chips_'+vista,height='content')


def indicador(vista, publicar=False, pausado=False, lateral=False):
    lectura = estado(vista)
    puente = _componente()
    puente(data=dict(vista=vista, publicar=publicar, pausado=pausado, fecha=lectura.get('fecha'),
                      lateral=lateral,metricas=st.session_state.get('mfy_metricas_'+vista,[]),
                      conectado=lectura.get('conectado', True), falta_sql=lectura.get('falta_sql', False)),
           key='mfy_live_'+vista+('_datos' if publicar else '_lateral' if lateral else '_cabecera'), height=0 if publicar else 'content')
