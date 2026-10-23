"""Las tres vistas del portal; los permisos también se aplican en Supabase."""
from datetime import date, timedelta, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st

from mente_futuro.domain import MODALITIES, PAYMENTS, SERVICES, STATES, TOPICS, code, csv_bytes, money, quote_total, today, validate_request
from mente_futuro.presentation import quote_html
from mente_futuro.ui import flash, show_error
from utils.permisos import require_admin
from utils.estados import etiqueta_estado, etiqueta_opcion_estado
from utils.componentes import (badge_estado, leyenda_estados, tabla_registros, encabezado_pagina,
                               tarjeta_kpi, titulo_seccion, cargando_datos)
from servicios.lecturas_locales import leer_con_respaldo


def _lectura(repo,clave,consulta):
    datos,respaldo=leer_con_respaldo(repo,clave,consulta)
    if respaldo:
        st.warning("Mostramos la última lectura de esta sesión mientras vuelve la conexión. Conservamos tus cambios pendientes.")
    return datos


def case_table(cases):
    return pd.DataFrame([{
        "Caso":code(c), "Cliente":c["cliente"], "Servicio":c["servicio"], "Temática":c["tematica"],
        "Estado":etiqueta_estado(c["estado"]), "Fecha":pd.to_datetime(c["created_at"], utc=True).tz_convert("America/Santiago").date(),
    } for c in cases])


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
            st.download_button("Descargar cotización", data=quote_html(q), file_name=f"{code(q,'COT')}.html", mime="text/html", key=f"download_{q['id']}")
            st.caption("Abre el archivo descargado para imprimirlo o guardarlo como PDF desde el navegador.")
            if repo is not None:
                from paginas.acciones_cotizacion import descargas,acciones,guardar_plantilla
                # Documentos antiguos conservan también la descarga HTML original.
                try:
                    repo.quote_settings()
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


def legacy_issue_quote(repo, case):
    require_admin(repo)
    if case["estado"] in ("Vendido", "En ejecución", "Finalizado", "Cancelado"):
        st.info("Este caso está cerrado para nuevas cotizaciones. Puedes consultar las propuestas emitidas.")
        return
    tariffs = {t["id"]:t for t in _lectura(repo,"tarifas",repo.tariffs) if t["activa"] and t["servicio"] == case["servicio"]}
    selected = st.selectbox("Tarifa de referencia",[None,*tariffs],format_func=lambda x:f"{tariffs[x]['nombre']} · {money(tariffs[x]['monto_clp'])}" if x else "Cotización personalizada",key=f"tariff_for_{case['id']}")
    tariff = tariffs.get(selected)
    if tariff:
        st.caption(f"Referencia: {tariff['participantes']} participantes · {tariff['horas']} horas. {tariff['fuente']}")
        if tariff["participantes"] != case["participantes"] or float(tariff["horas"]) != float(case["horas"]):
            st.warning("La cantidad de participantes o las horas difieren de esta referencia. Ajusta el monto y el alcance antes de emitir.")
    # Un cambio autoguardado del contacto no borra la propuesta que se prepara.
    key = f"quote_{case['id']}_{selected}"
    operation_key = f"quote_operation_{case['id']}"
    if operation_key not in st.session_state:
        st.session_state[operation_key] = str(uuid4())
    with st.container(border=True, key="mfy_form_quote"):
        titulo_seccion(2, "Tu propuesta a medida")
        a,b,c = st.columns(3)
        base = a.number_input("Valor base (CLP)",min_value=0,max_value=100000000000,value=int(tariff["monto_clp"]) if tariff else 0,step=1000,key=key+"base")
        discount = b.number_input("Descuento (%)",0.0,100.0,0.0,step=0.5,key=key+"discount")
        iva_labels = ["Exento de IVA", "IVA 19%"]
        tax_default = {"Exento":0,"IVA 19%":1}.get(tariff.get("tratamiento_iva")) if tariff else None
        tax_label = c.selectbox("Tratamiento de IVA *",iva_labels,index=tax_default,placeholder="Selecciona una opción",key=key+"tax")
        detail = st.text_area("Detalle incluido en la propuesta *",value=tariff["detalle"] if tariff else case["detalle"],max_chars=5000,height=130,key=key+"detail")
        validity = st.date_input("Válida hasta", value=today()+timedelta(days=30),min_value=today(), format="DD/MM/YYYY",key=key+"validity")
        conditions = st.text_area("Condiciones comerciales",value="50% de anticipo para reservar la fecha y 50% al finalizar la actividad. Pago mediante transferencia. La fecha queda reservada una vez recibido el anticipo.",max_chars=5000,height=100,key=key+"conditions")
        tax = 19 if tax_label == "IVA 19%" else 0
        if tax_label:
            st.metric("Total de la propuesta (CLP)",money(quote_total(base,discount,tax)))
        st.caption("Revisa las condiciones para este servicio. Los descuentos son manuales y el documento conservará los valores al momento de emitir.")
        submitted = st.button("Emitir y guardar cotización",type="primary",key=key+"emit")
    if submitted:
        if len(detail.strip()) < 2 or tax_label is None:
            st.error("Agrega el detalle del servicio y selecciona el tratamiento de IVA.")
        else:
            try:
                repo.issue_quote(case, dict(tarifa_id=selected, base_clp=base, descuento_pct=discount, iva_pct=tax, detalle=detail.strip(), condiciones=conditions.strip(), valida_hasta=validity.isoformat()),st.session_state[operation_key])
                del st.session_state[operation_key]
                flash("Cotización guardada. Está disponible en el historial de Administración.")
            except Exception as error:
                show_error(error)


