"""Componentes comunes y acceso al portal."""
from html import escape
import logging

import streamlit as st
from supabase_auth.errors import AuthApiError

from .presentation import LOGO
from .repository import ConfigurationError, public_client

logger = logging.getLogger(__name__)


def show_error(error, message="No pudimos completar la operación. Tus datos no se han confirmado como guardados."):
    if isinstance(error, (ValueError, PermissionError, ConfigurationError)):
        st.error(str(error))
    elif getattr(error, "code", "") in ("PGRST205", "42P01", "PGRST202"):
        st.error("La base de datos necesita completar su configuración inicial.")
        st.caption("Ejecuta la migración incluida en supabase/migrations. Los pasos están en README.md.")
    else:
        st.error(message)
        st.caption("Puedes volver a intentar. Si el problema continúa, contacta a la administradora.")
    logger.warning("Operación fallida: %s (código %s)", type(error).__name__, getattr(error, "code", "n/a"))


def flash(message):
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
    st.markdown(f'<div class="eyebrow">MI ESPACIO / {escape(section)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="intro">{escape(subtitle)}</div>', unsafe_allow_html=True)


def login():
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.image(str(LOGO), width=280)
        st.markdown('''<div class="login-intro"><div class="eyebrow">PORTAL DE GESTIÓN</div>
        <h1>Tu próximo paso,<br>en un solo lugar.</h1>
        <p>Un espacio para conectar tus necesidades con nuevas oportunidades de aprendizaje y desarrollo.</p>
        <div class="login-features"><span><b>01</b> Cuéntanos qué necesitas</span>
        <span><b>02</b> Revisa tus solicitudes y cotizaciones</span>
        <span><b>03</b> Sigue el avance de cada servicio</span></div></div>''', unsafe_allow_html=True)
    with right:
        st.markdown("<div style='height:45px'></div>", unsafe_allow_html=True)
        st.subheader("Te damos la bienvenida")
        st.caption("Ingresa a tu espacio de Mente y Futuro.")
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
                            st.rerun()
                        st.success("Revisa tu correo para confirmar la cuenta y luego inicia sesión. Si ya tenías una cuenta, ingresa con tus datos.")
                    except Exception as error:
                        show_error(error, "No se pudo completar el registro. Revisa los datos o intenta más tarde.")
        st.markdown('<div class="note">Cada cliente tiene un espacio personal para consultar sus solicitudes. La administración utiliza una cuenta con permisos propios.</div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">MENTE Y FUTURO · Creando canales para el aprendizaje</div>', unsafe_allow_html=True)
