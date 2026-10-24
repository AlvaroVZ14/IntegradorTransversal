"""Entrada pública acotada. Nunca consulta perfiles, casos, tarifas ni configuración privada."""
from urllib.parse import urlsplit
import streamlit as st
from servicios.repositorio import public_client, fila_rpc
from utils.solicitud_borrador import DEFAULTS
from utils.validaciones import validar_campo
from mente_futuro.domain import validate_request
from servicios.solicitud_rapida import formatear_rut, normalizar_telefono

CAMPOS=tuple(k for k in DEFAULTS if k not in ('cliente_id','origen'))
PASOS=(('cliente','contacto','rut','cargo','email','telefono'),
       ('servicio','tematica','participantes','horas','modalidad'),
       ('lugar','fecha_preferida','detalle'))


def url_publica(valor):
    if not isinstance(valor,str) or not valor.strip():return ''
    valor=valor.strip()
    if any(ord(c)<32 for c in valor) or len(valor)>2048:return ''
    if '://' not in valor:
        if ':' in valor:return ''
        valor='https://'+valor
    try:
        p=urlsplit(valor)
        if p.scheme not in ('http','https') or not p.hostname or '.' not in p.hostname or p.username or p.password:return ''
        if any(c.isspace() for c in p.netloc):return ''
        return valor
    except ValueError:return ''


def configuracion_visible(datos):
    datos=datos if isinstance(datos,dict) else {}
    redes=datos.get('redes') if isinstance(datos.get('redes'),dict) else {}
    correo=datos.get('correo_contacto','')
    return dict(sitio_web=url_publica(datos.get('sitio_web')),
                redes={k:url_publica(redes.get(k)) for k in ('facebook','instagram')},
                correo_contacto=correo.strip() if isinstance(correo,str) and correo.strip() and not validar_campo('email',correo.strip()) else '')


def cliente_publico():
    if '_public_form_client' not in st.session_state:
        st.session_state['_public_form_client']=public_client(timeout=8)
    return st.session_state['_public_form_client']


@st.cache_data(ttl=60,show_spinner=False)
def configuracion_publica():
    try:
        cliente=public_client(timeout=3)
        datos=fila_rpc(cliente.rpc('mf_configuracion_publica',{}).execute().data)
        return configuracion_visible(datos)
    except Exception:
        # La ausencia o caída de un enlace nunca bloquea el formulario.
        return configuracion_visible({})


def datos_solicitud(valores):
    datos={k:(valores.get(k,'').strip() if isinstance(valores.get(k),str) else valores.get(k)) for k in CAMPOS}
    datos['cliente']=datos['cliente'] or datos['contacto']
    datos['rut']=formatear_rut(datos['rut'])
    datos['telefono']=normalizar_telefono(datos['telefono'])
    return datos


def errores_paso(valores,paso):
    datos=datos_solicitud(valores)
    errores={}
    for campo in PASOS[paso-1]:
        error=validar_campo(campo,datos[campo])
        if error:errores[campo]=error
    if paso==3:
        from mente_futuro.domain import today
        from datetime import date
        fecha=datos.get('fecha_preferida')
        if fecha:
            try:
                if date.fromisoformat(str(fecha))<today():errores['fecha_preferida']='Elige una fecha desde hoy en adelante.'
            except ValueError:errores['fecha_preferida']='Selecciona una fecha válida.'
    return errores


def enviar(borrador,consentimiento,trampa,repo=None):
    if not consentimiento:raise ValueError('Debes autorizar el uso de tus datos para enviar la solicitud.')
    if trampa:raise ValueError('No pudimos confirmar el envío. Revisa el formulario e intenta nuevamente.')
    datos=datos_solicitud(borrador['values'])
    for paso in (1,2,3):
        errores=errores_paso(datos,paso)
        if errores:raise ValueError(next(iter(errores.values())))
    errores=validate_request(datos)
    if errores:raise ValueError(errores[0])
    datos['consentimiento']=True
    if repo is not None:
        respuesta=repo.create_request(datos,borrador['id'])
    else:
        respuesta=fila_rpc(cliente_publico().rpc('registrar_solicitud_publica',{
            'p_solicitud_id':borrador['id'],'p_token':borrador['token'],
            'p_datos':datos,'p_honeypot':trampa}).execute().data)
    if not isinstance(respuesta,dict) or not respuesta.get('codigo'):
        raise RuntimeError('No se confirmó el envío.')
    from servicios.dashboard_cache import invalidar_dashboard
    invalidar_dashboard()
    return respuesta['codigo']
