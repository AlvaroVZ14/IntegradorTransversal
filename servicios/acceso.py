"""Confirmación de correo y límites amables de la interfaz. Auth valida en servidor."""
import re
from time import time
import streamlit as st
from servicios.repositorio import public_client

def permitir_intento(tipo,ahora=None):
    ahora=time() if ahora is None else ahora
    limite=5 if tipo=='registro' else 10
    clave='acceso_intentos_'+tipo
    intentos=[t for t in st.session_state.get(clave,[]) if ahora-t<300]
    if len(intentos)>=limite:raise ValueError('Espera unos minutos antes de volver a intentarlo.')
    st.session_state[clave]=[*intentos,ahora]

def confirmar_enlace():
    """Token de un solo uso; no lee roles ni redirecciones del enlace."""
    if 'token_hash' in st.query_params:
        token=st.query_params.pop('token_hash');tipo=st.query_params.pop('type','email')
        st.query_params['vista']='acceso'
        if isinstance(token,str) and re.fullmatch(r'[a-fA-F0-9]{32,128}',token) and tipo in ('email','signup'):
            st.session_state['_confirmacion_correo']=token
        else:st.session_state['_confirmacion_error']='El enlace no es válido. Puedes iniciar sesión o solicitar otro correo de confirmación.'
    token=st.session_state.get('_confirmacion_correo')
    if not token:return False
    from mente_futuro.presentation import LOGO
    with st.container(key='mfy_login'):
        st.image(str(LOGO),width='stretch')
        st.title('Confirma tu correo')
        st.write('Al confirmar, tus datos quedarán listos para tus próximas solicitudes.')
        if st.button('Confirmar correo y continuar',type='primary',width='stretch'):
            try:
                permitir_intento('confirmacion')
                client=public_client()
                resultado=client.auth.verify_otp({'token_hash':token,'type':'email'})
                if not resultado.session:raise ValueError('No se confirmó la sesión.')
                st.session_state.auth_client=client
                st.session_state.inicio_tras_login=True
                st.session_state.pop('_confirmacion_correo',None)
                st.query_params.pop('vista',None)
                st.rerun()
            except Exception:
                st.session_state.pop('_confirmacion_correo',None)
                st.session_state['_confirmacion_error']='El enlace venció o ya fue utilizado. Inicia sesión si ya confirmaste tu cuenta; si no, solicita un nuevo correo.'
                st.rerun()
    return True
