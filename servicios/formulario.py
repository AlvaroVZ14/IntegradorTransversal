"""Datos y reglas compartidas del formulario; la identidad no procede del navegador."""
from datetime import date
import streamlit as st
from mente_futuro.domain import SERVICES,TOPICS,today,code
from servicios.repositorio import public_client,fila_rpc
from servicios.solicitud_rapida import formatear_rut,normalizar_telefono
from utils.formulario_config import CAMPOS,OBLIGATORIOS
from utils.validaciones import validar_campo

def modo_servidor(repo):
    if repo is None:return 'publico'
    return 'interno' if repo.profile.get('rol')=='admin' else 'cliente'

@st.cache_data(ttl=60,show_spinner=False)
def catalogo_publico():
    try:
        datos=fila_rpc(public_client(timeout=3).rpc('mf_catalogo_solicitudes',{}).execute().data)
        if not all(isinstance(datos.get(k),list) and all(isinstance(v,str) and 1<=len(v)<=180 for v in datos[k]) for k in ('servicios','tematicas')):
            raise ValueError('Catálogo no válido')
        return {**datos,'pendiente':False}
    except Exception:
        # Compatibilidad temporal con la versión anterior, hasta aplicar el SQL.
        # Estas son las mismas opciones heredadas, no otro catálogo editable.
        return dict(servicios=list(SERVICES),tematicas=list(TOPICS),version=1,pendiente=True)

def datos_normalizados(valores,modo,repo=None):
    datos={k:v.strip() if isinstance(v,str) else v for k,v in valores.items() if k in CAMPOS or k=='tematica'}
    datos.pop('consentimiento',None);datos.pop('consentimiento_confirmado',None)
    datos['rut']=formatear_rut(datos.get('rut',''))
    datos['telefono']=normalizar_telefono(datos.get('telefono',''))
    temas=list(dict.fromkeys(datos.get('tematicas') or []))
    datos['tematicas']=temas;datos['tematica']=temas[0] if temas else None
    if modo=='cliente':
        datos.update(contacto=repo.profile.get('nombre','').strip(),email=repo.user.email or '')
    if modo!='interno':
        for k in ('cliente_id','origen','referido_por'):datos.pop(k,None)
        datos['cliente']=datos.get('cliente') or datos.get('contacto','')
    else:
        for k in ('cliente','contacto','email','servicio','tematica','modalidad'):
            if not datos.get(k):datos[k]=None
    return datos

def errores(valores,modo,repo=None,paso=None,*,completo=False,catalogo=None):
    datos=datos_normalizados(valores,modo,repo)
    resultado={}
    for k,c in CAMPOS.items():
        if modo not in c.modos or (paso and c.paso!=paso) or c.tipo in ('cuenta','consentimiento','confirmacion'):continue
        valor=datos.get(k)
        falta=valor is None or valor=='' or valor==[]
        if k in OBLIGATORIOS and falta:
            if modo!='interno' or completo:resultado[k]='Completa este campo para continuar.'
            continue
        if falta:continue
        if k=='tematicas':
            opciones=(catalogo or {}).get('tematicas',TOPICS)
            if not isinstance(valor,list) or any(t not in opciones for t in valor):resultado[k]='Selecciona temáticas válidas.'
        elif k=='dirigido_a' and len(valor)>1000:resultado[k]='Usa como máximo 1.000 caracteres.'
        elif k=='referido_por' and len(valor)>160:resultado[k]='Usa como máximo 160 caracteres.'
        else:
            error=validar_campo(k,valor)
            if error:resultado[k]=error
        if k=='fecha_preferida' and valor:
            try:
                if date.fromisoformat(str(valor))<today():resultado[k]='Elige una fecha desde hoy en adelante.'
            except (ValueError,TypeError):resultado[k]='Selecciona una fecha válida.'
    return resultado

def faltantes(valores,repo=None):return list(errores(valores,'interno',repo,completo=True))

def guardar(borrador,modo,repo,consentimiento,trampa,catalogo):
    if modo!=modo_servidor(repo):raise PermissionError('Modo de formulario no permitido.')
    fallos=errores(borrador['values'],modo,repo,catalogo=catalogo)
    if fallos:raise ValueError(next(iter(fallos.values())))
    if modo!='interno' and not consentimiento:raise ValueError('Debes autorizar el uso de tus datos para enviar la solicitud.')
    if trampa:raise ValueError('No pudimos confirmar el formulario. Revisa los datos e intenta nuevamente.')
    datos=datos_normalizados(borrador['values'],modo,repo)
    if modo!='interno':
        from utils.canales import normalizar_canal
        if catalogo.get('version',1)>=3:
            datos['canal_captacion']=normalizar_canal(borrador.get('canal_captacion','directo'))
        elif borrador.get('canal_explicito'):
            raise ValueError('Estamos preparando este enlace. Conservamos tu borrador; vuelve a intentarlo más tarde.')
    if modo=='interno':datos['consentimiento_confirmado']=bool(consentimiento)
    else:datos.update(consentimiento=True,honeypot='')
    if catalogo.get('pendiente'):
        # Conserva el registro anterior para casos completos, sin fingir guardar
        # campos nuevos que todavía no existen en la base de datos.
        if datos.get('dirigido_a') or datos.get('referido_por') or len(datos['tematicas'])>1 or (modo=='interno' and (consentimiento or faltantes(borrador['values'],repo))):
            raise ValueError('Activa el SQL del formulario unificado para guardar estos datos. Conservamos tu borrador.' if modo=='interno'
                else 'Estamos preparando esta actualización. Conservamos tu borrador; vuelve a intentarlo más tarde.')
        for k in ('dirigido_a','referido_por','tematicas','honeypot','consentimiento_confirmado'):datos.pop(k,None)
        if modo=='interno':resultado=repo.create_request_legacy(datos,borrador['id'])
        elif modo=='cliente':resultado=repo.create_request(datos,borrador['id'])
        else:
            from servicios.formulario_publico import cliente_publico
            resultado=fila_rpc(cliente_publico().rpc('registrar_solicitud_publica',dict(p_solicitud_id=borrador['id'],p_token=borrador['token'],p_datos=datos,p_honeypot=trampa)).execute().data)
    elif modo=='publico':
        from servicios.formulario_publico import cliente_publico
        resultado=fila_rpc(cliente_publico().rpc('registrar_solicitud_publica',dict(p_solicitud_id=borrador['id'],p_token=borrador['token'],p_datos=datos,p_honeypot=trampa)).execute().data)
    else:resultado=repo.create_request(datos,borrador['id'])
    if not resultado:raise RuntimeError('No se confirmó el guardado.')
    from servicios.dashboard_cache import invalidar_dashboard
    invalidar_dashboard()
    return dict(codigo=code(resultado) if modo=='interno' else resultado['codigo'],caso=resultado if modo=='interno' else None)
