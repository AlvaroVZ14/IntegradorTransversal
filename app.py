import streamlit as st
from supabase_auth.errors import AuthApiError

from mente_futuro.presentation import CSS, LOGO, FAVICON
from servicios.repositorio import Repository, public_client
from servicios.sesion import restaurar, perfil_verificado
from utils.permisos import guard_route
from mente_futuro.ui import login, logout, show_error
from utils.componentes import identidad_usuario, pie_portal
from utils.navegacion import crear_paginas, cerrar_menu_movil_al_navegar, menu_lateral, resolver_ruta_desconocida,rutas_para_perfil
from utils.borrador_local import limpiar_borrador_al_salir
from utils.sesion_cookie import cookie_inicial, ordenar_cookie, recordar_sesion, puente_cookie, pantalla_restaurando, mantener_sesion_activa

st.set_page_config(page_title='Mente y Futuro · Portal',page_icon=FAVICON.read_text(encoding='utf-8'),layout='wide')
st.markdown(CSS,unsafe_allow_html=True)


def main():
    st.session_state.pop('_repo_actual',None)
    st.session_state['_vista_externa']=False
    # Antes de Auth, red, cookies o cualquier retorno temprano: siempre igual.
    desconocida=resolver_ruta_desconocida()
    registro,paginas=crear_paginas()
    actual=st.navigation(registro,position='hidden')
    # st.switch_page limpia los parámetros de URL: retener solo la atribución,
    # sin usarla para decidir sesión, rol o destino.
    if 'canal' in st.query_params:
        from utils.canales import normalizar_canal
        st.session_state['_canal_entrada']=normalizar_canal(st.query_params['canal'])
    if desconocida:st.session_state['ruta_inexistente']=True
    from servicios.acceso import confirmar_enlace
    if confirmar_enlace():return
    cookie=cookie_inicial()
    if st.query_params.get('vista')=='solicitud':
        # Entrada anónima independiente: nunca restaura ni utiliza Auth para
        # consultar/guardar. Una cuenta abierta no convierte este formulario en interno.
        st.session_state['_vista_externa']=True
        from paginas.formulario import formulario
        from utils.componentes import mostrar_celebracion
        formulario(modo='publico',volver_a_app=bool(cookie or st.session_state.get('auth_client')))
        mostrar_celebracion()
        return
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
            from time import time
            if st.session_state.get('_cookie_expires',time()+1)<=time():raise PermissionError('Sesión vencida')
            getter=getattr(client.auth,'get_session',None)
            if getter:getter()
            user,perfil=perfil_verificado(client)
            repo=Repository(client,user,perfil)
            recordar_sesion(client,perfil)
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
    if repo is None or st.query_params.get('vista')=='acceso':
        if actual.title!='Inicio':st.session_state['destino_tras_login']=actual.title
        login()
        if repo and st.button('Volver a la app',type='tertiary',key='login_volver_app'):
            st.query_params.pop('vista',None);st.rerun()
        return
    st.session_state._repo_actual=repo
    destino=None
    if st.session_state.pop('inicio_tras_login',False):
        destino=guard_route(repo.profile,st.session_state.pop('destino_tras_login',None))
    if actual.title=='Inicio' or st.session_state.pop('ruta_inexistente',False):
        destino=destino or ('Hoy' if repo.is_owner else 'Nueva solicitud')
    st.query_params.pop('vista',None)
    if 'pagina' in st.query_params:destino=guard_route(repo.profile,st.query_params.pop('pagina'))
    if 'pending_navigation' in st.session_state:destino=guard_route(repo.profile,st.session_state.pop('pending_navigation'))
    segura=guard_route(repo.profile,destino or actual.title)
    autorizadas=rutas_para_perfil(repo.profile,paginas)
    if not repo.is_owner:
        for key in list(st.query_params):
            if key not in ('vista','canal'):del st.query_params[key]
        if 'canal' in st.query_params:
            from utils.canales import normalizar_canal
            canal=normalizar_canal(st.query_params['canal'])
            if st.query_params['canal']!=canal:st.query_params['canal']=canal
        st.session_state.pop('selected_case',None)
    if segura!=actual.title:st.switch_page(autorizadas[segura])
    st.session_state.navigation=segura
    mantener_sesion_activa()
    if not repo.is_owner:
        st.session_state['_vista_externa']=True
        actual.run()
        from utils.componentes import mostrar_celebracion
        mostrar_celebracion()
        return
    st.logo(str(LOGO),size='large',icon_image=FAVICON.read_text(encoding='utf-8'))
    with st.sidebar,st.container(key='mfy_sidebar'):
        menu_lateral(repo.profile,autorizadas,segura)
        with st.container(key='mfy_sidebar_bottom'):
            identidad_usuario(repo.profile.get('nombre'),repo.is_owner)
            from utils.en_vivo import indicador
            indicador({'Hoy':'hoy','Dashboard':'dashboard','Casos y cotizaciones':'casos'}.get(segura,'solicitud'),lateral=True)
            if st.button('Cerrar sesión',key='logout',width='stretch',icon=':material/logout:'):logout()
    cerrar_menu_movil_al_navegar()
    limpiar_borrador_al_salir(repo.user.id)
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
        if not st.session_state.get('_vista_externa'):pie_portal()
