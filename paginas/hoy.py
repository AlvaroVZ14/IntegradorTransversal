"""Inicio administrativo: agenda de lectura y acciones siempre explícitas."""
from datetime import datetime
from time import time
from uuid import uuid4
from urllib.parse import urlencode,quote
import streamlit as st

from mente_futuro.domain import code,money
from mente_futuro.ui import flash,show_error
from servicios.hoy import configuracion_hoy,pendientes,saludo,mensaje_listo,CHILE
from servicios.envio_cotizacion import enlace_whatsapp
from utils.permisos import require_admin
from utils.componentes import encabezado_pagina,tarjeta_kpi
from utils.mensaje_listo import copiar_mensaje
from utils.validaciones import validar_campo
from servicios.en_vivo import cargar, carga_inicial, estado
from utils.en_vivo import indicador


def abrir_caso(caso,tab='datos'):
    st.session_state.selected_case=caso['id']
    st.session_state.pending_navigation='Casos y cotizaciones'
    st.session_state.casos_busqueda=''
    st.session_state.casos_estado_filtro='Todos los estados'
    st.session_state.pop('abrir_cotizacion',None);st.session_state.pop('abrir_venta',None)
    if tab=='cotizar':st.session_state.abrir_cotizacion=caso['id']
    elif tab=='venta':st.session_state.abrir_venta=caso['id']
    else:st.session_state.abrir_datos_caso=True


def _abrir_mensaje(tipo,caso,q=None,venta=None):
    st.session_state.hoy_mensaje=dict(tipo=tipo,caso=caso,cotizacion=q,venta=venta)


def _cerrar_mensaje():
    st.session_state.pop('hoy_mensaje',None)


@st.dialog('Mensaje listo para revisar',width='large',on_dismiss=_cerrar_mensaje)
def dialogo_mensaje(repo,contexto,config):
    require_admin(repo)
    caso=contexto['caso'];q=contexto['cotizacion'];tipo=contexto['tipo']
    asunto,texto=mensaje_listo(tipo,caso,q,contexto['venta'],config)
    key=f"hoy_msg_{tipo}_{caso['id']}_{(q or {}).get('id','sin-cotizacion')}"
    titulo=st.text_input('Asunto',value=asunto,key=key+'_asunto',max_chars=250)
    cuerpo=st.text_area('Mensaje',value=texto,key=key+'_cuerpo',height=230,max_chars=5000)
    copiar_mensaje(cuerpo,key+'_copiar')
    a,b=st.columns(2)
    enlace=enlace_whatsapp(caso.get('telefono',''),cuerpo)
    if enlace:a.link_button('Abrir en WhatsApp',enlace,width='stretch')
    else:a.caption('Completa un teléfono con código de país para abrir WhatsApp.')
    if not validar_campo('email',caso.get('email','')):
        b.link_button('Abrir en correo','mailto:'+quote(caso['email'],safe='@')+'?'+urlencode({'subject':titulo,'body':cuerpo}),width='stretch')
    else:b.caption('Completa el correo del contacto para abrir el mensaje.')
    st.caption('Copiar o abrir prepara el mensaje. Después de contactar a la persona, registra que lo realizaste; la app no envía nada desde esta ventana.')
    label={'seguimiento':'Registrar seguimiento realizado','pago':'Registrar recordatorio realizado','agradecimiento':'Registrar agradecimiento realizado'}[tipo]
    if st.button(label,type='primary',key=key+'_registrar'):
        operacion=st.session_state.setdefault(key+'_operacion',str(uuid4()))
        try:
            repo.record_today_contact(caso['id'],(q or {}).get('id'),tipo,operacion)
            st.session_state.pop(key+'_operacion',None);_cerrar_mensaje()
            flash('Seguimiento realizado el '+datetime.now(CHILE).strftime('%d/%m/%Y') if tipo=='seguimiento' else 'Contacto registrado en el historial del caso.')
        except Exception:st.error('No pudimos registrar el contacto. Puedes reintentar; no se enviará ningún mensaje desde la app.')


def _cerrar(repo,item):
    caso=item['caso'];venta=item['venta']
    op=st.session_state.setdefault('hoy_cerrar_op_'+caso['id'],str(uuid4()))
    try:
        resultado=repo.close_case_today(caso,venta,op)
        evento=resultado['evento']
        st.session_state.hoy_cierre=dict(id=evento['id'],caso_id=caso['id'],
            vence=datetime.fromisoformat(evento['created_at'].replace('Z','+00:00')).timestamp()+10)
        st.session_state.hoy_post_cierre={**item,'caso':resultado['caso']}
        flash('Caso cerrado. Puedes deshacer durante 10 segundos.')
    except Exception:
        st.error('No pudimos cerrar el caso. Revisa si cambió el pago, la fecha realizada o el caso; no se confirmó el cierre.')


