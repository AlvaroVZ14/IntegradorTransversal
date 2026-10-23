"""Componentes comunes y acceso al portal."""
import logging

import streamlit as st
from supabase_auth.errors import AuthApiError

from .presentation import LOGO
from .repository import ConfigurationError, public_client
from utils.componentes import encabezado_pagina

logger = logging.getLogger(__name__)


def show_error(error, message="No pudimos completar la operación. Tus datos no se han confirmado como guardados."):
    # Los mensajes de validación propios se conservan; los fallos técnicos no se exponen.
    if isinstance(error, ValueError) and str(error).startswith(("Este caso", "La tarifa", "La venta", "Ingresa", "Revisa", "Debes", "Selecciona", "La fecha")):
        st.error(str(error))
    elif isinstance(error, PermissionError):
        st.error("Esta sección está disponible solo para Administración. Vuelve a Nueva solicitud.")
    elif isinstance(error, ConfigurationError):
        st.error("El portal necesita completar su configuración. Contacta a la administradora para ayudarte.")
    elif getattr(error, "code", "") in ("PGRST205", "42P01", "PGRST202"):
        st.error("Estamos preparando el portal. Por favor, contacta a la administradora o vuelve a intentarlo más tarde.")
    else:
        st.error(message)
        st.caption("Puedes volver a intentar. Si el problema continúa, contacta a la administradora.")
    logger.warning("Operación fallida: %s (código %s)", type(error).__name__, getattr(error, "code", "n/a"))


def flash(message):
    from servicios.dashboard_cache import invalidar_dashboard
    invalidar_dashboard()
    st.session_state["notice"] = message
    st.rerun()


def logout():
    client = st.session_state.get("auth_client")
    try:
        if client:
            client.auth.sign_out({"scope": "local"})
    except Exception:
        pass
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


def header(title, subtitle, section):
    """Adaptador de importaciones anteriores al encabezado común."""
    encabezado_pagina(title, subtitle, section, "✦")


def login():
    with st.container(key="mfy_login"):
        st.image(str(LOGO), width="stretch")
        st.title("Te damos la bienvenida")
        st.markdown('<p class="mfy-login-subtitle">Conectemos tus necesidades con nuevas oportunidades.</p>', unsafe_allow_html=True)
        signin, signup = st.tabs(["Iniciar sesión", "Crear cuenta de cliente"])
        with signin:
            with st.form("login"):
                email = st.text_input("Correo electrónico", max_chars=254, placeholder="nombre@correo.cl")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar a mi espacio", type="primary", width="stretch")
            if submitted:
                if not email.strip() or not password:
                    st.error("Ingresa tu correo y contraseña.")
                else:
                    try:
                        client = public_client()
                        result = client.auth.sign_in_with_password({"email":email.strip(), "password":password})
                        if result.session:
                            st.session_state.auth_client = client
                            st.session_state.inicio_tras_login = True
                            st.rerun()
                    except AuthApiError:
                        st.error("No fue posible ingresar. Revisa tu correo, contraseña y confirmación de cuenta.")
                    except Exception as error:
                        show_error(error, "No pudimos conectar con el servicio de acceso. Intenta nuevamente.")
        with signup:
            with st.form("signup"):
                name = st.text_input("Nombre completo", max_chars=160)
                new_email = st.text_input("Tu correo", max_chars=254)
                new_password = st.text_input("Crea una contraseña", type="password", help="Usa al menos 8 caracteres.")
                confirm = st.text_input("Repite la contraseña", type="password")
                submitted = st.form_submit_button("Crear mi cuenta", type="primary", width="stretch")
            if submitted:
                if len(name.strip()) < 2 or "@" not in new_email or len(new_password) < 8 or new_password != confirm:
                    st.error("Completa tu nombre y correo, y usa contraseñas iguales de al menos 8 caracteres.")
                else:
                    try:
                        client = public_client()
                        result = client.auth.sign_up({"email":new_email.strip(), "password":new_password, "options":{"data":{"nombre":name.strip()}}})
                        if result.session:
                            st.session_state.auth_client = client
                            st.session_state.inicio_tras_login = True
                            st.rerun()
                        st.success("Revisa tu correo para confirmar la cuenta y luego inicia sesión. Si ya tenías una cuenta, ingresa con tus datos.")
                    except Exception as error:
                        show_error(error, "No se pudo completar el registro. Revisa los datos o intenta más tarde.")
        st.markdown('<div class="note">Desde tu cuenta puedes enviar una solicitud. Revisaremos tus necesidades y te contactaremos para preparar una propuesta a tu medida.</div>', unsafe_allow_html=True)
    st.markdown('''<div class="mfy-login-steps"><span><b>01</b> Cuéntanos qué necesitas</span>
    <span><b>02</b> Revisamos tu solicitud</span>
    <span><b>03</b> Te enviamos una propuesta a tu medida</span></div>''', unsafe_allow_html=True)
