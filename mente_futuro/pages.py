"""Las tres vistas del portal; los permisos también se aplican en Supabase."""
from datetime import date, timedelta
from html import escape
from uuid import uuid4

import altair as alt
import pandas as pd
import streamlit as st

from .domain import MODALITIES, PAYMENTS, SERVICES, STATES, TOPICS, code, csv_bytes, dashboard_data, money, quote_total, today, validate_request
from .presentation import quote_html
from .ui import flash, header, show_error


def request_page(repo):
    header("Nueva solicitud", "El primer paso para dar forma a una nueva experiencia de aprendizaje.", "SOLICITUDES")
    st.markdown('<div class="banner"><b>Cuéntanos qué tienes en mente</b><p>Completa los datos del servicio. Revisaremos tu solicitud para preparar una propuesta a tu medida.</p></div>', unsafe_allow_html=True)
    if "request_id" not in st.session_state:
        st.session_state.request_id = str(uuid4())
    profiles = repo.profiles() if repo.is_owner else []
    with st.form("new_request"):
        st.markdown('<div class="step">01 / DATOS DE CONTACTO</div>', unsafe_allow_html=True)
        left, right = st.columns(2, gap="large")
        with left:
            customer = st.text_input("Nombre o empresa *", max_chars=180, placeholder="¿Para quién es el servicio?")
            email = st.text_input("Correo de contacto *", value="" if repo.is_owner else repo.user.email, max_chars=254, placeholder="nombre@empresa.cl")
        with right:
            contact = st.text_input("Persona de contacto *", max_chars=160, value="" if repo.is_owner else repo.profile.get("nombre", ""))
            phone = st.text_input("Teléfono", max_chars=40, placeholder="+56 9 1234 5678")
        linked_client = None
        if repo.is_owner:
            options = {p["id"]: f"{p['nombre']} · {p['email']}" for p in profiles if p["rol"] == "cliente"}
            linked_client = st.selectbox("Vincular a una cuenta de cliente", [None, *options], format_func=lambda x: options.get(x, "Sin cuenta vinculada"), help="Solo la cuenta elegida podrá consultar este caso. Puedes vincularla más adelante.")
        st.divider()
        st.markdown('<div class="step">02 / LA EXPERIENCIA QUE BUSCAS</div>', unsafe_allow_html=True)
        a,b = st.columns(2, gap="large")
        with a:
            service = st.selectbox("Tipo de servicio *", SERVICES)
            topic = st.selectbox("Temática principal *", TOPICS)
            participants = st.number_input("Participantes *", min_value=1, max_value=10000, value=1)
        with b:
            modality = st.selectbox("Modalidad *", MODALITIES, index=2)
            hours = st.number_input("Horas totales estimadas *", min_value=0.5, max_value=1000.0, value=1.0, step=0.5, help="Suma de horas de atención de todas las sesiones. En dúo separado, suma las horas de ambas personas.")
            preferred = st.date_input("Fecha preferida (opcional)", value=None, min_value=today(), format="DD/MM/YYYY")
        location = st.text_input("Lugar o ciudad", max_chars=250, placeholder="Indica la ciudad si el servicio es presencial")
        detail = st.text_area("¿Qué te gustaría lograr?", max_chars=5000, height=110, placeholder="Cuéntanos tus objetivos, necesidades o información que debamos considerar.")
        st.caption("* Campos obligatorios. El valor final se confirma en la cotización.")
        submitted = st.form_submit_button("Enviar solicitud", type="primary", width="stretch")
    if submitted:
        data = dict(cliente=customer.strip(), contacto=contact.strip(), email=email.strip(), telefono=phone.strip(), servicio=service, tematica=topic, participantes=participants, horas=hours, modalidad=modality, lugar=location.strip(), fecha_preferida=preferred.isoformat() if preferred else None, detalle=detail.strip(), cliente_id=linked_client)
        errors = validate_request(data)
        if errors:
            for error in errors:
                st.error(error)
        else:
            try:
                case = repo.create_request(data, st.session_state.request_id)
                st.session_state.request_id = str(uuid4())
                st.session_state.selected_case = case["id"]
                st.session_state.pending_navigation = "Casos y cotizaciones"
                flash(f"Solicitud {code(case)} guardada. Ya puedes consultar su avance aquí.")
            except Exception as error:
                show_error(error)


