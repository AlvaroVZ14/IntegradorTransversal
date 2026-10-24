"""Reloj local del navegador; no genera reruns ni consultas por segundo."""
from pathlib import Path
from streamlit.components.v2 import component
from servicios.en_vivo import estado
from utils.estilos import CSS_EN_VIVO


def indicador(vista, publicar=False, pausado=False):
    lectura = estado(vista)
    puente = component('mfy_en_vivo', html='<span class="live" role="status"></span>',
                       css=CSS_EN_VIVO,
                       js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    puente(data=dict(vista=vista, publicar=publicar, pausado=pausado, fecha=lectura.get('fecha'),
                      conectado=lectura.get('conectado', True), falta_sql=lectura.get('falta_sql', False)),
           key='mfy_live_'+vista+('_datos' if publicar else '_cabecera'), height=0 if publicar else 65)
