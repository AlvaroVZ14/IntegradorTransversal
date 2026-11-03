"""Las tres vistas del portal; los permisos también se aplican en Supabase."""
from datetime import date
from uuid import uuid4

import pandas as pd
import streamlit as st

from mente_futuro.domain import PAYMENTS, SERVICES, STATES, TOPICS, code, csv_bytes, money, today
from servicios.documentos_cotizacion import generar_pdf,nombre_archivo
from servicios.cotizacion_defaults import RESERVA_PCT_DEFAULT,REMUNERACION_PCT_DEFAULT
from mente_futuro.ui import flash, show_error
from utils.permisos import require_admin
from utils.estados import etiqueta_estado, etiqueta_opcion_estado
from utils.componentes import (badge_estado, tabla_registros, encabezado_pagina,
                               titulo_seccion, cargando_datos)
from servicios.lecturas_locales import leer_con_respaldo
from servicios.en_vivo import cargar, carga_inicial
from utils.en_vivo import indicador as indicador_en_vivo


def _lectura(repo,clave,consulta):
    datos,respaldo=leer_con_respaldo(repo,clave,consulta)
    if respaldo:
        st.warning("Mostramos la última lectura de esta sesión mientras vuelve la conexión. Conservamos tus cambios pendientes.")
    return datos


def case_table(cases):
    frame=pd.DataFrame([{
        "Caso":code(c), "Cliente":c["cliente"] or 'Por completar', "Servicio":c["servicio"] or 'Por definir', "Temática":c["tematica"] or 'Por definir',
        "Estado":etiqueta_estado(c["estado"]), "Fecha":pd.to_datetime(c["created_at"], utc=True).tz_convert("America/Santiago").date(),
    } for c in cases])
    if any(c.get('datos_incompletos') for c in cases):frame['Datos']=['Faltan datos' if c.get('datos_incompletos') else 'Completos' for c in cases]
    return frame


def quote_history(quotes,repo=None,case=None):
    if not quotes:
        st.info("Este caso todavía no tiene cotizaciones emitidas.")
        return
    for q in quotes:
        expired = date.fromisoformat(q["valida_hasta"]) < today()
        label = f"{code(q, 'COT')} · {money(q['total_clp'])} · {'Vencida' if expired else 'Vigente'}"
        with st.expander(label, expanded=q == quotes[0]):
            st.caption(f"Emitida el {date.fromisoformat(q['fecha_emision']):%d/%m/%Y} · Válida hasta {date.fromisoformat(q['valida_hasta']):%d/%m/%Y}")
            st.text(q["detalle"])
            a,b,c = st.columns(3)
            a.metric("Valor base",money(q["base_clp"]))
            b.metric("Descuento",f"{q['descuento_pct']}%")
            c.metric("Total CLP",money(q["total_clp"]))
            st.caption("Exento de IVA" if q["iva_pct"] == 0 else "Total incluye IVA de 19%")
            st.text(q["condiciones"])
            try:
                if repo is not None:
                    from paginas.acciones_cotizacion import archivos
                    _,pdf=archivos(repo,q)
                else:pdf=generar_pdf(q)
                st.download_button("Descargar cotización", data=pdf, file_name=nombre_archivo(q), mime="application/pdf", key=f"download_{q['id']}")
            except Exception:
                st.warning('No pudimos preparar el PDF. La cotización sigue guardada; vuelve a intentar la descarga.')
            if repo is not None:
                from paginas.acciones_cotizacion import descargas,acciones,guardar_plantilla
                # Conserva las descargas adicionales y las acciones existentes.
                try:
                    descargas(repo,q)
                    acciones(repo,case,q)
                    guardar_plantilla(repo,case,q)
                except Exception:
                    st.caption('Activa el cotizador asistido para las descargas Word/PDF y decisiones integradas.')
        if repo is not None and st.session_state.get('cotizacion_lista')==q['id']:
            from paginas.acciones_cotizacion import descargas
            with st.container(key='mfy_quote_downloads'):
                st.write('Cotización lista ✓')
                descargas(repo,q,'lista')
                if st.button('Cerrar aviso',key='close_ready_'+q['id']):
                    st.session_state.pop('cotizacion_lista',None);st.rerun()


