"""Componentes visuales reutilizables; los estilos están en estilos.py."""
from contextlib import contextmanager
from html import escape
from datetime import date, datetime
from math import isfinite
from re import sub

import streamlit as st

from utils.estados import estado_visual
from utils.estilos import ESTADOS_COLORES


def ampolleta_svg():
    """Motivo vectorial de la marca; no carga imágenes ni código externo."""
    return ('<svg class="mfy-bulb" viewBox="0 0 160 190" fill="none" aria-hidden="true" focusable="false">'
            '<g class="mfy-bulb-rays" stroke="#FFCC00" stroke-width="7" stroke-linecap="round">'
            '<path d="M80 10v14M22 37l11 11M8 91h16M138 37l-11 11M136 91h16M24 145l11-11M136 145l-11-11"/></g>'
            '<path class="mfy-bulb-glass" d="M80 38c-31 0-52 23-52 51 0 22 10 33 22 49 5 7 7 17 7 25h46c0-8 2-18 7-25 12-16 22-27 22-49 0-28-21-51-52-51Z" '
            'fill="#CCCCFF" fill-opacity=".13" stroke="#CCCCFF" stroke-width="6"/>'
            '<g stroke-width="5" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M77 65c-10-12-27-3-26 9-13 2-17 19-8 27-7 13 2 27 16 26 2 10 10 15 18 10V65Z" fill="#9966FF" stroke="#9966FF"/>'
            '<path d="M84 65c10-12 27-3 26 9 13 2 17 19 8 27 7 13-2 27-16 26-2 10-10 15-18 10V65Z" fill="#6699FF" stroke="#6699FF"/>'
            '<path d="M58 77c9 0 11 7 11 12M47 98c7 6 13 6 18 0M62 114c8-1 13 4 15 9M102 77c-9 0-11 7-11 12M113 98c-7 6-13 6-18 0M98 114c-8-1-13 4-15 9" stroke="white"/>'
            '<path d="M58 174h44M64 184h32" stroke="#FFCC00"/></g></svg>')


def html_chips_vidrio(metricas):
    return '<div class="mfy-glass-chips">'+''.join(
        f'<span class="mfy-glass-chip"><small>{escape(str(label))}</small><strong>{escape(str(valor))}</strong></span>'
        for label,valor in metricas)+'</div>'


def sparkline_svg(valores, etiquetas=None, key='serie', formato='entero'):
    """Hasta seis valores reales. Los None son huecos, nunca ceros inventados."""
    valores=list(valores)[-6:]
    etiquetas=list(etiquetas or [])[-len(valores):]
    numeros=[float(v) if v is not None and isfinite(float(v)) else None for v in valores]
    validos=[v for v in numeros if v is not None]
    if not validos:return ''
    inferior,superior=min(0,min(validos)),max(validos)
    amplitud=superior-inferior or 1
    segmentos=[];actual=[];puntos=[]
    for i,v in enumerate(numeros):
        if v is None:
            if actual:segmentos.append(actual);actual=[]
            continue
        x=4+i*192/max(1,len(numeros)-1);y=35-(v-inferior)/amplitud*28
        actual.append(f'{x:.2f},{y:.2f}');puntos.append((x,y))
    if actual:segmentos.append(actual)
    def numero(v):
        if formato=='moneda':return '$'+f'{v:,.0f}'.replace(',','.')
        if formato=='porcentaje':return f'{v:.1f}'.replace('.',',')+'%'
        return f'{v:,.0f}'.replace(',','.')
    descripcion=' · '.join(f'{etiquetas[i] if i<len(etiquetas) else i+1}: {numero(v)}' for i,v in enumerate(numeros) if v is not None)
    ident='spark-'+sub(r'[^a-zA-Z0-9_-]','',str(key))
    return (f'<svg class="mfy-sparkline" viewBox="0 0 200 42" role="img" aria-label="{escape(descripcion,quote=True)}">'
        f'<title>{escape(descripcion)}</title><defs><linearGradient id="{ident}" x2="0" y2="1">'
        '<stop class="mfy-spark-top"/><stop offset="1" class="mfy-spark-bottom"/></linearGradient></defs>'
        +''.join(f'<polygon points="{s[0].split(",")[0]},39 {" ".join(s)} {s[-1].split(",")[0]},39" fill="url(#{ident})"/>'
                  f'<polyline points="{" ".join(s)}"/>' for s in segmentos)
        +''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.4"/>' for x,y in puntos)+'</svg>')


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
            '<span class="mfy-hero-orbit" aria-hidden="true">'+ampolleta_svg()+'</span>')


