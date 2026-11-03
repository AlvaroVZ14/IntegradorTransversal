"""Documentos privados del caso: administración. El acceso cliente se prepara por RLS."""
from hashlib import sha256
from uuid import UUID,uuid4,uuid5
import streamlit as st
from servicios.archivos_caso import TIPOS,TIPOS_TODOS
from servicios.documentos_caso import DocumentosCaso
from servicios.aviso_documento import avisar_documento
from utils.permisos import require_admin


def _mensaje_error(error):
    if getattr(error,'code','') in ('42P01','PGRST205','PGRST202'):
        st.info('Para activar Documentos, aplica 202611020002_documentos_caso.sql en Supabase. Las demás pestañas siguen disponibles.')
    elif isinstance(error,ValueError):st.warning(str(error))
    else:st.warning('No pudimos completar esta operación. El documento no se ha confirmado; puedes reintentar.')


def _visibilidad(documentos,doc):
    llave='doc_visible_'+doc['id'];valor=st.session_state[llave]
    try:
        documentos.visibilidad(doc['id'],valor)
        st.session_state.pop('doc_enlace_'+doc['id'],None)
    except Exception:
        # Una respuesta perdida no demuestra que el servidor rechazó el cambio.
        # La siguiente lectura repone el interruptor con el valor real.
        st.session_state.pop(llave,None)
        st.session_state['doc_aviso']='No pudimos confirmar la respuesta al cambio. Revisa la visibilidad que muestra el documento.'


def _disponibilidad(destinatario):
    st.success('El cliente ya puede verlo en su cuenta' if destinatario.get('tiene_cuenta') else
               'El cliente lo verá cuando cree su cuenta con ese correo')
    st.caption('Los documentos visibles aparecen en «Mis documentos» al ingresar con el correo confirmado del caso.')