def edit_case(repo, case):
    from paginas.edicion_caso import editar_caso
    editar_caso(repo, case)


def issue_quote(repo,case):
    require_admin(repo)
    from paginas.cotizador import editor_cotizacion
    editor_cotizacion(repo,case)


def sale_form(repo, case, quotes):
    require_admin(repo)
    sale = next((s for s in _lectura(repo,"ventas",repo.sales) if s["caso_id"] == case["id"]),None)
    if sale:
        st.metric("Venta registrada",money(sale["monto_clp"]))
        if sale.get('reserva_clp') is not None and sale.get('remuneracion_clp') is not None:
            a,b=st.columns(2)
            a.metric('Reserva',money(sale['reserva_clp']),help=f"{sale['reserva_pct']}% del monto de la venta")
            b.metric('Remuneración',money(sale['remuneracion_clp']),help=f"{sale['remuneracion_pct']}% del monto de la venta")
        if sale.get('documento_numero'):st.caption('N° de documento: '+sale['documento_numero'])
        st.caption(f"Fecha de venta: {date.fromisoformat(sale['fecha_venta']):%d/%m/%Y}. Una venta anulada se excluye del dashboard.")
        with st.form(f"sale_{sale['id']}_{sale['version']}"):
            titulo_seccion(3, "Estado de la venta")
            payment = st.selectbox("Estado del pago",PAYMENTS,index=PAYMENTS.index(sale["estado_pago"]))
            annulled = st.checkbox("Venta anulada",value=sale["anulada"])
            confirm_annulled = st.checkbox("Confirmo anular esta venta") if not sale["anulada"] else True
            submitted = st.form_submit_button("Guardar estado de la venta",type="primary")
        if submitted:
            if annulled and not sale["anulada"] and not confirm_annulled:
                st.error("Confirma la anulación de la venta para continuar.")
                return
            try:
                repo.update_sale(sale,payment,annulled)
                flash("Venta actualizada.")
            except Exception as error:
                show_error(error)
        return
    if not quotes:
        st.info("Emite una cotización antes de registrar la venta.")
        return
    if case["estado"] in ("Cancelado", "Finalizado"):
        st.info("El caso está cerrado. Revisa su estado antes de registrar una venta.")
        return
    options = {q["id"]:q for q in quotes}
    chosen = st.selectbox("Cotización aceptada",list(options),format_func=lambda x:f"{code(options[x],'COT')} · {money(options[x]['total_clp'])}")
    quote = options[chosen]
    st.metric("Monto de la venta",money(quote["total_clp"]))
    with st.form(f"new_sale_{case['id']}_{chosen}"):
        titulo_seccion(3, "Registra la venta")
        sale_date = st.date_input("Fecha de aceptación",value=min(today(),date.fromisoformat(quote["valida_hasta"])),min_value=date.fromisoformat(quote["fecha_emision"]),max_value=today(),format="DD/MM/YYYY")
        payment = st.selectbox("Estado del pago",PAYMENTS)
        a,b=st.columns(2)
        reserva=a.number_input('Reserva (%)',0.0,100.0,RESERVA_PCT_DEFAULT,step=.5,key='venta_reserva_'+chosen)
        remuneracion=b.number_input('Remuneración (%)',0.0,100.0,REMUNERACION_PCT_DEFAULT,step=.5,key='venta_remuneracion_'+chosen)
        documento=st.text_input('N° de documento (opcional)',max_chars=100,key='venta_documento_'+chosen)
        confirmed = st.checkbox("El cliente aceptó esta cotización")
        st.caption("Registrar venta confirma la aceptación; la casilla anterior queda como apoyo opcional.")
        submitted = st.form_submit_button("Registrar venta",type="primary")
    if submitted:
        if round(reserva+remuneracion,2)!=100:
            st.error('Reserva y remuneración deben sumar 100%.');return
        if sale_date > date.fromisoformat(quote["valida_hasta"]):
            st.error("La fecha de aceptación debe estar dentro de la vigencia de la cotización.")
        else:
            try:
                from paginas.acciones_cotizacion import _decidir
                op=st.session_state.setdefault('venta_operacion_'+chosen,str(uuid4()))
                _decidir(repo,case,quote,dict(accion='vender',monto_clp=int(quote['total_clp']),
                    fecha=sale_date.isoformat(),estado_pago=payment,reserva_pct=reserva,
                    remuneracion_pct=remuneracion,documento_numero=documento),op)
            except Exception as error:
                show_error(error)


