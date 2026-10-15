import streamlit as st
from supabase_auth.errors import AuthApiError

from mente_futuro.pages import request_page, cases_page, dashboard_page
from mente_futuro.presentation import CSS, LOGO
from mente_futuro.repository import Repository
from mente_futuro.ui import login, logout, show_error

st.set_page_config(page_title="Mente y Futuro · Gestión", page_icon="💡", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


def main():
    if "auth_client" not in st.session_state:
        login()
        return
    client = st.session_state.auth_client
    try:
        response = client.auth.get_user()
        user = response.user if response else None
        if not user:
            logout()
    except AuthApiError:
        st.warning("Tu sesión terminó. Vuelve a ingresar.")
        if st.button("Volver al ingreso"):
            logout()
        return
    except Exception as error:
        show_error(error,"No pudimos verificar tu sesión. Revisa la conexión e intenta nuevamente.")
        if st.button("Reintentar"):
            st.rerun()
        return
    with st.sidebar:
        st.image(str(LOGO),width="stretch")
        st.caption("GESTIÓN Y APRENDIZAJE")
        if st.button("Cerrar sesión",key="logout",width="stretch"):
            logout()
    try:
        profiles = client.table("mf_perfiles").select("*").eq("id",user.id).execute().data
        if not profiles:
            st.error("Tu cuenta necesita completar su configuración. Contacta a la administradora.")
            return
        repo = Repository(client,user,profiles[0])
        with st.sidebar:
            st.divider()
            st.write(f"**{repo.profile.get('nombre') or 'Mi cuenta'}**")
            st.caption("Administración · Acceso completo" if repo.is_owner else "Cliente · Espacio personal")
            pages = ["Nueva solicitud","Casos y cotizaciones"] + (["Dashboard"] if repo.is_owner else [])
            if "pending_navigation" in st.session_state:
                st.session_state.navigation = st.session_state.pop("pending_navigation")
            if st.session_state.get("navigation") not in pages:
                st.session_state.navigation = "Dashboard" if repo.is_owner else "Nueva solicitud"
            page = st.radio("Navegación",pages,key="navigation",label_visibility="collapsed")
            st.divider()
            if st.button("Actualizar información",width="stretch"):
                st.rerun()
            st.markdown('<div class="note">Pequeños pasos.<br><b>Grandes posibilidades.</b></div>',unsafe_allow_html=True)
            st.caption("Mente y Futuro · Portal de gestión")
        if "notice" in st.session_state:
            st.success(st.session_state.pop("notice"))
        {"Nueva solicitud":request_page,"Casos y cotizaciones":cases_page,"Dashboard":dashboard_page}[page](repo)
    except Exception as error:
        show_error(error,"No pudimos cargar la información. Reintenta en unos momentos.")


if __name__ == "__main__":
    main()
