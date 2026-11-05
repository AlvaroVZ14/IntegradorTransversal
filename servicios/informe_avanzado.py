"""Configuración del informe privado, sin consultar sus datos ni sus permisos."""
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


def validar_url(valor):
    if valor is None or valor == '':
        return None
    if not isinstance(valor, str) or len(valor) > 2048 or any(c.isspace() for c in valor):
        raise ValueError('Revisa el enlace de inserción del informe en los secretos de Streamlit.')
    try:
        p = urlsplit(valor)
    except ValueError:
        raise ValueError('Revisa el enlace de inserción del informe en los secretos de Streamlit.') from None
    if (p.scheme != 'https' or p.netloc not in ('lookerstudio.google.com', 'datastudio.google.com')
            or p.query or p.fragment or not re.fullmatch(r'/embed/reporting/[A-Za-z0-9_-]{8,200}(?:/page/[A-Za-z0-9_-]{1,200})?/?', p.path)):
        raise ValueError('Usa la URL de inserción de Looker Studio, copiada desde Insertar informe.')
    return {'embed': valor, 'abrir': valor.replace('/embed/reporting/', '/reporting/', 1)}


def leer_informe():
    import streamlit as st
    try:
        seccion = st.secrets.get('looker', {})
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None
    if not hasattr(seccion, 'get'):
        raise ValueError('Revisa la sección del informe en los secretos de Streamlit.')
    return validar_url(seccion.get('url', ''))


def fecha_sincronizacion(valor):
    if not valor:
        return 'Aún no hay una sincronización confirmada de la hoja.'
    try:
        fecha = datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return 'Última sincronización de la hoja: ' + fecha.astimezone(ZoneInfo('America/Santiago')).strftime('%d/%m/%Y a las %H:%M') + ' · hora de Chile.'
    except (ValueError, TypeError):
        return 'No pudimos comprobar la hora de sincronización de la hoja.'
