"""Solicitud sin cuenta. La administración conserva su formulario interno completo."""
from datetime import date
from html import escape

import streamlit as st
from mente_futuro.domain import SERVICES, TOPICS, MODALITIES
from mente_futuro.presentation import LOGO
from servicios import formulario_publico as servicio
from servicios.solicitud_rapida import formatear_rut, normalizar_telefono
from utils.componentes import preparar_celebracion, titulo_seccion
from utils.publico_borrador import iniciar, puente, descartar

ETIQUETAS={'cliente':'Empresa o institución','contacto':'Nombre y apellido','rut':'RUT (opcional)',
    'cargo':'Cargo (opcional)','email':'Correo electrónico','telefono':'Teléfono (opcional)',
    'servicio':'Tipo de servicio','tematica':'Temática principal','participantes':'Participantes',
    'horas':'Horas estimadas','modalidad':'Modalidad','lugar':'Lugar (opcional)',
    'fecha_preferida':'Fecha preferida (opcional)','detalle':'Cuéntanos un poco más (opcional)'}
ICONOS_SERVICIO=['◉','◎','✦','✧','＋']
ICONOS_TEMA=['✦','◎','◌','↗','♡','＋']


def _cambio(campo):
    borrador=iniciar()
    valor=st.session_state['publico_'+campo]
    recibido=valor
    if isinstance(valor,date):valor=valor.isoformat()
    if campo=='rut':valor=formatear_rut(valor)
    if campo=='telefono':valor=normalizar_telefono(valor)
    borrador['values'][campo]=valor
    st.session_state['publico_'+campo]=date.fromisoformat(valor) if campo=='fecha_preferida' and valor else valor
    st.session_state.setdefault('publico_tocados',set()).add(campo)
    st.session_state.publico_ack=dict(borrador['values'])
    # Reconoce el texto previo al formato para no recuperarlo como una edición pendiente.
    st.session_state.publico_ack[campo]=recibido.isoformat() if isinstance(recibido,date) else recibido


def _error(campo,paso):
    errores=servicio.errores_paso(iniciar()['values'],paso)
    if campo in st.session_state.get('publico_tocados',set()) and campo in errores:
        st.markdown(f'<p class="mfy-field-error" role="alert">{escape(errores[campo])}</p>',unsafe_allow_html=True)


def _campo(campo,paso):
    key='publico_'+campo
    valor=iniciar()['values'][campo]
    if key not in st.session_state:
        st.session_state[key]=date.fromisoformat(valor) if campo=='fecha_preferida' and valor else valor
    comunes=dict(key=key,on_change=_cambio,args=(campo,))
    if campo in ('participantes','horas'):
        st.number_input(ETIQUETAS[campo],min_value=1 if campo=='participantes' else .5,
            max_value=10000 if campo=='participantes' else 1000.0,
            step=1 if campo=='participantes' else .5,**comunes)
    elif campo=='fecha_preferida':
        st.date_input(ETIQUETAS[campo],format='DD/MM/YYYY',**comunes)
    elif campo=='detalle':st.text_area(ETIQUETAS[campo],max_chars=5000,height=115,**comunes)
    else:
        limites={'cliente':180,'contacto':160,'rut':16,'cargo':160,'email':254,'telefono':40,'lugar':250}
        st.text_input(ETIQUETAS[campo],max_chars=limites[campo],**comunes)
    _error(campo,paso)


def _seleccion(campo,opciones,iconos=None):
    key='publico_'+campo
    if key not in st.session_state:st.session_state[key]=iniciar()['values'][campo]
    with st.container(key='mfy_public_'+campo):
        st.pills(ETIQUETAS[campo],opciones,selection_mode='single',key=key,
            format_func=(lambda x:iconos[opciones.index(x)]+'  '+x) if iconos else str,
            on_change=_cambio,args=(campo,))
    _error(campo,2)


def _enlaces(config):
    enlaces=[]
    # Solo destinos validados y provenientes de mf_configuracion.datos.
    iconos={
        'facebook':'<path d="M14 8h3V4h-3c-4 0-5 2-5 5v3H6v4h3v8h4v-8h3l1-4h-4V9c0-1 0-1 1-1Z"/>',
        'instagram':'<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1"/>'}
    for red in ('facebook','instagram'):
        url=config['redes'].get(red)
        if url:enlaces.append(f'<a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="{red.capitalize()}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">{iconos[red]}</svg></a>')
    if config.get('sitio_web'):
        enlaces.append(f'<a href="{escape(config["sitio_web"],quote=True)}" target="_blank" rel="noopener noreferrer">Volver al sitio ↗</a>')
    return '<nav class="mfy-public-links" aria-label="Contacto y redes">'+''.join(enlaces)+'</nav>' if enlaces else ''


def _resumen(valores):
    datos=servicio.datos_solicitud(valores)
    filas=[]
    for campo in servicio.CAMPOS:
        valor=datos.get(campo)
        if valor in (None,''):continue
        if campo=='fecha_preferida':valor=date.fromisoformat(valor).strftime('%d/%m/%Y')
        filas.append(f'<div><dt>{escape(ETIQUETAS[campo])}</dt><dd>{escape(str(valor))}</dd></div>')
    st.markdown('<div class="mfy-public-summary"><h3>Revisa tu solicitud</h3><dl>'+''.join(filas)+'</dl></div>',unsafe_allow_html=True)


