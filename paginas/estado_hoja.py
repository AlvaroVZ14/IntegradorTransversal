"""Panel administrativo. Solo recibe estado público acotado, nunca secretos."""
from datetime import datetime,timezone
from uuid import uuid4
import streamlit as st
from utils.permisos import require_admin

@st.cache_data(ttl=30,show_spinner=False,max_entries=64)
def _leer(scope,revision,_repo):
    respuesta=_repo.client.rpc('mf_estado_hoja',{}).execute().data
    if not isinstance(respuesta,dict):raise ValueError()
    return respuesta

def estado_guardado():
    datos=st.session_state.get('hoja_estado_vista',{})
    return {'integrada':datos.get('integrada',False),'ultima_sincronizacion':datos.get('ultimo_exito')}

def _accion(repo,reconstruir=False):
    require_admin(repo)
    from servicios.hoja_sync import avisar
    avisar(admin=True,reconstruir=reconstruir)
    _leer.clear()
    st.toast('Lo pondremos al día. Puedes seguir trabajando.')

@st.fragment(run_every='30s')
def panel_hoja(repo):
    require_admin(repo)
    from servicios.hoja_sync import estado_local
    st.markdown('**Estado de la hoja**')
    scope=st.session_state.setdefault('hoja_estado_scope',str(uuid4()))
    try:
        datos=_leer(scope,st.session_state.get('dashboard_revision',0),repo)
        st.session_state.hoja_estado_vista=datos
    except Exception:
        datos=st.session_state.get('hoja_estado_vista',{})
        if datos:st.warning('No pudimos comprobar la hoja. Tus datos siguen guardados en la app.')
        else:st.info('La conexión con la hoja está pendiente de activar.')
    local=estado_local()
    if not local.get('configurada') and not datos.get('integrada'):
        st.caption('Podrás ver aquí su actualización cuando terminemos de conectarla.')
        return
    pendientes=int(datos.get('pendientes',0))
    if datos.get('actualizando'):
        st.warning(f'Actualizando… faltan {pendientes} cambios')
    elif datos.get('mensaje') or local.get('aviso'):
        st.error('No pudimos actualizar la hoja. Tus datos están a salvo; lo reintentamos solos')
    elif pendientes or not datos.get('ultimo_exito'):
        st.warning(f'Actualizando… faltan {pendientes} cambios')
    else:
        fecha=datetime.fromisoformat(datos['ultimo_exito'].replace('Z','+00:00'))
        minutos=max(0,int((datetime.now(timezone.utc)-fecha).total_seconds()/60))
        st.success('Al día · última actualización hace '+('menos de un minuto' if minutos==0 else str(minutos)+' minutos'))
    if local.get('url'):st.link_button('Abrir hoja',local['url'],icon=':material/table:')
    st.button('Sincronizar ahora',key='hoja_sync_ahora',on_click=_accion,args=(repo,),disabled=not local.get('configurada'))
    with st.expander('Ver registro'):
        if datos.get('registro'):st.dataframe(datos['registro'],hide_index=True,width='stretch')
        else:st.caption('Aún no hay actualizaciones registradas.')
    with st.expander('Reconstruir la copia de datos'):
        st.caption('Reemplaza las tres pestañas de datos. Conserva las fórmulas de Resumen y los datos de la app.')
        confirmar=st.checkbox('Confirmo reconstruir toda la hoja de datos',key='hoja_confirmar_reconstruccion')
        st.button('Reconstruir toda la hoja',key='hoja_reconstruir',disabled=not confirmar or not local.get('configurada'),on_click=_accion,args=(repo,True))
