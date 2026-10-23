"""Solicitud asistida; el cliente conserva identidad bloqueada y único RPC."""
from datetime import date

import streamlit as st

from mente_futuro.domain import MODALITIES, SERVICES, TOPICS, code, today, validate_request
from mente_futuro.ui import flash, show_error
from servicios.solicitud_rapida import (ORIGENES, cuenta_por_correo, clientes_existentes,
    duplicados, errores_adicionales, formatear_rut, normalizar_telefono, sugerencias, sugerir_correo, cargar_catalogos)
from utils.componentes import encabezado_pagina, seccion_formulario, cargando_datos
from utils.solicitud_borrador import iniciar, recuperar, limpiar
from utils.validaciones import validar_campo


def _valores():
    return st.session_state.solicitud_borrador['values']


def _vincular(perfiles):
    valores=_valores()
    correo=valores['email'].strip().casefold()
    if st.session_state.get('solicitud_manual_correo') == correo:return
    catalogo=st.session_state.get('solicitud_catalogos',{})
    casos=catalogo.get('datos',([],[],[]))[1]
    cuenta=cuenta_por_correo(correo,perfiles,casos)
    valores['cliente_id']=cuenta['id'] if cuenta else None
    st.session_state['request_cliente_id']=valores['cliente_id']


def _cambio(campo,perfiles):
    valores=_valores()
    valor=st.session_state['request_'+campo]
    valores[campo]=valor.isoformat() if campo=='fecha_preferida' and valor else valor
    st.session_state.solicitud_ack=dict(valores)
    if campo=='rut':valores[campo]=formatear_rut(valor)
    if campo=='telefono':valores[campo]=normalizar_telefono(valor)
    if campo in ('rut','telefono'):st.session_state['request_'+campo]=valores[campo]
    if campo=='email':
        st.session_state.pop('solicitud_manual_correo',None)
        _vincular(perfiles)
    if campo=='cliente_id':st.session_state.solicitud_manual_correo=valores['email'].strip().casefold()
    if campo=='origen':st.session_state.solicitud_ultimo_origen=valor


def _usar_cliente(clientes,perfiles):
    elegido=st.session_state.get('solicitud_busqueda')
    if not elegido:return
    valores=_valores()
    st.session_state.solicitud_ack=dict(valores)
    for campo in ('cliente','rut','contacto','cargo','email','telefono'):
        valores[campo]=clientes[elegido].get(campo) or ''
        st.session_state['request_'+campo]=valores[campo]
    valores['rut']=formatear_rut(valores['rut'])
    valores['telefono']=normalizar_telefono(valores['telefono'])
    st.session_state['request_rut']=valores['rut']
    st.session_state['request_telefono']=valores['telefono']
    st.session_state.pop('solicitud_manual_correo',None)
    _vincular(perfiles)


def _aplicar(cambios,perfiles):
    st.session_state.solicitud_ack=dict(_valores())
    _valores().update(cambios)
    for campo,valor in cambios.items():st.session_state['request_'+campo]=valor
    if 'email' in cambios:
        st.session_state.pop('solicitud_manual_correo',None)
        _vincular(perfiles)


def _abrir(caso,cotizar=False):
    st.session_state.selected_case=caso['id']
    st.session_state.pending_navigation='Casos y cotizaciones'
    if cotizar:st.session_state.abrir_cotizacion=caso['id']


