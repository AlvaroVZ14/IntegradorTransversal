"""Tarjeta de perfil dentro de Mis documentos. No registra ninguna ruta."""
import streamlit as st
from streamlit.components.v2 import component
from servicios.perfil_cliente import PerfilCliente,EDITABLES,validar_perfil,actualizar_borrador_perfil
from servicios.redes_sociales import REDES


def mi_perfil(repo):
    with st.container(key='mfy_perfil_cliente'):
        with st.expander('Mi perfil',expanded=False):
            base='mi_perfil_'+str(repo.user.id)
            try:servicio=PerfilCliente(repo);actual=servicio.leer()
            except PermissionError as error:st.info(str(error));return
            except Exception:
                actual=st.session_state.get(base+'_base')
                if not actual:
                    st.info('Todavía no pudimos cargar tu perfil. Puedes seguir consultando tus documentos e intentarlo más tarde.');return
                st.warning('Mostramos tu última lectura. Conservamos lo escrito mientras vuelve la conexión.')
            anterior=st.session_state.get(base+'_base')
            if anterior and (anterior['id'],anterior['version'])!=(actual['id'],actual['version']):
                originales={**{k:anterior.get(k,'') for k in ('telefono','cargo')},**{k:anterior['redes_sociales'].get(k,'') for k in REDES}}
                if all(st.session_state.get(base+'_'+k,v)==v for k,v in originales.items()):
                    st.session_state[base+'_refresco']=actual
            if refresco:=st.session_state.pop(base+'_refresco',None):
                st.session_state[base+'_base']=refresco
                for k in EDITABLES:st.session_state[base+'_'+k]=refresco.get(k,'') if k not in REDES else refresco['redes_sociales'].get(k,'')
            if base+'_base' not in st.session_state:st.session_state[base+'_base']=actual
            edicion=st.session_state[base+'_base']
            if st.session_state.pop(base+'_listo',False):st.success('Listo, actualizamos tus datos')
            with st.form(base+'_form'):
                st.text_input('Empresa',value=edicion['empresa'],disabled=True)
                st.text_input('Nombre de contacto',value=edicion['nombre'],disabled=True)
                st.text_input('Correo',value=edicion['correo'],disabled=True,help='Es el correo de tu cuenta')
                st.caption('Es el correo de tu cuenta')
                errores=st.session_state.get(base+'_errores',{})
                datos={}
                for campo in EDITABLES:
                    label,icono=REDES.get(campo,('Teléfono' if campo=='telefono' else 'Cargo',None))
                    valor=edicion.get(campo,'') if campo not in REDES else edicion['redes_sociales'].get(campo,'')
                    llave=base+'_'+campo
                    if llave not in st.session_state:st.session_state[llave]=valor
                    datos[campo]=st.text_input(label,key=llave,
                        max_chars=200 if campo in REDES else 40 if campo=='telefono' else 160,
                        **({'icon':icono} if icono else {}))
                    if campo in errores:st.error(errores[campo])
                guardar=st.form_submit_button('Guardar cambios',type='primary',width='stretch')
            if guardar:
                errores=validar_perfil(datos);st.session_state[base+'_errores']=errores
                if errores:st.rerun()
                try:
                    actualizado=servicio.guardar(st.session_state[base+'_base'],datos)
                    borrador=st.session_state.get('formularios',{}).get('cliente:'+str(repo.user.id))
                    anteriores=dict(borrador['values']) if borrador else {}
                    cambios=actualizar_borrador_perfil(st.session_state,repo.user.id,actualizado)
                    st.session_state[base+'_refresco']=actualizado
                    st.session_state[base+'_listo']=True
                    if cambios:st.session_state[base+'_patch']={'fields':cambios,'previous':anteriores}
                    st.rerun()
                except Exception as error:
                    if getattr(error,'code','')=='40001':
                        try:
                            nuevo=servicio.leer()
                            if nuevo['id']==st.session_state[base+'_base']['id']:st.session_state[base+'_base']=nuevo
                        except Exception:pass  # Mantener también la base si cayó la red.
                        st.warning('Tu perfil cambió en otra sesión. Conservamos lo escrito; revísalo antes de volver a guardar.')
                    else:st.warning('No pudimos confirmar el guardado. Conservamos lo que escribiste; revisa la conexión e intenta nuevamente.')
            # Actualiza solo la precarga del borrador de ESTA pestaña, sin borrar
            # servicio, detalles ni campos que la persona ya editó manualmente.
            if patch:=st.session_state.pop(base+'_patch',None):
                puente=component('mfy_perfil_borrador',html='<span aria-hidden="true"></span>',js="""
                export default function({data}) {
                  try {
                    const key='mfy-formulario:cliente:'+data.user;
                    const draft=JSON.parse(sessionStorage.getItem(key)||'null');
                    if(draft?.values) {
                      for(const [field,value] of Object.entries(data.fields)) {
                        const local=draft.values[field];
                        if(local===undefined || local===data.previous[field] || local===value)draft.values[field]=value;
                      }
                      sessionStorage.setItem(key,JSON.stringify(draft));
                    }
                  } catch {}
                }
                """)
                puente(data={'user':str(repo.user.id),**patch},key='perfil_borrador_patch',height=0)