def _abrir_detalle():
    st.session_state.caso_abierto = st.session_state.get('selected_case')
    st.session_state.caso_navegar = True


def _cerrar_detalle():
    st.session_state.pop('caso_abierto', None)
    st.session_state.pop('selected_case', None)


def _cambio_estado_registro():
    state=st.session_state
    estado=state.get('casos_estado_filtro','Todos los estados')
    state.casos_chips_estados=estado if estado in ('Todos los estados',*STATES) else None
    state.selected_case=None
    state.pop('caso_abierto',None)
    state.pop('caso_navegar',None)


def _cambio_chip_estado():
    st.session_state.casos_estado_filtro=st.session_state.get('casos_chips_estados') or 'Todos los estados'
    _cambio_estado_registro()


def _listado_casos(repo):
    require_admin(repo)
    from servicios.hoy import FILTROS_ACCION,casos_por_accion
    filtro_previo=st.session_state.get('casos_estado_filtro','Todos los estados')
    # Una sola lectura: los filtros de acción necesitan cotizaciones/pagos y
    # reutilizan el snapshot de Hoy, que también contiene el registro completo.
    vista='hoy' if filtro_previo in FILTROS_ACCION else 'casos'
    with carga_inicial(vista, 'Buscando tus casos…'):
        lectura = cargar(repo, vista)
    if 'datos' not in lectura:
        indicador_en_vivo('casos', publicar=True, pausado=bool(st.session_state.get('caso_abierto')))
        st.info('Aún no pudimos conectar. El listado aparecerá cuando vuelva la conexión.')
        return
    cases = lectura['datos']['casos']
    indicador_en_vivo('casos', publicar=True, pausado=bool(st.session_state.get('caso_abierto')))
    st.write("")
    a,b = st.columns([2,1])
    search = a.text_input("Buscar un caso",placeholder="Nombre, servicio o número de caso",label_visibility="collapsed",key='casos_busqueda')
    state = b.selectbox("Filtrar estado",["Todos los estados",*STATES,*FILTROS_ACCION],label_visibility="collapsed",format_func=etiqueta_opcion_estado,
                        key='casos_estado_filtro',on_change=_cambio_estado_registro,
                        help='Elige un estado o uno de los tres grupos de pendientes de Hoy.')
    st.session_state.setdefault('casos_chips_estados',state if state in ('Todos los estados',*STATES) else None)
    st.pills('Estados del caso',['Todos los estados',*STATES],selection_mode='single',
             format_func=etiqueta_opcion_estado,key='casos_chips_estados',on_change=_cambio_chip_estado)
    if state in FILTROS_ACCION:
        cases=casos_por_accion(lectura['datos'],state)
    filtered = [c for c in cases if (state in ('Todos los estados',*FILTROS_ACCION) or c["estado"] == state)
                and search.casefold() in f"{c['cliente']} {c['servicio']} {code(c)}".casefold()]
    if not filtered:
        st.info("No hay casos que mostrar. Crea una solicitud o ajusta los filtros.")
        return
    frame = case_table(filtered)
    tabla_registros(frame)
    if repo.is_owner:
        st.download_button("Exportar listado CSV",csv_bytes(frame),file_name="casos-mente-y-futuro.csv",mime="text/csv")
    st.divider()
    options = {c["id"]:c for c in filtered}
    if st.session_state.get('selected_case') not in options:
        st.session_state.selected_case = None
    st.selectbox("Abrir detalle",list(options),index=None,placeholder='Selecciona un caso',
                 format_func=lambda x:f"{code(options[x])} · {options[x]['cliente']}",
                 key="selected_case",on_change=_abrir_detalle)


