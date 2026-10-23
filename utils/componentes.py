"""Componentes visuales reutilizables; los estilos están en estilos.py."""
from contextlib import contextmanager
from html import escape
from datetime import date, datetime

import streamlit as st

from utils.estados import estado_visual
from utils.estilos import ESTADOS_COLORES


def identidad_usuario(nombre, es_admin):
    nombre = str(nombre or "Mi cuenta")
    rol = "Administración" if es_admin else "Cliente"
    partes = nombre.split()
    iniciales = ''.join(p[:1] for p in (partes[:1] + partes[-1:] if len(partes)>1 else partes)).upper()
    st.markdown(f'<div class="mfy-identity"><span class="mfy-avatar" aria-hidden="true">{escape(iniciales)}</span>'
                f'<div><strong>{escape(nombre)}</strong><small>{rol}</small></div></div>', unsafe_allow_html=True)


def badge_estado(estado, cantidad=None):
    etiqueta = estado_visual(estado)
    indice = list(ESTADOS_COLORES).index(etiqueta) if etiqueta in ESTADOS_COLORES else 4
    titulo = ' title="Solicitud en revisión"' if estado == "En revisión" else ""
    texto = etiqueta + (f" · {int(cantidad)}" if cantidad is not None else "")
    return f'<span class="mfy-badge mfy-state-{indice}"{titulo}>{escape(texto)}</span>'


def leyenda_estados():
    st.markdown('<div class="mfy-state-key">'+''.join(badge_estado(e) for e in ESTADOS_COLORES)+'</div>', unsafe_allow_html=True)


def html_tabla_registros(frame, titulo="Registro de casos"):
    """Tabla accesible que se convierte en fichas en celular. Escapa todos los datos."""
    encabezados = ''.join(f'<th scope="col">{escape(str(c))}</th>' for c in frame.columns)
    filas = []
    for registro in frame.to_dict("records"):
        celdas = []
        for columna, valor in registro.items():
            if columna == "Estado":
                contenido = badge_estado(valor)
            else:
                if isinstance(valor, (date, datetime)):
                    valor = valor.strftime("%d/%m/%Y")
                contenido = f'<span>{escape(str(valor if valor is not None else "—"))}</span>'
            celdas.append(f'<td data-label="{escape(str(columna), quote=True)}">{contenido}</td>')
        filas.append('<tr>'+''.join(celdas)+'</tr>')
    return ('<div class="mfy-table-wrap" tabindex="0"><table class="mfy-table">'
            f'<caption>{escape(titulo)} · {len(frame)} registros</caption><thead><tr>{encabezados}</tr></thead>'
            '<tbody>'+''.join(filas)+'</tbody></table></div>')


def tabla_registros(frame, titulo="Registro de casos"):
    st.markdown(html_tabla_registros(frame, titulo), unsafe_allow_html=True)


def pie_portal():
    st.markdown('<div class="footer">Mente y Futuro · Sistema de gestión</div>', unsafe_allow_html=True)


def html_contenido_encabezado(titulo, subtitulo, etiqueta, icono):
    """Solo texto escapado: no permite introducir HTML a través de los datos."""
    return (f'<div class="mfy-hero-copy"><span class="mfy-eyebrow">MENTE Y FUTURO · {escape(str(etiqueta).upper())}</span>'
            f'<h1>{escape(str(titulo))}</h1><p>{escape(str(subtitulo))}</p></div>'
            f'<span class="mfy-hero-orbit" aria-hidden="true">{escape(str(icono))}</span>')


def encabezado_pagina(titulo, subtitulo, etiqueta, icono, acciones=None):
    """Un encabezado por página. acciones es una función que dibuja widgets nativos.

    Los botones conservan callbacks, foco y permisos de Streamlit. No se acepta
    HTML de acciones ni JavaScript; en móvil las acciones se sitúan bajo el título.
    """
    with st.container(key="mfy_page_header"):
        if acciones is None:
            st.markdown(html_contenido_encabezado(titulo, subtitulo, etiqueta, icono), unsafe_allow_html=True)
        else:
            texto, botones = st.columns([4, 1], gap="large")
            with texto:
                st.markdown(html_contenido_encabezado(titulo, subtitulo, etiqueta, icono), unsafe_allow_html=True)
            with botones, st.container(key="mfy_header_actions"):
                acciones()


def html_encabezado(agrupacion, desde, hasta):
    """Compatibilidad para la vista HTML del dashboard: usa el mismo contenido."""
    return '<section class="mfy-hero">'+html_contenido_encabezado(
        "Una mirada a tu negocio", f"{agrupacion} · {desde:%d/%m/%Y} – {hasta:%d/%m/%Y}", "DASHBOARD", "✦")+'</section>'


def titulo_seccion(numero, titulo):
    st.markdown(f'<div class="mfy-section-title"><span aria-hidden="true">{int(numero):02d}</span>'
                f'<h2><span class="mfy-sr-only">{int(numero):02d} / </span>{escape(str(titulo).upper())}</h2>'
                '<i aria-hidden="true"></i></div>', unsafe_allow_html=True)


@contextmanager
def seccion_formulario(numero, titulo, key):
    # Tres pasos de animación como máximo: 300 ms + 0/50/100 ms.
    with st.container(key=f"mfy_form_section_s{min(int(numero), 3)}_{key}"):
        titulo_seccion(numero, titulo)
        yield


@contextmanager
def cargando_datos(mensaje="Preparando la información…", cantidad=3):
    marcador = st.empty()
    marcador.markdown(esqueletos(cantidad), unsafe_allow_html=True)
    try:
        with st.spinner(mensaje):
            yield
    finally:
        marcador.empty()


def chips_activos(valores):
    st.markdown('<div class="mfy-chips">'+''.join(f'<span>{escape(str(v))}</span>' for v in valores)+'</div>', unsafe_allow_html=True)


def tarjeta_kpi(label, value, *, icon="↗", tone="azul", delta=None, help=None, caption=None, inverse=False, key):
    with st.container(key=f"mfy_kpi_{key}"):
        st.markdown(f'<div class="mfy-kpi-icon mfy-tone-{escape(tone)}" aria-hidden="true">{escape(icon)}</div>', unsafe_allow_html=True)
        st.metric(label, value, delta=delta, help=help, delta_color="inverse" if inverse else "normal")
        if caption:
            st.caption(caption)


@contextmanager
def tarjeta_grafico(titulo, subtitulo, key):
    with st.container(key=f"mfy_chart_{key}"):
        st.subheader(titulo)
        st.caption(subtitulo)
        yield


def estado_vacio(mensaje="Aún no hay datos en este período. Prueba con un rango más amplio.", icon="◌"):
    st.markdown(f'<div class="mfy-empty" role="status"><span aria-hidden="true">{escape(icon)}</span><p>{escape(mensaje)}</p></div>', unsafe_allow_html=True)


def dato_destacado(texto):
    st.markdown(f'<aside class="mfy-highlight"><span>DATO DESTACADO</span><p>{escape(texto)}</p></aside>', unsafe_allow_html=True)


def esqueletos(cantidad=4):
    return ('<div class="mfy-skeleton-grid" role="status" aria-live="polite">'
            '<span class="mfy-sr-only">Cargando información</span>'
            + ''.join('<div class="mfy-skeleton" aria-hidden="true"></div>' for _ in range(cantidad))+'</div>')
