"""Interfaz del tablero. Cálculos y períodos viven en servicios/dashboard.py."""

import pandas as pd
import streamlit as st

from mente_futuro.domain import code, csv_bytes, money, today
from servicios.dashboard import datos_dashboard, ventas_por_dimension
from servicios.periodos import (AGRUPACIONES, periodo_vigente, validar_rango,
                                navegar_periodo, puede_avanzar, etiqueta_rango)
from utils.estados import etiqueta_estado
from utils.permisos import require_admin
from utils.responsive import es_pantalla_movil
from utils.componentes import (estado_vacio, encabezado_pagina,
                               tarjeta_grafico, tarjeta_kpi, badge_estado, leyenda_estados, tabla_registros)
from utils.graficos_dashboard import (barras_horizontales, barras_ventas, embudo_estados, origenes,
                                     solicitudes_vs_ventas, ventas_por_periodo)
from mente_futuro.ui import show_error, logout
from servicios.en_vivo import carga_inicial, estado


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
    container = st.expander('Filtros', expanded=False, key='dashboard_filters') if mobile else st.container(key='dashboard_filters')
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
        fig.update_layout(uirevision=key, height=320)
        st.plotly_chart(fig, width="stretch", theme=None, key=key,
                        config={"displayModeBar":False,"responsive":True,"scrollZoom":False})


