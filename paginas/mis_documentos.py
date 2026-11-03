"""Única vista de documentos para clientes; no usa consultas de gestión."""
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from mente_futuro.domain import code
from servicios.mis_documentos import MisDocumentos
from utils.componentes import encabezado_pagina
from utils.permisos import proteger_pagina
from servicios.archivos_caso import TIPOS_CLIENTE
from servicios.aviso_documento import avisar_socia
from hashlib import sha256
from uuid import UUID, uuid4, uuid5

VACIO = 'Cuando la socia comunitaria suba los documentos de tu servicio, los verás aquí.'


def _error_documento(error):
    if isinstance(error, ValueError):
        return str(error)
    texto = str(error)
    if '20 archivos en una hora' in texto:
        return 'Alcanzaste 20 archivos en una hora. Intenta más tarde.'
    if 'máximo de 20 archivos' in texto:
        return 'Este caso alcanzó el máximo de 20 archivos. Contacta a la socia comunitaria.'
    return 'No pudimos completar esta operación. Revisa la conexión y vuelve a intentarlo; conservamos tu selección mientras esta página siga abierta.'


def _descarga(documentos, doc):
    st.caption(doc['nombre'] + ' · ' + fecha_chile(doc['fecha_subida']) +
               (f" · {doc['tamano']/1024:.1f} KB".replace('.', ',') if doc.get('tamano') else ''))
    if doc.get('estado_archivo', 'disponible') == 'disponible':
        st.download_button('Descargar', data=lambda id=doc['id']: documentos.descargar(id),
                           file_name=doc['nombre'], mime=doc['tipo_mime'],
                           key='descargar_cliente_' + doc['id'], width='stretch', on_click='ignore')
    else:
        st.caption('Documento pendiente. Puedes reintentar la subida o completar su eliminación.')


def _enviar_documentos(documentos, caso):
    cid = caso['id']
    mensaje = st.session_state.pop('documentos_cliente_resultado_' + cid, None)
    if mensaje:
        st.success(mensaje)
    if not caso.get('puede_enviar', False):
        return
    st.markdown('#### Enviar documentos')
    st.caption('No subas claves ni datos bancarios')
    st.caption('PDF, Word (.docx), Excel (.xlsx), PNG, JPG o WebP. Máximo 10 MB por archivo y 20 archivos por caso; hasta 20 subidas por hora por cuenta.')
    token = st.session_state.setdefault('documentos_cliente_lote_' + cid, str(uuid4()))
    with st.form('enviar_documentos_' + token):
        tipo = st.selectbox('Tipo de documento', TIPOS_CLIENTE, key='tipo_' + token)
        archivos = st.file_uploader('Selecciona uno o varios archivos',
            type=['pdf', 'docx', 'xlsx', 'png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True, max_upload_size=10, key='archivos_' + token)
        nota = st.text_area('Nota del documento (opcional)', max_chars=2000, key='nota_' + token)
        enviar = st.form_submit_button('Enviar documentos', type='primary', width='stretch')
    if not enviar:
        return
    if not archivos:
        st.info('Selecciona al menos un archivo.')
        return
    if len(archivos) > 20:
        st.warning('Selecciona hasta 20 archivos por caso.')
        return
    completos = True
    for i, archivo in enumerate(archivos):
        try:
            contenido = archivo.getvalue()
            identificador = uuid5(UUID(token), f'{i}:{tipo}:{nota}:{sha256(contenido).hexdigest()}')
            doc = documentos.subir(cid, tipo, archivo.name, contenido, nota, identificador)
            # El archivo ya está disponible. Un fallo SMTP nunca revierte la subida.
            avisar_socia(documentos, doc['id'], dict(st.secrets.get('smtp', {})))
        except Exception as error:
            completos = False
            st.warning(_error_documento(error))
    if completos:
        st.session_state['documentos_cliente_lote_' + cid] = str(uuid4())
        st.session_state['documentos_cliente_resultado_' + cid] = 'Recibimos tu documento. La socia comunitaria lo verá en tu caso.'
        st.rerun()


def fecha_chile(valor):
    fecha = datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
    if fecha.tzinfo:
        fecha = fecha.astimezone(ZoneInfo('America/Santiago'))
    return fecha.strftime('%d/%m/%Y')


def mis_documentos(repo):
    documentos = MisDocumentos(repo)  # También valida rol al entrar directamente.
    encabezado_pagina('Mis documentos', 'Los documentos de tus servicios, en un solo lugar.',
                      'MENTE Y FUTURO · CLIENTES', ':material/description:')
    from paginas.mi_perfil import mi_perfil
    mi_perfil(repo)
    try:
        casos = documentos.listar()
    except Exception:
        st.warning('No pudimos cargar tus documentos. Revisa la conexión y vuelve a intentarlo.')
        return
    empresas = list(dict.fromkeys(c['cliente'] for c in casos if c.get('cliente')))
    st.write('Te damos la bienvenida' + (', ' + ' · '.join(empresas) if empresas else '') + '.')
    if not casos:
        st.info(VACIO)
        return
    for caso in casos:
        with st.container(border=True):
            st.subheader(f"{code(caso)} · {caso.get('servicio') or 'Servicio por definir'}")
            st.caption(fecha_chile(caso['created_at']))
            recibidos = [d for d in caso['documentos'] if not d.get('es_mio')]
            enviados = [d for d in caso['documentos'] if d.get('es_mio')]
            if not recibidos:
                st.info(VACIO)
            for doc in recibidos:
                st.write(doc['tipo'])
                _descarga(documentos, doc)
            _enviar_documentos(documentos, caso)
            if enviados:
                st.markdown('#### Documentos que enviaste')
            for doc in enviados:
                with st.container(border=True):
                    st.write(doc['tipo'])
                    _descarga(documentos, doc)
                    if caso.get('puede_enviar', False):
                        confirmar = st.checkbox('Confirmo eliminar este documento', key='cliente_confirmar_' + doc['id'])
                        if st.button('Eliminar documento', key='cliente_eliminar_' + doc['id'], disabled=not confirmar):
                            try:
                                documentos.eliminar(doc['id'])
                                st.session_state['documentos_cliente_resultado_' + caso['id']] = 'Documento eliminado.'
                                st.rerun()
                            except Exception as error:
                                st.warning(_error_documento(error))


if __name__ == '__main__':
    mis_documentos(proteger_pagina('Mis documentos'))
