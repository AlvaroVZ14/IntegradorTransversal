"""Registro nativo de páginas. La autorización sigue en utils.permisos."""
import streamlit as st
from streamlit.components.v2 import component

from utils.permisos import allowed_pages

PAGINAS = {
    "Hoy": ("paginas/hoy.py", "hoy", ":material/today:", "INICIO"),
    "Nueva solicitud": ("paginas/nueva_solicitud.py", "nueva-solicitud", ":material/add_circle:", "GESTIÓN"),
    "Casos y cotizaciones": ("paginas/gestion.py", "casos", ":material/folder_open:", "GESTIÓN"),
    "Dashboard": ("paginas/dashboard.py", "dashboard", ":material/dashboard:", "ANÁLISIS"),
    "Estado": ("paginas/estado.py", "estado", ":material/monitor_heart:", "MANTENIMIENTO"),
}


def crear_paginas(perfil):
    permitidas = allowed_pages(perfil)
    inicio = "Hoy" if "Hoy" in permitidas else "Nueva solicitud"
    grupos, paginas = {}, {}
    for titulo in permitidas:
        archivo, ruta, icono, grupo = PAGINAS[titulo]
        pagina = st.Page(archivo, title=titulo, icon=icono, url_path=ruta, default=titulo == inicio)
        paginas[titulo] = pagina
        grupos.setdefault(grupo, []).append(pagina)
    if perfil.get('rol') == 'admin':
        pagina = st.Page('paginas/estado.py',title='Estado',url_path='estado',
                         icon=':material/monitor_heart:',visibility='hidden')
        paginas['Estado'] = pagina
        # Se registra, pero no crea un grupo ni un ítem visible en el menú.
        grupos.setdefault('', []).append(pagina)
    return grupos, paginas


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
          const selector = '[data-testid="stSidebarNavLink"], .st-key-mfy_single_page [data-testid="stPageLink-NavLink"]';
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
