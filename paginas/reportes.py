"""Sección de reportes de Administración, independiente de los filtros del tablero."""
from uuid import uuid4
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mente_futuro.domain import money,today
from servicios.reportes import AGRUPACIONES,INDICADORES,reporte_periodos,totales_reporte,exportar_reporte,validar_rango
from servicios.en_vivo import estado
from utils.permisos import require_admin
from utils.plotly_tema import aplicar_tema
from utils.estilos import AZUL,MORADO


@st.cache_data(ttl=60,show_spinner=False,max_entries=64)
def _cotizaciones(usuario,ambito,revision,_repo):
    return _repo.all_quotes()


def contenido_reportes(repo,casos,ventas):
    require_admin(repo)
    hoy=today()
    st.session_state.setdefault('reporte_desde',hoy.replace(month=1,day=1))
    st.session_state.setdefault('reporte_hasta',hoy)
    with st.form('reportes_filtros'):
        a,b,c=st.columns(3)
        agrupacion=a.selectbox('Agrupación del reporte',AGRUPACIONES,key='reporte_agrupacion')
        desde=b.date_input('Desde',value=None,format='DD/MM/YYYY',key='reporte_desde')
        hasta=c.date_input('Hasta',value=None,format='DD/MM/YYYY',key='reporte_hasta')
        st.form_submit_button('Generar reporte',type='primary',width='stretch')
    try:validar_rango(desde,hasta,agrupacion)
    except ValueError as error:st.warning(str(error));return
    try:
        ambito=st.session_state.setdefault('reportes_ambito',str(uuid4()))
        cotizaciones=_cotizaciones(repo.user.id,ambito,st.session_state.get('dashboard_revision',0),repo)
        frame=reporte_periodos(casos,cotizaciones,ventas,desde,hasta,agrupacion)
    except PermissionError:raise
    except Exception:
        st.warning('No pudimos preparar el reporte. Revisa la conexión y vuelve a intentarlo.');return
    total=totales_reporte(frame)
    st.caption(f'{agrupacion} · {desde:%d/%m/%Y} – {hasta:%d/%m/%Y} · Ambos días incluidos. '
               'Este reporte usa sus propios filtros y considera todos los servicios y temáticas.')
    tabla=frame.copy()
    for columna in ('Desde','Hasta'):tabla[columna]=tabla[columna].map(lambda f:f.strftime('%d/%m/%Y'))
    tabla=pd.concat([tabla,pd.DataFrame([{'Período':'Total del rango','Desde':'','Hasta':'',**total}])],ignore_index=True)
    for columna in INDICADORES:
        if columna.endswith('(CLP)'):tabla[columna]=tabla[columna].map(money)
    st.dataframe(tabla,hide_index=True,width='stretch',height=min(480,38*(len(tabla)+1)),
        key='tabla_reporte',column_config={k:st.column_config.NumberColumn(k,format='%d')
                                          for k in INDICADORES if not k.endswith('(CLP)')})
    indicador=st.selectbox('Indicador del gráfico',INDICADORES,index=3,key='reporte_indicador')
    moneda=indicador.endswith('(CLP)')
    valores=frame[indicador].astype(int).tolist()
    fig=go.Figure(go.Bar(x=frame['Período'].tolist(),y=valores,
        marker_color=MORADO if indicador=='Solicitudes' else AZUL,
        customdata=[money(v) if moneda else str(v) for v in valores],
        hovertemplate='%{x}<br>%{customdata}<extra></extra>'))
    fig.update_xaxes(tickangle=-45 if len(frame)>6 else 0,type='category',automargin=True)
    fig.update_yaxes(tickformat=',.0f' if moneda else ',d',tickprefix='$' if moneda else '',
                     rangemode='tozero',**({} if moneda else {'dtick':1}))
    fig.update_layout(uirevision='reporte_'+indicador)
    st.plotly_chart(aplicar_tema(fig,True),width='stretch',theme=None,key='grafico_reporte',
                    config={'displayModeBar':False,'responsive':True,'scrollZoom':False})
    if not any(total.values()):st.info('No hay movimientos en este rango. Los períodos se muestran en cero.')
    st.download_button('Descargar reporte CSV',exportar_reporte(frame),
        file_name=f'Reporte_{agrupacion}_{desde:%Y%m%d}_{hasta:%Y%m%d}.csv',mime='text/csv',key='descargar_reporte',width='stretch')
    st.caption('Cotizaciones: versiones emitidas, sin borradores. Ventas cerradas: registros no anulados por fecha de venta. '
               'Pago pendiente: valor completo de ventas no pagadas, no saldo restante. '
               'El CSV conserva montos numéricos en pesos chilenos y se puede abrir en Excel.')


def panel_reportes(repo):
    require_admin(repo)
    with st.expander('Reportes por período',key='reportes_panel',on_change='rerun') as panel:
        if not panel.open:return
        datos=estado('dashboard').get('datos')
        if datos is None:
            st.info('El reporte estará disponible cuando se recupere la conexión.');return
        contenido_reportes(repo,datos['casos'],datos['ventas'])
