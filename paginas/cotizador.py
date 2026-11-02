"""Editor administrativo prellenado, borrador persistente y generación explícita."""
from copy import deepcopy
from datetime import date,timedelta
from time import time
from uuid import uuid4
import streamlit as st

from mente_futuro.domain import money,quote_total,today
from mente_futuro.ui import flash,show_error
from servicios.cotizacion_asistida import (SECCIONES,prellenar,textos_plantilla,recomendar_tarifa,faltantes,datos_emision)
from servicios.documentos_cotizacion import generar_word,generar_pdf
from utils.permisos import require_admin
from utils.componentes import titulo_seccion
from utils.cotizacion_borrador import capturar,valores_texto
from servicios.propuesta_documento import ampliar_borrador
from servicios.cotizacion_defaults import VIGENCIA_DIAS_DEFAULT,CONDICIONES_DEFAULT,CONDICION_IVA_AFECTA_DEFAULT
from servicios.pago_cotizacion import CAMPOS_PAGO,LIMITES_PAGO,leer_pago_secrets,pago_para_documento,normalizar_pago


def _guardar(repo,caso_id,draft):
    if not draft['pendiente'] or time()<draft.get('reintento',0):return False
    try:
        row=repo.save_quote_draft(caso_id,draft['datos'],draft['version'])
        if not row:raise ConnectionError()
        draft.update(version=row['version'],pendiente=False,error=None,reintento=0,guardado=True)
        draft['confirmado']=valores_texto(draft['datos'])
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
    if campo=='exento':
        campo='iva_pct';valor=0 if valor else 19
        condiciones=draft['datos'].get('condiciones','').splitlines()
        originales=(CONDICIONES_DEFAULT.splitlines()[0],CONDICION_IVA_AFECTA_DEFAULT)
        if condiciones and condiciones[0] in originales:
            condiciones[0]=originales[0] if valor==0 else originales[1]
            draft['datos']['condiciones']='\n'.join(condiciones)
            st.session_state.pop(f'cotedit_{caso_id}_condiciones',None)
    destino=draft['datos'].setdefault(grupo,{}) if grupo else draft['datos']
    if destino.get(campo)==valor:return
    destino[campo]=valor
    if campo=='valida_hasta':draft['datos']['vigencia_automatica']=False
    if campo=='fecha_emision' and draft['datos'].get('vigencia_automatica'):
        draft['datos']['valida_hasta']=(date.fromisoformat(valor)+timedelta(days=VIGENCIA_DIAS_DEFAULT)).isoformat()
        st.session_state.pop(f'cotedit_{caso_id}_valida_hasta',None)
    draft['pendiente']=True;draft['reintento']=0
    _guardar(repo,caso_id,draft)