def case_table(cases):
    return pd.DataFrame([{
        "Caso":code(c), "Cliente":c["cliente"], "Servicio":c["servicio"], "Temática":c["tematica"],
        "Estado":c["estado"], "Fecha":pd.to_datetime(c["created_at"], utc=True).tz_convert("America/Santiago").date(),
    } for c in cases])


def quote_history(quotes):
    if not quotes:
        st.info("Este caso todavía no tiene cotizaciones emitidas.")
        return
    for q in quotes:
        expired = date.fromisoformat(q["valida_hasta"]) < today()
        label = f"{code(q, 'COT')} · {money(q['total_clp'])} · {'Vencida' if expired else 'Vigente'}"
        with st.expander(label, expanded=q == quotes[0]):
            st.caption(f"Emitida el {q['fecha_emision']} · Válida hasta {q['valida_hasta']}")
            st.text(q["detalle"])
            a,b,c = st.columns(3)
            a.metric("Valor base",money(q["base_clp"]))
            b.metric("Descuento",f"{q['descuento_pct']}%")
            c.metric("Total CLP",money(q["total_clp"]))
            st.caption("Exento de IVA" if q["iva_pct"] == 0 else "Total incluye IVA de 19%")
            st.text(q["condiciones"])
            st.download_button("Descargar cotización", data=quote_html(q), file_name=f"{code(q,'COT')}.html", mime="text/html", key=f"download_{q['id']}")
            st.caption("Abre el archivo descargado para imprimirlo o guardarlo como PDF desde el navegador.")


def edit_case(repo, case):
    with st.form(f"edit_case_{case['id']}_{case['version']}"):
        a,b = st.columns(2)
        with a:
            customer = st.text_input("Cliente", value=case["cliente"], max_chars=180)
            contact = st.text_input("Contacto", value=case["contacto"], max_chars=160)
            email = st.text_input("Correo", value=case["email"], max_chars=254)
            phone = st.text_input("Teléfono", value=case["telefono"], max_chars=40)
            service = st.selectbox("Servicio", SERVICES, index=SERVICES.index(case["servicio"]))
            topic = st.selectbox("Temática", TOPICS, index=TOPICS.index(case["tematica"]))
        with b:
            states = [s for s in STATES if s != "Vendido" or case["estado"] == "Vendido"]
            state = st.selectbox("Estado del caso", states, index=states.index(case["estado"]))
            people = st.number_input("Participantes", 1,10000,case["participantes"])
            hours = st.number_input("Horas totales",0.5,1000.0,float(case["horas"]),step=0.5)
            modality = st.selectbox("Modalidad",MODALITIES,index=MODALITIES.index(case["modalidad"]))
            location = st.text_input("Lugar",value=case["lugar"], max_chars=250)
            preferred = st.date_input("Fecha preferida",value=date.fromisoformat(case["fecha_preferida"]) if case["fecha_preferida"] else None,format="DD/MM/YYYY")
        detail = st.text_area("Objetivos y detalle compartido con el cliente",value=case["detalle"], max_chars=5000)
        profiles = {p["id"]:f"{p['nombre']} · {p['email']}" for p in repo.profiles() if p["rol"] == "cliente"}
        ids = [None, *profiles]
        linked = st.selectbox("Cuenta de cliente con acceso al caso", ids, index=ids.index(case["cliente_id"]) if case["cliente_id"] in ids else 0, format_func=lambda x:profiles.get(x,"Sin cuenta vinculada"))
        st.caption("El cliente vinculado puede consultar este caso y sus cotizaciones. Las ventas se registran en la pestaña Venta.")
        submitted = st.form_submit_button("Guardar cambios",type="primary")
    if submitted:
        changes = dict(cliente=customer.strip(), contacto=contact.strip(), email=email.strip(), telefono=phone.strip(), servicio=service, tematica=topic, participantes=people, horas=hours, modalidad=modality, lugar=location.strip(), fecha_preferida=preferred.isoformat() if preferred else None, detalle=detail.strip(), estado=state, cliente_id=linked)
        errors = validate_request({**changes,"fecha_preferida":None})
        if errors:
            for error in errors:
                st.error(error)
        else:
            try:
                repo.update_case(case, changes)
                flash("Cambios guardados.")
            except Exception as error:
                show_error(error)


