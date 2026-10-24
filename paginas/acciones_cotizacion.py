"""Descargas, correo confirmado y decisiones sobre una versión emitida."""
from datetime import date,datetime
from time import time
from uuid import uuid4
from pathlib import Path
import json
import streamlit as st
from streamlit.components.v2 import component

from mente_futuro.domain import code,money,today,PAYMENTS
from mente_futuro.ui import flash,show_error
from servicios.cotizacion_asistida import configuracion,mensaje_cliente,SECCIONES
from servicios.documentos_cotizacion import generar_word,generar_pdf
from servicios.envio_cotizacion import enviar_correo,enlace_whatsapp
from utils.permisos import require_admin
from utils.estilos import CSS_COPIAR


def _cerrar_dialogo():
    st.session_state.pop('cot_dialogo',None)


def _abrir_dialogo(tipo,q):
    st.session_state.cot_dialogo=dict(tipo=tipo,id=q['id'],caso_id=q['caso_id'])
    if tipo=='aceptar':st.session_state.pop('aceptar_'+q['id']+'_op',None)
    if tipo=='rechazar':st.session_state.pop('rechazo_op_'+q['id'],None)


@st.cache_data(show_spinner=False,max_entries=24)
def _archivos(usuario,cotizacion_json):
    q=json.loads(cotizacion_json)
    return generar_word(q),generar_pdf(q)


def archivos(repo,q):
    require_admin(repo)
    return _archivos(repo.user.id,json.dumps(q,sort_keys=True,default=str))


def descargas(repo,q,prefijo='hist'):
    require_admin(repo)
    try:
        word,pdf=archivos(repo,q)
        a,b=st.columns(2)
        a.download_button('Descargar Word',word,file_name=code(q,'COT')+'.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',key=prefijo+'_word_'+q['id'])
        b.download_button('Descargar PDF',pdf,file_name=code(q,'COT')+'.pdf',mime='application/pdf',key=prefijo+'_pdf_'+q['id'])
    except Exception:
        st.warning('No pudimos preparar los documentos. La versión sigue guardada; puedes reintentar la descarga.')
    st.button('Enviar al cliente',key=prefijo+'_send_'+q['id'],on_click=_abrir_dialogo,args=('envio',q))