@st.fragment(run_every='60s')
def _listado_en_vivo(repo):
    require_admin(repo)
    if st.session_state.pop('caso_navegar', False):
        st.rerun(scope='app')
    _listado_casos(repo)


def cases_content(repo):
    require_admin(repo)
    seleccionado=st.session_state.get('selected_case')
    if seleccionado:
        st.session_state.caso_abierto=seleccionado
        st.session_state.pop('caso_navegar', None)
    if not st.session_state.get('caso_abierto'):
        _listado_en_vivo(repo)
        return
    # No se registra un timer de listado mientras hay un detalle abierto.
    _listado_casos(repo)
    seleccionado=st.session_state.get('caso_abierto')
    if not seleccionado:return
    st.button('Volver al listado',key='caso_volver_listado',on_click=_cerrar_detalle,
              icon=':material/arrow_back:')
    case = _lectura(repo, 'detalle:'+seleccionado, lambda:repo.get_case(seleccionado))
    st.subheader(f"{code(case)} · {case.get('servicio') or 'Servicio por definir'}")
    st.markdown(badge_estado(case["estado"]),unsafe_allow_html=True)
    from utils.canales import etiqueta_canal
    from utils.componentes import chips_activos
    chips_activos(['Canal · '+etiqueta_canal(case.get('canal_captacion'))])
    if case.get('datos_incompletos'):
        from utils.formulario_config import CAMPOS
        st.warning('Faltan datos: '+', '.join(CAMPOS['tematicas' if k=='tematica' else k].etiqueta for k in case.get('datos_pendientes',[])))
    st.write("")
    quotes = _lectura(repo,f"cotizaciones:{case['id']}",lambda:repo.quotes(case["id"]))
    if repo.is_owner:
        cotizar=st.session_state.pop('abrir_cotizacion',None)==case['id']
        if st.session_state.pop('abrir_datos_caso',False):cotizar=False
        venta=st.session_state.pop('abrir_venta',None)==case['id']
        tab_key='caso_pestana_'+case['id']
        if venta:st.session_state[tab_key]='Venta'
        elif cotizar:st.session_state[tab_key]='Cotizaciones'
        detail_tab, quote_tab, sale_tab, docs_tab = st.tabs(["Datos y seguimiento","Cotizaciones","Venta","Documentos"],key=tab_key,on_change='rerun')
        with detail_tab:
            edit_case(repo,case)
        with quote_tab:
            st.subheader("Historial de cotizaciones")
            quote_history(quotes,repo,case)
            st.divider()
            st.subheader("Preparar una cotización")
            issue_quote(repo,case)
        with sale_tab:
            sale_form(repo,case,quotes)
        with docs_tab:
            if docs_tab.open:
                from paginas.documentos_caso import documentos_caso
                documentos_caso(repo,case,quotes)
        from paginas.acciones_cotizacion import historial_eventos,aviso_deshacer
        historial_eventos(repo,case)
        aviso_deshacer(repo)