def issue_quote(repo, case):
    if case["estado"] in ("Vendido", "En ejecución", "Finalizado", "Cancelado"):
        st.info("Este caso está cerrado para nuevas cotizaciones. Puedes consultar las propuestas emitidas.")
        return
    tariffs = {t["id"]:t for t in repo.tariffs() if t["activa"] and t["servicio"] == case["servicio"]}
    selected = st.selectbox("Tarifa de referencia",[None,*tariffs],format_func=lambda x:f"{tariffs[x]['nombre']} · {money(tariffs[x]['monto_clp'])}" if x else "Cotización personalizada",key=f"tariff_for_{case['id']}")
    tariff = tariffs.get(selected)
    if tariff:
        st.caption(f"Referencia: {tariff['participantes']} participantes · {tariff['horas']} horas. {tariff['fuente']}")
        if tariff["participantes"] != case["participantes"] or float(tariff["horas"]) != float(case["horas"]):
            st.warning("La cantidad de participantes o las horas difieren de esta referencia. Ajusta el monto y el alcance antes de emitir.")
    key = f"quote_{case['id']}_{selected}_{case['version']}"
    operation_key = f"quote_operation_{case['id']}"
    if operation_key not in st.session_state:
        st.session_state[operation_key] = str(uuid4())
    with st.container(border=True):
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
                flash("Cotización guardada. Está disponible en el historial y en el espacio del cliente vinculado.")
            except Exception as error:
                show_error(error)


def sale_form(repo, case, quotes):
    sale = next((s for s in repo.sales() if s["caso_id"] == case["id"]),None)
    if sale:
        st.metric("Venta registrada",money(sale["monto_clp"]))
        st.caption(f"Fecha de venta: {sale['fecha_venta']}. Una venta anulada se excluye del dashboard.")
        with st.form(f"sale_{sale['id']}_{sale['version']}"):
            payment = st.selectbox("Estado del pago",PAYMENTS,index=PAYMENTS.index(sale["estado_pago"]))
            annulled = st.checkbox("Venta anulada",value=sale["anulada"])
            submitted = st.form_submit_button("Guardar estado de la venta",type="primary")
        if submitted:
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
        sale_date = st.date_input("Fecha de aceptación",value=min(today(),date.fromisoformat(quote["valida_hasta"])),min_value=date.fromisoformat(quote["fecha_emision"]),max_value=today(),format="DD/MM/YYYY")
        payment = st.selectbox("Estado del pago",PAYMENTS)
        confirmed = st.checkbox("El cliente aceptó esta cotización")
        submitted = st.form_submit_button("Registrar venta",type="primary")
    if submitted:
        if not confirmed:
            st.error("Confirma la aceptación del cliente para registrar la venta.")
        elif sale_date > date.fromisoformat(quote["valida_hasta"]):
            st.error("La fecha de aceptación debe estar dentro de la vigencia de la cotización.")
        else:
            try:
                repo.record_sale(case,quote,sale_date,payment)
                flash("Venta guardada. El dashboard ya puede incluirla en el período correspondiente.")
            except Exception as error:
                show_error(error)


