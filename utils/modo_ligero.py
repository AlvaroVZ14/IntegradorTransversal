"""Preferencia visual local por cuenta; no almacena credenciales ni datos de negocio."""
import streamlit as st
from streamlit.components.v2 import component

JS_APARIENCIA = """
export default function({data,setStateValue}) {
 const key='mfy.apariencia.v1.'+data.usuario;
 let manual=false;
 try {
   if(data.guardar) localStorage.setItem(key, JSON.stringify(data.manual));
   manual=localStorage.getItem(key)==='true';
 } catch { manual=data.manual; }
 const motion=matchMedia('(prefers-reduced-motion: reduce)');
 const ahorro=matchMedia('(prefers-reduced-data: reduce)');
 const connection=navigator.connection;
 const aplicar=()=>{document.documentElement.dataset.mfyLight=String(manual||motion.matches||ahorro.matches||!!connection?.saveData);};
 aplicar();
 // Una respuesta inicial; no se usa un temporizador ni se consulta el servidor.
 if(!data.restaurado || data.guardar) setStateValue('recordado',manual);
 motion.addEventListener('change',aplicar);ahorro.addEventListener('change',aplicar);
 connection?.addEventListener('change',aplicar);
 return ()=>{motion.removeEventListener('change',aplicar);ahorro.removeEventListener('change',aplicar);connection?.removeEventListener('change',aplicar);};
}
"""


def _cambio():
    st.session_state['_tema_guardar']=True
    st.session_state['_tema_restaurado']=True


def aplicar_modo_ligero(repo=None):
    usuario=str(repo.user.id) if repo else 'visitante'
    if st.session_state.get('_tema_usuario')!=usuario:
        st.session_state.update(_tema_usuario=usuario,_tema_restaurado=False,tema_modo_ligero=False)
    guardar=st.session_state.pop('_tema_guardar',False)
    puente=component('mfy_apariencia_local',html='<span class="mfy-apariencia-marker" aria-hidden="true"></span>',js=JS_APARIENCIA)
    estado=puente(data=dict(usuario=usuario,manual=bool(st.session_state.get('tema_modo_ligero',False)),
                           guardar=guardar,restaurado=st.session_state.get('_tema_restaurado',False)),
        default={'recordado':None},on_recordado_change=lambda:None,key='mfy_apariencia_'+usuario,height=0)
    if not st.session_state.get('_tema_restaurado') and isinstance(estado.recordado,bool):
        st.session_state.tema_modo_ligero=estado.recordado
        st.session_state['_tema_restaurado']=True


def control_modo_ligero():
    st.toggle('Modo ligero',key='tema_modo_ligero',on_change=_cambio,
              help='Reduce la decoración en este navegador. También se activa si tu equipo pide menos movimiento o ahorro de datos.')