def _restablecer(repo,caso_id,campo,texto,lista=None,valores=None):
    draft=st.session_state.cotizadores[caso_id]
    draft['datos']['textos'][campo]=texto
    st.session_state[f'cotedit_{caso_id}_{campo}']=texto
    draft.setdefault('reset_local',{})[campo]=str(uuid4())
    if lista:
        draft['datos'][lista]=deepcopy(valores or [])
        ampliar_borrador(draft['datos'],{})
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
    tarifas=repo.tariffs();plantillas=repo.program_templates()
    inicial=prellenar(caso,tarifas,plantillas)
    ampliar_borrador(inicial,caso,next((p for p in plantillas if p['id']==inicial.get('plantilla_id')),None))
    drafts=st.session_state.setdefault('cotizadores',{})
    if caso['id'] not in drafts:
        row=repo.quote_draft(caso['id'])
        datos={**inicial,**deepcopy(row['datos'])} if row else inicial
        if row and 'vigencia_automatica' not in row['datos']:datos['vigencia_automatica']=False
        drafts[caso['id']]=dict(datos=datos,version=row['version'] if row else 0,pendiente=not bool(row),
            guardado=bool(row),error=None,operacion=str(uuid4()))
    draft=drafts[caso['id']];d=draft['datos']
    for nombre,valor in inicial.items():
        if nombre not in d:d[nombre]=deepcopy(valor);draft.update(pendiente=True,reintento=0)
    ampliar_borrador(d,caso)
    if 'pago' not in d:
        d['pago']=leer_pago_secrets();draft.update(pendiente=True,reintento=0)
    elif not isinstance(d['pago'],dict):
        d['pago']=normalizar_pago(d['pago']);draft.update(pendiente=True,reintento=0)
    if 'incluir_pago' not in d:
        d['incluir_pago']=True;draft.update(pendiente=True,reintento=0)
    vigencia=(date.fromisoformat(d['fecha_emision'])+timedelta(days=VIGENCIA_DIAS_DEFAULT)).isoformat()
    if d.get('vigencia_automatica') and d['valida_hasta']!=vigencia:
        d['valida_hasta']=vigencia
        st.session_state.pop(f"cotedit_{caso['id']}_valida_hasta",None)
        draft.update(pendiente=True,reintento=0)
    if date.fromisoformat(d['valida_hasta'])<date.fromisoformat(d['fecha_emision']):
        d['valida_hasta']=vigencia
        st.session_state.pop(f"cotedit_{caso['id']}_valida_hasta",None)
        draft.update(pendiente=True,reintento=0)
        st.info('Renovamos la vigencia de este borrador desde hoy. Puedes ajustarla en Condiciones.')
    capturar(repo,caso['id'],draft)
    _guardar(repo,caso['id'],draft)
    def campo(nombre,label,tipo='text_input',grupo=None,**kwargs):
        sufijo='mostrar_'+nombre if grupo=='mostrar' else nombre
        key=f"cotedit_{caso['id']}_{sufijo}"
        valor=(d.get(grupo,{}) if grupo else d).get(nombre)
        if nombre=='iva_pct':valor='IVA 19%' if valor==19 else 'Exento de IVA'
        if nombre in ('valida_hasta','fecha_emision') and isinstance(valor,str):valor=date.fromisoformat(valor)
        if key not in st.session_state:st.session_state[key]=valor
        st.markdown(f'<span id="cot-{nombre}"></span>',unsafe_allow_html=True)
        return getattr(st,tipo)(label,key=key,on_change=_editar,args=(repo,caso['id'],nombre,grupo),**kwargs)
    falta=faltantes(caso,d)
    if falta:
        st.warning('Para generar, completa: '+', '.join(label for label,_ in falta)+'. Tu borrador se conserva.')
        for label,dest in falta:
            tab='Importes' if dest=='importes' else 'Condiciones' if dest=='condiciones' else 'Programa'
            st.markdown(f'<a href="#cot-{dest}">Ir a {label}</a>',unsafe_allow_html=True)
            if st.button('Abrir '+label,key='missing_'+caso['id']+label):
                st.session_state['cot_tabs_'+caso['id']]=tab;st.rerun()
    else:st.info('Prellenado automáticamente. Revisa y genera.')
    campo('fecha_emision','Fecha de emisión','date_input',format='DD/MM/YYYY')
    _estado_borrador(repo,caso['id'])
    recomendada=recomendar_tarifa(caso,tarifas)
    opciones={t['id']:t for t in tarifas if t.get('activa',True) and t['servicio']==caso['servicio']}
    if d.get('tarifa_id') and d['tarifa_id'] not in opciones:
        opciones[d['tarifa_id']]=next((t for t in tarifas if t['id']==d['tarifa_id']),{'nombre':'Referencia anterior','monto_clp':d['base_clp']})
    def cambiar_tarifa():
        _editar(repo,caso['id'],'tarifa_id')
        t=opciones.get(d['tarifa_id'])
        if t:
            d.update(base_clp=int(t['monto_clp']),detalle=t.get('detalle') or d['detalle'],item_descripcion=t.get('detalle') or d['servicio'])
            draft.setdefault('reset_local',{})['detalle']=str(uuid4())
            for f in ('base_clp','detalle','iva_pct','item_descripcion'):st.session_state.pop(f"cotedit_{caso['id']}_{f}",None)
            draft.update(pendiente=True,reintento=0);_guardar(repo,caso['id'],draft)
    llave=f"cotedit_{caso['id']}_tarifa_id"
    if llave not in st.session_state:st.session_state[llave]=d['tarifa_id']
    st.selectbox('Tarifa de referencia',[None,*opciones],key=llave,on_change=cambiar_tarifa,
        format_func=lambda x:('Recomendada · ' if recomendada and x==recomendada['id'] else '')+f"{opciones[x]['nombre']} · {money(opciones[x]['monto_clp'])}" if x else 'Cotización personalizada')
    t=opciones.get(d.get('tarifa_id'))
    if t:
        st.caption(f"Referencia: {t.get('participantes','—')} participantes · {t.get('horas','—')} horas. {t.get('fuente','')}")
        if t.get('participantes')!=caso.get('participantes') or float(t.get('horas',0))!=float(caso.get('horas') or 0):
            st.warning('La cantidad de participantes o las horas difieren de esta referencia. Ajusta el monto y el alcance antes de emitir.')
    plantilla_opciones={p['id']:p for p in plantillas if p.get('activa',True)}
    if d.get('plantilla_id') not in plantilla_opciones:d['plantilla_id']=None
    seleccion=st.selectbox('Plantilla de programa',[None,*plantilla_opciones],index=[None,*plantilla_opciones].index(d.get('plantilla_id')),
        format_func=lambda x:plantilla_opciones[x]['nombre'] if x else 'Texto personalizado',key='plantilla_select_'+caso['id'])
    if seleccion!=d.get('plantilla_id'):
        st.caption('La selección conserva tu edición actual hasta pulsar Cargar textos.')
        if st.button('Cargar textos de esta plantilla',key='load_tpl_'+caso['id']):
            d['plantilla_id']=seleccion;d['textos']=textos_plantilla(caso,t,plantilla_opciones.get(seleccion))
            plantilla_textos=(plantilla_opciones.get(seleccion) or {}).get('textos') or {}
            for lista in ('objetivos_especificos','momentos'):d[lista]=deepcopy(plantilla_textos.get(lista) or [])
            ampliar_borrador(d,caso)
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
            campo('cliente','Cliente *',max_chars=180)
            campo('servicio','Servicio de la propuesta *',max_chars=180)
            a,b,c=st.columns(3)
            with a:campo('modalidad','Modalidad de la propuesta','selectbox',options=['Presencial','Online','Híbrida','Por definir'])
            with b:campo('participantes','Participantes de la propuesta','number_input',min_value=1,max_value=10000)
            with c:campo('horas','Horas de la propuesta','number_input',min_value=.5,max_value=1000.0,step=.5)
            campo('detalle_modalidad','Detalle de la modalidad *','text_area',max_chars=1000,height=100,
                  help='Por ejemplo: presencial, dos jornadas de cuatro horas en las oficinas del cliente.')
            campo('detalle','Detalle incluido en la propuesta (opcional)','text_area',max_chars=5000,height=130,
                  help='Opcional. Si queda vacío, el documento usa el servicio y el detalle de la modalidad.')
            for k,label in SECCIONES.items():
                if k=='incluye':continue
                campo(k,'Incluir '+label.lower(),'toggle',grupo='mostrar')
                # El interruptor afecta al documento, nunca borra ni oculta la edición.
                etiqueta={'objetivos':'Objetivo general','metodologia':'Frase introductoria de metodología','descripcion':'Descripción del servicio'}.get(k,label)
                campo(k,etiqueta,'text_area',grupo='textos',max_chars=5000,height=100)
                st.button('Restablecer al texto de la plantilla',key='reset_'+caso['id']+k,
                    on_click=_restablecer,args=(repo,caso['id'],k,origen[k],
                        'objetivos_especificos' if k=='objetivos' else 'momentos' if k=='metodologia' else None,
                        ((plantilla_opciones.get(d.get('plantilla_id')) or {}).get('textos') or {}).get('objetivos_especificos' if k=='objetivos' else 'momentos',[])))
                if k in ('objetivos','metodologia'):
                    from paginas.listas_propuesta import editar_lista
                    st.caption('Objetivos específicos' if k=='objetivos' else 'Momentos metodológicos')
                    editar_lista(repo,caso['id'],draft,'objetivos_especificos' if k=='objetivos' else 'momentos',_guardar)
            campo('jornadas_duracion','Jornadas y duración',max_chars=1000)
        with importes:
            st.markdown('<span id="cot-importes"></span>',unsafe_allow_html=True)
            a,b,c=st.columns(3)
            with a:campo('base_clp','Valor base (CLP)','number_input',min_value=0,max_value=100000000000,step=1000)
            with b:campo('descuento_pct','Descuento (%)','number_input',min_value=0.0,max_value=100.0,step=.5)
            with c:
                key='cotedit_'+caso['id']+'_exento'
                if key not in st.session_state:st.session_state[key]=d['iva_pct']==0
                st.toggle('Exento de IVA',key=key,on_change=_editar,args=(repo,caso['id'],'exento'))
            campo('item_descripcion','Descripción del ítem 1','text_area',max_chars=5000,height=100)
            campo('descuento_motivo','Motivo del descuento',max_chars=500)
            campo('descuento_periodo','Período del descuento (opcional)',max_chars=500)
            campo('incluye','Incluir qué incluye','toggle',grupo='mostrar')
            campo('incluye','Qué incluye','text_area',grupo='textos',max_chars=5000,height=150)
            st.button('Restablecer al texto de la plantilla',key='reset_'+caso['id']+'incluye',
                      on_click=_restablecer,args=(repo,caso['id'],'incluye',origen['incluye']))
            st.metric('Total de la propuesta (CLP)',money(quote_total(d['base_clp'],d['descuento_pct'],d['iva_pct'])))
            st.caption('Los descuentos son manuales. La versión conservará estos valores al generar.')
        with condiciones:
            campo('valida_hasta','Válida hasta','date_input',min_value=date.fromisoformat(d['fecha_emision']),format='DD/MM/YYYY')
            campo('mostrar_condiciones','Incluir condiciones generales','toggle')
            campo('condiciones','Condiciones comerciales','text_area',max_chars=5000,height=150)
            campo('nombre_archivo','Nombre del archivo (sin extensión)',max_chars=180,
                  help='Puedes conservar {folio} y {cliente}; se reemplazan al descargar.')
            st.caption('Una condición por línea. Estos valores se editan solo para esta cotización.')
            st.subheader('Datos para el pago')
            campo('incluir_pago','Incluir datos de pago','toggle')
            for nombre,etiqueta in CAMPOS_PAGO.items():
                campo(nombre,etiqueta,grupo='pago',max_chars=LIMITES_PAGO[nombre])
            st.caption('Se guardan solo en esta cotización y se incluyen al final del documento.')
            if d['incluir_pago'] and not pago_para_documento(d):
                st.info('Los datos de pago están incompletos. Puedes completar estos campos o generar la cotización sin esta sección.')
        antiguo=st.button('Emitir y guardar cotización',key='emit_legacy_'+caso['id'])
    with st.container(key='mfy_generate'):
        generar=st.button('Generar cotización',type='primary',key='generate_'+caso['id'],width='stretch')
    prueba=dict(datos_emision(d),snapshot=caso,numero=0,fecha_emision=d['fecha_emision'],total_clp=quote_total(d['base_clp'],d['descuento_pct'],d['iva_pct']))
    with st.expander('Vista previa del documento',expanded=False):
        st.caption('Borrador: el folio definitivo se asigna al generar la cotización.')
        try:st.pdf(generar_pdf(prueba),height=700,key='preview_'+caso['id'],alt='Vista previa de la cotización')
        except Exception:st.info('La vista previa no está disponible en este momento. Puedes conservar el borrador y reintentar.')
    if generar or antiguo:
        if falta:
            st.error('Completa los datos indicados antes de generar. Tu borrador se conserva.');return
        try:
            # Comprueba ambos generadores antes de crear la versión definitiva.
            prueba.update(numero=1)
            generar_word(prueba);generar_pdf(prueba)
            q=repo.issue_quote(caso,datos_emision(d),draft['operacion'])
            # Algunos repositorios históricos no devolvían fila; recupera por operación.
            if not q:q=next(q for q in repo.quotes(caso['id']) if q.get('operacion_id')==draft['operacion'])
            if hasattr(repo.client,'storage'):
                try:
                    from servicios.documentos_caso import DocumentosCaso
                    DocumentosCaso(repo).sincronizar_cotizacion(caso,q)
                except Exception:
                    # La cotización ya fue emitida: no repetir emisión ni bloquear descarga.
                    st.session_state['doc_aviso']='La cotización se guardó. Su copia en Documentos se completará al abrir esa pestaña.'
            draft['operacion']=str(uuid4());st.session_state.cotizacion_lista=q['id']
            st.session_state.abrir_cotizacion=caso['id']
            flash('Se recuperó la versión ya emitida. Tus cambios posteriores siguen en el borrador; genera otra versión para incluirlos.' if q.get('documento')!=datos_emision(d)['documento'] else 'Cotización generada. Descarga Word o PDF y revisa antes de enviar.')
        except Exception as error:
            if getattr(error,'code','')=='PGRST202':
                st.error('Falta activar la actualización de documentos en Supabase. Aplica 202611020001_fecha_propuesta.sql. Tu borrador sigue guardado y no se creó una versión.')
            else:show_error(error)