def issue_quote(repo,case):
    require_admin(repo)
    try:
        repo.quote_settings()
    except Exception as error:
        if isinstance(error,AttributeError) or getattr(error,'code','') in ('PGRST205','42P01','PGRST202'):
            st.info('Activa 202610220003_cotizador_asistido.sql para el editor asistido. Mientras tanto, se conserva el cotizador anterior.')
            legacy_issue_quote(repo,case)
        else:show_error(error)
        return
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
        confirmed = st.checkbox("El cliente aceptó esta cotización")
        st.caption("Registrar venta confirma la aceptación; la casilla anterior queda como apoyo opcional.")
        submitted = st.form_submit_button("Registrar venta",type="primary")
    if submitted:
        if sale_date > date.fromisoformat(quote["valida_hasta"]):
            st.error("La fecha de aceptación debe estar dentro de la vigencia de la cotización.")
        else:
            try:
                venta=repo.record_sale(case,quote,sale_date,payment)
                if venta and venta.get("caso_version_aceptada") and venta.get("estado_caso_anterior"):
                    st.session_state.deshacer_venta={"id":venta["id"],"caso_id":case["id"],
                        "version":venta["caso_version_aceptada"],
                        "vence":datetime.fromisoformat(venta["created_at"].replace("Z","+00:00")).timestamp()+10}
                flash("Venta guardada. El dashboard ya puede incluirla en el período correspondiente.")
            except Exception as error:
                show_error(error)


