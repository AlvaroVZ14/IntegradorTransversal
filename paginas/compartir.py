"""Herramientas de publicación. Copiar y abrir no envían solicitudes."""
import streamlit as st
from utils.permisos import require_admin
from utils.componentes import encabezado_pagina
from utils.canales import CANALES
from utils.mensaje_listo import copiar_mensaje
from servicios.compartir import resolver_url,url_detectada,es_local,enlace_canal,archivos_qr,TEXTOS,texto_listo

def abrir_configuracion():
    st.session_state.abrir_configuracion=True
    st.session_state.pending_navigation='Casos y cotizaciones'

def tarjeta_compartir(datos):
    """Reutiliza la configuración de la lectura de Hoy, sin otra consulta."""
    with st.container(key='mfy_form_compartir_hoy'):
        st.subheader('Comparte tu formulario')
        st.caption('Un enlace para que las personas te cuenten qué necesita su equipo.')
        base,detectada=resolver_url(datos,url_detectada())
        if base and not es_local(base):
            copiar_mensaje(enlace_canal(base,'directo'),'hoy_copiar_formulario',etiqueta='Copiar enlace',confirmacion='Enlace copiado ✓')
            if detectada:st.caption('Usamos la dirección detectada. Confírmala y guárdala en Compartir.')
        else:st.caption('Configura la URL pública para compartir tu formulario.')
        st.page_link('paginas/compartir.py',label='Ir a Compartir',icon=':material/share:')

def compartir_page(repo):
    require_admin(repo)
    encabezado_pagina('Tu formulario, donde te necesiten','Enlaces, códigos QR y mensajes listos para compartir.','COMPARTIR',':material/share:')
    try:row=repo.sharing_settings()
    except Exception as error:
        if getattr(error,'code','')=='PGRST202':
            st.info('Para activar Compartir, ejecuta 202610240002_compartir_canales.sql después del SQL del formulario unificado.')
        else:st.warning('No pudimos cargar tus enlaces. Revisa la conexión y vuelve a intentarlo.')
        return
    datos=row['datos'];base,detectada=resolver_url(datos,url_detectada())
    if detectada:
        st.info('La URL pública aún no está configurada. Intentamos detectar la dirección de esta aplicación; revísala antes de compartirla.')
        if base:
            st.code(base,language=None,wrap_lines=True)
            if es_local(base):st.warning('Esta dirección es local o privada: no funcionará para tus clientes. Configura la dirección publicada.')
            elif st.button('Guardar URL detectada',type='primary'):
                try:
                    repo.save_quote_settings({**datos,'url_publica':base},row['version'])
                    st.success('URL pública guardada.');st.rerun()
                except Exception:st.warning('No pudimos guardar la URL. Conservamos tus datos; vuelve a intentarlo.')
    st.button('Editar URL pública en Configuración',on_click=abrir_configuracion,icon=':material/settings:')
    if not base or es_local(base):
        st.info('Completa una URL pública válida en Configuración para preparar los enlaces y QR.')
        return
    st.caption('Los enlaces solo identifican el canal. No contienen datos personales ni conceden acceso a la administración.')
    canales=list(CANALES)
    for offset in range(0,len(canales),2):
        for columna,canal in zip(st.columns(2),canales[offset:offset+2]):
            label,icono,ayuda=CANALES[canal];enlace=enlace_canal(base,canal)
            with columna,st.container(key='mfy_form_compartir_'+canal):
                st.subheader(label,help=ayuda)
                st.caption(ayuda)
                st.code(enlace,language=None,wrap_lines=True)
                copiar_mensaje(enlace,'compartir_link_'+canal,confirmacion='Enlace copiado ✓')
                st.link_button('Abrir',enlace,icon=':material/open_in_new:',width='stretch')
    with st.container(key='mfy_form_compartir_descargas'):
        st.subheader('Un QR para cada canal')
        canal=st.selectbox('Canal del QR',canales,index=canales.index('qr'),format_func=lambda c:CANALES[c][0],key='compartir_qr_canal')
        enlace=enlace_canal(base,canal)
        try:
            png,svg=archivos_qr(enlace)
            st.image(png,width=280,caption='QR de '+CANALES[canal][0])
            st.caption('Azul marino sobre blanco, margen de seguridad y corrección alta. El enlace es el mismo del canal seleccionado.')
            a,b=st.columns(2)
            a.download_button('Descargar PNG · alta resolución',png,f'formulario-{canal}.png','image/png',width='stretch',on_click='ignore')
            b.download_button('Descargar SVG · vectorial',svg,f'formulario-{canal}.svg','image/svg+xml',width='stretch',on_click='ignore')
        except Exception:st.warning('No pudimos generar el QR. Comprueba que el enlace sea válido y que estén instaladas las dependencias.')
    st.subheader('Textos listos para publicar')
    st.caption('Ajusta el tono y conserva {enlace}: se reemplaza por el enlace del canal al copiar. Editar y copiar no publica nada.')
    plantillas=datos.get('compartir') if isinstance(datos.get('compartir'),dict) else {}
    editados={}
    for tab,(key,(label,canal)) in zip(st.tabs([v[0] for v in TEXTOS.values()]),TEXTOS.items()):
        with tab:
            editados[key]=st.text_area('Texto de '+label,value=plantillas.get(key,''),max_chars=3000,height=150,key='compartir_texto_'+key)
            texto=texto_listo(editados[key],enlace_canal(base,canal))
            if '{enlace}' not in editados[key]:st.caption('Agrega {enlace} donde quieras incluir la dirección del formulario.')
            st.code(texto,language=None,wrap_lines=True)
            copiar_mensaje(texto,'compartir_copiar_texto_'+key,etiqueta='Copiar texto',confirmacion='Texto copiado ✓')
    if st.button('Guardar textos para compartir',type='primary'):
        if any(not t.strip() or '{enlace}' not in t for t in editados.values()):
            st.warning('Completa todos los textos e incluye {enlace} en cada uno antes de guardar.')
        else:
            try:
                repo.save_quote_settings({**datos,'compartir':{**plantillas,**editados}},row['version'])
                st.success('Textos guardados.');st.rerun()
            except Exception:st.warning('No pudimos guardar los textos. Conservamos lo escrito; vuelve a intentarlo.')
    with st.container(key='mfy_form_compartir_como'):
        st.subheader('Cómo publicarlo')
        st.write('1. Elige el canal y copia su enlace o descarga su QR.')
        st.write('2. Ajusta y copia el texto de ese canal.')
        st.write('3. Pégalo en tu perfil, sitio o mensaje y publica cuando quieras.')
        st.write('4. Abre el enlace en una ventana privada y revisa que aparezca el formulario.')
        st.caption('El canal representa el enlace utilizado, no una verificación de la red de origen. Si reenvían el enlace de Instagram por WhatsApp, seguirá indicando Instagram.')

if __name__=='__main__':
    from utils.permisos import proteger_pagina
    compartir_page(proteger_pagina('Compartir',admin=True))