def documentos_caso(repo,caso,cotizaciones):
    require_admin(repo);documentos=DocumentosCaso(repo)
    st.subheader('Documentos del caso')
    st.caption('PDF, Word (.docx), Excel (.xlsx) e imágenes PNG, JPG o WebP. Hasta 10 MB por archivo. Los nombres se reemplazan por identificadores sin datos personales.')
    try:
        filas=documentos.listar(caso['id'])
        registrados={d.get('cotizacion_id'):d for d in filas if d.get('cotizacion_id')}
        for q in cotizaciones:
            if q['id'] not in registrados or registrados[q['id']]['estado_archivo']=='pendiente':
                try:documentos.sincronizar_cotizacion(caso,q)
                except Exception:
                    st.info('Una cotización aún no se pudo incorporar a Documentos. Su descarga sigue disponible en Cotizaciones.');break
        filas=documentos.listar(caso['id'])
    except Exception as error:_mensaje_error(error);return
    if aviso:=st.session_state.pop('doc_aviso',None):st.warning(aviso)
    cid=caso['id'];token=st.session_state.setdefault('doc_carga_'+cid,str(uuid4()))
    with st.form('doc_subida_'+token):
        tipo=st.selectbox('Tipo de documento',TIPOS)
        nota=st.text_area('Nota del documento (opcional)',max_chars=2000)
        archivos=st.file_uploader('Selecciona uno o varios archivos',type=['pdf','docx','xlsx','png','jpg','jpeg','webp'],accept_multiple_files=True,max_upload_size=10)
        # None aplica en servidor el valor por defecto del tipo elegido.
        visibilidad=st.selectbox('Visibilidad al subir',['Según el tipo','Visible para el cliente','Solo Administración'])
        st.caption('Según el tipo: asistencia, informes, certificados y material son visibles; cotizaciones y otros son privados.')
        avisar=st.toggle('Avisar al cliente por correo',value=True)
        st.caption('Al subir documentos visibles se enviará un aviso breve, sin adjuntos. El correo no contiene datos del caso.')
        subir=st.form_submit_button('Subir documentos',type='primary')
    if subir:
        if not archivos:st.info('Selecciona al menos un archivo.');return
        completados=True;destinatario=None
        for i,archivo in enumerate(archivos):
            try:
                contenido=archivo.getvalue()
                op=uuid5(UUID(token),f'{i}:{tipo}:{nota}:{visibilidad}:{sha256(contenido).hexdigest()}')
                visible=None if visibilidad=='Según el tipo' else visibilidad=='Visible para el cliente'
                d=documentos.subir(cid,tipo,archivo.name,contenido,nota,visible,op)
                st.success('Documento guardado: '+d['nombre'])
                if d['visible_cliente']:
                    try:
                        destinatario=destinatario or documentos.destinatario(cid)
                        _disponibilidad(destinatario)
                        if avisar:
                            settings=dict(st.secrets.get('smtp',{}))
                            resultado=avisar_documento(documentos,d,settings,destinatario.get('correo',''))
                            if resultado not in ('enviado','ya_reservado'):
                                st.warning('El archivo quedó guardado. No pudimos confirmar el aviso por correo; no lo reenviamos automáticamente.')
                    except Exception:st.warning('El archivo quedó guardado. No pudimos preparar el aviso por correo.')
            except Exception as error:completados=False;_mensaje_error(error)
        if completados:st.session_state['doc_carga_'+cid]=str(uuid4())
        filas=documentos.listar(cid)
    activos=[d for d in filas if d['estado_archivo']!='eliminado']
    if not activos:st.info('Este caso aún no tiene documentos. Puedes subir el primero.');return
    origen=st.selectbox('Origen de los documentos',['Todos','Enviados por la socia','Enviados por el cliente'],key='doc_origen_'+cid)
    if origen!='Todos':
        activos=[d for d in activos if d.get('origen','socia')==('cliente' if origen=='Enviados por el cliente' else 'socia')]
    if not activos:st.info('No hay documentos de este origen.')
    from datetime import datetime
    from zoneinfo import ZoneInfo
    for d in activos:
        with st.container(border=True):
            if d.get('origen')=='cliente':st.caption('📎 Enviado por el cliente')
            st.write(d['tipo']+' · '+d['nombre'])
            if d.get('origen')=='cliente':
                with st.form('doc_tipo_'+d['id']):
                    tipo_editado=st.selectbox('Tipo de documento',TIPOS_TODOS,index=TIPOS_TODOS.index(d['tipo']))
                    if st.form_submit_button('Cambiar tipo'):
                        try:documentos.cambiar_tipo(d['id'],tipo_editado);st.rerun()
                        except Exception as error:_mensaje_error(error)
            fecha=datetime.fromisoformat(d['fecha_subida'].replace('Z','+00:00')).astimezone(ZoneInfo('America/Santiago'))
            st.caption(f"{fecha:%d/%m/%Y %H:%M} · {d['tamano']/1024:.1f} KB".replace('.',','))
            if d.get('nota'):st.text(d['nota'])
            if d.get('aviso_estado') in ('reservado','fallido','incierto'):
                st.caption('Aviso por correo sin confirmar. No se reenvió automáticamente.')
            if d['estado_archivo']=='pendiente':st.info('La subida está pendiente de confirmación. Puedes reintentar el mismo archivo.')
            llave='doc_visible_'+d['id']
            if llave not in st.session_state:st.session_state[llave]=d['visible_cliente']
            st.toggle('Visible para el cliente',key=llave,on_change=_visibilidad,args=(documentos,d),disabled=d['estado_archivo']!='disponible')
            if d.get('origen')=='cliente':
                st.caption('Quien lo envió conserva acceso a su archivo. La visibilidad permite compartirlo también con los demás contactos autorizados del caso.')
            if d['estado_archivo']=='disponible':
                if st.button('Preparar descarga',key='doc_sign_'+d['id']):
                    try:st.session_state['doc_enlace_'+d['id']]={'url':documentos.enlace(d['id']),'fecha':__import__('time').time()}
                    except Exception as error:_mensaje_error(error)
                enlace=st.session_state.get('doc_enlace_'+d['id'])
                if enlace and __import__('time').time()-enlace['fecha']<540:
                    st.link_button('Descargar documento',enlace['url'])
                    st.caption('Enlace privado temporal: válido durante 10 minutos desde su creación.')
            confirmar=st.checkbox('Confirmo eliminar este documento',key='doc_confirm_'+d['id'])
            if st.button('Eliminar documento' if d['estado_archivo']!='eliminando' else 'Completar eliminación',key='doc_delete_'+d['id'],disabled=not confirmar):
                try:
                    documentos.eliminar(d['id']);st.session_state.pop('doc_enlace_'+d['id'],None)
                    st.success('Documento eliminado.');st.rerun()
                except Exception:st.warning('No pudimos confirmar la eliminación. Revisa la visibilidad y reintenta cuando vuelva la conexión.')
