"""Editor administrativo prellenado, borrador persistente y generación explícita."""
from copy import deepcopy
from datetime import date,datetime
from time import time
from uuid import uuid4
import streamlit as st

from mente_futuro.domain import MODALITIES,code,money,quote_total,today
from mente_futuro.ui import flash,show_error
from servicios.cotizacion_asistida import (SECCIONES,EMISOR,configuracion,prellenar,textos_plantilla,
    recomendar_tarifa,faltantes,datos_emision,cargar_configuracion,actualizar_emisor)
from servicios.documentos_cotizacion import generar_word,generar_pdf
from utils.permisos import require_admin
from utils.componentes import titulo_seccion
from utils.cotizacion_borrador import capturar,TEXTOS


def _guardar(repo,caso_id,draft):
    if not draft['pendiente'] or time()<draft.get('reintento',0):return False
    try:
        row=repo.save_quote_draft(caso_id,draft['datos'],draft['version'])
        if not row:raise ConnectionError()
        draft.update(version=row['version'],pendiente=False,error=None,reintento=0,guardado=True)
        draft['confirmado']={f:draft['datos']['textos'].get(f,'') if f in SECCIONES else draft['datos'].get(f,'') for f in TEXTOS}
        return True
    except Exception as error:
        draft['error']='conflicto' if getattr(error,'code','')=='40001' else 'conexion'
        draft['reintento']=time()+5
        return False


def _editar(repo,caso_id,campo,grupo=None):
    draft=st.session_state.cotizadores[caso_id]
    sufijo='mostrar_'+campo if grupo=='mostrar' else campo
    valor=st.session_state[f'cotedit_{caso_id}_{sufijo}']
    if campo=='iva_pct':valor=19 if valor=='IVA 19%' else 0
    if isinstance(valor,date):valor=valor.isoformat()
    destino=draft['datos'].setdefault(grupo,{}) if grupo else draft['datos']
    if destino.get(campo)==valor:return
    destino[campo]=valor
    draft['pendiente']=True;draft['reintento']=0
    _guardar(repo,caso_id,draft)


def _restablecer(repo,caso_id,campo,texto):
    draft=st.session_state.cotizadores[caso_id]
    draft['datos']['textos'][campo]=texto
    st.session_state[f'cotedit_{caso_id}_{campo}']=texto
    draft.setdefault('reset_local',{})[campo]=str(uuid4())
    draft['pendiente']=True;draft['reintento']=0
    _guardar(repo,caso_id,draft)


@st.fragment(run_every='2s')
def _estado_borrador(repo,caso_id):
    draft=st.session_state.cotizadores[caso_id]
    if draft.get('error')!='conflicto':_guardar(repo,caso_id,draft)
    if draft.get('error'):
        st.warning('El borrador cambió en otra sesión. Conservamos tu edición; revisa antes de reemplazarlo.' if draft['error']=='conflicto' else 'Tu borrador sigue en esta sesión. Reintentaremos guardarlo cuando vuelva la conexión.')
        if draft['error']=='conflicto' and st.button('Guardar mi borrador sobre el actual',key='force_draft_'+caso_id):
            row=repo.quote_draft(caso_id);draft['version']=row['version'] if row else 0
            draft.update(reintento=0,error=None);_guardar(repo,caso_id,draft);st.rerun()
    elif draft['pendiente']:st.caption('Guardando borrador…')
    elif draft.get('guardado'):st.caption('Borrador guardado ✓ · No crea una versión de cotización.')


