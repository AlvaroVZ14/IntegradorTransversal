"""Interfaz del tablero. Cálculos y períodos viven en servicios/dashboard.py."""

import pandas as pd
import streamlit as st
from time import time

from mente_futuro.domain import SERVICES, TOPICS, code, csv_bytes, money, today
from servicios.dashboard import AGRUPACIONES, RANGOS, ajustar_rango, datos_dashboard, rango_rapido
from utils.estados import etiqueta_estado
from utils.permisos import require_admin
from utils.responsive import es_pantalla_movil
from servicios.dashboard_cache import cargar_dashboard, invalidar_dashboard
from utils.componentes import (chips_activos, dato_destacado, esqueletos, estado_vacio, encabezado_pagina,
                               tarjeta_grafico, tarjeta_kpi, badge_estado, leyenda_estados, tabla_registros)
from utils.graficos_dashboard import (barras_horizontales, distribucion, embudo_estados, frase_destacada,
                                     modalidades, origenes, reparto, solicitudes_vs_ventas,
                                     tematicas_dona, ventas_por_periodo)
from utils.estilos import AZUL
from mente_futuro.ui import show_error, logout


def _normalizar():
    state = st.session_state
    start, end, message = ajustar_rango(state.dash_desde, state.dash_hasta, state.dash_agrupacion)
    state.dash_desde, state.dash_hasta = start, end
    if message:
        state.dash_rango = "Personalizado"
        state.dash_aviso = message


def _cambiar_rapido():
    if st.session_state.dash_rango != "Personalizado":
        st.session_state.dash_desde, st.session_state.dash_hasta = rango_rapido(st.session_state.dash_rango, today())
    _normalizar()


def _cambiar_fecha():
    st.session_state.dash_rango = "Personalizado"
    _normalizar()


def _limpiar():
    start, end = rango_rapido("Últimos 6 meses", today())
    st.session_state.update(dash_agrupacion="Mensual", dash_rango="Últimos 6 meses",
                            dash_desde=start, dash_hasta=end, dash_servicio="Todos", dash_tematica="Todas")
    st.session_state.pop("dash_aviso", None)


def filtros():
    if "dash_agrupacion" not in st.session_state:
        _limpiar()
    mobile = es_pantalla_movil()
    container = st.expander("Filtros", expanded=False, key="dashboard_filters") if mobile else st.container(key="dashboard_filters")
    with container:
        columns = [st.container() for _ in range(7)] if mobile else st.columns([1.1, 1.5, 1.05, 1.05, 1.5, 1.5, .7], gap="small")
        columns[0].selectbox("Agrupar por", AGRUPACIONES, key="dash_agrupacion", on_change=_normalizar)
        columns[1].selectbox("Rango rápido", RANGOS, key="dash_rango", on_change=_cambiar_rapido)
        columns[2].date_input("Desde", key="dash_desde", format="DD/MM/YYYY", on_change=_cambiar_fecha)
        columns[3].date_input("Hasta", key="dash_hasta", format="DD/MM/YYYY", on_change=_cambiar_fecha)
        columns[4].selectbox("Servicio", ["Todos", *SERVICES], key="dash_servicio")
        columns[5].selectbox("Temática", ["Todas", *TOPICS], key="dash_tematica")
        with columns[6]:
            st.write("")
            st.button("Limpiar", on_click=_limpiar, width="stretch")
    if "dash_aviso" in st.session_state:
        st.info(st.session_state.pop("dash_aviso"))
    state = st.session_state
    chips_activos([state.dash_agrupacion, f"{state.dash_desde:%d/%m/%Y} · {state.dash_hasta:%d/%m/%Y}",
                   "Todos los servicios" if state.dash_servicio=="Todos" else state.dash_servicio,
                   "Todas las temáticas" if state.dash_tematica=="Todas" else state.dash_tematica])
    return state.dash_desde, state.dash_hasta, state.dash_agrupacion, state.dash_servicio, state.dash_tematica


# Adaptadores para las importaciones anteriores del dashboard.
def grafico_periodos(serie, solicitudes=False):
    return solicitudes_vs_ventas(serie) if solicitudes else ventas_por_periodo(serie)


def grafico_conteos(frame, category, value):
    return barras_horizontales(frame[category].tolist(),frame[value].tolist())


