import streamlit as st
from supabase_auth.errors import AuthApiError

from mente_futuro.presentation import CSS, LOGO, FAVICON
from servicios.repositorio import Repository, public_client
from servicios.sesion import restaurar, perfil_verificado
from utils.permisos import guard_route
from mente_futuro.ui import login, logout, show_error
from utils.componentes import identidad_usuario, pie_portal
from utils.navegacion import crear_paginas, cerrar_menu_movil_al_navegar, menu_lateral, resolver_ruta_desconocida
from utils.borrador_local import limpiar_borrador_al_salir
from utils.sesion_cookie import cookie_inicial, ordenar_cookie, recordar_admin, puente_cookie, pantalla_restaurando, mantener_sesion_activa

st.set_page_config(page_title='Mente y Futuro · Portal',page_icon=FAVICON.read_text(encoding='utf-8'),layout='wide')
st.markdown(CSS,unsafe_allow_html=True)


def main():
    st.session_state.pop('_repo_actual',None)
    # Antes de Auth, red, cookies o cualquier retorno temprano: siempre igual.
    desconocida=resolver_ruta_desconocida()
    registro,paginas=crear_paginas()
    actual=st.navigation(registro,position='hidden')
    if desconocida:st.session_state['ruta_inexistente']=True
    if st.query_params.get('vista')=='solicitud':
        # Canal público separado: nunca restaura ni utiliza una sesión privada.
        from paginas.solicitud_publica import formulario_publico
        from utils.componentes import mostrar_celebracion
        formulario_publico()
        mostrar_celebracion()
        return
    cookie=cookie_inicial()
    if 'auth_client' not in st.session_state and not st.session_state.get('_restauracion_intentada'):
        st.session_state['_restauracion_intentada']=True
        if cookie:
            carga=st.empty()
            carga.image(str(LOGO),width=260)
            with st.spinner('Recuperando tu sesión…'):
                try:
                    restored=restaurar(cookie,public_client)
                    if restored:
                        client,user,perfil,session,expires=restored
                        st.session_state.auth_client=client
                        st.session_state['_cookie_expires']=expires
                    else:ordenar_cookie('clear')
                except (AuthApiError,PermissionError):
                    ordenar_cookie('clear')
                except Exception:
                    # No borrar un token válido por una caída de red.
                    st.session_state['_restauracion_intentada']=False
                    pantalla_restaurando()
                    st.warning('No pudimos conectar para recuperar tu sesión. Reintenta cuando vuelva la conexión.')
                    return
            carga.empty()
    client=st.session_state.get('auth_client')
    repo=None
    if client:
        try:
            getter=getattr(client.auth,'get_session',None)
            if getter:getter()
            user,perfil=perfil_verificado(client)
            repo=Repository(client,user,perfil)
            recordar_admin(client,perfil)
        except (AuthApiError,PermissionError):
            logout()
        except Exception as error:
            show_error(error,'No pudimos verificar tu sesión. Revisa la conexión e intenta nuevamente.')
            if st.button('Reintentar'):st.rerun()
            return
    if not puente_cookie():
        pantalla_restaurando()
        return
    if st.session_state.pop('_cookie_aviso',False):
        st.warning('El navegador no permitió recordar tu sesión. Puedes usar la app; al recargar tendrás que ingresar nuevamente.')
    if repo is None:
        if st.query_params.get('vista')=='solicitud':
            st.session_state['destino_tras_login']='Nueva solicitud'
        elif actual.title!='Inicio':st.session_state['destino_tras_login']=actual.title
        login()
        return
    st.session_state._repo_actual=repo
    destino=None
    if st.session_state.pop('inicio_tras_login',False):
        destino=guard_route(repo.profile,st.session_state.pop('destino_tras_login',None))
    if actual.title=='Inicio' or st.session_state.pop('ruta_inexistente',False):
        destino=destino or ('Hoy' if repo.is_owner else 'Nueva solicitud')
    if 'pagina' in st.query_params:destino=guard_route(repo.profile,st.query_params.pop('pagina'))
    if 'pending_navigation' in st.session_state:destino=guard_route(repo.profile,st.session_state.pop('pending_navigation'))
    segura=guard_route(repo.profile,destino or actual.title)
    if not repo.is_owner:
        for key in list(st.query_params):
            if key!='vista':del st.query_params[key]
        st.session_state.pop('selected_case',None)
    if segura!=actual.title:st.switch_page(paginas[segura])
    st.session_state.navigation=segura
    st.logo(str(LOGO),size='large',icon_image=FAVICON.read_text(encoding='utf-8'))
    with st.sidebar,st.container(key='mfy_sidebar'):
        menu_lateral(repo.profile,paginas,segura)
        with st.container(key='mfy_sidebar_bottom'):
            identidad_usuario(repo.profile.get('nombre'),repo.is_owner)
            from utils.en_vivo import indicador
            indicador({'Hoy':'hoy','Dashboard':'dashboard','Casos y cotizaciones':'casos'}.get(segura,'solicitud'),lateral=True)
            if st.button('Cerrar sesión',key='logout',width='stretch',icon=':material/logout:'):logout()
    cerrar_menu_movil_al_navegar()
    limpiar_borrador_al_salir(repo.user.id)
    mantener_sesion_activa()
    if 'notice' in st.session_state:st.success(st.session_state.pop('notice'))
    actual.run()
    from utils.componentes import mostrar_celebracion
    mostrar_celebracion()


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        show_error(error,'No pudimos cargar la información. Reintenta en unos momentos.')
        if st.button('Volver al ingreso',key='recover_login'):logout()
    finally:
        if st.query_params.get('vista')!='solicitud':pie_portal()