def editor_cotizacion(repo,caso):
    require_admin(repo)
    if caso['estado'] in ('Vendido','En ejecución','Finalizado','Cancelado'):
        st.info('Este caso está cerrado para nuevas cotizaciones. Puedes consultar las propuestas emitidas.')
        return
    config,config_guardada=cargar_configuracion(repo)
    tarifas=repo.tariffs();plantillas=repo.program_templates()
    drafts=st.session_state.setdefault('cotizadores',{})
    if caso['id'] not in drafts:
        row=repo.quote_draft(caso['id'])
        inicial=prellenar(caso,tarifas,plantillas,config)
        datos={**inicial,**deepcopy(row['datos'])} if row else inicial
        drafts[caso['id']]=dict(datos=datos,version=row['version'] if row else 0,pendiente=not bool(row),
            guardado=bool(row),error=None,operacion=str(uuid4()))
    draft=drafts[caso['id']];d=draft['datos']
    if actualizar_emisor(d,config):
        draft.update(pendiente=True,reintento=0)
    capturar(repo,caso['id'],draft)
    _guardar(repo,caso['id'],draft)
    def campo(nombre,label,tipo='text_input',grupo=None,**kwargs):
        sufijo='mostrar_'+nombre if grupo=='mostrar' else nombre
        key=f"cotedit_{caso['id']}_{sufijo}"
        valor=(d.get(grupo,{}) if grupo else d).get(nombre)
        if nombre=='iva_pct':valor='IVA 19%' if valor==19 else 'Exento de IVA'
        if nombre=='valida_hasta' and isinstance(valor,str):valor=date.fromisoformat(valor)
        if key not in st.session_state:st.session_state[key]=valor
        st.markdown(f'<span id="cot-{nombre}"></span>',unsafe_allow_html=True)
        return getattr(st,tipo)(label,key=key,on_change=_editar,args=(repo,caso['id'],nombre,grupo),**kwargs)
    falta=faltantes(caso,d)
    falta_config=[label for label,dest in falta if dest=='configuracion']
    falta_propuesta=[(label,dest) for label,dest in falta if dest!='configuracion']
    if falta_config or not config_guardada:
        if falta_config:
            st.warning('Administración: completa en Ajustes (Configuración) los datos de la empresa: '
                       +', '.join(falta_config)+'. El borrador se guarda; estos datos se necesitan para emitir el documento.')
        else:
            st.warning('No pudimos guardar los valores iniciales de Configuración. Tu borrador se conserva; revisa Ajustes o vuelve a intentarlo.')
        if st.button('Ir a Ajustes (Configuración)',key='issuer_'+caso['id']):
            st.session_state.abrir_configuracion=True;st.rerun()
    if falta_propuesta:
        st.warning('Antes de generar falta: '+', '.join(label for label,_ in falta_propuesta)+'.')
        if any(dest=='caso' for _,dest in falta):
            if st.button('Completar datos del caso',key='case_'+caso['id']):
                st.session_state.abrir_datos_caso=True;st.rerun()
        for label,dest in falta:
            if dest not in ('caso','configuracion'):
                tab='Importes' if dest=='importes' else 'Condiciones' if dest=='condiciones' else 'Programa'
                if st.button('Ir a '+label,key='missing_'+caso['id']+label):
                    st.session_state['cot_tabs_'+caso['id']]=tab;st.rerun()
    elif not falta_config and config_guardada:st.info('Prellenado automáticamente. Revisa y genera.')
    _estado_borrador(repo,caso['id'])
    recomendada=recomendar_tarifa(caso,tarifas)
    opciones={t['id']:t for t in tarifas if t.get('activa',True) and t['servicio']==caso['servicio']}
    if d.get('tarifa_id') and d['tarifa_id'] not in opciones:
        opciones[d['tarifa_id']]=next((t for t in tarifas if t['id']==d['tarifa_id']),{'nombre':'Referencia anterior','monto_clp':d['base_clp']})
    def cambiar_tarifa():
        _editar(repo,caso['id'],'tarifa_id')
        t=opciones.get(d['tarifa_id'])
        if t:
            d.update(base_clp=int(t['monto_clp']),detalle=t.get('detalle') or d['detalle'])
            draft.setdefault('reset_local',{})['detalle']=str(uuid4())
            if t.get('tratamiento_iva') in ('Exento','IVA 19%'):d['iva_pct']=19 if t['tratamiento_iva']=='IVA 19%' else 0
            for f in ('base_clp','detalle','iva_pct'):st.session_state.pop(f"cotedit_{caso['id']}_{f}",None)
            draft.update(pendiente=True,reintento=0);_guardar(repo,caso['id'],draft)
    llave=f"cotedit_{caso['id']}_tarifa_id"
    if llave not in st.session_state:st.session_state[llave]=d['tarifa_id']
    st.selectbox('Tarifa de referencia',[None,*opciones],key=llave,on_change=cambiar_tarifa,
        format_func=lambda x:('Recomendada · ' if recomendada and x==recomendada['id'] else '')+f"{opciones[x]['nombre']} · {money(opciones[x]['monto_clp'])}" if x else 'Cotización personalizada')
    t=opciones.get(d.get('tarifa_id'))
    if t:
        st.caption(f"Referencia: {t.get('participantes','—')} participantes · {t.get('horas','—')} horas. {t.get('fuente','')}")
        if t.get('participantes')!=caso['participantes'] or float(t.get('horas',0))!=float(caso['horas']):
            st.warning('La cantidad de participantes o las horas difieren de esta referencia. Ajusta el monto y el alcance antes de emitir.')
    plantilla_opciones={p['id']:p for p in plantillas if p.get('activa',True)}
    if d.get('plantilla_id') not in plantilla_opciones:d['plantilla_id']=None
    seleccion=st.selectbox('Plantilla de programa',[None,*plantilla_opciones],index=[None,*plantilla_opciones].index(d.get('plantilla_id')),
        format_func=lambda x:plantilla_opciones[x]['nombre'] if x else 'Texto personalizado',key='plantilla_select_'+caso['id'])
    if seleccion!=d.get('plantilla_id'):
        st.caption('La selección conserva tu edición actual hasta pulsar Cargar textos.')
        if st.button('Cargar textos de esta plantilla',key='load_tpl_'+caso['id']):
            d['plantilla_id']=seleccion;d['textos']=textos_plantilla(caso,t,plantilla_opciones.get(seleccion))
            for k in SECCIONES:draft.setdefault('reset_local',{})[k]=str(uuid4())
            for k in SECCIONES:st.session_state.pop(f"cotedit_{caso['id']}_{k}",None)
            draft.update(pendiente=True,reintento=0);_guardar(repo,caso['id'],draft);st.rerun()
    origen=textos_plantilla(caso,t,plantilla_opciones.get(d.get('plantilla_id')))
    with st.container(key='mfy_form_quote'):
        titulo_seccion(2,'Tu propuesta a medida')
        # Descartar la pestaña antigua conservada por una sesión abierta.
        if st.session_state.get('cot_tabs_'+caso['id'])=='Vista previa':
            st.session_state['cot_tabs_'+caso['id']]='Programa'
        programa,importes,condiciones=st.tabs(['Programa','Importes','Condiciones'],key='cot_tabs_'+caso['id'],on_change='rerun')
        with programa:
            a,b,c=st.columns(3)
            with a:campo('modalidad','Modalidad de la propuesta','selectbox',options=MODALITIES)
            with b:campo('participantes','Participantes de la propuesta','number_input',min_value=1,max_value=10000)
            with c:campo('horas','Horas de la propuesta','number_input',min_value=.5,max_value=1000.0,step=.5)
            campo('detalle','Detalle incluido en la propuesta *','text_area',max_chars=5000,height=130)
            for k,label in SECCIONES.items():
                campo(k,'Incluir '+label.lower(),'toggle',grupo='mostrar')
                # El interruptor afecta al documento, nunca borra ni oculta la edición.
                campo(k,label,'text_area',grupo='textos',max_chars=5000,height=100)
                st.button('Restablecer al texto de la plantilla',key='reset_'+caso['id']+k,
                    on_click=_restablecer,args=(repo,caso['id'],k,origen[k]))
        with importes:
            a,b,c=st.columns(3)
            with a:campo('base_clp','Valor base (CLP)','number_input',min_value=0,max_value=100000000000,step=1000)
            with b:campo('descuento_pct','Descuento (%)','number_input',min_value=0.0,max_value=100.0,step=.5)
            with c:campo('iva_pct','Tratamiento de IVA *','selectbox',options=['Exento de IVA','IVA 19%'])
            campo('descuento_motivo','Motivo del descuento',max_chars=500)
            st.caption('Los descuentos son manuales. La versión conservará estos valores al generar.')
        with condiciones:
            campo('valida_hasta','Válida hasta','date_input',format='DD/MM/YYYY')
            campo('condiciones','Condiciones comerciales','text_area',max_chars=5000,height=150)
            st.caption('Los datos de la empresa se leen automáticamente desde Configuración. Los totales se calculan al generar la cotización.')
        antiguo=st.button('Emitir y guardar cotización',key='emit_legacy_'+caso['id'])
    with st.container(key='mfy_generate'):
        generar=st.button('Generar cotización',type='primary',key='generate_'+caso['id'],width='stretch')
    if generar or antiguo:
        if falta:
            st.error('Completa los datos indicados antes de generar. Tu borrador se conserva.');return
        try:
            # Comprueba ambos generadores antes de crear la versión definitiva.
            prueba=dict(datos_emision(d),snapshot=caso,numero=1,created_at=today().isoformat(),fecha_emision=today().isoformat(),total_clp=quote_total(d['base_clp'],d['descuento_pct'],d['iva_pct']))
            generar_word(prueba);generar_pdf(prueba)
            q=repo.issue_quote(caso,datos_emision(d),draft['operacion'])
            # Algunos repositorios históricos no devolvían fila; recupera por operación.
            if not q:q=next(q for q in repo.quotes(caso['id']) if q.get('operacion_id')==draft['operacion'])
            draft['operacion']=str(uuid4());st.session_state.cotizacion_lista=q['id']
            st.session_state.abrir_cotizacion=caso['id']
            flash('Se recuperó la versión ya emitida. Tus cambios posteriores siguen en el borrador; genera otra versión para incluirlos.' if q.get('documento')!=d else 'Cotización generada. Descarga Word o PDF y revisa antes de enviar.')
        except Exception as error:show_error(error)