def _delta(data, key):
    actual, previous = data[key], data["previous"][key]
    if actual is None or previous is None:
        return None
    variation = data["variations"][key]
    if variation is None:
        return "Sin base anterior" if previous==0 and actual>0 else None
    return f"{variation:+.1f}%".replace(".", ",")


def _mostrar(fig, key, mensaje=None):
    if fig is None:
        estado_vacio(mensaje or "Aún no hay solicitudes en este período. Prueba con un rango más amplio.")
    else:
        st.plotly_chart(fig, width="stretch", theme=None, key=key,
                        config={"displayModeBar":False,"responsive":True,"scrollZoom":False})


def _contenido_dashboard(repo):
    require_admin(repo)
    hero = st.container()
    start, end, grouping, service, topic = filtros()
    with hero:
        encabezado_pagina("Una mirada a tu negocio", f"{grouping} · {start:%d/%m/%Y} – {end:%d/%m/%Y}",
                          "DASHBOARD", "✦", acciones=lambda: st.button(
                              "Actualizar", key="dashboard_actualizar", on_click=invalidar_dashboard,
                              icon=":material/refresh:", width="stretch"))
    loading = st.empty()
    loading.markdown(esqueletos(), unsafe_allow_html=True)
    try:
        with st.spinner("Preparando tu tablero…"):
            cases, sales = cargar_dashboard(repo)
            data = datos_dashboard(cases, sales, start, end, grouping, service, topic)
    finally:
        loading.empty()
    minutos=max(0,int((time()-st.session_state.get("dashboard_loaded_at",time()))//60))
    st.caption(f"Actualizado hace {minutos} min",help="Se actualiza automáticamente cada 30 segundos; la consulta conserva su caché de 60 segundos y se invalida después de escribir.")
    reduced = st.session_state.get("dashboard_reduced_motion",False)
    previous_start, previous_end = data["previous_range"]
    st.caption(f"Comparado con {previous_start:%d/%m/%Y} – {previous_end:%d/%m/%Y}", help=
        "Bloque anterior con igual cantidad de períodos completos. El rango actual puede ser parcial; si la base es cero no se inventa un porcentaje.")
    conversion = data["conversion"]
    conversion_text = None
    if conversion is not None:
        number = f"{conversion/10:.1f}".rstrip("0").rstrip(".").replace(".",",")
        conversion_text = f"De cada 10 solicitudes, {number} terminaron en venta"
    cards = [
        ("Ventas del período",money(data["total"]),"total","↗","azul",None,None),
        ("Ventas cerradas",data["sales_count"],"sales_count","✓","azul",None,None),
        ("Nuevas solicitudes",data["requests_count"],"requests_count","✉","morado",None,None),
        ("Venta promedio",money(data["average"]) if data["average"] is not None else "—","average","◈","amarillo","Total vendido dividido por los casos vendidos en el período",None),
        ("Solicitudes que se vendieron",f"{conversion:.1f}%".replace(".",",") if conversion is not None else "—","conversion","◎","morado","Solicitudes creadas en el rango que tienen venta no anulada hasta su fecha final.",conversion_text),
        ("Ventas con pago pendiente",money(data["pending_payment"]),"pending_payment","◷","amarillo","Valor completo de las ventas no pagadas totalmente, incluidas las que tienen abonos; no es el saldo exacto por cobrar.",None),
    ]
    for offset in [0,3]:
        for column,card in zip(st.columns(3),cards[offset:offset+3]):
            label,value,key,icon,tone,help_text,caption = card
            with column:
                tarjeta_kpi(label,value,key=key,icon=icon,tone=tone,delta=_delta(data,key),help=help_text,
                            caption=caption,inverse=key=="pending_payment")
    a,b = st.columns(2)
    with a:
        with tarjeta_grafico("Ventas por período","Total vendido, promedio y mejor período · CLP","ventas"):
            _mostrar(ventas_por_periodo(data["series"],reduced),"plot_ventas",
                     "Aún no hay ventas en este período. Prueba con un rango más amplio.")
    with b:
        with tarjeta_grafico("Solicitudes vs ventas","Cantidad de solicitudes y ventas cerradas por período","comparacion"):
            _mostrar(solicitudes_vs_ventas(data["series"],reduced),"plot_comparacion")
    a,b = st.columns(2)
    with a:
        with tarjeta_grafico("Temáticas más solicitadas","Las 5 principales y otras · porcentaje de solicitudes","tematicas"):
            _mostrar(tematicas_dona(data["topics"],reduced),"plot_temas")
    with b:
        with tarjeta_grafico("Embudo por estado del caso","Distribución actual de casos; no representa transiciones históricas","embudo"):
            leyenda_estados()
            _mostrar(embudo_estados(data["states"],reduced),"plot_embudo","Aún no hay casos en estas etapas del período.")
            outside = data["states"][~data["states"].estado.isin(["Solicitud","Cotizada","Aceptada","En seguimiento","Cerrada"])]
            if not outside.empty:
                st.caption("Otros casos del período (fuera del embudo):")
                st.markdown('<div class="mfy-state-key">'+''.join(badge_estado(r.estado,r.Casos) for r in outside.itertuples())+'</div>',unsafe_allow_html=True)
                if "En revisión" in outside.estado.values:
                    st.caption("La solicitud en revisión conserva su subetapa original.")
    ids = set(data["requests"].id)
    filtered_cases = [c for c in cases if c["id"] in ids]
    sale_ids = set(data["sales"].caso_id)
    filtered_sales = [s for s in sales if s["caso_id"] in sale_ids and not s["anulada"] and start <= pd.Timestamp(s["fecha_venta"]).date() <= end]
    a,b = st.columns(2)
    with a:
        with tarjeta_grafico("Origen de las solicitudes","Incluye referidos por colega cuando están registrados","origen"):
            _mostrar(origenes(filtered_cases,reduced),"plot_origen")
    with b:
        dato_destacado(frase_destacada(data,grouping))
    with st.expander("Ver más gráficos"):
        a,b = st.columns(2)
        with a:
            with tarjeta_grafico("Modalidad","Participación por modalidad registrada","modalidad"):
                _mostrar(modalidades(filtered_cases,reduced),"plot_modalidad")
        with b:
            with tarjeta_grafico("Reserva vs remuneración","Reparto efectivamente registrado · CLP","reparto"):
                _mostrar(reparto(filtered_sales,reduced),"plot_reparto",
                         "El reparto de reserva y remuneración aún no está registrado.")
        counts = distribucion(filtered_cases,"servicio")
        with tarjeta_grafico("Tipo de servicio","Solicitudes por servicio · cantidad y porcentaje","servicio"):
            _mostrar(barras_horizontales(list(counts),list(counts.values()),AZUL,reduced),"plot_servicio")
    requests = data["requests"]
    if not requests.empty:
        with st.expander("Ver solicitudes del período"):
            rows = [{"Caso":code(c),"Cliente":c["cliente"],"Servicio":c["servicio"],"Temática":c["tematica"],
                     "Estado":etiqueta_estado(c["estado"]),"Fecha":pd.to_datetime(c["created_at"],utc=True).tz_convert("America/Santiago").date()}
                    for c in requests.to_dict("records")]
            tabla_registros(pd.DataFrame(rows),"Solicitudes del período")
    export = data["series"].rename(columns={"inicio":"Inicio","fin":"Fin","periodo":"Período","total":"Ventas CLP","cantidad":"Ventas cerradas","solicitudes":"Solicitudes"}).copy()
    for column in ["Inicio","Fin"]:
        export[column] = pd.to_datetime(export[column]).dt.strftime("%d/%m/%Y")
    st.download_button("Exportar resumen por período",csv_bytes(export),"resumen-por-periodo.csv","text/csv")
    st.caption("CLP · Ventas por fecha de aceptación · Solicitudes en hora de Chile · Anuladas excluidas.")


@st.fragment(run_every="30s")
def _actualizar_dashboard(repo):
    try:
        _contenido_dashboard(repo)
    except Exception as error:
        show_error(error,"No pudimos cargar la información. Reintenta en unos momentos.")
        if st.button("Volver al ingreso",key="dashboard_error_login"):
            logout()


def dashboard_page(repo):
    require_admin(repo)
    _actualizar_dashboard(repo)


if __name__ == "__main__":
    from utils.permisos import proteger_pagina
    dashboard_page(proteger_pagina('Dashboard',admin=True))