@st.dialog('Enviar cotización al cliente',width='large',on_dismiss=_cerrar_dialogo)
def dialogo_envio(repo,q):
    require_admin(repo)
    asunto,texto=mensaje_cliente(q)
    correo,whatsapp=st.tabs(['Correo','WhatsApp'])
    llave='correo_'+q['id']
    operation=st.session_state.setdefault(llave+'_op',str(uuid4()))
    with correo:
        st.caption('Revisa el destinatario, el mensaje y los adjuntos. No se envía al abrir esta ventana.')
        destinatario=st.text_input('Para',value=q['snapshot'].get('email',''),key=llave+'_to')
        titulo=st.text_input('Asunto',value=asunto,key=llave+'_subject')
        cuerpo=st.text_area('Mensaje de correo',value=texto,height=220,key=llave+'_body')
        word_elegido=st.checkbox('Adjuntar Word',value=True,key=llave+'_word')
        pdf_elegido=st.checkbox('Adjuntar PDF',value=True,key=llave+'_pdf')
        confirmar=st.checkbox('Confirmo enviar este correo al destinatario indicado',key=llave+'_confirm')
        if st.button('Enviar',type='primary',disabled=not confirmar,key=llave+'_send'):
            try:
                settings=dict(st.secrets.get('smtp',{}))
                word,pdf=archivos(repo,q);adjuntos=[]
                if word_elegido:adjuntos.append((code(q,'COT')+'.docx',word,'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
                if pdf_elegido:adjuntos.append((code(q,'COT')+'.pdf',pdf,'application/pdf'))
                resultado=enviar_correo(repo,q,operation,destinatario,titulo,cuerpo,adjuntos,settings,confirmar)
                if resultado=='enviado':
                    st.session_state[llave+'_enviado']=True
                    st.success('Correo aceptado por el servidor y registrado en el caso. Esto no garantiza su entrega al buzón.')
                else:
                    st.session_state[llave+'_sin_registro']=True
                    st.warning('El servidor aceptó el correo, pero no pudimos registrar la fecha. No vuelvas a enviarlo: reintenta solo el registro.')
            except ValueError as error:st.error(str(error))
            except Exception:st.error('No pudimos preparar el correo. Comprueba la configuración y la conexión; no se confirmó el envío.')
        if st.session_state.get(llave+'_sin_registro') and st.button('Reintentar solo registro del correo',key=llave+'_register'):
            try:repo.confirm_quote_send(operation,'enviado');st.success('Envío registrado.');st.session_state.pop(llave+'_sin_registro',None)
            except Exception:st.warning('El registro sigue pendiente; no se reenvió el correo.')
        def nuevo_intento():
            st.session_state[llave+'_op']=str(uuid4());st.session_state[llave+'_confirm']=False
        if st.button('Preparar otro intento de correo',key=llave+'_new',on_click=nuevo_intento):
            st.info('Nuevo intento preparado. Revisa primero si el correo anterior salió para evitar duplicados.')
    with whatsapp:
        mensaje=st.text_area('Mensaje de WhatsApp',value=texto,height=220,key=llave+'_wa_body')
        copiar=component('mfy_copiar_mensaje',html='<button type="button" aria-label="Copiar mensaje de WhatsApp">Copiar mensaje de WhatsApp</button>',js="""
        export default function({parentElement,data,setStateValue}) {
          const button=parentElement.querySelector('button');
          const copy=async()=>{try{await navigator.clipboard.writeText(data.text);setStateValue('copiado',true);}catch{setStateValue('fallo',true);}};
          button.addEventListener('click',copy);return()=>button.removeEventListener('click',copy);
        }
        """,css=CSS_COPIAR)
        estado=copiar(data={'text':mensaje},default={'copiado':False,'fallo':False},on_copiado_change=lambda:None,on_fallo_change=lambda:None,key=llave+'_copy',height=50)
        if estado.copiado:st.caption('Mensaje copiado. Adjunta el documento descargado en WhatsApp.')
        if estado.fallo:st.caption('Puedes seleccionar y copiar el texto del cuadro anterior.')
        enlace=enlace_whatsapp(q['snapshot'].get('telefono',''),mensaje)
        if enlace:st.link_button('Abrir WhatsApp',enlace)
        else:st.caption('Completa un teléfono con código de país para habilitar WhatsApp.')
        st.caption('Abrir WhatsApp no envía el mensaje ni adjunta archivos automáticamente.')
        confirmado=st.checkbox('Ya envié esta cotización por WhatsApp',key=llave+'_wa_confirm')
        if st.button('Registrar envío por WhatsApp',disabled=not confirmado,key=llave+'_wa_register'):
            try:
                op=st.session_state.setdefault(llave+'_wa_op',str(uuid4()))
                repo.prepare_quote_send(q['id'],op,'WhatsApp',q['snapshot'].get('telefono',''))
                repo.confirm_quote_send(op,'enviado');st.success('Envío por WhatsApp registrado en el caso.')
            except Exception:st.warning('No pudimos registrar la fecha. Puedes reintentar; no se enviará ningún mensaje desde la app.')


def _decidir(repo,caso,q,datos,op):
    resultado=repo.decide_quote(caso,q,datos,op)
    evento=resultado['evento']
    if datos['accion']=='vender':
        from utils.componentes import preparar_celebracion
        preparar_celebracion('venta:'+str(evento['id']),'¡Venta registrada! Un nuevo paso para tu negocio.')
    _cerrar_dialogo()
    st.session_state.pop('cotizacion_lista',None)
    if datos['accion'] in ('aceptar','vender'):
        st.session_state.deshacer_decision=dict(id=evento['id'],caso_id=caso['id'],
            vence=datetime.fromisoformat(evento['created_at'].replace('Z','+00:00')).timestamp()+10)
    st.session_state.abrir_cotizacion=caso['id']
    flash('Aceptación y venta registradas. El caso está En seguimiento.' if datos['accion']=='vender' else 'Decisión registrada.')


@st.dialog('Aceptar cotización y registrar venta',width='large',on_dismiss=_cerrar_dialogo)
def dialogo_aceptar(repo,caso,q):
    require_admin(repo)
    config=configuracion(repo.quote_settings()['datos'])
    llave='aceptar_'+q['id'];op=st.session_state.setdefault(llave+'_op',str(uuid4()))
    monto=st.number_input('Monto de la venta (CLP)',min_value=0,max_value=100000000000,value=int(q['total_clp']),step=1000,key=llave+'_monto')
    fecha=st.date_input('Fecha de la venta',value=today(),format='DD/MM/YYYY',key=llave+'_fecha')
    a,b=st.columns(2)
    reserva=a.number_input('Reserva (%)',0.0,100.0,float(config['reserva_pct']),step=.5,key=llave+'_reserva')
    remuneracion=b.number_input('Remuneración (%)',0.0,100.0,float(config['remuneracion_pct']),step=.5,key=llave+'_remuneracion')
    pago=st.selectbox('Estado del pago',PAYMENTS,key=llave+'_pago')
    documento=st.text_input('N° de documento (opcional)',max_chars=100,key=llave+'_documento')
    if round(reserva+remuneracion,2)!=100:st.error('Reserva y remuneración deben sumar 100%.')
    st.caption('Aceptar y registrar venta crea una sola venta y deja el caso En seguimiento. Deshacer estará disponible durante 10 segundos.')
    if st.button('Aceptar y registrar venta',type='primary',key=llave+'_vender'):
        if round(reserva+remuneracion,2)!=100:return
        try:_decidir(repo,caso,q,dict(accion='vender',monto_clp=monto,fecha=fecha.isoformat(),reserva_pct=reserva,
            remuneracion_pct=remuneracion,estado_pago=pago,documento_numero=documento),op)
        except Exception:st.error('No pudimos registrar la venta. Revisa vigencia, reparto y conexión; no se confirmó el cambio.')
    if st.button('Solo marcar aceptada',key=llave+'_solo'):
        try:_decidir(repo,caso,q,dict(accion='aceptar'),op)
        except Exception:st.error('No pudimos registrar la aceptación. El caso puede haber cambiado o la cotización estar vencida.')


@st.dialog('Marcar cotización como rechazada',on_dismiss=_cerrar_dialogo)
def dialogo_rechazar(repo,caso,q):
    require_admin(repo)
    motivo=st.selectbox('Motivo (opcional)',['','Precio','Fecha','Eligió otra empresa','Otro'])
    nota=st.text_area('Detalle opcional',max_chars=500)
    if st.button('Confirmar rechazo',type='primary'):
        op=st.session_state.setdefault('rechazo_op_'+q['id'],str(uuid4()))
        try:_decidir(repo,caso,q,dict(accion='rechazar',motivo=motivo,nota=nota),op)
        except Exception:st.error('No pudimos registrar el rechazo. Conservamos el caso sin confirmar cambios.')


def acciones(repo,caso,q):
    require_admin(repo)
    if not hasattr(repo,'decide_quote'):return
    if caso['estado'] in ('Finalizado','Cancelado','En ejecución'):return
    if any(s['caso_id']==caso['id'] for s in repo.sales()):return
    a,b=st.columns(2)
    a.button('Marcar como aceptada',key='accept_'+q['id'],on_click=_abrir_dialogo,args=('aceptar',q))
    b.button('Marcar como rechazada',key='reject_'+q['id'],on_click=_abrir_dialogo,args=('rechazar',q))


def mostrar_dialogo(repo):
    require_admin(repo)
    activo=st.session_state.get('cot_dialogo')
    if not activo:return
    caso=repo.get_case(activo['caso_id'])
    q=next((q for q in repo.quotes(caso['id']) if q['id']==activo['id']),None)
    if not q:_cerrar_dialogo();return
    if activo['tipo']=='envio':dialogo_envio(repo,q)
    elif activo['tipo']=='aceptar':dialogo_aceptar(repo,caso,q)
    elif activo['tipo']=='rechazar':dialogo_rechazar(repo,caso,q)


def _undo(repo):
    accion=st.session_state.get('deshacer_decision')
    if not accion:return
    try:
        row=repo.undo_quote_decision(accion['id'])
        st.session_state.get('borradores_casos',{}).pop(accion['caso_id'],None)
        st.session_state.pop('deshacer_decision',None)
        for key in list(st.session_state):
            if key.startswith('aceptar_') and key.endswith('_op'):st.session_state.pop(key,None)
        st.session_state.notice='Se deshizo la aceptación. La cotización se conserva.'
        st.session_state.cot_undo_refrescar=True
    except Exception:st.session_state.notice='No se pudo deshacer: terminó el plazo, cambió el caso o falló la conexión.'


@st.fragment(run_every='1s')
def aviso_deshacer(repo):
    if st.session_state.pop('cot_undo_refrescar',False):st.rerun(scope='app')
    accion=st.session_state.get('deshacer_decision')
    if accion and time()<accion['vence']:
        with st.container(key='mfy_quote_ready'):
            st.write('Aceptación registrada')
            st.button('Deshacer',key='undo_quote_decision',on_click=_undo,args=(repo,))


def historial_eventos(repo,caso):
    require_admin(repo)
    try:eventos=repo.quote_events(caso['id'])
    except Exception:return
    if eventos:
        with st.expander('Historial del caso y envíos'):
            for e in eventos:
                fecha=datetime.fromisoformat(e['created_at'].replace('Z','+00:00'))
                from zoneinfo import ZoneInfo
                fecha=fecha.astimezone(ZoneInfo('America/Santiago'))
                if e['tipo']=='envio':texto=f"Cotización enviada el {fecha:%d/%m/%Y} por {e['datos'].get('canal')}"
                elif e['tipo']=='seguimiento':
                    nombre={'seguimiento':'Seguimiento realizado','pago':'Recordatorio de pago realizado','agradecimiento':'Agradecimiento realizado'}.get(e['datos'].get('tipo_mensaje'),'Contacto realizado')
                    texto=f'{nombre} el {fecha:%d/%m/%Y}'
                else:texto=f"{e['tipo'].capitalize()} · {fecha:%d/%m/%Y %H:%M}"
                st.write(texto+(' · Deshecho' if e.get('deshecho_en') else ''))


def guardar_plantilla(repo,caso,q):
    documento=q.get('documento') or {}
    if not documento.get('textos'):return
    existentes=repo.program_templates()
    if any(p.get('textos')==documento['textos'] for p in existentes):return
    if st.button('Guardar como plantilla',key='save_template_'+q['id']):
        try:
            existentes=repo.program_templates()
            if not any(p['servicio']==caso['servicio'] and p.get('tematica')==caso['tematica'] and p.get('textos')==documento['textos'] for p in existentes):
                repo.save_program_template(dict(nombre=f"{caso['servicio']} · {caso['tematica']}",servicio=caso['servicio'],tematica=caso['tematica'],textos=documento['textos']))
            st.success('Plantilla disponible para futuras propuestas. La versión emitida no cambió.')
        except Exception:st.warning('No pudimos guardar la plantilla. Tus descargas siguen disponibles.')
