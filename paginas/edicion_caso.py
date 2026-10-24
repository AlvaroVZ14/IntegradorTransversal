"""Detalle editable: mismos campos, con borrador y guardado independiente por campo."""
from datetime import date
from time import time

import streamlit as st

from mente_futuro.domain import SERVICES, TOPICS, STATES, MODALITIES
from servicios.autoguardado import preparar, editar, guardar, deshacer
from utils.componentes import titulo_seccion
from utils.estados import etiqueta_opcion_estado
from utils.permisos import require_admin
from utils.borrador_local import recuperar_borrador


def _almacen():
    return st.session_state.setdefault("borradores_casos",{})


def _key(caso_id,campo):
    return f"mfy_edit_{caso_id}_{campo}"


def _cambio(repo,caso_id,campo):
    borrador=_almacen()[caso_id]
    editar(borrador,campo,st.session_state[_key(caso_id,campo)])
    with st.spinner("Guardando…"):
        guardar(repo,borrador,campos=[campo])


def _deshacer(repo,caso_id):
    borrador=_almacen()[caso_id]
    try:
        actualizado=deshacer(repo,borrador)
        st.session_state[_key(caso_id,"estado")]=actualizado["estado"]
        st.session_state.autoguardado_refrescar=True
    except ValueError as error:
        st.session_state.autoguardado_aviso=str(error)
    except Exception:
        st.session_state.autoguardado_aviso="No pudimos deshacer por ahora. Puedes reintentar mientras siga disponible."


def _deshacer_venta(repo,caso_id):
    accion=st.session_state.get("deshacer_venta")
    if not accion or accion["caso_id"]!=caso_id or time()>=accion["vence"]:
        st.session_state.autoguardado_aviso="El plazo para deshacer terminó."
        return
    try:
        actualizado=repo.undo_acceptance(accion["id"],accion["version"])
        _almacen()[caso_id]["ultimo"]=actualizado
        st.session_state[_key(caso_id,"estado")]=actualizado["estado"]
        st.session_state.pop("deshacer_venta",None)
        st.session_state.autoguardado_refrescar=True
    except Exception:
        st.session_state.autoguardado_aviso="No pudimos deshacer. Revisa la conexión; el caso puede haber cambiado o terminado el plazo."


@st.fragment(run_every="1s")
def _indicador(repo,caso_id):
    borrador=_almacen()[caso_id]
    if guardar(repo,borrador):
        st.rerun(scope="app")
    if st.session_state.pop("autoguardado_refrescar",False):
        st.rerun(scope="app")
    if "autoguardado_aviso" in st.session_state:
        st.warning(st.session_state.pop("autoguardado_aviso"))
    if borrador["pendientes"]:
        if borrador.get("fallo"):
            st.warning("Conservamos lo que escribiste en esta sesión. Reintentaremos al recuperar la conexión; no cierres esta pestaña.")
        else:
            st.caption("Hay cambios pendientes de validar o confirmar; los demás campos se guardan normalmente.")
    elif borrador["guardado"]:
        st.caption(f"Guardado ✓ {borrador['guardado']}")
    else:
        st.caption("Autoguardado activo · Los cambios se guardan al terminar de editar cada campo.")
    accion=borrador.get("deshacer")
    if accion and time()<accion["vence"]:
        with st.container(key="mfy_undo"):
            st.markdown('<div role="status">Estado actualizado</div>',unsafe_allow_html=True)
            st.caption(f"Puedes deshacer durante {max(1,int(accion['vence']-time()))} s.")
            st.button("Deshacer",key=f"undo_{caso_id}",on_click=_deshacer,args=(repo,caso_id),width="stretch")
    elif accion:
        borrador["deshacer"]=None
    venta=st.session_state.get("deshacer_venta")
    if not borrador.get("deshacer") and venta and venta["caso_id"]==caso_id and time()<venta["vence"]:
        with st.container(key="mfy_undo"):
            st.markdown('<div role="status">Aceptación registrada</div>',unsafe_allow_html=True)
            st.caption(f"Puedes deshacer durante {max(1,int(venta['vence']-time()))} s.")
            st.button("Deshacer",key=f"undo_venta_{caso_id}",on_click=_deshacer_venta,args=(repo,caso_id),width="stretch")