def configuracion_cotizador(repo):
    require_admin(repo)
    try:row=repo.quote_settings()
    except Exception:
        st.info('Activa la migración 202610220003_cotizador_asistido.sql para configurar el emisor, programas y reparto.');return
    config=configuracion(row['datos'])
    completos=sum(bool(str(config['emisor'].get(k,'')).strip()) for k in EMISOR)
    st.subheader(f'Completa los datos de tu empresa {completos}/9')
    st.progress(completos/9)
    faltan=[label for k,label in EMISOR.items() if not config['emisor'].get(k)]
    if faltan:st.info('Falta: '+', '.join(faltan))
    with st.form('config_cotizador_'+str(row['version'])):
        a,b=st.columns(2)
        emisor={}
        for i,(k,label) in enumerate(EMISOR.items()):
            with a if i%2==0 else b:emisor[k]=st.text_input(label,value=config['emisor'].get(k,''),max_chars=500)
        vigencia=st.number_input('Vigencia por defecto (días)',1,365,int(config['vigencia_dias']))
        condiciones=st.text_area('Condiciones generales',value=config['condiciones'],max_chars=5000)
        reserva=st.number_input('Reserva por defecto (%)',0.0,100.0,float(config['reserva_pct']),step=.5)
        remuneracion=st.number_input('Remuneración por defecto (%)',0.0,100.0,float(config['remuneracion_pct']),step=.5)
        iva=st.selectbox('IVA por defecto',[0,19],index=0 if config['iva_default']==0 else 1,format_func=lambda x:'Exento de IVA' if x==0 else 'Neto + IVA 19%')
        st.caption('Revisa el IVA, el reparto y las condiciones iniciales antes de guardar; no representan una regla comercial confirmada.')
        guardar=st.form_submit_button('Guardar configuración',type='primary')
    if guardar:
        if round(reserva+remuneracion,2)!=100:st.error('Reserva y remuneración deben sumar 100%.');return
        try:
            repo.save_quote_settings(dict(row['datos'],emisor=emisor,vigencia_dias=vigencia,condiciones=condiciones,
                reserva_pct=reserva,remuneracion_pct=remuneracion,iva_default=iva),row['version'])
            flash('Configuración guardada. Los borradores leerán el emisor actualizado automáticamente; las versiones emitidas no cambian.')
        except Exception as error:show_error(error)
    from paginas.hoy import configurar_hoy
    configurar_hoy(repo,row)
    from paginas.estado import tarjeta_respaldo
    tarjeta_respaldo(repo)
    from paginas.configuracion_formulario import configuracion_formulario
    configuracion_formulario(repo,row)
