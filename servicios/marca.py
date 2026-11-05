"""Única fuente de datos públicos de marca para el formulario (sin secretos).

Pendiente de confirmar con la dueña: Facebook, YouTube y LinkedIn.
Mantener sus valores vacíos hasta recibir las URLs oficiales; no son enlaces
de ejemplo ni se deben reemplazar por búsquedas o perfiles supuestos.
"""
from urllib.parse import urlsplit

NOMBRE='Mente y Futuro'
SITIO_WEB='https://menteyfuturo.cl'
CORREO_CONTACTO='contacto@menteyfuturo.cl'
REDES={
    'instagram':'https://www.instagram.com/menteyfuturospa/',
    'facebook':'',  # TODO: confirmar URL oficial de Facebook.
    'youtube':'',   # TODO: confirmar URL oficial de YouTube.
    'linkedin':'',  # TODO: confirmar URL oficial de LinkedIn.
}


def _url_segura(valor):
    """Los enlaces no ejecutan scripts ni incluyen credenciales/rastreadores."""
    if not isinstance(valor,str) or not valor or any(c.isspace() or ord(c)<32 for c in valor):return ''
    try:
        url=urlsplit(valor)
        if url.scheme!='https' or not url.hostname or '.' not in url.hostname or url.username or url.password:return ''
        if url.query or url.fragment:return ''
        return valor
    except ValueError:return ''


def datos_publicos():
    """Sin llamadas de red; devuelve una copia con destinos válidos."""
    return dict(nombre=NOMBRE,sitio_web=_url_segura(SITIO_WEB),correo_contacto=CORREO_CONTACTO,
                redes={red:url for red in ('instagram','facebook','youtube','linkedin')
                       if (url:=_url_segura(REDES.get(red,'')))})


def redes_pendientes():
    return tuple(red for red in ('instagram','facebook','youtube','linkedin') if not _url_segura(REDES.get(red,'')))
