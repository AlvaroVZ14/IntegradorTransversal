"""Registro nativo de páginas. La autorización sigue en utils.permisos."""
import streamlit as st
from streamlit.components.v2 import component

from utils.permisos import allowed_pages

PAGINAS = {
    "Hoy": ("paginas/hoy.py", "hoy", ":material/today:", "INICIO"),
    "Nueva solicitud": ("paginas/nueva_solicitud.py", "nueva-solicitud", ":material/add_circle:", "GESTIÓN"),
    "Casos y cotizaciones": ("paginas/gestion.py", "casos", ":material/folder_open:", "GESTIÓN"),
    "Compartir": ("paginas/compartir.py", "compartir", ":material/share:", "GESTIÓN"),
    "Dashboard": ("paginas/dashboard.py", "dashboard", ":material/dashboard:", "ANÁLISIS"),
    "Estado": ("paginas/estado.py", "estado", ":material/monitor_heart:", "MANTENIMIENTO"),
}


def inicio():
    """El marco resuelve el destino después de verificar la sesión."""


def crear_paginas(perfil=None):
    # Registro estable: que una URL exista NO otorga acceso a su contenido.
    paginas={'Inicio':st.Page(inicio,title='Inicio',default=True)}
    for titulo in PAGINAS:
        archivo, ruta, icono, grupo = PAGINAS[titulo]
        pagina = st.Page(archivo, title=titulo, icon=icono, url_path=ruta)
        paginas[titulo] = pagina
    return list(paginas.values()), paginas


def resolver_ruta_desconocida():
    """Compatibilidad acotada con Streamlit 1.65, que no tiene ruta catch-all.

    Cambia SOLO la intención de ruta antes de registrar/resolver las páginas.
    No intercepta diálogos ni autorización. También cubre rutas anidadas, que
    st.Page no admite como alias temporal. Se verifica mediante pruebas.
    """
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx=get_script_run_ctx()
    if not ctx:return False
    manager=ctx.pages_manager
    ruta=manager.intended_page_name
    if ruta and ruta not in {p[1] for p in PAGINAS.values()}:
        manager.set_script_intent('','')
        return True
    return False


def menu_lateral(perfil,paginas,actual):
    grupo_anterior=None
    with st.container(key='mfy_custom_nav'):
        for titulo in allowed_pages(perfil):
            archivo,ruta,icono,grupo=PAGINAS[titulo]
            if grupo!=grupo_anterior:
                st.markdown(f'<p class="mfy-nav-group">{grupo}</p>',unsafe_allow_html=True)
                grupo_anterior=grupo
            with st.container(key=('mfy_nav_active_' if actual==titulo else 'mfy_nav_item_')+ruta):
                st.page_link(paginas[titulo],label=titulo,icon=icono,width='stretch',help='Página actual' if actual==titulo else None)


def cerrar_menu_movil_al_navegar():
    """Complementa el cierre nativo por user-agent con el breakpoint de 767 px.

    También sirve al enlace del cliente (Streamlit oculta su menú con una sola
    página). Solo pulsa el control nativo de cierre; no cambia rutas ni permisos.
    Los selectores corresponden a Streamlit 1.65; si faltan, no hace nada.
    """
    puente = component(
        "mfy_cierre_menu_movil",
        html="<span aria-hidden='true'></span>",
        js="""
        export default function() {
          const media = window.matchMedia('(max-width: 767px)');
          const selector = '[data-testid="stSidebarNavLink"], .st-key-mfy_single_page [data-testid="stPageLink-NavLink"], .st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]';
          const close = event => {
            if (!media.matches || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            if (!(event.target instanceof Element) || !event.target.closest(selector)) return;
            requestAnimationFrame(() => {
              const sidebar = document.querySelector('[data-testid="stSidebar"][aria-expanded="true"]');
              const button = sidebar?.querySelector('[data-testid="stSidebarCollapseButton"] button');
              button?.click();
            });
          };
          document.addEventListener('click', close);
          return () => document.removeEventListener('click', close);
        }
        """,
    )
    puente(key="mfy_menu_movil", height=0)
