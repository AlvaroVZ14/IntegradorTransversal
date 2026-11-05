"""Herramientas de publicación. Copiar y abrir no envían solicitudes."""
import streamlit as st
from utils.permisos import require_admin
from utils.canales import CANALES
from utils.mensaje_listo import copiar_mensaje
from servicios.compartir import es_local,enlace_canal,archivos_qr,TEXTOS,texto_listo

def abrir_opciones_portal():
    st.session_state.abrir_opciones_portal=True
    st.session_state.pending_navigation='Casos y cotizaciones'

def tarjeta_compartir(datos):
    """Usa el enlace central del formulario, sin añadir consultas a Hoy."""
    with st.container(key='mfy_form_compartir_hoy'):
        texto,copiar,acceso=st.columns([2,1.2,1])
        texto.markdown('**↗ Comparte tu formulario**')
        from servicios.compartir import url_publica_app
        base=url_publica_app()
        if base and not es_local(base):
            with copiar:
                copiar_mensaje(enlace_canal(base,'directo'),'hoy_copiar_formulario',etiqueta='Copiar enlace',confirmacion='Enlace copiado')
        else:
            copiar.button('Copiar enlace',disabled=True,width='stretch',key='hoy_copiar_sin_url',
                          help='Completa una URL pública válida en Compartir.')
            st.caption('Configura la URL pública para compartir tu formulario.')
        acceso.page_link('paginas/compartir.py',label='Más opciones',icon=':material/share:')

def compartir_page(repo):
    require_admin(repo)
    from servicios.compartir import url_publica_app,enlaces_compartir,resumen_canales
    from servicios.en_vivo import cargar
    from mente_futuro.domain import today
    from ui.tema import ESTILOS_COMPARTIR
    st.markdown(ESTILOS_COMPARTIR,unsafe_allow_html=True)
    try:row=repo.sharing_settings()
    except Exception:
        st.warning('No pudimos cargar los textos guardados. Revisa la conexión y vuelve a intentarlo.')
        return
    datos=row['datos'];base=url_publica_app()
    if not base or es_local(base):
        st.warning('El enlace publicado aún no está disponible. Avísanos para corregirlo antes de compartir.')
        return
    with st.container(key='mfy_form_compartir_compacto'):
        st.subheader('Comparte tu formulario')
        contenido,qr_col=st.columns([3,1])
        with contenido:
            enlace=enlace_canal(base,'directo')
            st.code(enlace,language=None,wrap_lines=True)
            with st.container(key='mfy_share_copy'):
                copiar_mensaje(enlace,'compartir_link_directo',etiqueta='Copiar enlace',confirmacion='Enlace copiado')
            st.link_button('Abrir formulario',enlace,icon=':material/open_in_new:')
        with qr_col:
            canal=st.session_state.get('compartir_qr_canal','qr')
            if canal not in CANALES:canal='qr'
            qr_canal=canal
            try:
                png,svg=archivos_qr(enlace_canal(base,canal))
                st.image(png,width=160)
                st.download_button('Descargar QR (PNG)',png,f'formulario-{canal}.png','image/png',on_click='ignore')
            except Exception:
                png=svg=None
                st.warning('No pudimos preparar el QR. Puedes copiar el enlace mientras reintentas.')
        destinos=enlaces_compartir(base)
        columnas=st.columns(5)
        for columna,canal in zip(columnas,('whatsapp','instagram','facebook','linkedin','correo')):
            label,icono,_=CANALES[canal]
            with columna:
                if canal=='instagram':
                    copiar_mensaje(destinos[canal],'compartir_link_instagram',etiqueta='◎ Instagram',confirmacion='Enlace copiado')
                else:st.link_button(label,destinos[canal],icon=icono,width='stretch')
        st.caption('Instagram: pégalo en la biografía o en una historia.')
        try:
            lectura=cargar(repo,'casos')
            conteos=resumen_canales(lectura.get('datos',{}).get('casos',[]),today())
            if conteos:
                st.caption('Últimos 90 días: '+', '.join(f'{k} {v}' for k,v in sorted(conteos.items(),key=lambda x:x[1],reverse=True))+' · [Ver Dashboard]('+base+'dashboard)')
        except Exception:
            pass  # El resumen no bloquea compartir; no se inventan conteos.
    plantillas=datos.get('compartir') if isinstance(datos.get('compartir'),dict) else {}
    editados={}
    principales=('instagram_biografia','facebook','whatsapp')
    with st.expander('Textos listos'):
        st.caption('Edita el texto; {enlace} se reemplaza por el enlace del canal al copiar.')
        tabs=st.tabs([TEXTOS[k][0] for k in principales])
        for tab,key in zip(tabs,principales):
            label,canal=TEXTOS[key]
            with tab:
                editados[key]=st.text_area('Texto de '+label,value=plantillas.get(key) or 'Cuéntanos qué necesita tu equipo y te preparamos una propuesta a tu medida. {enlace}',max_chars=3000,height=85,key='compartir_texto_'+key)
                texto=texto_listo(editados[key],enlace_canal(base,canal))
                copiar_mensaje(texto,'compartir_copiar_texto_'+key,etiqueta='Copiar texto',confirmacion='Texto copiado')
        with st.expander('Más textos y opciones'):
            st.selectbox('Canal del QR',list(CANALES),index=list(CANALES).index('qr'),
                         format_func=lambda c:CANALES[c][0],key='compartir_qr_canal')
            for key in TEXTOS:
                if key in principales:continue
                label,canal=TEXTOS[key]
                editados[key]=st.text_area('Texto de '+label,value=plantillas.get(key) or 'Cuéntanos qué necesitas. {enlace}',max_chars=3000,height=85,key='compartir_texto_'+key)
                copiar_mensaje(texto_listo(editados[key],enlace_canal(base,canal)),'compartir_copiar_texto_'+key,etiqueta='Copiar texto')
            if svg:st.download_button('Descargar SVG · vectorial',svg,f'formulario-{qr_canal}.svg','image/svg+xml',on_click='ignore')
            st.button('Editar enlaces y contacto',on_click=abrir_opciones_portal,icon=':material/settings:')
        if st.button('Guardar textos para compartir',type='primary'):
            if any(not t.strip() or '{enlace}' not in t for t in editados.values()):
                st.warning('Incluye {enlace} en cada texto antes de guardar.')
            else:
                try:
                    repo.save_quote_settings({**datos,'compartir':{**plantillas,**editados}},row['version'])
                    st.success('Textos guardados.');st.rerun()
                except Exception:st.warning('No pudimos guardar. Conservamos tus textos para reintentar.')
    with st.expander('Cómo publicarlo'):
        st.write('1. Copia el enlace o descarga el QR. 2. Elige el canal. 3. Pega el texto y publica. 4. Abre el formulario en una ventana privada.')
        st.caption('El canal identifica el enlace utilizado, no cuenta visitas. Si reenvían un enlace de Instagram por WhatsApp, seguirá indicando Instagram.')

if __name__=='__main__':
    from utils.permisos import proteger_pagina
    compartir_page(proteger_pagina('Compartir',admin=True))