def editar_caso(repo,caso):
    require_admin(repo)
    borrador=preparar(_almacen(),caso)
    caso_id=caso["id"]
    recuperar_borrador(repo,caso_id,borrador)

    def campo(nombre,label,tipo,**opciones):
        llave=_key(caso_id,nombre)
        valor=borrador["pendientes"].get(nombre,{}).get("valor",borrador["ultimo"].get(nombre))
        if nombre in ('rut','cargo'):valor=valor or ''
        if nombre in ("fecha_preferida","fecha_realizacion"):
            valor=date.fromisoformat(valor) if isinstance(valor,str) and valor else valor
        if nombre=="horas" and valor is not None: valor=float(valor)
        if nombre=="participantes" and valor is not None: valor=int(valor)
        # El borrador manual sobrevive a la limpieza de widgets al cambiar de página.
        if llave not in st.session_state or nombre not in borrador["pendientes"]:
            st.session_state[llave]=valor
        getattr(st,tipo)(label,key=llave,on_change=_cambio,args=(repo,caso_id,nombre),**opciones)
        if nombre in borrador["errores"]:
            st.error(borrador["errores"][nombre])
        if nombre in borrador["conflictos"]:
            st.warning(borrador["conflictos"][nombre])
            if st.button("Guardar mi cambio",key=f"conflicto_{caso_id}_{nombre}"):
                try:
                    actual=repo.get_case(caso_id)
                    borrador["pendientes"][nombre]["base"]=actual.get(nombre)
                    borrador["conflictos"].pop(nombre,None)
                    guardar(repo,borrador,campos=[nombre])
                    st.rerun()
                except Exception:
                    st.warning("No pudimos conectar. Tu cambio sigue conservado.")

    with st.container(key="mfy_form_edit_case"):
        titulo_seccion(1,"Datos y seguimiento")
        a,b=st.columns(2)
        with a:
            campo("cliente","Cliente","text_input",max_chars=180)
            campo("rut","RUT (opcional)","text_input",max_chars=16)
            campo("contacto","Contacto","text_input",max_chars=160)
            campo("cargo","Cargo (opcional)","text_input",max_chars=160)
            campo("email","Correo","text_input",max_chars=254)
            campo("telefono","Teléfono","text_input",max_chars=40)
            campo("servicio","Servicio","selectbox",options=SERVICES)
            campo("tematica","Temática","selectbox",options=TOPICS)
            if 'tematicas' in caso:campo('tematicas','Temáticas','multiselect',options=TOPICS)
        with b:
            estados=[s for s in STATES if s!="Vendido" or borrador["ultimo"]["estado"]=="Vendido"]
            campo("estado","Estado del caso","selectbox",options=estados,format_func=etiqueta_opcion_estado)
            campo("participantes","Participantes","number_input",min_value=1,max_value=10000)
            campo("horas","Horas totales","number_input",min_value=.5,max_value=1000.0,step=.5)
            campo("modalidad","Modalidad","selectbox",options=MODALITIES)
            campo("lugar","Lugar","text_input",max_chars=250)
            campo("fecha_preferida","Fecha preferida","date_input",format="DD/MM/YYYY")
            # Dato opcional nuevo: nunca se deriva de la fecha solicitada.
            if 'fecha_realizacion' in caso:
                campo('fecha_realizacion','Jornada realizada el (opcional)','date_input',format='DD/MM/YYYY',
                      help='Confirma esta fecha solo después de realizar la jornada. Permite ofrecer el cierre cuando el pago esté completo.')
        campo("detalle","Objetivos y detalle compartido con el cliente","text_area",max_chars=5000)
        if 'dirigido_a' in caso:campo('dirigido_a','Dirigido a (opcional)','text_input',max_chars=1000)
        if 'referido_por' in caso:campo('referido_por','Referido por','text_input',max_chars=160)
        from servicios.solicitud_rapida import ORIGENES
        origen=borrador['ultimo'].get('origen')
        campo('origen','Origen de la solicitud','selectbox',options=ORIGENES+([origen] if origen and origen not in ORIGENES else []))
        try:
            perfiles=repo.profiles()
            st.session_state.perfiles_edicion=perfiles
        except Exception:
            perfiles=st.session_state.get("perfiles_edicion",[])
        perfiles={p["id"]:f"{p['nombre']} · {p['email']}" for p in perfiles if p["rol"]=="cliente"}
        # Una vinculación existente no desaparece si falla la consulta de perfiles.
        vinculado=borrador["pendientes"].get("cliente_id",{}).get("valor",caso.get("cliente_id"))
        if vinculado and vinculado not in perfiles:
            perfiles[vinculado]="Cuenta vinculada actual"
        campo("cliente_id","Cuenta de cliente con acceso al caso","selectbox",options=[None,*perfiles],
              format_func=lambda x:perfiles.get(x,"Sin cuenta vinculada"))
        st.caption("La cuenta vinculada identifica al solicitante. Las ventas se registran en la pestaña Venta.")
        if borrador["pendientes"].get("estado",{}).get("valor")=="Cancelado":
            confirmar=st.checkbox("Confirmo anular el caso",key=f"confirmar_anular_{caso_id}")
            if st.button("Anular caso",key=f"anular_{caso_id}",disabled=not confirmar):
                guardar(repo,borrador,campos=["estado"],confirmar_anulacion=True)
                st.rerun()
        if st.button("Guardar todo",key=f"guardar_todo_{caso_id}",help="Opcional: reintenta los cambios válidos pendientes."):
            guardar(repo,borrador,campos=list(borrador["pendientes"]))
            st.rerun()
        _indicador(repo,caso_id)
