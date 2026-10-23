import streamlit as st
from supabase_auth.errors import AuthApiError

from mente_futuro.presentation import CSS, LOGO, FAVICON
from servicios.repositorio import Repository
from utils.permisos import guard_route
from mente_futuro.ui import login, logout, show_error
from utils.componentes import identidad_usuario, pie_portal
from utils.navegacion import crear_paginas, cerrar_menu_movil_al_navegar, PAGINAS
from utils.borrador_local import limpiar_borrador_al_salir

st.set_page_config(page_title="Mente y Futuro · Portal", page_icon=FAVICON.read_text(encoding="utf-8"), layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


def main():
    # Se renueva en cada ejecución, después de comprobar Auth y el rol real.
    st.session_state.pop("_repo_actual", None)
    if "auth_client" not in st.session_state:
        st.navigation([st.Page(login, title="Ingresar", default=True)], position="hidden").run()
        return
    client = st.session_state.auth_client
    try:
        response = client.auth.get_user()
        user = response.user if response else None
        if not user:
            logout()
    except AuthApiError:
        st.navigation([st.Page(login, title="Ingresar", default=True)], position="hidden")
        st.warning("Tu sesión terminó. Vuelve a ingresar.")
        if st.button("Volver al ingreso"):
            logout()
        return
    except Exception as error:
        st.navigation([st.Page(login, title="Ingresar", default=True)], position="hidden")
        show_error(error,"No pudimos verificar tu sesión. Revisa la conexión e intenta nuevamente.")
        if st.button("Reintentar"):
            st.rerun()
        return
    navegacion_registrada = False
    try:
        profiles = client.table("mf_perfiles").select("*").eq("id",user.id).execute().data
        if not profiles:
            st.navigation([st.Page(login, title="Ingresar", default=True)], position="hidden")
            st.error("Tu cuenta necesita completar su configuración. Contacta a la administradora.")
            if st.button("Cerrar sesión",key="logout"):
                logout()
            return
        repo = Repository(client,user,profiles[0])
        st.session_state._repo_actual = repo
        if st.session_state.pop('inicio_tras_login',False):
            st.session_state.pending_navigation = 'Hoy' if repo.is_owner else 'Nueva solicitud'
        grupos, paginas = crear_paginas(repo.profile)
        # La lista registrada contiene SOLO páginas autorizadas. No hay páginas
        # privadas ocultas disponibles para clientes, ni autorización por URL.
        solicitada = None
        if not repo.is_owner:
            st.query_params.clear()
            st.session_state.pop("selected_case", None)
        elif "pagina" in st.query_params:
            solicitada = guard_route(repo.profile, st.query_params.pop("pagina"))
        if "pending_navigation" in st.session_state:
            solicitada = guard_route(repo.profile, st.session_state.pop("pending_navigation"))
        actual = st.navigation(grupos, position="sidebar", expanded=True)
        navegacion_registrada = True
        if solicitada is not None and actual.title != solicitada:
            st.switch_page(paginas[solicitada])
        segura = guard_route(repo.profile, actual.title)
        if segura != actual.title:
            st.switch_page(paginas[segura])
        st.session_state.navigation = segura  # Compatibilidad, no decide permisos.
        st.logo(str(LOGO), size="large", icon_image=FAVICON.read_text(encoding="utf-8"))
        with st.sidebar, st.container(key="mfy_sidebar"):
            # Streamlit no dibuja su menú cuando hay una sola página. Un enlace
            # nativo muestra esa única opción sin registrar páginas adicionales.
            if len(paginas) == 1:
                st.markdown('<p class="mfy-nav-group">GESTIÓN</p>', unsafe_allow_html=True)
                with st.container(key="mfy_single_page"):
                    st.page_link(paginas["Nueva solicitud"], label="Nueva solicitud",
                                 icon=PAGINAS["Nueva solicitud"][2], width="stretch",
                                 help="Página actual · Nueva solicitud")
                    st.markdown('<span class="mfy-sr-only">Página actual: Nueva solicitud</span>', unsafe_allow_html=True)
            with st.container(key="mfy_sidebar_bottom"):
                identidad_usuario(repo.profile.get("nombre"), repo.is_owner)
                if st.button("Cerrar sesión",key="logout",width="stretch",icon=":material/logout:"):
                    logout()
        cerrar_menu_movil_al_navegar()
        limpiar_borrador_al_salir(repo.user.id)
        if "notice" in st.session_state:
            st.success(st.session_state.pop("notice"))
        actual.run()
    except Exception as error:
        if not navegacion_registrada:
            st.session_state.pop("_repo_actual", None)
            st.navigation([st.Page(login, title="Ingresar", default=True)], position="hidden")
        show_error(error,"No pudimos cargar la información. Reintenta en unos momentos.")
        if st.button("Volver al ingreso", key="recover_login"):
            logout()


if __name__ == "__main__":
    try:
        main()
    finally:
        pie_portal()
