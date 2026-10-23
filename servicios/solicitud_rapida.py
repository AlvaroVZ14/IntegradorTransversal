"""Ayudas de registro. No consulta datos ni concede permisos a clientes."""
from datetime import datetime, timedelta
from statistics import median
import re
from zoneinfo import ZoneInfo

from utils.validaciones import rut_valido, validar_campo

ORIGENES = ['Llamada', 'Correo', 'Reunión', 'Programa propio', 'Referido por colega', 'Formulario web', 'Otro', 'No informado']
TEXTOS = ('cliente','rut','contacto','cargo','email','telefono','lugar','detalle')


def cargar_catalogos(repo):
    """Lectura administrativa por sesión y revisión, 60 s; nunca caché pública."""
    import streamlit as st
    from time import time
    repo.owner_only()
    clave=(repo.user.id,st.session_state.get('dashboard_revision',0))
    catalogo=st.session_state.get('solicitud_catalogos')
    if catalogo and catalogo['clave']==clave and time()-catalogo['fecha']<60:
        return catalogo['datos']
    datos=(repo.profiles(),repo.cases(),repo.tariffs())
    st.session_state.solicitud_catalogos=dict(clave=clave,fecha=time(),datos=datos)
    return datos


def formatear_rut(valor):
    limpio = re.sub(r'[.\s-]', '', str(valor)).upper()
    # No descarta caracteres incorrectos: la validación debe poder detectarlos.
    if not re.fullmatch(r'\d{1,8}[\dK]', limpio):
        return str(valor).upper()
    cuerpo, dv = limpio[:-1], limpio[-1]
    return f"{int(cuerpo):,}".replace(',', '.') + '-' + dv


def normalizar_telefono(valor):
    texto = str(valor or '').strip()
    if not re.fullmatch(r'[+\d\s().-]*', texto):
        return texto
    digitos = re.sub(r'\D', '', texto)
    if len(digitos) == 9 and digitos.startswith('9'):
        digitos = '56' + digitos
    if len(digitos) == 11 and digitos.startswith('569'):
        return f'+56 9 {digitos[3:7]} {digitos[7:]}'
    return texto  # Conserva también números fijos e internacionales válidos.


def sugerir_correo(valor):
    nombre, sep, dominio = str(valor).strip().rpartition('@')
    correcciones = {'gmial.com':'gmail.com','gmal.com':'gmail.com','gmail.con':'gmail.com',
                    'hotmial.com':'hotmail.com','outlok.com':'outlook.com'}
    return nombre + '@' + correcciones[dominio.lower()] if sep and dominio.lower() in correcciones else None


def cuenta_por_correo(correo, perfiles, casos=()):
    coincidencias = [p for p in perfiles if p.get('rol') == 'cliente' and
                    p.get('email','').strip().casefold() == correo.strip().casefold() and correo.strip()]
    if coincidencias:return coincidencias[0] if len(coincidencias)==1 else None
    # Un cliente registrado puede conservar un correo de contacto diferente del
    # de Auth. Reutiliza solo una vinculación previa inequívoca y aún válida.
    ids={c.get('cliente_id') for c in casos if correo.strip() and
         c.get('email','').strip().casefold()==correo.strip().casefold() and c.get('cliente_id')}
    candidatos=[p for p in perfiles if p.get('rol')=='cliente' and p['id'] in ids]
    return candidatos[0] if len(ids)==1 and len(candidatos)==1 else None


def clientes_existentes(casos):
    """No hay tabla de empresas: usa el caso más reciente por empresa y correo."""
    encontrados = {}
    for caso in sorted(casos, key=lambda c:c.get('created_at',''), reverse=True):
        identidad = (caso.get('cliente','').strip().casefold(), caso.get('email','').strip().casefold())
        if identidad[0]:
            encontrados.setdefault(identidad, caso)
    return list(encontrados.values())


def sugerencias(tematica, servicio, casos, tarifas):
    similares = [c for c in casos if c.get('tematica') == tematica and c.get('servicio') == servicio and c.get('estado') != 'Cancelado']
    fuente = 'casos anteriores de esta temática y servicio'
    if not similares:
        similares = [t for t in tarifas if t.get('activa',True) and t.get('servicio') == servicio]
        fuente = 'tarifas activas de este servicio (sin temática en el esquema)'
    valores = {}
    for campo in ('horas','participantes'):
        numeros = [float(c[campo]) for c in similares if c.get(campo) is not None and not validar_campo(campo,c[campo])]
        if numeros:
            valor = median(numeros)
            valores[campo] = max(.5,round(valor*2)/2) if campo == 'horas' else int(round(valor))
    return valores, fuente


def duplicados(datos, casos, ahora=None):
    ahora = ahora or datetime.now(ZoneInfo('America/Santiago'))
    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=ZoneInfo('America/Santiago'))
    limite = ahora-timedelta(days=30)
    resultado = []
    for caso in casos:
        if caso.get('estado') in ('Finalizado','Cancelado') or caso.get('tematica') != datos.get('tematica'):
            continue
        try:
            fecha = datetime.fromisoformat(caso['created_at'].replace('Z','+00:00'))
            if fecha.tzinfo is None: fecha=fecha.replace(tzinfo=ZoneInfo('America/Santiago'))
        except (KeyError,ValueError,TypeError):
            continue
        mismo = (bool(datos.get('cliente_id')) and datos['cliente_id'] == caso.get('cliente_id')) or (
            bool(datos.get('email','').strip()) and datos['email'].strip().casefold() == caso.get('email','').strip().casefold()) or (
            bool(datos.get('cliente','').strip()) and datos['cliente'].strip().casefold() == caso.get('cliente','').strip().casefold())
        if mismo and limite <= fecha <= ahora:
            resultado.append(caso)
    return resultado


def errores_adicionales(datos):
    errores = []
    if datos.get('rut') and not rut_valido(datos['rut']):
        errores.append('Revisa el RUT y su dígito verificador.')
    telefono = validar_campo('telefono', datos.get('telefono',''))
    if telefono: errores.append(telefono)
    if len(datos.get('cargo','')) > 160: errores.append('El cargo admite hasta 160 caracteres.')
    return errores