def _deshacer(repo):
    accion=st.session_state.get('hoy_cierre')
    if not accion:return
    try:
        repo.undo_close_today(accion['id'])
        st.session_state.get('borradores_casos',{}).pop(accion['caso_id'],None)
        st.session_state.pop('hoy_cerrar_op_'+accion['caso_id'],None)
        st.session_state.pop('hoy_cierre',None);st.session_state.pop('hoy_post_cierre',None)
        st.session_state.hoy_cierre_refrescar=True
    except Exception:st.session_state.hoy_aviso='No se pudo deshacer: terminó el plazo, cambió el caso/pago o falló la conexión.'


@st.fragment(run_every='1s')
def aviso_cierre(repo):
    if st.session_state.pop('hoy_cierre_refrescar',False):st.rerun(scope='app')
    if st.session_state.get('hoy_aviso'):st.warning(st.session_state.hoy_aviso)
    accion=st.session_state.get('hoy_cierre')
    if accion and time()<accion['vence']:
        with st.container(key='mfy_quote_ready'):
            st.write('Caso cerrado ✓')
            st.caption(f"Puedes deshacer durante {max(1,int(accion['vence']-time()))} s.")
            st.button('Deshacer',key='hoy_deshacer',on_click=_deshacer,args=(repo,))


def _contenido(repo, pausado=False):
    ahora=datetime.now(CHILE)
    if pausado:
        lectura=estado('hoy')
        if lectura.get('intento',(-1,))[0] != st.session_state.get('dashboard_revision',0):
            lectura=cargar(repo,'hoy')
    else:
        with carga_inicial('hoy', 'Revisando tus pendientes…'):
            lectura=cargar(repo,'hoy')
    indicador('hoy', publicar=True, pausado=pausado)
    if 'datos' not in lectura:
        st.info('Aún no pudimos conectar. Tus pendientes aparecerán cuando vuelva la conexión.')
        return
    datos=lectura['datos']
    casos,cotizaciones,ventas,eventos,envios=[datos[k] for k in ('casos','cotizaciones','ventas','eventos','envios')]
    config=configuracion_hoy(datos['configuracion'])
    tareas=pendientes(casos,cotizaciones,ventas,eventos,envios,config,ahora)
    total=sum(len(v) for v in tareas.values())
    columnas=st.columns(3)
    for columna,(label,valor,icono,tono) in zip(columnas,[('Acciones pendientes',total,'◷','azul'),('Por cotizar',len(tareas['solicitudes']),'✧','morado'),('Pagos por registrar',len(tareas['pagos']),'$','amarillo')]):
        with columna:tarjeta_kpi(label,valor,icon=icono,tone=tono,key='hoy_'+label)
    if not total:st.success('Todo al día. Buen trabajo')
    grupos=[('solicitudes','Solicitudes sin cotizar'),('seguimientos','Cotizaciones sin respuesta'),('datos','Faltan datos'),
            ('pagos','Ventas con pago pendiente o anticipo'),('cierres','Casos que se pueden cerrar'),('correos','Correos por revisar')]
    for clave,titulo in grupos:
        if not tareas[clave]:continue
        st.subheader(f'{titulo} · {len(tareas[clave])}')
        for i,item in enumerate(tareas[clave]):
            caso=item['caso'];q=item.get('cotizacion');venta=item.get('venta')
            with st.container(key=f'mfy_form_hoy_{clave}_{i}'):
                st.markdown('**'+code(caso)+' · '+caso['cliente']+'**')
                st.write(caso['servicio'])
                key='hoy_'+clave+'_'+caso['id']+'_'+str(i)
                if clave=='solicitudes':
                    st.caption(f"{item['dias']} días de espera · Más antiguas primero")
                    st.button('Cotizar',key=key,on_click=abrir_caso,args=(caso,'cotizar'))
                elif clave=='seguimientos':
                    st.caption(f"{code(q,'COT')} · {item['dias']} días desde la emisión")
                    st.button('Hacer seguimiento',key=key,on_click=_abrir_mensaje,args=('seguimiento',caso,q,venta))
                elif clave=='datos':
                    st.caption(' · '.join(item['faltantes']))
                    st.button('Completar',key=key,on_click=abrir_caso,args=(caso,'venta' if item.get('completar_venta') else 'datos'))
                elif clave=='pagos':
                    st.caption(f"{venta['estado_pago']} · {money(venta['monto_clp'])} total de venta")
                    a,b=st.columns(2)
                    a.button('Registrar pago',key=key,on_click=abrir_caso,args=(caso,'venta'))
                    b.button('Preparar recordatorio',key=key+'_recordar',on_click=_abrir_mensaje,args=('pago',caso,q,venta))
                elif clave=='cierres':
                    st.caption('Pagado · Jornada realizada el '+datetime.fromisoformat(caso['fecha_realizacion']).strftime('%d/%m/%Y'))
                    if st.button('Cerrar caso',key=key):_cerrar(repo,item)
                else:
                    envio=item['envio']
                    if q:st.caption(code(q,'COT'))
                    st.caption('Intento de correo '+envio['estado']+' · '+envio['destinatario']+'. No se reenvía automáticamente.')
                    st.button('Revisar envío',key=key,on_click=abrir_caso,args=(caso,'cotizar'))
                    if st.button('Marcar revisado',key=key+'_revisado'):
                        try:
                            op=st.session_state.setdefault(key+'_op',str(uuid4()))
                            repo.record_today_contact(caso['id'],envio['cotizacion_id'],'correo_revisado',op,dict(envio_id=envio['id'],estado=envio['estado']))
                            st.session_state.pop(key+'_op',None)
                            flash('Intento marcado como revisado. No se reenvió el correo.')
                        except Exception:st.warning('No pudimos registrar la revisión. Puedes reintentar.')
    post=st.session_state.get('hoy_post_cierre')
    if post:
        with st.container(key='mfy_form_post_cierre'):
            st.subheader('Cierra el ciclo con tu cliente')
            st.caption(code(post['caso'])+' · '+post['caso']['cliente'])
            if post.get('cotizacion'):
                from paginas.acciones_cotizacion import guardar_plantilla
                guardar_plantilla(repo,post['caso'],post['cotizacion'])
            st.button('Preparar agradecimiento',key='hoy_gracias',on_click=_abrir_mensaje,args=('agradecimiento',post['caso'],post.get('cotizacion'),post.get('venta')))
            if st.button('Cerrar sugerencias',key='hoy_close_suggestions'):st.session_state.pop('hoy_post_cierre',None);st.rerun()


