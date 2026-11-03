"""Redes opcionales de una empresa. No consulta sitios externos ni hace marketing."""
import re
from urllib.parse import urlsplit, urlunsplit

REDES = {'instagram': ('Instagram', ':material/photo_camera:'),
         'linkedin': ('LinkedIn', ':material/work:'),
         'facebook': ('Facebook', ':material/groups:'),
         'sitio_web': ('Sitio web', ':material/language:'),
         'otra_red': ('Otra red', ':material/link:')}


def normalizar_red(campo, valor):
    etiqueta = REDES[campo][0]
    def error():
        return ValueError(f'Revisa {etiqueta}: escribe un enlace válido de hasta 200 caracteres' +
                          (' o un usuario de Instagram.' if campo == 'instagram' else '.'))
    if valor is None:
        return ''
    if not isinstance(valor, str) or len(valor) > 200:
        raise error()
    texto = valor.strip()
    if not texto:
        return ''
    if re.search(r'[\x00-\x1f\x7f<>"\\]|%(?:00|0a|0d)', texto, re.I) or re.search(
            r'(?:javascript|vbscript|data|file|blob|about):', texto, re.I):
        raise error()
    if campo == 'instagram' and re.fullmatch(r'@?[a-zA-Z0-9_.]{1,30}', texto):
        usuario = texto.lstrip('@')
        if usuario.startswith('.') or usuario.endswith('.') or '..' in usuario:
            raise error()
        return f'https://www.instagram.com/{usuario}/'
    # Otra red admite texto libre. Solo se convierte en enlace si parece una URL.
    if campo == 'otra_red' and not re.match(r'(?i)^(?:https?://|www\.)', texto) and not re.fullmatch(r'[^\s/]+\.[^\s/]+(?:/[^\s]*)?', texto):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', texto):
            raise error()
        return texto
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', texto) and not re.match(r'(?i)^https?://', texto):
        raise error()
    if not re.match(r'(?i)^https?://', texto):
        texto = 'https://' + texto
    try:
        url = urlsplit(texto)
        host = (url.hostname or '').encode('idna').decode('ascii').lower()
        puerto = url.port
        if puerto is not None and not 1<=puerto<=65535:
            raise error()
        if url.scheme.lower() not in ('http', 'https') or url.username is not None or url.password is not None:
            raise error()
        if '.' not in host or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', p) for p in host.split('.')):
            raise error()
        if re.search(r'\s', texto):
            raise error()
        if campo == 'instagram':
            usuario = url.path.strip('/')
            if host not in ('instagram.com', 'www.instagram.com') or puerto is not None or not re.fullmatch(r'[a-zA-Z0-9_.]{1,30}', usuario) or usuario.startswith('.') or usuario.endswith('.') or '..' in usuario:
                raise error()
            texto = f'https://www.instagram.com/{usuario}/'
        else:
            texto = urlunsplit((url.scheme.lower(), host + (f':{puerto}' if puerto else ''), url.path, url.query, url.fragment))
    except (ValueError, UnicodeError):
        raise error() from None
    if len(texto) > 200:
        raise error()
    return texto


def normalizar_redes(valores):
    return {k: v for k in REDES if (v := normalizar_red(k, valores.get(k, '')))}


def redes_del_caso(caso):
    """Lecturas antiguas o importadas no convierten texto no validado en un enlace."""
    redes = caso.get('redes_sociales') or {}
    resultado = {}
    for campo in REDES:
        try:
            valor = normalizar_red(campo, redes.get(campo, ''))
            if valor:
                resultado[campo] = valor
        except ValueError:
            continue
    return resultado


def precargar_redes(repo, empresa=''):
    """Contrato reutilizable por el futuro perfil (28), con el JWT del cliente."""
    if repo.profile.get('rol') != 'cliente':
        raise PermissionError('Solo una cuenta de cliente consulta sus propias redes.')
    datos = repo.client.rpc('mf_mis_redes_empresa', {'p_empresa': empresa or ''}).execute().data or {}
    return datos