def cases_content(repo):
    require_admin(repo)
    with cargando_datos("Buscando tus casos…"):
        cases = _lectura(repo,"casos",repo.cases)
    indicadores = [
        ("Casos registrados",len(cases),"▤","azul",None,"casos_total"),
        ("Por revisar",sum(x["estado"] in ("Solicitud","En revisión") for x in cases),"◷","morado","Solicitudes nuevas y solicitudes en revisión. No incluye casos ya cotizados.","casos_revisar"),
        ("En desarrollo",sum(x["estado"] in ("Vendido","En ejecución") for x in cases),"↗","amarillo","Casos en Aceptada o En seguimiento. No incluye casos cerrados ni rechazados.","casos_desarrollo"),
    ]
    for columna, indicador in zip(st.columns(3), indicadores):
        label,value,icon,tone,ayuda,key = indicador
        with columna:
            tarjeta_kpi(label,value,icon=icon,tone=tone,help=ayuda,key=key)
    st.write("")
    a,b = st.columns([2,1])
    search = a.text_input("Buscar un caso",placeholder="Nombre, servicio o número de caso",label_visibility="collapsed",key='casos_busqueda')
    state = b.selectbox("Filtrar estado",["Todos los estados",*STATES],label_visibility="collapsed",format_func=etiqueta_opcion_estado,key='casos_estado_filtro')
    filtered = [c for c in cases if (state == "Todos los estados" or c["estado"] == state) and search.casefold() in f"{c['cliente']} {c['servicio']} {code(c)}".casefold()]
    if not filtered:
        st.info("No hay casos que mostrar. Crea una solicitud o ajusta los filtros.")
        return
    frame = case_table(filtered)
    leyenda_estados()
    tabla_registros(frame)
    if repo.is_owner:
        st.download_button("Exportar listado CSV",csv_bytes(frame),file_name="casos-mente-y-futuro.csv",mime="text/csv")
    st.divider()
    options = {c["id"]:c for c in filtered}
    if st.session_state.get("selected_case") not in options:
        st.session_state.selected_case = next(iter(options))
    selected = st.selectbox("Abrir detalle",list(options),format_func=lambda x:f"{code(options[x])} · {options[x]['cliente']}",key="selected_case")
    case = options[selected]
    st.subheader(f"{code(case)} · {case['servicio']}")
    st.markdown(badge_estado(case["estado"]),unsafe_allow_html=True)
    st.write("")
    quotes = _lectura(repo,f"cotizaciones:{case['id']}",lambda:repo.quotes(case["id"]))
    if repo.is_owner:
        cotizar=st.session_state.pop('abrir_cotizacion',None)==case['id']
        if st.session_state.pop('abrir_datos_caso',False):cotizar=False
        venta=st.session_state.pop('abrir_venta',None)==case['id']
        detail_tab, quote_tab, sale_tab = st.tabs(["Datos y seguimiento","Cotizaciones","Venta"],default='Venta' if venta else 'Cotizaciones' if cotizar else None)
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
    asistido=False
    try:repo.quote_settings();asistido=True
    except Exception:pass
    with st.form(f"edit_tariff_{selected}_{tariff.get('version',0)}"):
        titulo_seccion(1, "Configura el servicio")
        name = st.text_input("Nombre del plan",value=tariff.get("nombre",""),max_chars=180)
        a,b = st.columns(2)
        with a:
            service = st.selectbox("Servicio asociado",SERVICES,index=SERVICES.index(tariff.get("servicio",SERVICES[0])))
            tema=None
            if asistido:
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
                if asistido:datos['tematica']=tema
                repo.save_tariff(datos,tariff or None)
                flash("Tarifa guardada.")
            except Exception as error:
                show_error(error)


def cases_page(repo):
    require_admin(repo)
    encabezado_pagina("Casos y cotizaciones", "Cada solicitud, su propuesta y el siguiente paso.", "SEGUIMIENTO", "▤")
    configurar=st.session_state.pop('abrir_configuracion',False)
    cases_tab, tariffs_tab, config_tab = st.tabs(["Registro de casos", "Tarifas y servicios","Configuración"],default='Configuración' if configurar else None)
    with cases_tab:
        cases_content(repo)
    with tariffs_tab:
        tariffs_content(repo)
    with config_tab:
        from paginas.cotizador import configuracion_cotizador
        configuracion_cotizador(repo)
    from paginas.acciones_cotizacion import mostrar_dialogo
    mostrar_dialogo(repo)


# Compatibilidad para importaciones anteriores.
from paginas.dashboard import dashboard_page


if __name__ == "__main__":
    from utils.permisos import proteger_pagina
    cases_page(proteger_pagina('Casos y cotizaciones',admin=True))