def tariffs_content(repo):
    require_admin(repo)
    repo.owner_only()
    st.subheader("Tarifario de referencia")
    st.caption("Los valores orientan cada propuesta. Editar una tarifa no cambia cotizaciones ya emitidas.")
    with cargando_datos("Preparando tus tarifas…"):
        tariffs = _lectura(repo,"tarifas",repo.tariffs)
    if tariffs:
        frame = pd.DataFrame([{"Plan":t["nombre"],"Servicio":t["servicio"],"Valor CLP":money(t["monto_clp"]),"Participantes":t["participantes"],"Horas":t["horas"],"IVA":t["tratamiento_iva"],"Activa":t["activa"]} for t in tariffs])
        tabla_registros(frame,"Tarifas y servicios")
    options = {t["id"]:t for t in tariffs}
    selected = st.selectbox("Crear o editar una tarifa",[None,*options],format_func=lambda x:options[x]["nombre"] if x else "+ Nueva tarifa")
    tariff = options.get(selected,{})
    with st.form(f"edit_tariff_{selected}_{tariff.get('version',0)}"):
        titulo_seccion(1, "Configura el servicio")
        name = st.text_input("Nombre del plan",value=tariff.get("nombre",""),max_chars=180)
        a,b = st.columns(2)
        with a:
            service = st.selectbox("Servicio asociado",SERVICES,index=SERVICES.index(tariff.get("servicio",SERVICES[0])))
            tema=None
            temas=[None,*TOPICS]
            actual=tariff.get('tematica') if tariff.get('tematica') in temas else None
            tema=st.selectbox('Temática de referencia (opcional)',temas,index=temas.index(actual),format_func=lambda x:x or 'Todas las temáticas')
            amount = st.number_input("Valor de referencia (CLP)",0,100000000000,int(tariff.get("monto_clp",0)),step=1000)
            people = st.number_input("Participantes de referencia",1,10000,tariff.get("participantes",1))
        with b:
            hours = st.number_input("Horas de atención de referencia",0.5,1000.0,float(tariff.get("horas",1)),step=0.5)
            tax_options = ["Por confirmar","Exento","IVA 19%"]
            tax = st.selectbox("Tratamiento de IVA",tax_options,index=tax_options.index(tariff.get("tratamiento_iva","Por confirmar")))
            active = st.checkbox("Disponible para nuevas cotizaciones",value=tariff.get("activa",True))
        detail = st.text_area("Alcance y servicios incluidos",value=tariff.get("detalle",""),max_chars=5000)
        source = st.text_input("Fuente o referencia",value=tariff.get("fuente",""),max_chars=500)
        submitted = st.form_submit_button("Guardar tarifa",type="primary")
    if submitted:
        if len(name.strip()) < 2:
            st.error("Ingresa el nombre del plan.")
        else:
            try:
                datos=dict(nombre=name.strip(),servicio=service,monto_clp=amount,participantes=people,horas=hours,tratamiento_iva=tax,detalle=detail.strip(),fuente=source.strip(),activa=active)
                datos['tematica']=tema
                repo.save_tariff(datos,tariff or None)
                flash("Tarifa guardada.")
            except Exception as error:
                show_error(error)


def cases_page(repo):
    require_admin(repo)
    encabezado_pagina("Casos y cotizaciones", "Cada solicitud, su propuesta y el siguiente paso.", "SEGUIMIENTO", "▤", mostrar_metricas=False)
    if st.session_state.pop('abrir_opciones_portal',False):
        st.session_state.casos_pestana='Tarifas y servicios'
        st.session_state.opciones_portal=True
    if st.session_state.get('casos_pestana')=='Configuración':st.session_state.casos_pestana='Tarifas y servicios'
    cases_tab, tariffs_tab = st.tabs(["Registro de casos", "Tarifas y servicios"],
                                               key='casos_pestana',on_change='rerun')
    with cases_tab:
        cases_content(repo)
    with tariffs_tab:
        tariffs_content(repo)
        if tariffs_tab.open:
            from paginas.opciones_portal import opciones_portal
            opciones_portal(repo)
    from paginas.acciones_cotizacion import mostrar_dialogo
    mostrar_dialogo(repo)


# Compatibilidad para importaciones anteriores.
from paginas.dashboard import dashboard_page


if __name__ == "__main__":
    from utils.permisos import proteger_pagina
    cases_page(proteger_pagina('Casos y cotizaciones',admin=True))
