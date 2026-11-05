"""Catálogo único de imágenes de interfaz; no modifica recursos de documentos."""
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
LOGO_DOCUMENTOS = ASSETS / 'logo-mente-y-futuro.jpeg'
LOGO_PORTAL = ASSETS / 'marca-portal.svg'
ICONO_PORTAL = ASSETS / 'marca-icono.svg'
ILUSTRACIONES = {nombre:ASSETS / ('ilustracion-'+nombre+'.svg')
                for nombre in ('bienvenida','equipo','documentos','listo','vacio')}


@lru_cache(maxsize=16)
def leer_svg(nombre):
    """Solo nombres del catálogo, nunca una ruta aportada por usuarios."""
    ruta = ILUSTRACIONES.get(nombre)
    if ruta is None:
        raise ValueError('Ilustración no disponible.')
    return ruta.read_text(encoding='utf-8')


@lru_cache(maxsize=1)
def leer_icono():
    return ICONO_PORTAL.read_text(encoding='utf-8')
