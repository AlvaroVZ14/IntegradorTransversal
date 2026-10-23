"""Cookie mediante el componente oficial de Streamlit v2; sin librerías externas."""
import json
from pathlib import Path
from time import time
from urllib.parse import unquote
from uuid import uuid4
import streamlit as st
from streamlit.components.v2 import component
from servicios.sesion import COOKIE,DIAS
from mente_futuro.presentation import LOGO


def cookie_inicial():
    value=st.context.cookies.get(COOKIE,'')
    return unquote(value) if isinstance(value,str) else ''


def ordenar_cookie(accion,token=None,expires=None):
    st.session_state['_cookie_command']=dict(id=str(uuid4()),action=accion,token=token,expires=expires)


def recordar_admin(client,perfil):
    if perfil.get('rol')!='admin':
        if not st.session_state.get('_cookie_cliente_limpia'):
            ordenar_cookie('clear');st.session_state['_cookie_cliente_limpia']=True
            st.session_state.pop('_cookie_token_confirmado',None)
        return
    getter=getattr(client.auth,'get_session',None)
    if not getter:return
    session=getter()
    token=getattr(session,'refresh_token',None)
    if not token or st.session_state.get('_cookie_token_confirmado')==token:return
    vence=st.session_state.setdefault('_cookie_expires',time()+DIAS*86400)
    actual=st.session_state.get('_cookie_command',{})
    if actual.get('action')=='save' and actual.get('token')==token:return
    ordenar_cookie('save',token,vence)


def puente_cookie():
    command=st.session_state.get('_cookie_command',{})
    acknowledged=st.session_state.get('_cookie_ack','')
    bridge=component('mfy_sesion_cookie',html='<span aria-hidden="true"></span>',
        js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    result=bridge(data=dict(command,ack=acknowledged),default={'ack':{}},
        on_ack_change=lambda:None,key='mfy_sesion_cookie',height=0)
    ack=result.ack or {}
    if not command or command.get('id')==acknowledged:return True
    if ack.get('id')!=command['id']:return False
    st.session_state['_cookie_ack']=command['id']
    if command.get('action')=='save':
        st.session_state['_cookie_token_confirmado']=command.get('token')
        if not ack.get('ok'):st.session_state['_cookie_aviso']=True
    # Evita que el token siga viajando como datos del componente después de guardar.
    st.session_state.pop('_cookie_command',None)
    return True


def pantalla_restaurando():
    with st.container(key='mfy_login'):
        st.image(str(LOGO),width='stretch')
        st.info('Preparando tu sesión…')
        if st.button('Reintentar recuperación',key='reintentar_cookie'):st.rerun()


@st.fragment(run_every='30s')
def mantener_sesion_activa():
    """Renueva también cuando solo se actualizan fragmentos del Dashboard."""
    from supabase_auth.errors import AuthApiError
    client=st.session_state.get('auth_client')
    if not client:return
    getter=getattr(client.auth,'get_session',None)
    if not getter:return
    try:
        session=getter()
        token=getattr(session,'refresh_token',None)
        repo=st.session_state.get('_repo_actual')
        if (repo and repo.profile.get('rol')=='admin' and token
            and token!=st.session_state.get('_cookie_token_confirmado')
            and not st.session_state.get('_cookie_command')):
            # El marco revalida el rol y escribe la cookie antes de dibujar datos.
            st.rerun(scope='app')
    except AuthApiError:
        from mente_futuro.ui import logout
        logout()
    except Exception:
        st.caption('No pudimos renovar la sesión ahora. Reintentaremos cuando vuelva la conexión.')
