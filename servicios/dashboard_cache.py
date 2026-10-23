"""La misma consulta existente, con caché de 60 segundos aislada por sesión."""
from uuid import uuid4
from time import time
import streamlit as st


@st.cache_data(ttl=60, show_spinner=False, max_entries=64)
def _consultar(ambito, revision, _repo):
    _repo.owner_only()
    return _repo.cases(), _repo.sales(), time()


def cargar_dashboard(repo):
    repo.owner_only()
    if "dashboard_cache_scope" not in st.session_state:
        st.session_state.dashboard_cache_scope = str(uuid4())
    casos,ventas,fecha = _consultar(st.session_state.dashboard_cache_scope,
                     st.session_state.get("dashboard_revision", 0), repo)
    st.session_state.dashboard_loaded_at=fecha
    return casos,ventas


def invalidar_dashboard():
    st.session_state.dashboard_revision = st.session_state.get("dashboard_revision", 0) + 1
    for lectura in st.session_state.get("lecturas_edicion",{}).values():
        lectura["reintento"]=0
