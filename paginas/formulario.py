"""Única interfaz de solicitud: público, cuenta cliente y registro interno."""
from copy import deepcopy
from datetime import date
from html import escape
from uuid import uuid4
import streamlit as st

from mente_futuro.domain import code
from mente_futuro.presentation import LOGO
from servicios import formulario as servicio
from servicios.formulario_publico import configuracion_publica
from servicios.solicitud_rapida import (cargar_catalogos,clientes_existentes,cuenta_por_correo,
 duplicados,sugerencias,sugerir_correo,formatear_rut,normalizar_telefono)
from utils import formulario_borrador as respaldo
from utils.formulario_config import CAMPOS,PASOS,OPCIONES,BLOQUEADOS,campos_paso
from utils.componentes import html_contenido_encabezado,titulo_seccion,preparar_celebracion,enlaces_publicos


class Formulario:
    def __init__(self,repo):
        self.repo=repo;self.modo=servicio.modo_servidor(repo);self.interno=self.modo=='interno'
        self.catalogo=servicio.catalogo_publico()
        self.b=respaldo.iniciar(self.modo,repo,self.catalogo);self.v=self.b['values']
        self.prefix=respaldo.prefijo(self.modo);self.scope=respaldo.contexto(self.modo,repo)
        self.perfiles,self.casos,self.tarifas=[],[],[]
        if self.interno:
            try:self.perfiles,self.casos,self.tarifas=cargar_catalogos(repo)
            except Exception:
                anterior=st.session_state.get('solicitud_catalogos',{})
                if anterior.get('clave',(None,))[0]==repo.user.id:self.perfiles,self.casos,self.tarifas=anterior['datos']
                st.warning('No pudimos cargar las sugerencias. Puedes completar los datos a mano.')

    def cambio(self,campo):
        # Un logout o cambio de entrada puede desmontar los widgets mientras
        # llega un on_change pendiente. No reactivar borradores de otra sesión.
        actual=st.session_state.get('formularios',{}).get(self.scope)
        if (self.prefix+campo not in st.session_state or actual is None or
            actual.get('id')!=self.b.get('id')):return
        # El callback puede conservar una copia previa del mismo borrador.
        self.b=actual;self.v=actual['values']
        valor=st.session_state[self.prefix+campo];recibido=valor
        if isinstance(valor,date):valor=valor.isoformat()
        if campo=='rut':valor=formatear_rut(valor)
        if campo=='telefono':valor=normalizar_telefono(valor)
        self.v[campo]=valor
        self.b['ack']=dict(self.v);self.b['ack'][campo]=recibido
        if campo not in self.b['tocados']:self.b['tocados'].append(campo)
        if campo in ('rut','telefono'):st.session_state[self.prefix+campo]=valor
        if campo=='tematicas':self.v['tematica']=valor[0] if valor else None
        if campo=='email':st.session_state.pop('solicitud_manual_correo',None);self.vincular()
        if campo=='cliente_id':st.session_state.solicitud_manual_correo=(self.v['email'] or '').strip().casefold()
        if campo=='origen':st.session_state.solicitud_ultimo_origen=valor

    def vincular(self):
        if not self.interno:return
        correo=(self.v['email'] or '').strip().casefold()
        if st.session_state.get('solicitud_manual_correo')==correo:return
        cuenta=cuenta_por_correo(correo,self.perfiles,self.casos)
        self.v['cliente_id']=cuenta['id'] if cuenta else None
        st.session_state[self.prefix+'cliente_id']=self.v['cliente_id']

    def aplicar(self,cambios):
        self.b['ack']=dict(self.v)
        for campo,valor in cambios.items():
            if campo=='rut':valor=formatear_rut(valor)
            if campo=='telefono':valor=normalizar_telefono(valor)
            self.v[campo]=valor;st.session_state[self.prefix+campo]=valor
        if 'email' in cambios:st.session_state.pop('solicitud_manual_correo',None);self.vincular()

    def usar_cliente(self,clientes):
        elegido=st.session_state.get('solicitud_busqueda')
        if elegido:self.aplicar({k:clientes[elegido].get(k) or '' for k in ('cliente','contacto','rut','cargo','email','telefono')})

    def errores(self,paso=None,completo=False):
        return servicio.errores(self.v,self.modo,self.repo,paso,completo=completo,catalogo=self.catalogo)

    def campo(self,k):
        c=CAMPOS[k];key=self.prefix+k
        valor=self.v.get(k)
        if k in BLOQUEADOS[self.modo]:st.session_state[key]=valor
        if key not in st.session_state:st.session_state[key]=date.fromisoformat(valor) if k=='fecha_preferida' and valor else valor
        args=dict(key=key,on_change=self.cambio,args=(k,),help=c.ayuda or None)
        if c.tipo in ('servicio','tematicas','modalidad'):
            opciones=self.catalogo['servicios'] if k=='servicio' else self.catalogo['tematicas'] if k=='tematicas' else OPCIONES[k]
            if k=='tematicas':
                # Conserva el orden de selección para la temática principal.
                actual=list(self.v[k] or [])
                opciones=[*actual,*[v for v in opciones if v not in actual]]
            with st.container(key='mfy_public_'+('tematica' if k=='tematicas' else k)):
                st.pills(c.etiqueta,opciones,selection_mode='multi' if k=='tematicas' else 'single',
                    format_func=(lambda x:'✦  '+x) if k!='modalidad' else str,**args)
            if k=='tematicas' and self.v[k]:st.caption('Temática principal: '+self.v[k][0])
        elif c.tipo in ('entero','decimal'):
            st.number_input(c.etiqueta,min_value=1 if k=='participantes' else .5,max_value=10000 if k=='participantes' else 1000.0,
                step=1 if k=='participantes' else .5,**args)
        elif c.tipo=='fecha':st.date_input(c.etiqueta,format='DD/MM/YYYY',**args)
        elif c.tipo=='parrafo':st.text_area(c.etiqueta,max_chars=c.limite,height=115,**args)
        elif c.tipo=='cuenta':
            opciones={p['id']:f"{p['nombre']} · {p['email']}" for p in self.perfiles if p['rol']=='cliente'}
            if valor and valor not in opciones:opciones[valor]='Cuenta vinculada actual (sin conexión)'
            st.selectbox(c.etiqueta,[None,*opciones],format_func=lambda v:opciones.get(v,'Sin cuenta vinculada'),**args)
            if self.v[k] in opciones:st.info('Vinculada a la cuenta de '+opciones[self.v[k]])
        elif c.tipo=='origen':st.selectbox(c.etiqueta,OPCIONES[k],**args)
        else:st.text_input(c.etiqueta,max_chars=c.limite,disabled=k in BLOQUEADOS[self.modo],**args)
        if k in self.b['tocados'] and k in self.errores():
            st.markdown(f'<p class="mfy-field-error" role="alert">{escape(self.errores()[k])}</p>',unsafe_allow_html=True)

    def cabecera(self):
        if self.modo=='cliente' and '_repo_actual' not in st.session_state:
            with st.container(key='mfy_client_bar'):
                logo,a,b=st.columns([1,2,1.5])
                with logo:st.image(str(LOGO),width=90)
                with a:st.write(self.repo.profile.get('nombre','Mi cuenta'))
                with b:
                    from mente_futuro.ui import logout
                    st.button('Cerrar sesión',key='logout',on_click=logout,width='stretch')
        with st.container(key='mfy_public_header'):
            if not self.interno:
                with st.container(key='mfy_public_top'):
                    a,b=st.columns([1,1.3])
                    with a:
                        # La marca vive en la barra superior común; conservar
                        # el hueco de enlaces evita modificar el contenido del formulario.
                        st.empty()
                    with b:self.enlaces=st.empty()
            else:self.enlaces=None
            st.markdown('<div class="mfy-form-heading">'+html_contenido_encabezado('Cuéntanos qué necesita tu equipo',
                'Una propuesta a tu medida comienza aquí.','SOLICITUDES','')+'</div>',unsafe_allow_html=True)

    def progreso(self):
        paso=self.b['step']
        if self.interno:
            key='ff_paso_interno'
            st.session_state[key]=paso
            def navegar():
                self.b['step']=st.session_state.get(key) or paso
            with st.container(key='mfy_steps'):
                st.pills('Pasos de la solicitud',[1,2,3],key=key,on_change=navegar,
                    format_func=lambda n:f'{n} · {PASOS[n-1]}',label_visibility='collapsed')
        etiquetas='' if self.interno else '<div class="mfy-progress-labels">'+''.join(f'<span>{i+1} · {t}</span>' for i,t in enumerate(PASOS))+'</div>'
        st.markdown(f'<div class="mfy-public-progress mfy-progress-{paso}" role="progressbar" aria-label="Avance de la solicitud" aria-valuemin="1" aria-valuemax="3" aria-valuenow="{paso}">'
            +etiquetas+'<div class="mfy-progress-track"><i></i></div></div>',unsafe_allow_html=True)

    def resumen(self):
        datos=servicio.datos_normalizados(self.v,self.modo,self.repo)
        filas=[]
        for k,c in CAMPOS.items():
            if self.modo not in c.modos or c.tipo in ('cuenta','consentimiento','confirmacion') or k=='referido_por' and self.v['origen']!='Referido por colega':continue
            valor=datos.get(k)
            if valor in (None,'',[]):continue
            if k=='fecha_preferida':valor=date.fromisoformat(valor).strftime('%d/%m/%Y')
            if isinstance(valor,list):valor=' · '.join(valor)
            filas.append(f'<div><dt>{escape(c.etiqueta)}</dt><dd>{escape(str(valor))}</dd></div>')
        st.markdown('<div class="mfy-public-summary"><h3>Revisa tu solicitud</h3><dl>'+''.join(filas)+'</dl></div>',unsafe_allow_html=True)

    def contenido(self):
        paso=self.b['step'];titulo_seccion(paso,PASOS[paso-1])
        if paso==1 and self.interno:
            clientes={c['id']:c for c in clientes_existentes(self.casos)}
            if st.session_state.get('solicitud_busqueda') not in clientes:st.session_state.pop('solicitud_busqueda',None)
            st.selectbox('Buscar empresa o cliente existente',list(clientes),index=None,key='solicitud_busqueda',
                placeholder='Escribe una empresa, contacto o correo…',
                format_func=lambda x:f"{clientes[x]['cliente']} · {clientes[x].get('contacto') or ''} · {clientes[x].get('email') or ''}",
                on_change=self.usar_cliente,args=(clientes,),help='Selecciona para precargar. Los datos siguen siendo editables.')
        if paso==1 and not self.interno:st.caption('Si consultas a título personal, puedes dejar Empresa en blanco.')
        for k,c in campos_paso(self.modo,paso).items():
            if c.tipo in ('consentimiento','confirmacion'):continue
            if k=='referido_por' and self.v['origen']!='Referido por colega':continue
            self.campo(k)
            if k=='email' and self.interno:
                sugerencia=sugerir_correo(self.v['email'])
                if sugerencia:
                    st.caption('¿Quisiste decir '+sugerencia+'?')
                    st.button('Usar '+sugerencia,key='corregir_correo',on_click=self.aplicar,args=({'email':sugerencia},))
        if paso==3:
            if self.interno:
                propuestos,fuente=sugerencias(self.v['tematicas'][0] if self.v['tematicas'] else None,self.v['servicio'],self.casos,self.tarifas)
                if propuestos:
                    st.caption('Sugerencia: '+' · '.join(f"{v:g} {'horas' if k=='horas' else 'participantes'}" for k,v in propuestos.items())+f', según {fuente}. Puedes ajustarla.')
                    st.button('Aplicar sugerencia',on_click=self.aplicar,args=(propuestos,))
            self.resumen()
            campo='consentimiento_confirmado' if self.interno else 'consentimiento'
            key=self.prefix+campo
            if self.interno and key not in st.session_state:st.session_state[key]=self.b.get('confirmado',False)
            def confirmar():self.b['confirmado']=bool(st.session_state[key])
            st.checkbox(CAMPOS[campo].etiqueta,key=key,on_change=confirmar if self.interno else None)
            if self.b.get('error_consentimiento') and not st.session_state.get(key):st.error('Debes autorizar el uso de tus datos para enviar la solicitud.')
        if self.interno:
            pendientes=servicio.faltantes(self.v,self.repo)
            if pendientes:st.info('Puedes guardar como Faltan datos. Pendiente: '+', '.join(CAMPOS[k].etiqueta for k in pendientes))
        else:st.text_input('Deja este campo vacío',key=self.prefix+'sitio_confirmacion')
        if self.b.get('error'):st.error(self.b['error'])

    def repetidos(self):
        if not self.interno:return False
        firma=tuple(str(self.v.get(k) or '') for k in ('cliente','email','cliente_id','tematica'))
        if st.session_state.get('solicitud_duplicado_firma')!=firma:
            st.session_state.pop('solicitud_duplicado',None);st.session_state.solicitud_duplicado_firma=firma
        encontrados=[c for c in duplicados(self.v,self.casos) if c['id']!=self.b['id']]
        if encontrados:
            st.warning('¿Es la misma solicitud? Hay un caso abierto del mismo cliente y temática en los últimos 30 días.')
            for c in encontrados[:5]:st.button(f"Abrir {code(c)} · {c.get('cliente') or 'Sin empresa'}",key='duplicado_'+c['id'],on_click=self.abrir,args=(c,False))
            st.checkbox('Crear otra solicitud de todas formas',key='solicitud_duplicado')
        return bool(encontrados)

    def abrir(self,caso,cotizar=False):
        st.session_state.selected_case=caso['id'];st.session_state.pending_navigation='Casos y cotizaciones'
        if cotizar:st.session_state.abrir_cotizacion=caso['id']

    def validar_avance(self,paso):
        fallos=self.errores(paso)
        self.b['tocados']=list(set(self.b['tocados'])|set(campos_paso(self.modo,paso)))
        if fallos:self.b['focus']=dict(field=next(iter(fallos)),id=str(uuid4()));st.rerun()

    def guardar(self,accion,repetidos):
        for paso in (1,2,3):
            fallos=self.errores(paso,completo=accion=='cotizar')
            if fallos:
                self.b['step']=paso;self.validar_avance(paso)
                self.b['error']='Completa los datos pendientes antes de cotizar.';st.rerun()
        consent=self.b.get('confirmado',False) if self.interno else st.session_state.get(self.prefix+'consentimiento',False)
        if not self.interno and not consent:self.b['error_consentimiento']=True;self.b['step']=3;st.rerun()
        continuar=st.session_state.get('solicitud_duplicado',False)
        if repetidos and not continuar:self.b['error']='Revisa la coincidencia o marca Crear otra solicitud de todas formas.';st.rerun()
        try:
            if self.interno and not continuar:
                nuevos=[c for c in duplicados(self.v,self.repo.cases()) if c['id']!=self.b['id']]
                if nuevos:self.b['error']='Apareció una solicitud similar. Revisa la coincidencia antes de crear otra.';st.rerun()
            with st.spinner('Guardando tu solicitud…'):
                resultado=servicio.guardar(self.b,self.modo,self.repo,consent,st.session_state.get(self.prefix+'sitio_confirmacion',''),self.catalogo)
            recibo={**resultado,'borrador':deepcopy(self.b)}
            respaldo.limpiar(self.b,self.modo,self.repo)
            st.session_state.setdefault('formulario_recibos',{})[self.scope]=recibo
            if accion=='otra':st.session_state.formulario_recibos.pop(self.scope,None)
            elif accion=='cotizar':self.abrir(resultado['caso'],True)
            preparar_celebracion('solicitud:'+resultado['codigo'],'¡Solicitud guardada!' if self.interno else '¡Solicitud recibida!')
            st.rerun()
        except ValueError as error:self.b['error']=str(error);st.rerun()
        except Exception:
            self.b['error']='No pudimos confirmar el guardado. Conservamos tu borrador; revisa tu conexión y reintenta sin cambiar los datos.';st.rerun()

    def acciones(self):
        repetidos=self.repetidos()
        with st.container(key='mfy_public_actions'):
            if self.interno:
                if st.button('Guardar',key='ff_guardar',type='primary',width='stretch'):self.guardar('guardar',repetidos)
                a,b=st.columns(2)
                with a:
                    if st.button('Guardar y cotizar ahora',width='stretch'):self.guardar('cotizar',repetidos)
                with b:
                    if st.button('Guardar y registrar otra',width='stretch'):self.guardar('otra',repetidos)
            else:
                a,b=st.columns([1,2])
                with a:
                    if self.b['step']>1 and st.button('Atrás',key=self.prefix+'atras',width='stretch'):
                        self.b['step']-=1;st.rerun()
                with b:
                    if st.button('Enviar solicitud' if self.b['step']==3 else 'Siguiente',key=self.prefix+'siguiente',type='primary',width='stretch'):
                        self.validar_avance(self.b['step'])
                        if self.b['step']<3:self.b['step']+=1;st.rerun()
                        self.guardar('guardar',False)

    def exito(self,recibo):
        respaldo.recuperar(recibo['borrador'],self.modo,self.repo,self.catalogo)
        with st.container(key='mfy_form_publico_success'):
            st.markdown('<div class="mfy-public-success"><svg viewBox="0 0 64 64" role="img" aria-label="Guardado">'
                '<circle cx="32" cy="32" r="29" fill="#E7F5ED"/><path d="m18 33 9 9 19-21" fill="none" stroke="#216342" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                '<h2>¡Solicitud guardada!</h2><p>Tu número es <strong>'+escape(recibo['codigo'])+'</strong>.</p>'
                +('' if self.interno else '<p>Te contactaremos dentro de las próximas <strong>48 horas hábiles</strong>.</p>')+'</div>',unsafe_allow_html=True)
            if self.interno:
                caso=recibo['caso'];falta=caso.get('datos_pendientes') or []
                if falta:st.info('Faltan datos: '+', '.join(CAMPOS['tematicas' if k=='tematica' else k].etiqueta for k in falta))
                st.button('Abrir caso',on_click=self.abrir,args=(caso,False),width='stretch')
                st.button('Cotizar',on_click=self.abrir,args=(caso,True),disabled=bool(falta),width='stretch')
            else:st.button('Enviar solicitud',key=self.prefix+'enviada',disabled=True,width='stretch')
            if st.button('Registrar otra solicitud' if self.interno else 'Enviar otra solicitud',key=self.prefix+'otra',width='stretch'):
                st.session_state.formulario_recibos.pop(self.scope,None);st.rerun()

    def render(self,volver_a_app=False):
        with st.container(key='mfy_formulario_interno' if self.interno else 'mfy_public'):
            self.cabecera()
            recibo=st.session_state.get('formulario_recibos',{}).get(self.scope)
            if recibo:self.exito(recibo)
            else:
                respaldo.recuperar(self.b,self.modo,self.repo,self.catalogo)
                if self.modo=='cliente':self.v.update(contacto=self.repo.profile.get('nombre',''),email=self.repo.user.email or '')
                if self.interno:self.vincular()
                with st.container(key='mfy_form_publico'):
                    self.progreso();self.contenido()
                self.acciones()
                st.caption('El borrador se conserva en esta sesión y, si tu navegador lo permite, en esta pestaña hasta 24 horas. No se envía hasta confirmar.')
            config=configuracion_publica()
            if self.enlaces is not None:self.enlaces.markdown(enlaces_publicos(config),unsafe_allow_html=True)
            if not self.interno:
                privacidad=config.get('politica_privacidad')
                if privacidad:st.markdown(f'<p class="mfy-public-contact"><a href="{escape(privacidad,quote=True)}" target="_blank" rel="noopener noreferrer">Política de privacidad</a></p>',unsafe_allow_html=True)
                correo=config.get('correo_contacto')
                if correo:
                    from urllib.parse import quote
                    st.markdown(f'<p class="mfy-public-contact">También puedes escribirnos a <a href="mailto:{quote(correo,safe="@.")}">{escape(correo)}</a>.</p>',unsafe_allow_html=True)
                if st.button('Volver a la app' if volver_a_app else 'Acceso del equipo y cuentas',key='ff_acceso',type='tertiary',width='stretch'):
                    st.query_params.clear()
                    if volver_a_app:st.session_state.pending_navigation='Hoy'
                    else:st.query_params['vista']='acceso'
                    st.rerun()


def formulario(modo=None,repo=None,*,volver_a_app=False):
    real=servicio.modo_servidor(repo)
    if modo is not None and modo!=real:raise PermissionError('El modo del formulario depende de tu sesión.')
    Formulario(repo).render(volver_a_app=volver_a_app)
