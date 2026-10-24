"""La misma consulta existente, con caché de 60 segundos aislada por sesión."""
import streamlit as st


def cargar_dashboard(repo):
    from servicios.en_vivo import cargar
    lectura = cargar(repo, 'dashboard')
    st.session_state.dashboard_loaded_at = lectura.get('fecha')
    return lectura['datos']['casos'], lectura['datos']['ventas']


def invalidar_dashboard():
    st.session_state.dashboard_revision = st.session_state.get("dashboard_revision", 0) + 1
    for lectura in st.session_state.get("lecturas_edicion",{}).values():
        lectura["reintento"]=0