def cases_content(repo):
    cases = repo.cases()
    a,b,c = st.columns(3)
    a.metric("Casos registrados",len(cases))
    b.metric("Por revisar",sum(x["estado"] in ("Solicitud","En revisión") for x in cases))
    c.metric("En desarrollo",sum(x["estado"] in ("Vendido","En ejecución") for x in cases))
    st.write("")
    a,b = st.columns([2,1])
    search = a.text_input("Buscar un caso",placeholder="Nombre, servicio o número de caso",label_visibility="collapsed")
    state = b.selectbox("Filtrar estado",["Todos los estados",*STATES],label_visibility="collapsed")
    filtered = [c for c in cases if (state == "Todos los estados" or c["estado"] == state) and search.casefold() in f"{c['cliente']} {c['servicio']} {code(c)}".casefold()]
    if not filtered:
        st.info("No hay casos que mostrar. Crea una solicitud o ajusta los filtros.")
        return
    frame = case_table(filtered)
    st.dataframe(frame,hide_index=True,width="stretch",column_config={"Fecha":st.column_config.DateColumn(format="DD/MM/YYYY")})
    if repo.is_owner:
        st.download_button("Exportar listado CSV",csv_bytes(frame),file_name="casos-mente-y-futuro.csv",mime="text/csv")
    st.divider()
    options = {c["id"]:c for c in filtered}
    if st.session_state.get("selected_case") not in options:
        st.session_state.selected_case = next(iter(options))
    selected = st.selectbox("Abrir detalle",list(options),format_func=lambda x:f"{code(options[x])} · {options[x]['cliente']}",key="selected_case")
    case = options[selected]
    st.subheader(f"{code(case)} · {case['servicio']}")
    st.markdown(f'<span class="pill">{escape(case["estado"])}</span>',unsafe_allow_html=True)
    st.write("")
    quotes = repo.quotes(case["id"])
    if repo.is_owner:
        detail_tab, quote_tab, sale_tab = st.tabs(["Datos y seguimiento","Cotizaciones","Venta"])
        with detail_tab:
            edit_case(repo,case)
        with quote_tab:
            st.subheader("Historial de cotizaciones")
            quote_history(quotes)
            st.divider()
            st.subheader("Preparar una cotización")
            issue_quote(repo,case)
        with sale_tab:
            sale_form(repo,case,quotes)
    else:
        a,b = st.columns(2)
        a.write(f"**Temática:** {case['tematica']}")
        a.write(f"**Participantes:** {case['participantes']}")
        b.write(f"**Modalidad:** {case['modalidad']}")
        b.write(f"**Horas estimadas:** {case['horas']}")
        if case["detalle"]:
            st.text(case["detalle"])
        st.subheader("Tus cotizaciones")
        quote_history(quotes)


def tariffs_content(repo):
    repo.owner_only()
    st.subheader("Tarifario de referencia")
    st.caption("Los valores orientan cada propuesta. Editar una tarifa no cambia cotizaciones ya emitidas.")
    tariffs = repo.tariffs()
    if tariffs:
        frame = pd.DataFrame([{"Plan":t["nombre"],"Servicio":t["servicio"],"Valor CLP":money(t["monto_clp"]),"Participantes":t["participantes"],"Horas":t["horas"],"IVA":t["tratamiento_iva"],"Activa":t["activa"]} for t in tariffs])
        st.dataframe(frame,hide_index=True,width="stretch")
    options = {t["id"]:t for t in tariffs}
    selected = st.selectbox("Crear o editar una tarifa",[None,*options],format_func=lambda x:options[x]["nombre"] if x else "+ Nueva tarifa")
    tariff = options.get(selected,{})
    with st.form(f"edit_tariff_{selected}_{tariff.get('version',0)}"):
        name = st.text_input("Nombre del plan",value=tariff.get("nombre",""),max_chars=180)
        a,b = st.columns(2)
        with a:
            service = st.selectbox("Servicio asociado",SERVICES,index=SERVICES.index(tariff.get("servicio",SERVICES[0])))
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
                repo.save_tariff(dict(nombre=name.strip(),servicio=service,monto_clp=amount,participantes=people,horas=hours,tratamiento_iva=tax,detalle=detail.strip(),fuente=source.strip(),activa=active),tariff or None)
                flash("Tarifa guardada.")
            except Exception as error:
                show_error(error)


