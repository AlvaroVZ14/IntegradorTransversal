"""Registro nativo de páginas. La autorización sigue en utils.permisos."""
import streamlit as st
from streamlit.components.v2 import component

from utils.permisos import allowed_pages,es_admin

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
    visibles=allowed_pages(perfil) if perfil else []
    paginas={'Inicio':st.Page(inicio,title='Inicio',default=True,visibility='hidden')}
    for titulo in PAGINAS:
        archivo, ruta, icono, grupo = PAGINAS[titulo]
        pagina = st.Page(archivo, title=titulo, icon=icono, url_path=ruta,
                         visibility='visible' if titulo in visibles else 'hidden')
        paginas[titulo] = pagina
    return list(paginas.values()), paginas


def registrar_navegacion(perfil=None):
    """Menú nativo superior; URLs estables y visibilidad basada en el rol verificado."""
    from mente_futuro.presentation import LOGO
    registro,paginas=crear_paginas(perfil)
    if perfil:
        titulos=allowed_pages(perfil)
        if len(titulos)>5:
            # Máximo cinco entradas principales contando el desplegable Más.
            principales=titulos[:4]
            registro={'':[p for p in registro if p.title not in titulos[4:]],
                      'Más':[paginas[t] for t in titulos[4:]]}
        actual=st.navigation(registro,position='top')
        st.logo(str(LOGO),size='large')
    else:
        actual=st.navigation(registro,position='hidden')
    return actual,paginas


def barra_publica():
    """Marca sin enlaces ni sesión; la cabecera del formulario conserva su texto."""
    from mente_futuro.presentation import LOGO
    st.logo(str(LOGO),size='large')
    st.markdown('<span class="mfy-public-nav-marker" aria-hidden="true"></span>',unsafe_allow_html=True)


def barra_cuenta(repo,actual):
    """Acciones de cuenta existentes, ahora en la esquina superior derecha."""
    from utils.componentes import identidad_usuario
    from mente_futuro.ui import logout
    st.markdown('<span class="mfy-top-nav-marker" aria-hidden="true"></span>',unsafe_allow_html=True)
    # Streamlit oculta su menú si hay un solo destino visible.
    if not repo.is_owner:
        with st.container(key='mfy_top_single'):
            st.page_link('paginas/nueva_solicitud.py',label='Nueva solicitud',icon=':material/add_circle:')
    with st.container(key='mfy_top_account'):
        with st.popover('Mi cuenta',icon=':material/account_circle:',help='Mi cuenta y cerrar sesión'):
            identidad_usuario(repo.profile.get('nombre'),repo.is_owner)
            st.button('Cerrar sesión',key='logout',width='stretch',icon=':material/logout:',on_click=logout)
    # El menú nativo reduce enlaces a "N more"; el popover estándar da una
    # hamburguesa explícita, en español y con los mismos destinos autorizados.
    with st.container(key='mfy_top_mobile'):
        with st.popover('Menú',icon=':material/menu:',help='Abrir menú de navegación'):
            with st.container(key='mfy_mobile_links'):
                for titulo in allowed_pages(repo.profile):
                    archivo,ruta,icono,_=PAGINAS[titulo]
                    with st.container(key=('mfy_mobile_active_' if actual==titulo else 'mfy_mobile_item_')+ruta):
                        st.page_link(archivo,label=titulo,icon=icono)
                identidad_usuario(repo.profile.get('nombre'),repo.is_owner)
                st.button('Cerrar sesión',key='mobile_logout',width='stretch',icon=':material/logout:',on_click=logout)
    ajustar_menu_superior()


def ajustar_menu_superior():
    """Solo presentación: traducir el overflow nativo y cerrar el menú móvil."""
    puente=component('mfy_top_navigation_accessibility',html='<span aria-hidden="true"></span>',js="""
    export default function() {
      const translate = () => {
        document.querySelectorAll('[data-testid="stHeader"] .rc-overflow-item-rest [data-testid="stTopNavSection"]').forEach(button => {
          const text = button.querySelector('p');
          if (text && text.textContent !== 'Más') text.textContent = 'Más';
          if (button.getAttribute('aria-label') !== 'Más secciones') button.setAttribute('aria-label', 'Más secciones');
        });
      };
      const observer = new MutationObserver(translate);
      observer.observe(document.body, {childList:true,subtree:true});
      translate();
      const close = event => {
        if (!(event.target instanceof Element) || !event.target.closest('.st-key-mfy_mobile_links [data-testid="stPageLink-NavLink"]')) return;
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        document.querySelector('.st-key-mfy_top_mobile button')?.click();
      };
      document.addEventListener('click', close);
      return () => { observer.disconnect(); document.removeEventListener('click', close); };
    }
    """)
    puente(key='mfy_top_navigation_accessibility',height=0)


def rutas_para_perfil(perfil,paginas):
    """Destinos ejecutables del marco; independientes del registro de URLs."""
    titulos=allowed_pages(perfil)
    if es_admin(perfil):titulos.append('Estado')
    return {titulo:paginas[titulo] for titulo in titulos}


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