def request_page(repo):
    encabezado_pagina('Nueva solicitud', 'Cuéntanos qué tienes en mente. Completa los datos del servicio y tus objetivos.', 'SOLICITUDES', '✧')
    borrador=iniciar(repo)
    recuperar(repo,borrador)
    if not repo.is_owner and st.session_state.get('request_receipt'):
        st.success(f"Solicitud {st.session_state.request_receipt} enviada correctamente.")
        st.write('Te contactaremos dentro de las próximas 48 horas hábiles')
        if st.button('Enviar otra solicitud',type='primary'):
            st.session_state.pop('request_receipt',None)
            st.rerun()
        return
    perfiles,casos,tarifas=[],[],[]
    if repo.is_owner:
        with cargando_datos('Preparando tu formulario…'):
            try:
                perfiles,casos,tarifas=cargar_catalogos(repo)
            except Exception:
                respaldo=st.session_state.get('solicitud_catalogos')
                if respaldo and respaldo['clave'][0]==repo.user.id:perfiles,casos,tarifas=respaldo['datos']
                st.warning('No pudimos cargar todas las sugerencias. Puedes completar los datos a mano y reintentar el envío.')
    valores=borrador['values']
    nombre=repo.profile.get('nombre','').strip()
    if not repo.is_owner:
        valores.update(contacto=nombre,email=repo.user.email or '',cliente_id=None,origen='Formulario web')
    else:
        ids={p['id'] for p in perfiles if p['rol']=='cliente'}
        if perfiles:
            if valores['cliente_id'] not in ids:valores['cliente_id']=None
            _vincular(perfiles)

    def campo(campo,label,tipo='text_input',**kwargs):
        llave='request_'+campo
        if llave not in st.session_state:
            valor=valores[campo]
            if campo=='fecha_preferida' and valor:valor=date.fromisoformat(valor)
            st.session_state[llave]=valor
        resultado=getattr(st,tipo)(label,key=llave,on_change=_cambio,args=(campo,perfiles),**kwargs)
        if campo in ('email','rut','telefono') and valores[campo]:
            error=validar_campo(campo,valores[campo])
            if error:st.error(error)
        return resultado

    with st.container(key='mfy_request'):
        with seccion_formulario(1,'Datos de contacto','request_contact'):
            if repo.is_owner:
                clientes={c['id']:c for c in clientes_existentes(casos)}
                if st.session_state.get('solicitud_busqueda') not in clientes:st.session_state.pop('solicitud_busqueda',None)
                st.selectbox('Buscar empresa o cliente existente',list(clientes),index=None,
                    placeholder='Escribe una empresa, contacto o correo…',key='solicitud_busqueda',
                    format_func=lambda x:f"{clientes[x]['cliente']} · {clientes[x].get('contacto','')} · {clientes[x].get('email','')}",
                    on_change=_usar_cliente,args=(clientes,perfiles),help='Selecciona para precargar. Todos los datos se pueden modificar después.')
            left,right=st.columns(2,gap='large')
            with left:
                if repo.is_owner:
                    campo('cliente','Nombre o empresa *',max_chars=180)
                else:
                    st.text_input('Nombre de tu cuenta',value=nombre,disabled=True)
                    campo('cliente','Empresa u organización (opcional)',max_chars=180)
                campo('rut','RUT (opcional)',max_chars=16,placeholder='12.345.678-5')
                campo('email','Correo de contacto *',disabled=not repo.is_owner,max_chars=254)
                sugerencia=sugerir_correo(valores['email']) if repo.is_owner else None
                if sugerencia:
                    st.caption(f'¿Quisiste decir {sugerencia}?')
                    st.button('Usar '+sugerencia,key='corregir_correo',on_click=_aplicar,args=({'email':sugerencia},perfiles))
            with right:
                campo('contacto','Persona de contacto *',disabled=not repo.is_owner,max_chars=160)
                campo('cargo','Cargo (opcional)',max_chars=160)
                campo('telefono','Teléfono',max_chars=40,placeholder='+56 9 1234 5678')
            if repo.is_owner:
                opciones={p['id']:f"{p['nombre']} · {p['email']}" for p in perfiles if p['rol']=='cliente'}
                if valores['cliente_id'] and valores['cliente_id'] not in opciones:
                    opciones[valores['cliente_id']]='Cuenta vinculada actual (sin conexión)'
                st.session_state['request_cliente_id']=valores['cliente_id']
                campo('cliente_id','Vincular a una cuenta de cliente','selectbox',options=[None,*opciones],
                    format_func=lambda x:opciones.get(x,'Sin cuenta vinculada'))
                if valores['cliente_id'] in opciones:st.info('Vinculada a la cuenta de '+opciones[valores['cliente_id']])
        with seccion_formulario(2,'La experiencia que buscas','request_service'):
            a,b=st.columns(2,gap='large')
            with a:
                campo('servicio','Tipo de servicio *','selectbox',options=SERVICES)
                campo('tematica','Temática principal *','selectbox',options=TOPICS)
                campo('participantes','Participantes *','number_input',min_value=1,max_value=10000)
            with b:
                campo('modalidad','Modalidad *','selectbox',options=MODALITIES)
                campo('horas','Horas totales estimadas *','number_input',min_value=.5,max_value=1000.0,step=.5)
                fecha=valores['fecha_preferida']
                minimo=min(today(),date.fromisoformat(fecha)) if fecha else today()
                campo('fecha_preferida','Fecha preferida (opcional)','date_input',min_value=minimo,format='DD/MM/YYYY')
            if repo.is_owner:
                valores_sugeridos,fuente=sugerencias(valores['tematica'],valores['servicio'],casos,tarifas)
                if valores_sugeridos:
                    texto=' · '.join(f"{v:g} {'horas' if k=='horas' else 'participantes'}" for k,v in valores_sugeridos.items())
                    st.caption(f'Sugerencia: {texto}, según {fuente}. Puedes ajustarla.')
                    st.button('Aplicar sugerencia',on_click=_aplicar,args=(valores_sugeridos,perfiles))
            campo('lugar','Lugar o ciudad',max_chars=250)
            campo('detalle','¿Qué te gustaría lograr?','text_area',max_chars=5000,height=110)
        with seccion_formulario(3,'Confirma tu solicitud','request_confirm'):
            if repo.is_owner:campo('origen','Origen de la solicitud','selectbox',options=ORIGENES)
            consent=True
            if not repo.is_owner:
                consent=st.checkbox('Autorizo a Mente y Futuro a utilizar mis datos para gestionar esta solicitud y contactarme. *',key='request_consent')
            repetidos=[c for c in duplicados(valores,casos) if c['id']!=borrador['id']] if repo.is_owner else []
            firma=tuple((valores.get(k) or '') for k in ('cliente','email','cliente_id','tematica'))
            if st.session_state.get('solicitud_duplicado_firma') != firma:
                st.session_state.pop('solicitud_duplicado',None)
                st.session_state.solicitud_duplicado_firma=firma
            continuar=False
            if repetidos:
                st.warning('¿Es la misma solicitud? Hay un caso abierto del mismo cliente y temática en los últimos 30 días.')
                for caso in repetidos[:5]:
                    st.button(f"Abrir {code(caso)} · {caso['cliente']}",key='duplicado_'+caso['id'],on_click=_abrir,args=(caso,))
                continuar=st.checkbox('Crear otra solicitud de todas formas',key='solicitud_duplicado')
            st.caption('* Campos obligatorios. El valor final se confirma en la propuesta.')
            st.caption('Borrador conservado en esta sesión y, si el navegador lo permite, en esta pestaña. No se envía hasta confirmar.')
            submitted=st.button('Enviar solicitud',type='primary',width='stretch')
            cotizar,otra=False,False
            if repo.is_owner:
                a,b=st.columns(2)
                with a:cotizar=st.button('Guardar y cotizar ahora',width='stretch')
                with b:otra=st.button('Guardar y registrar otra',width='stretch')
    if not (submitted or cotizar or otra):return
    data={k:v.strip() if isinstance(v,str) else v for k,v in valores.items()}
    data['cliente']=data['cliente'] or nombre
    data['rut']=formatear_rut(data['rut'])
    data['telefono']=normalizar_telefono(data['telefono'])
    if not repo.is_owner:data.update(contacto=nombre,email=repo.user.email or '',cliente_id=None,origen='Formulario web')
    errors=validate_request(data)+errores_adicionales(data)
    if not consent:errors.append('Debes autorizar el uso de tus datos para enviar la solicitud.')
    if repetidos and not continuar:errors.append('Revisa la coincidencia o marca Crear otra solicitud de todas formas.')
    if errors:
        for error in errors:st.error(error)
        return
    if not repo.is_owner:data['consentimiento']=consent
    try:
        if repo.is_owner and not continuar:
            nuevos=[c for c in duplicados(data,repo.cases()) if c['id']!=borrador['id']]
            if nuevos:
                st.warning('Apareció una solicitud similar. Revisa la coincidencia antes de crear otra.')
                return
        result=repo.create_request(data,borrador['id'])
        limpiar(borrador)
        if repo.is_owner:
            if otra:
                flash(f'Solicitud {code(result)} guardada. Puedes registrar otra con el mismo origen.')
            else:
                _abrir(result,cotizar)
                flash(f'Solicitud {code(result)} guardada.')
        else:
            st.session_state.request_receipt=result['codigo']
            st.rerun()
    except Exception as error:
        if repo.is_owner and getattr(error,'code','') in ('PGRST204','42703'):
            st.error('Falta activar los campos RUT y cargo en Supabase. Ejecuta la migración 202610220002_solicitud_rapida.sql; conservamos tu borrador.')
        else:
            show_error(error)


if __name__=='__main__':
    from utils.permisos import proteger_pagina
    request_page(proteger_pagina('Nueva solicitud'))
