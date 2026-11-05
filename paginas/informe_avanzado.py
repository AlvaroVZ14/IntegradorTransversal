"""Se ejecuta únicamente al seleccionar Informe avanzado y con rol admin."""
import streamlit as st
from uuid import uuid4
from streamlit.components.v1 import iframe
from servicios.informe_avanzado import fecha_sincronizacion
from utils.permisos import require_admin
from utils.componentes import encabezado_pagina


def ayuda_informe():
    with st.expander('Ayuda · Informe avanzado'):
        st.markdown('**¿Cómo cambio el período?** Usa Agrupar por y el calendario dentro del informe. Sus controles son independientes de los del Dashboard.')
        st.markdown('**¿Cómo descargo un PDF?** Abre el informe en una pestaña nueva y elige Compartir → Descargar informe → PDF.')
        st.markdown('**¿Qué hago si no carga?** Ábrelo en una pestaña nueva, inicia sesión con la cuenta de Google autorizada y comprueba tu conexión. No necesitas hacerlo público.')


def mostrar_informe(repo, enlaces):
    require_admin(repo)
    encabezado_pagina('Informe avanzado', 'Más perspectivas para conocer tu negocio.', 'DASHBOARD', '✦', mostrar_metricas=False)
    # El botón queda antes del iframe y siempre es accesible si Google lo bloquea.
    st.link_button('Abrir en una pestaña nueva', enlaces['abrir'], icon=':material/open_in_new:', width='stretch')
    st.info('Si el informe no aparece, ábrelo en una pestaña nueva e inicia sesión con la cuenta de Google que tiene acceso.')
    with st.container(key='mfy_looker_embed'):
        iframe(enlaces['embed'], height=720, scrolling=True)
    st.markdown('**Cómo leer este informe**  \nElige la agrupación y las fechas dentro del informe.  \nLas ventas se muestran por fecha de venta y las solicitudes por fecha de recepción.  \nLa hoja y el informe pueden tardar unos minutos en mostrar los últimos cambios.')
    from paginas.estado_hoja import _leer
    datos = st.session_state.get('hoja_estado_vista', {})
    try:
        datos = _leer(st.session_state.setdefault('hoja_estado_scope', str(uuid4())), st.session_state.get('dashboard_revision', 0), repo)
        st.session_state.hoja_estado_vista = datos
    except Exception:
        st.caption('No pudimos comprobar ahora la sincronización de la hoja.')
    st.caption(fecha_sincronizacion(datos.get('ultimo_exito')))
    ayuda_informe()
