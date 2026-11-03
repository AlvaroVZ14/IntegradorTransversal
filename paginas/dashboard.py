"""Interfaz del tablero. Cálculos y períodos viven en servicios/dashboard.py."""

import pandas as pd
import streamlit as st

from mente_futuro.domain import code, csv_bytes, money, today
from servicios.dashboard import datos_dashboard
from servicios.periodos import (AGRUPACIONES, periodo_vigente, validar_rango,
                                navegar_periodo, puede_avanzar, etiqueta_rango)
from utils.estados import etiqueta_estado
from utils.permisos import require_admin
from utils.responsive import es_pantalla_movil
from utils.componentes import (dato_destacado, estado_vacio, encabezado_pagina,
                               tarjeta_grafico, tarjeta_kpi, badge_estado, leyenda_estados, tabla_registros)
from utils.graficos_dashboard import (barras_horizontales, distribucion, embudo_estados, frase_destacada,
                                     modalidades, origenes, reparto, solicitudes_vs_ventas,
                                     tematicas_dona, ventas_por_periodo)
from utils.estilos import AZUL
from mente_futuro.ui import show_error, logout
from servicios.en_vivo import carga_inicial, estado
from utils.en_vivo import indicador
from utils.metricas_visuales import contexto_cohortes


def _aplicar(personalizado=False):
    state = st.session_state
    try:
        desde, hasta = validar_rango(state.dash_desde, state.dash_hasta)
    except ValueError as error:
        state.dash_error = str(error)
        return
    state.dash_aplicado = (desde, hasta, state.dash_agrupacion, personalizado)
    state.pop('dash_error', None)


def _limpiar():
    state = st.session_state
    agrupacion = state.get('dash_agrupacion', 'Mensual')
    if agrupacion not in AGRUPACIONES:
        agrupacion = 'Mensual'
    state.dash_agrupacion = agrupacion
    state.dash_desde, state.dash_hasta = periodo_vigente(agrupacion, today())
    _aplicar()


def _cambiar_fecha():
    _aplicar(personalizado=True)


def _mover(direccion):
    state = st.session_state
    desde, _, agrupacion, _ = state.dash_aplicado
    state.dash_desde, state.dash_hasta = navegar_periodo(desde, agrupacion, direccion, today())
    _aplicar()


def filtros():
    state = st.session_state
    if 'dash_aplicado' not in state:
        # Conserva un rango manual de una sesión anterior; descarta filtros retirados.
        if (state.get('dash_rango') == 'Personalizado' and state.get('dash_agrupacion') in AGRUPACIONES
                and state.get('dash_desde') and state.get('dash_hasta')
                and state.dash_desde <= state.dash_hasta):
            _aplicar(personalizado=True)
        else:
            _limpiar()
    for key in ('dash_rango', 'dash_servicio', 'dash_tematica', 'dash_aviso'):
        state.pop(key, None)
    desde_aplicado, hasta_aplicado, grupo_aplicado, _ = state.dash_aplicado
    # Streamlit limpia claves de widgets al salir de una página. El rango válido
    # permanece separado de los widgets y se repone al volver al Dashboard.
    if 'dash_desde' not in state or 'dash_hasta' not in state:
        state.pop('dash_error', None)
    state.setdefault('dash_agrupacion', grupo_aplicado)
    state.setdefault('dash_desde', desde_aplicado)
    state.setdefault('dash_hasta', hasta_aplicado)
    mobile = es_pantalla_movil()
    container = st.expander('Filtros', expanded=True, key='dashboard_filters') if mobile else st.container(key='dashboard_filters')
    with container:
        columns = [st.container() for _ in range(4)] if mobile else st.columns([1.4, 1.2, 1.2, 1], gap='small')
        columns[0].selectbox('Agrupar por', AGRUPACIONES, key='dash_agrupacion', on_change=_limpiar)
        columns[1].date_input('Desde', key='dash_desde', format='DD/MM/YYYY', on_change=_cambiar_fecha)
        columns[2].date_input('Hasta', key='dash_hasta', format='DD/MM/YYYY', on_change=_cambiar_fecha)
        with columns[3]:
            st.write('')
            st.button('Limpiar', on_click=_limpiar, width='stretch')
        anterior, siguiente = st.columns(2)
        desde, _, agrupacion, _ = state.dash_aplicado
        anterior.button('Anterior', icon=':material/chevron_left:', on_click=_mover, args=(-1,), width='stretch')
        siguiente.button('Siguiente', icon=':material/chevron_right:', on_click=_mover, args=(1,),
                         disabled=not puede_avanzar(desde, agrupacion, today()), width='stretch')
    if state.get('dash_error'):
        st.warning(state.dash_error)
    return state.dash_aplicado