def encabezado_pagina(titulo, subtitulo, etiqueta, icono, acciones=None):
    """Un encabezado por página. acciones es una función que dibuja widgets nativos.

    Los botones conservan callbacks, foco y permisos de Streamlit. No se acepta
    HTML de acciones ni JavaScript; en móvil las acciones se sitúan bajo el título.
    """
    vista={'HOY':'hoy','DASHBOARD':'dashboard','SEGUIMIENTO':'casos'}.get(str(etiqueta).upper())
    def contenido():
        st.markdown(html_contenido_encabezado(titulo, subtitulo, etiqueta, icono), unsafe_allow_html=True)
        if vista:
            from utils.en_vivo import metricas_cabecera
            metricas_cabecera(vista)
        elif str(etiqueta).upper()=='SOLICITUDES':
            st.markdown(html_chips_vidrio([('01','Datos de contacto'),('02','Servicio y objetivos')]),unsafe_allow_html=True)
    with st.container(key="mfy_page_header"):
        if acciones is None:
            contenido()
        else:
            texto, botones = st.columns([3, 1], gap="large")
            with texto:
                contenido()
            with botones, st.container(key="mfy_header_actions"):
                acciones()


def panel_marca_login():
    with st.container(key='mfy_login_brand'):
        st.markdown(html_contenido_encabezado('Tu próximo paso, en un solo lugar.',
            'Conversemos sobre lo que necesita tu equipo.','BIENVENIDA',''),unsafe_allow_html=True)
        st.markdown('''<div class="mfy-login-steps"><span><b>01</b> Cuéntanos qué necesitas</span>
        <span><b>02</b> Revisamos tu solicitud</span>
        <span><b>03</b> Te enviamos una propuesta a tu medida</span></div>''',unsafe_allow_html=True)


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


def tarjeta_kpi(label, value, *, icon="↗", tone="azul", delta=None, help=None, caption=None, inverse=False, key,
                serie=None, etiquetas=None, contexto_serie=None, formato_serie='entero'):
    with st.container(key=f"mfy_kpi_{key}"):
        st.markdown(f'<div class="mfy-kpi-icon mfy-tone-{escape(tone)}" aria-hidden="true">{escape(icon)}</div>', unsafe_allow_html=True)
        st.metric(label, value, delta=delta, help=help, delta_color="inverse" if inverse else "normal")
        if caption:
            st.caption(caption)
        if serie is not None:
            st.markdown(sparkline_svg(serie,etiquetas,key,formato_serie),unsafe_allow_html=True)
            if contexto_serie:st.caption(contexto_serie)


def todo_al_dia():
    st.markdown('<div class="mfy-all-done">'+ampolleta_svg()+
                '<div><strong>Todo al día. Buen trabajo</strong><p>Hoy tienes espacio para nuevas ideas.</p></div></div>',unsafe_allow_html=True)


def preparar_celebracion(identificador, mensaje):
    """Solo se llama después de una escritura confirmada. No ejecuta escrituras."""
    st.session_state['mfy_celebracion']=dict(id=str(identificador),mensaje=mensaje)


def mostrar_celebracion():
    from pathlib import Path
    from streamlit.components.v2 import component
    evento=st.session_state.pop('mfy_celebracion',None)
    if not evento or st.session_state.get('mfy_celebracion_vista')==evento['id']:return
    st.session_state['mfy_celebracion_vista']=evento['id']
    st.toast(evento['mensaje'],icon=':material/celebration:')
    componente=component('mfy_celebracion',html='<span aria-hidden="true"></span>',
        js=Path(__file__).with_name('celebracion.js').read_text(encoding='utf-8'))
    componente(data={'id':evento['id']},key='mfy_celebracion',height=0)


@contextmanager
def tarjeta_grafico(titulo, subtitulo, key, help=None):
    with st.container(key=f"mfy_chart_{key}"):
        st.subheader(titulo)
        st.caption(subtitulo,help=help)
        yield


def estado_vacio(mensaje="Aún no hay datos en este período. Prueba con un rango más amplio.", icon="◌"):
    st.markdown(f'<div class="mfy-empty" role="status"><span aria-hidden="true">{escape(icon)}</span><p>{escape(mensaje)}</p></div>', unsafe_allow_html=True)


def dato_destacado(texto):
    st.markdown(f'<aside class="mfy-highlight"><span>DATO DESTACADO</span><p>{escape(texto)}</p></aside>', unsafe_allow_html=True)


def esqueletos(cantidad=4):
    return ('<div class="mfy-skeleton-grid" role="status" aria-live="polite">'
            '<span class="mfy-sr-only">Cargando información</span>'
            + ''.join('<div class="mfy-skeleton" aria-hidden="true"></div>' for _ in range(cantidad))+'</div>')