def cases_page(repo):
    header("Casos y cotizaciones", "Cada solicitud, su propuesta y el siguiente paso." if repo.is_owner else "Consulta el avance de tus solicitudes y descarga tus propuestas.", "SEGUIMIENTO")
    if repo.is_owner:
        cases_tab, tariffs_tab = st.tabs(["Registro de casos", "Tarifas y servicios"])
        with cases_tab:
            cases_content(repo)
        with tariffs_tab:
            tariffs_content(repo)
    else:
        cases_content(repo)


def chart(frame, x, y, color, horizontal=False):
    spec = alt.Chart(frame).mark_bar(cornerRadiusTopLeft=4,cornerRadiusTopRight=4,color=color).encode(
        x=alt.X(x,title=None,axis=alt.Axis(labelAngle=0)),
        y=alt.Y(y,title=None,sort="-x" if horizontal else None),
        tooltip=list(frame.columns),
    ).properties(height=270).configure_view(strokeWidth=0).configure_axis(gridColor="#edf0f7",labelColor="#75829a")
    st.altair_chart(spec,width="stretch")


def dashboard_page(repo):
    repo.owner_only()
    header("Una mirada a tu negocio", "Información para acompañar tus decisiones, período a período.", "DASHBOARD")
    a,b,c = st.columns([1,1,1.4])
    start = a.date_input("Desde",value=today().replace(day=1),format="DD/MM/YYYY")
    end = b.date_input("Hasta",value=today(),format="DD/MM/YYYY")
    service = c.selectbox("Servicio",["Todos",*SERVICES])
    if start > end:
        st.warning("La fecha inicial debe ser anterior o igual a la fecha final.")
        return
    cases, sales = repo.cases(),repo.sales()
    data = dashboard_data(cases,sales,start,end,service)
    st.write("")
    a,b,c,d = st.columns(4)
    a.metric("Ventas del período",money(data["total"]))
    b.metric("Ventas cerradas",data["sales_count"])
    c.metric("Nuevas solicitudes",data["requests_count"])
    d.metric("Ticket promedio",money(data["average"]))
    st.write("")
    if not cases:
        st.info("Tu dashboard está listo. Los indicadores aparecerán a medida que registres solicitudes y ventas.")
    left,right = st.columns([1.55,1],gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Ventas por mes")
            st.caption("Monto total de las ventas confirmadas · CLP")
            chart(data["monthly"],"Mes:O","monto_clp:Q","#7299F2")
    with right:
        with st.container(border=True):
            st.subheader("Temáticas más solicitadas")
            st.caption("Solicitudes creadas en el período")
            if data["topics"].empty:
                st.info("Todavía no hay solicitudes en este período.")
            else:
                chart(data["topics"],"Solicitudes:Q","tematica:N","#AB87ED",True)
    left,right = st.columns([1.55,1],gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Estado de las solicitudes")
            if data["states"].empty:
                st.caption("Sin solicitudes en el período seleccionado.")
            else:
                chart(data["states"],"estado:N","Casos:Q","#EBC84F")
    with right:
        st.metric("Conversión de solicitudes",f"{data['conversion']:.1f}%")
        st.caption("Solicitudes creadas en este período con venta confirmada hasta la fecha final seleccionada.")
        st.metric("Ventas con pago pendiente",money(data["pending_payment"]))
        st.caption("Valor total de ventas no pagadas completamente; incluye abonos. No representa el saldo exacto por cobrar.")
    st.subheader("Solicitudes del período")
    ids = set(data["requests"].id)
    filtered = [c for c in cases if c["id"] in ids]
    if filtered:
        st.dataframe(case_table(filtered),hide_index=True,width="stretch")
    a,b = st.columns(2)
    a.download_button("Exportar ventas por mes",csv_bytes(data["monthly"].rename(columns={"monto_clp":"Ventas CLP"})),"ventas-por-mes.csv","text/csv")
    b.download_button("Exportar ventas del período",csv_bytes(data["sales"].drop(columns=["Mes"],errors="ignore")),"ventas-detalle.csv","text/csv")
    st.caption("Ventas según fecha de aceptación; solicitudes según fecha de creación en Chile. Las ventas anuladas se excluyen. Los montos incluyen los impuestos definidos en cada cotización.")