# Adaptadores para las importaciones anteriores del dashboard.
def grafico_periodos(serie, solicitudes=False):
    return solicitudes_vs_ventas(serie) if solicitudes else ventas_por_periodo(serie)


def grafico_conteos(frame, category, value):
    return barras_horizontales(frame[category].tolist(),frame[value].tolist())


def _delta(data, key):
    actual, previous = data[key], data['previous'][key]
    if (key != 'requests_count' and not data['previous']['sales_count']) or previous in (None, 0):
        return 'Sin datos del período anterior'
    if actual is None:
        return None
    variation = data['variations'][key]
    return f'{variation:+.1f}%'.replace('.', ',') if variation is not None else None


def _mostrar(fig, key, mensaje=None):
    if fig is None:
        estado_vacio(mensaje or "Aún no hay solicitudes en este período. Prueba con un rango más amplio.")
    else:
        fig.update_layout(uirevision=key)
        st.plotly_chart(fig, width="stretch", theme=None, key=key,
                        config={"displayModeBar":False,"responsive":True,"scrollZoom":False})


def _contenido_dashboard(repo, filtros_activos):
    require_admin(repo)
    start, end, grouping, _ = filtros_activos
    repetida = estado('dashboard').get('intentado', False)
    with carga_inicial('dashboard', 'Preparando tu tablero…'):
        from servicios.en_vivo import cargar
        lectura = cargar(repo, 'dashboard')
    if 'datos' not in lectura:
        indicador('dashboard', publicar=True)
        st.info('Aún no pudimos conectar. La información aparecerá cuando vuelva la conexión.')
        return
    cases, sales = lectura['datos']['casos'], lectura['datos']['ventas']
    data = datos_dashboard(cases, sales, start, end, grouping)
    indicador('dashboard', publicar=True)
    reduced = repetida or st.session_state.get("dashboard_reduced_motion",False)
    previous_start, previous_end = data["previous_range"]
    st.caption(f"Comparado con {previous_start:%d/%m/%Y} – {previous_end:%d/%m/%Y}", help=
        "Días inmediatamente anteriores, con la misma duración inclusiva que el rango elegido. Sin ventas previas no se inventa un porcentaje.")
    conversion = data["conversion"]
    conversion_text = None
    if conversion is not None:
        number = f"{conversion/10:.1f}".rstrip("0").rstrip(".").replace(".",",")
        conversion_text = f"De cada 10 solicitudes, {number} terminaron en venta"
    cards = [
        ("Total vendido",money(data["total"]),"total","↗","azul",
         "Suma de las ventas no anuladas por fecha de venta. La cantidad cuenta registros de venta, no casos en estado Cerrada.",
         f"{data['sales_count']} {'venta registrada' if data['sales_count']==1 else 'ventas registradas'}"+
         (f" · {_delta(data,'sales_count')} en cantidad" if data["variations"]["sales_count"] is not None else '')),
        ("Venta promedio",money(data["average"]) if data["average"] is not None else "—","average","◈","amarillo","Total vendido dividido por los casos vendidos en el período",None),
        ("Solicitudes que se vendieron",f"{conversion:.1f}%".replace(".",",") if conversion is not None else "—","conversion","◎","morado","Solicitudes creadas en el rango que tienen venta no anulada hasta su fecha final.",conversion_text),
        ("Ventas con pago pendiente",money(data["pending_payment"]),"pending_payment","◷","amarillo","Valor completo de las ventas no pagadas totalmente, incluidas las que tienen abonos; no es el saldo exacto por cobrar.",None),
    ]
    serie=data['evolution'].tail(6)
    tendencias={'total':serie.total.tolist(),'sales_count':serie.cantidad.tolist(),
                'requests_count':serie.solicitudes.tolist(),
                'average':[t/n if n else None for t,n in zip(serie.total,serie.cantidad)]}
    tendencias.update(contexto_cohortes({**data, 'series':data['evolution']},sales,end))
    contexto={'total':'Total vendido por período','sales_count':'Ventas registradas por período',
              'requests_count':'Solicitudes recibidas por período','average':'Promedio de ventas por período',
              'conversion':'Solicitudes de cada período vendidas al fin del rango',
              'pending_payment':'Ventas actuales por cobrar, por fecha de venta'}
    for offset in [0,2]:
        for column,card in zip(st.columns(2),cards[offset:offset+2]):
            label,value,key,icon,tone,help_text,caption = card
            with column:
                delta = _delta(data,key)
                if delta == 'Sin datos del período anterior':
                    caption = (caption + ' · ' if caption else '') + delta
                    delta = None
                tarjeta_kpi(label,value,key=key,icon=icon,tone=tone,delta=delta,help=help_text,
                            caption=caption,inverse=key=="pending_payment",serie=tendencias.get(key),
                            etiquetas=serie.periodo.tolist(),contexto_serie=contexto.get(key),
                            formato_serie='moneda' if key in ('total','average','pending_payment') else 'porcentaje' if key=='conversion' else 'entero')
    with st.expander('Ver detalle de indicadores'):
        # Reubicar valores, sin recalcularlos ni perder sus comparaciones.
        indicadores=[('Total vendido','total',True),('Cantidad de ventas','sales_count',False),
                     ('Solicitudes recibidas en el período','requests_count',False),
                     ('Venta promedio','average',True),('Solicitudes que se vendieron','conversion',False),
                     ('Ventas con pago pendiente','pending_payment',True)]
        def valor(key,datos,moneda):
            n=datos[key]
            if n is None:return '—'
            if key=='conversion':return f'{n:.1f}%'.replace('.',',')
            return money(n) if moneda else str(n)
        tabla_registros(pd.DataFrame([{'Indicador':label,'Valor':valor(key,data,moneda),
            'Período anterior':valor(key,data['previous'],moneda),'Variación':_delta(data,key) or '—'}
            for label,key,moneda in indicadores]),'Detalle de indicadores')
    a,b = st.columns(2)
    unidad = {'Semanal':'Semanas', 'Mensual':'Meses', 'Trimestral':'Trimestres',
              'Semestral':'Semestres', 'Anual':'Años'}[data['evolution_grouping']]
    with a:
        with tarjeta_grafico("Ventas por período",f"{unidad} del rango elegido · total, promedio y mejor período · CLP","ventas"):
            _mostrar(ventas_por_periodo(data["evolution"],reduced),"plot_ventas",
                     "Aún no hay ventas en este período. Prueba con un rango más amplio.")
    with b:
        with tarjeta_grafico("Solicitudes vs ventas",f"{unidad} del rango elegido · cantidad de solicitudes y ventas cerradas","comparacion"):
            _mostrar(solicitudes_vs_ventas(data["evolution"],reduced),"plot_comparacion")
    a,b = st.columns(2)
    with a:
        with tarjeta_grafico("Temáticas más solicitadas","Las 5 principales y otras · porcentaje de solicitudes","tematicas"):
            _mostrar(tematicas_dona(data["topics"],reduced),"plot_temas")
    with b:
        with tarjeta_grafico("Embudo por estado del caso","En qué etapa están tus casos","embudo",
                            help="Distribución actual de casos; no representa transiciones históricas."):
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
    with tarjeta_grafico('Solicitudes por canal','Canal del enlace usado · mismo período y filtros del tablero','canales'):
        from utils.canales import conteo_canales
        canales=conteo_canales(filtered_cases)
        _mostrar(barras_horizontales(list(canales),list(canales.values()),AZUL,reduced),'plot_canales')
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
    st.caption("Montos en pesos chilenos",help="Ventas por fecha de aceptación. Solicitudes en hora de Chile. Ventas anuladas excluidas.")


@st.fragment(run_every="60s")
def _actualizar_dashboard(repo, filtros_activos):
    try:
        _contenido_dashboard(repo, filtros_activos)
    except Exception as error:
        show_error(error,"No pudimos cargar la información. Reintenta en unos momentos.")
        if st.button("Volver al ingreso",key="dashboard_error_login"):
            logout()


def dashboard_page(repo):
    require_admin(repo)
    hero = st.container()
    activos = filtros()
    start, end, grouping, personalizado = activos
    with hero:
        encabezado_pagina("Una mirada a tu negocio", etiqueta_rango(start, end, grouping, personalizado),
                          "DASHBOARD", "✦", mostrar_metricas=False)
    _actualizar_dashboard(repo, activos)
    from paginas.reportes import panel_reportes
    panel_reportes(repo)


if __name__ == "__main__":
    from utils.permisos import proteger_pagina
    dashboard_page(proteger_pagina('Dashboard',admin=True))
