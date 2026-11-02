"""Herramientas del portal que se conservan fuera del flujo de cotización."""
import streamlit as st
from utils.permisos import require_admin


def opciones_portal(repo):
    require_admin(repo)
    with st.expander('Enlaces, avisos y respaldos',key='opciones_portal',on_change='rerun') as panel:
        if not panel.open:return
        try:row=repo.quote_settings()
        except Exception:
            st.warning('No pudimos cargar las opciones del portal. Esto no afecta la creación de cotizaciones.');return
        from paginas.configuracion_formulario import configuracion_formulario
        from paginas.hoy import configurar_hoy
        from paginas.estado import tarjeta_respaldo
        configuracion_formulario(repo,row)
        configurar_hoy(repo,row)
        tarjeta_respaldo(repo)
