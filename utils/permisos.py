"""El rol siempre procede de mf_perfiles, nunca de la URL o user_metadata."""
ADMIN_PAGES = ("Hoy", "Nueva solicitud", "Casos y cotizaciones", "Dashboard")
CLIENT_PAGE = "Nueva solicitud"


def es_admin(profile):
    return profile.get("rol") == "admin"


def require_admin(repo):
    if not es_admin(repo.profile):
        raise PermissionError("Esta sección está disponible solo para Administración.")


def allowed_pages(profile):
    return list(ADMIN_PAGES) if es_admin(profile) else [CLIENT_PAGE]


def guard_route(profile, route):
    pages = allowed_pages(profile)
    if es_admin(profile) and route == 'Estado':
        return route
    return route if route in pages else 'Hoy' if es_admin(profile) else CLIENT_PAGE


def proteger_pagina(titulo,admin=False):
    """Defensa adicional en cada archivo de página, aunque el marco ya guarde."""
    import streamlit as st
    repo=st.session_state.get('_repo_actual')
    if repo is None:
        st.session_state['destino_tras_login']=titulo
        if st.query_params.get('vista')=='acceso':
            from mente_futuro.ui import login
            login()
        else:
            from paginas.formulario import formulario
            formulario()
        st.stop()
    if admin and not es_admin(repo.profile):
        st.session_state['pending_navigation']='Nueva solicitud'
        st.switch_page('paginas/nueva_solicitud.py')
    return repo
