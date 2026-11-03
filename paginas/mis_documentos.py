"""Única vista de documentos para clientes; no usa consultas de gestión."""
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from mente_futuro.domain import code
from servicios.mis_documentos import MisDocumentos
from utils.componentes import encabezado_pagina
from utils.permisos import proteger_pagina

VACIO = 'Cuando la socia comunitaria suba los documentos de tu servicio, los verás aquí.'


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
    if not casos or not any(c['documentos'] for c in casos):
        st.info(VACIO)
        return
    for caso in casos:
        with st.container(border=True):
            st.subheader(f"{code(caso)} · {caso.get('servicio') or 'Servicio por definir'}")
            st.caption(fecha_chile(caso['created_at']))
            if not caso['documentos']:
                st.info(VACIO)
            for doc in caso['documentos']:
                st.write(doc['tipo'])
                st.caption(fecha_chile(doc['fecha_subida']))
                st.download_button('Descargar', data=lambda id=doc['id']: documentos.descargar(id),
                                   file_name=doc['nombre'], mime=doc['tipo_mime'],
                                   key='descargar_cliente_' + doc['id'], width='stretch', on_click='ignore')


if __name__ == '__main__':
    mis_documentos(proteger_pagina('Mis documentos'))
