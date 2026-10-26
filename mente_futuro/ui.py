"""Componentes comunes y acceso al portal."""
import logging

import streamlit as st
from supabase_auth.errors import AuthApiError

from .presentation import LOGO
from .repository import ConfigurationError, public_client
from utils.componentes import encabezado_pagina, panel_marca_login

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
    from utils.sesion_cookie import ordenar_cookie
    ordenar_cookie('clear')
    st.session_state['_restauracion_intentada']=True
    st.rerun()


def header(title, subtitle, section):
    """Adaptador de importaciones anteriores al encabezado común."""
    encabezado_pagina(title, subtitle, section, "✦")


def login():
    with st.container(key='mfy_login_layout'):
        marca,acceso=st.columns([1.05,1],gap='large')
        with marca:panel_marca_login()
        with acceso:_tarjeta_login()


def _tarjeta_login():
    from servicios.acceso import permitir_intento
    from utils.validaciones import validar_campo
    with st.container(key="mfy_login"):
        st.image(str(LOGO), width="stretch")
        st.title("Te damos la bienvenida")
        st.markdown('<p class="mfy-login-subtitle">Acceso del equipo y cuentas de cliente.</p>', unsafe_allow_html=True)
        if st.session_state.get('_confirmacion_error'):st.warning(st.session_state.pop('_confirmacion_error'))
        signin, signup = st.tabs(["Iniciar sesión", "Crear cuenta de cliente"],key='acceso_pestana',on_change='rerun')
        with signin:
            with st.form("login"):
                email = st.text_input("Correo electrónico",key='login_correo', max_chars=254, placeholder="nombre@correo.cl")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar a mi espacio", type="primary", width="stretch")
            if submitted:
                if not email.strip() or not password:
                    st.error("Ingresa tu correo y contraseña.")
                else:
                    try:
                        permitir_intento('ingreso')
                        client = public_client()
                        result = client.auth.sign_in_with_password({"email":email.strip(), "password":password})
                        if result.session:
                            from servicios.sesion import iniciar_sesion
                            iniciar_sesion(client)
                            st.rerun()
                    except AuthApiError:
                        st.error("No fue posible ingresar. Revisa tu correo, contraseña y confirmación de cuenta.")
                    except ValueError as error:
                        st.warning(str(error))
                    except Exception as error:
                        show_error(error, "No pudimos conectar con el servicio de acceso. Intenta nuevamente.")
            with st.expander('¿No recibiste el correo de confirmación?'):
                reenviar=st.text_input('Correo de la cuenta',max_chars=254,key='reenviar_correo')
                if st.button('Solicitar otro correo',key='reenviar_confirmacion'):
                    if validar_campo('email',reenviar):st.error('Escribe un correo válido para continuar.')
                    else:
                        try:
                            permitir_intento('registro')
                            public_client().auth.resend({'type':'signup','email':reenviar.strip()})
                            st.info('Si la cuenta necesita confirmación, recibirás un correo. Revisa también Spam.')
                        except Exception:st.warning('No pudimos solicitar el correo. Espera unos minutos o envía tu solicitud sin crear cuenta.')
        with signup:
            st.write('Tus datos quedan listos para tus próximas solicitudes.')
            with st.form("signup"):
                name = st.text_input("Nombre completo", max_chars=160)
                new_email = st.text_input("Tu correo", max_chars=254)
                new_password = st.text_input("Crea una contraseña", type="password", help="Usa al menos 8 caracteres.")
                confirm = st.text_input("Repite la contraseña", type="password")
                honey=st.text_input('Deja este campo vacío',key='signup_sitio_confirmacion')
                submitted = st.form_submit_button("Crear mi cuenta", type="primary", width="stretch")
            if submitted:
                if honey or len(name.strip()) < 2 or validar_campo('email',new_email.strip()) or len(new_password) < 8 or new_password != confirm:
                    st.error("Completa tu nombre y correo, y usa contraseñas iguales de al menos 8 caracteres.")
                else:
                    try:
                        permitir_intento('registro')
                        client = public_client()
                        result = client.auth.sign_up({"email":new_email.strip(), "password":new_password, "options":{"data":{"nombre":name.strip()}}})
                        if result.session:
                            from servicios.sesion import iniciar_sesion
                            iniciar_sesion(client)
                            st.rerun()
                        st.session_state['_signup_aviso']=new_email.strip()
                    except Exception as error:
                        if getattr(error,'code','') in ('user_already_exists','email_exists'):
                            st.session_state['_signup_aviso']=new_email.strip()
                        else:st.warning('No pudimos completar el registro o enviar su confirmación. Puedes reintentar más tarde o enviar tu solicitud sin crear cuenta.')
            if st.session_state.get('_signup_aviso'):
                st.info('Si este correo es nuevo, revisa el mensaje para confirmar tu cuenta. Si ya tenías una cuenta, puedes iniciar sesión con tus datos.')
                def ingresar():
                    st.session_state['login_correo']=st.session_state['_signup_aviso']
                    st.session_state['acceso_pestana']='Iniciar sesión'
                st.button('Iniciar sesión con este correo',on_click=ingresar,width='stretch')
        st.markdown('<div class="note">Puedes enviar una solicitud sin cuenta. Crear una cuenta es opcional: deja tu nombre y correo listos para próximas solicitudes. Administración conserva su acceso de gestión.</div>', unsafe_allow_html=True)
        if st.button('Enviar solicitud sin cuenta',type='tertiary',width='stretch'):
            st.query_params['vista']='solicitud';st.rerun()