def formulario_publico():
    with st.container(key='mfy_public'):
        with st.container(key='mfy_public_header'):
            with st.container(key='mfy_public_top'):
                marca,contacto=st.columns([1,1.3])
                with marca:
                    with st.container(key='mfy_public_logo'):st.image(str(LOGO),width=190)
                with contacto:enlaces=st.empty()
            st.markdown('<div class="mfy-public-heading"><div><span class="mfy-eyebrow">MENTE Y FUTURO · CONVERSEMOS</span>'
                '<h1>Cuéntanos qué necesita tu equipo</h1><p>Una propuesta a tu medida comienza aquí.</p></div>'
                +'</div>',unsafe_allow_html=True)
        recibo=st.session_state.get('publico_recibo')
        if recibo:
            puente(recibo['borrador'])
            with st.container(key='mfy_form_publico_success'):
                st.markdown('<div class="mfy-public-success"><svg viewBox="0 0 64 64" role="img" aria-label="Enviado">'
                    '<circle cx="32" cy="32" r="29" fill="#E7F5ED"/><path d="m18 33 9 9 19-21" fill="none" stroke="#216342" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                    '<h2>¡Recibimos tu solicitud!</h2><p>Tu número es <strong>'+escape(recibo['codigo'])+'</strong>.</p>'
                    '<p>Te contactaremos dentro de las próximas <strong>48 horas hábiles</strong>.</p></div>',unsafe_allow_html=True)
                if st.button('Enviar otra solicitud',key='publico_otra',width='stretch'):
                    st.session_state.pop('publico_recibo',None);st.rerun()
        else:
            borrador=iniciar()
            puente(borrador)
            paso=borrador['step']
            with st.container(key='mfy_form_publico'):
                st.markdown(f'<div class="mfy-public-progress mfy-progress-{paso}" role="progressbar" aria-label="Avance de la solicitud" aria-valuemin="1" aria-valuemax="3" aria-valuenow="{paso}">'
                    '<div class="mfy-progress-labels"><span>1 · Contacto</span><span>2 · Tu equipo</span><span>3 · Enviar</span></div><div class="mfy-progress-track"><i></i></div></div>',unsafe_allow_html=True)
                titulo_seccion(paso,('Tu empresa y contacto','Qué necesitas','Detalles y consentimiento')[paso-1])
                if paso==1:
                    st.caption('Sin crear una cuenta. Si consultas a título personal, puedes dejar Empresa en blanco.')
                    for campo in servicio.PASOS[0]:_campo(campo,1)
                elif paso==2:
                    _seleccion('servicio',SERVICES,ICONOS_SERVICIO)
                    _seleccion('tematica',TOPICS,ICONOS_TEMA)
                    _seleccion('modalidad',MODALITIES)
                    for campo in ('participantes','horas'):_campo(campo,2)
                else:
                    for campo in servicio.PASOS[2]:_campo(campo,3)
                    _resumen(borrador['values'])
                    consentimiento=st.checkbox('Autorizo a Mente y Futuro a usar estos datos para responder y preparar mi solicitud.',key='publico_consentimiento')
                    if st.session_state.get('publico_error_consentimiento') and not consentimiento:
                        st.markdown('<p class="mfy-field-error" role="alert">Autoriza el uso de tus datos para poder enviar.</p>',unsafe_allow_html=True)
                # Honeypot sin visibilidad ni foco para personas; nunca se persiste.
                st.text_input('Deja este campo vacío',key='publico_sitio_confirmacion')
                if st.session_state.get('publico_error_envio'):st.warning(st.session_state.publico_error_envio)
            with st.container(key='mfy_public_actions'):
                atras,siguiente=st.columns([1,2])
                with atras:
                    if paso>1 and st.button('Atrás',key='publico_atras',width='stretch'):
                        borrador['step']-=1;st.rerun()
                with siguiente:
                    if st.button('Enviar solicitud' if paso==3 else 'Siguiente',key='publico_siguiente',type='primary',width='stretch'):
                        errores=servicio.errores_paso(borrador['values'],paso)
                        st.session_state.setdefault('publico_tocados',set()).update(servicio.PASOS[paso-1])
                        if errores:
                            from uuid import uuid4
                            st.session_state.publico_focus=dict(field=next(iter(errores)),id=str(uuid4()))
                            st.rerun()
                        if paso<3:borrador['step']+=1;st.rerun()
                        st.session_state.publico_error_consentimiento=not st.session_state.get('publico_consentimiento',False)
                        if st.session_state.publico_error_consentimiento:st.rerun()
                        try:
                            with st.spinner('Enviando tu solicitud…'):
                                codigo=servicio.enviar(borrador,True,st.session_state.get('publico_sitio_confirmacion',''))
                            from copy import deepcopy
                            st.session_state.publico_recibo=dict(codigo=codigo,borrador=deepcopy(borrador))
                            descartar(borrador)
                            preparar_celebracion(borrador['id'],'¡Solicitud recibida!')
                            st.rerun()
                        except ValueError as error:st.session_state.publico_error_envio=str(error);st.rerun()
                        except Exception:
                            st.session_state.publico_error_envio='No pudimos confirmar el envío. Conservamos lo escrito; revisa tu conexión y reintenta sin cambiar los datos.'
                            st.rerun()
            st.caption('Si tu navegador lo permite, el borrador se conserva en esta pestaña hasta 24 horas. En un dispositivo compartido, cierra la pestaña al terminar.')
        # Esta lectura no bloquea el primer render del formulario ni consulta tablas privadas.
        configuracion=servicio.configuracion_publica()
        enlaces.markdown(_enlaces(configuracion),unsafe_allow_html=True)
        if configuracion.get('correo_contacto'):
            from urllib.parse import quote
            correo=configuracion['correo_contacto']
            st.markdown(f'<p class="mfy-public-contact">También puedes escribirnos a <a href="mailto:{quote(correo,safe="@.")}">{escape(correo)}</a>.</p>',unsafe_allow_html=True)