def _contenido_dashboard(repo, filtros_activos, demo=False):
    require_admin(repo)
    start, end, grouping, _ = filtros_activos
    repetida = estado('dashboard').get('intentado', False)
    if demo:
        from servicios.dashboard_demo import datos_demo
        cases, sales = datos_demo(start, end)
        st.info('Datos de prueba ficticios. No son ventas reales y no se guardan en Supabase.')
    else:
        with carga_inicial('dashboard', 'Preparando tu tablero…'):
            from servicios.en_vivo import cargar
            lectura = cargar(repo, 'dashboard')
        if 'datos' not in lectura:
            st.info('Aún no pudimos conectar. La información aparecerá cuando vuelva la conexión.')
            return
        cases, sales = lectura['datos']['casos'], lectura['datos']['ventas']
    data = datos_dashboard(cases, sales, start, end, grouping)
    reduced = repetida or st.session_state.get('dashboard_reduced_motion', False)
    previous_start, previous_end = data['previous_range']
    st.caption(f'Comparado con {previous_start:%d/%m/%Y} – {previous_end:%d/%m/%Y}',
               help='Días inmediatamente anteriores con igual duración. Sin ventas previas no se inventa un porcentaje.')
    conversion = data['conversion']
    cards = [
        ('Total vendido', money(data['total']), 'total', '↗', 'azul',
         'Suma de las ventas no anuladas por fecha de venta. La variación compara con el rango anterior de igual duración.'),
        ('Venta promedio', money(data['average']) if data['average'] is not None else '—', 'average', '◈', 'azul',
         'Total vendido dividido por los casos vendidos en el período.'),
        ('Conversión', f'{conversion:.1f}%'.replace('.', ',') if conversion is not None else '—', 'conversion', '◎', 'morado',
         'Porcentaje de solicitudes creadas en el rango que tuvieron una venta no anulada hasta el último día del rango.'),
        ('Pago pendiente', money(data['pending_payment']), 'pending_payment', '◷', 'amarillo',
         'Monto completo de las ventas del período cuyo pago no está completado. Incluye anticipos; no representa el saldo restante.')]
    with st.container(key='mfy_dashboard_kpis'):
        for column, card in zip(st.columns(4, gap='small'), cards):
            label, value, key, icon, tone, ayuda = card
            delta = _delta(data, key) if key == 'total' else None
            caption = delta if delta == 'Sin datos del período anterior' else None
            with column:
                tarjeta_kpi(label, value, key=key, icon=icon, tone=tone, help=ayuda,
                            delta=None if caption else delta, caption=caption)
    unidad = {'Semanal':'Semanas', 'Mensual':'Meses', 'Trimestral':'Trimestres',
              'Semestral':'Semestres', 'Anual':'Años'}[data['evolution_grouping']]
    ventas = data['sales'].to_dict('records')
    ids = set(data['requests'].id)
    solicitudes = [c for c in cases if c['id'] in ids]
    a, b = st.columns(2)
    with a:
        with tarjeta_grafico('Ventas por período', f'{unidad} del rango elegido; línea amarilla = promedio.', 'ventas'):
            _mostrar(ventas_por_periodo(data['evolution'], reduced), 'plot_ventas',
                     'Aún no hay ventas en este período. Prueba con un rango más amplio.')
    with b:
        with tarjeta_grafico('Ventas por temática', 'Monto vendido según la temática principal del caso.', 'tematicas'):
            _mostrar(barras_ventas(ventas_por_dimension(cases, ventas, 'tematica'), reduced), 'plot_temas',
                     'Las ventas por temática aparecerán cuando registres una venta en este período.')
    a, b = st.columns(2)
    with a:
        with tarjeta_grafico('Ventas por tipo de servicio', 'Monto vendido por servicio, dentro de las fechas elegidas.', 'servicio'):
            _mostrar(barras_ventas(ventas_por_dimension(cases, ventas, 'servicio'), reduced), 'plot_servicio',
                     'Las ventas por servicio aparecerán cuando registres una venta en este período.')
    with b:
        with tarjeta_grafico('Embudo de casos por estado', 'Distribución actual de las solicitudes recibidas en el período.', 'embudo',
                            help='Muestra cantidades actuales, no transiciones históricas de un mismo caso.'):
            leyenda_estados()
            _mostrar(embudo_estados(data['states'], reduced), 'plot_embudo', 'Aún no hay casos en estas etapas del período.')
            fuera = data['states'][~data['states'].estado.isin(['Solicitud','Cotizada','Aceptada','En seguimiento','Cerrada'])]
            if not fuera.empty:
                st.markdown('<div class="mfy-state-key">'+''.join(badge_estado(r.estado,r.Casos) for r in fuera.itertuples())+'</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        with tarjeta_grafico('Origen de las solicitudes', 'Cómo llegaron las solicitudes recibidas en el rango elegido.', 'origen'):
            _mostrar(origenes(solicitudes, reduced), 'plot_origen')
    from utils.canales import conteo_canales
    canales=conteo_canales(solicitudes)
    if canales:
        with b:
            with tarjeta_grafico('Solicitudes por canal', 'Canal del enlace de las solicitudes recibidas en el rango elegido.', 'canales'):
                _mostrar(barras_horizontales(list(canales),list(canales.values()),reduced_motion=reduced),'plot_canales')
    with st.expander('Ver detalle de indicadores'):
        # Solo conteos adicionales: no repite los cuatro KPI de arriba.
        tabla_registros(pd.DataFrame([
            {'Indicador':nombre, 'Valor':str(data[key]), 'Período anterior':str(data['previous'][key]),
             'Variación':_delta(data,key) or '—'} for nombre,key in
            [('Cantidad de ventas','sales_count'),('Solicitudes recibidas en el período','requests_count')]]), 'Detalle de indicadores')
    if not data['requests'].empty:
        with st.expander('Ver solicitudes del período'):
            rows = [{'Caso':code(c), 'Cliente':c['cliente'], 'Servicio':c['servicio'], 'Temática':c['tematica'],
                     'Estado':etiqueta_estado(c['estado']),
                     'Fecha':pd.to_datetime(c['created_at'],utc=True).tz_convert('America/Santiago').date()}
                    for c in data['requests'].to_dict('records')]
            tabla_registros(pd.DataFrame(rows), 'Solicitudes del período')
    export = data['series'].rename(columns={'inicio':'Inicio','fin':'Fin','periodo':'Período','total':'Ventas CLP',
        'cantidad':'Cantidad de ventas','solicitudes':'Solicitudes'}).copy()
    for column in ('Inicio','Fin'):
        export[column] = pd.to_datetime(export[column]).dt.strftime('%d/%m/%Y')
    st.download_button('Exportar resumen por período', csv_bytes(export),
                       'DEMO-resumen-por-periodo.csv' if demo else 'resumen-por-periodo.csv', 'text/csv')


@st.fragment(run_every="60s")
def _actualizar_dashboard(repo, filtros_activos, demo=False):
    try:
        _contenido_dashboard(repo, filtros_activos, demo)
    except Exception as error:
        show_error(error,"No pudimos cargar la información. Reintenta en unos momentos.")
        if st.button("Volver al ingreso",key="dashboard_error_login"):
            logout()


def dashboard_page(repo):
    require_admin(repo)
    with st.container(key='mfy_dashboard'):
        hero = st.container()
        activos = filtros()
        start, end, grouping, personalizado = activos
        with hero:
            encabezado_pagina('Una mirada a tu negocio', etiqueta_rango(start, end, grouping, personalizado),
                              'DASHBOARD', '✦', mostrar_metricas=False)
        demo = st.toggle('Ver datos de prueba', key='dash_demo', value=False,
                         help='Muestra un ejemplo ficticio solo en este Dashboard. No agrega ni modifica datos reales.')
        _actualizar_dashboard(repo, activos, demo)
        if not demo:
            from paginas.reportes import panel_reportes
            panel_reportes(repo)



if __name__ == "__main__":
    from utils.permisos import proteger_pagina
    dashboard_page(proteger_pagina('Dashboard',admin=True))