@st.fragment(run_every='30s')
def _actualizar(repo):
    if st.session_state.get('pending_navigation'):st.rerun(scope='app')
    # Un diálogo se abre en una ejecución completa y queda fuera del temporizador.
    if st.session_state.get('hoy_mensaje') or st.session_state.get('hoy_post_cierre'):
        st.rerun(scope='app')
    try:_contenido(repo)
    except Exception as error:
        if getattr(error,'code','') in ('PGRST205','PGRST204','PGRST202','42703','42P01'):
            st.info('Para activar Hoy, aplica 202610220004_hoy.sql después del SQL del cotizador asistido. Las otras páginas siguen disponibles.')
        else:show_error(error,'No pudimos revisar tus pendientes. Puedes volver a intentarlo; no se modificó ningún caso.')


def hoy_page(repo):
    require_admin(repo)
    ahora=datetime.now(CHILE)
    nombre=((repo.profile.get('nombre') or '').split() or ['Administración'])[0]
    encabezado_pagina(f'{saludo(ahora.hour)}, {nombre}',f'{ahora:%d/%m/%Y} · Tus próximos pasos, en un solo lugar.',
                      'HOY','☀',acciones=lambda:indicador('hoy'))
    if st.session_state.get('hoy_mensaje') or st.session_state.get('hoy_post_cierre'):
        # Conserva las tarjetas mientras se edita el mensaje, sin programar lecturas.
        _contenido(repo, pausado=True)
        if st.session_state.get('hoy_mensaje'):
            config=configuracion_hoy(estado('hoy').get('datos',{}).get('configuracion',{}))
            dialogo_mensaje(repo,st.session_state.hoy_mensaje,config)
    else:
        _actualizar(repo)
    aviso_cierre(repo)


def configurar_hoy(repo,row):
    require_admin(repo)
    config=configuracion_hoy(row['datos'])
    st.subheader('Hoy · Avisos y mensajes')
    with st.form('hoy_config_'+str(row['version'])):
        dias=st.number_input('Días sin respuesta para sugerir seguimiento',1,365,config['dias_sin_respuesta'])
        pausa=st.number_input('Días de pausa después de un seguimiento',1,365,config['dias_entre_seguimientos'])
        minutos=st.number_input('Minutos para revisar un correo sin confirmación',1,1440,config['minutos_correo_pendiente'])
        st.caption('Variables: {contacto}, {cliente}, {servicio}, {cotizacion}, {monto}, {fecha_jornada}.')
        seguimiento=st.text_area('Plantilla de seguimiento',value=config['seguimiento'],max_chars=5000)
        pago=st.text_area('Plantilla de recordatorio de pago',value=config['pago'],max_chars=5000)
        gracias=st.text_area('Plantilla de agradecimiento post-jornada',value=config['agradecimiento'],max_chars=5000)
        guardar=st.form_submit_button('Guardar avisos y mensajes',type='primary')
    if guardar:
        if not all(x.strip() for x in (seguimiento,pago,gracias)):st.error('Completa las tres plantillas antes de guardar.');return
        nuevo={**row['datos'],'hoy':dict(dias_sin_respuesta=dias,dias_entre_seguimientos=pausa,
            minutos_correo_pendiente=minutos,seguimiento=seguimiento,pago=pago,agradecimiento=gracias)}
        try:repo.save_quote_settings(nuevo,row['version']);flash('Avisos y mensajes guardados.')
        except Exception:st.warning('No pudimos guardar la configuración. Conservamos lo escrito para que reintentes.')


if __name__=='__main__':
    from utils.permisos import proteger_pagina
    hoy_page(proteger_pagina('Hoy',admin=True))
