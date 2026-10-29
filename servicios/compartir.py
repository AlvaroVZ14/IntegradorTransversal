"""Enlaces públicos y QR locales. No hace peticiones a sitios externos."""
from io import BytesIO
from urllib.parse import urlsplit, urlunsplit, urlencode
from xml.etree import ElementTree as ET
import ipaddress
import streamlit as st
from utils.canales import CANALES, normalizar_canal

TEXTOS = {
    'instagram_biografia': ('Instagram · Biografía', 'instagram'),
    'instagram_publicacion': ('Instagram · Publicación', 'instagram'),
    'facebook': ('Facebook', 'facebook'),
    'whatsapp': ('WhatsApp', 'whatsapp'),
    'sitio_web': ('Sitio web', 'sitio_web'),
}

def url_base(valor):
    """Acepta solo una URL absoluta, sin credenciales, parámetros ni fragmentos."""
    if not isinstance(valor,str) or len(valor)>2048 or any(ord(c)<33 for c in valor.strip()):return ''
    try:
        p=urlsplit(valor.strip())
        if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:return ''
        p.port  # Valida también un puerto mal escrito.
        if any(c in p.netloc for c in ('\\','%','<','>','"',"'")):return ''
        camino=p.path.split('/~/')[0].rstrip('/')
        from utils.navegacion_portal import PAGINAS
        if camino.rsplit('/',1)[-1] in {v[1] for v in PAGINAS.values()}:camino=camino.rsplit('/',1)[0]
        return urlunsplit((p.scheme,p.netloc,camino+'/' if camino else '/', '', ''))
    except (ValueError,TypeError):return ''

def es_local(url):
    host=urlsplit(url).hostname or ''
    if host in ('localhost','localhost.localdomain') or host.endswith('.local'):return True
    try:return not ipaddress.ip_address(host).is_global
    except ValueError:return '.' not in host

def resolver_url(datos,detectada=''):
    configurada=url_base(datos.get('url_publica'))
    if configurada:return configurada,False
    return url_base(detectada),True

def url_detectada():
    try:return st.context.url
    except Exception:return ''

def enlace_canal(base,canal):
    base=url_base(base)
    if not base:raise ValueError('Configura primero la URL pública de la aplicación.')
    return base+'?'+urlencode({'vista':'solicitud','canal':normalizar_canal(canal)})

def texto_listo(plantilla,enlace):
    # No interpreta llaves de otros formatos ni evalúa expresiones.
    return plantilla.replace('{enlace}',enlace) if isinstance(plantilla,str) else ''

@st.cache_data(ttl=600,max_entries=24,show_spinner=False)
def archivos_qr(enlace):
    import qrcode
    from qrcode.image.svg import SvgPathFillImage
    if not isinstance(enlace,str) or len(enlace)>2048:raise ValueError('El enlace es demasiado largo para generar el QR.')
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=24,border=4)
    qr.add_data(enlace);qr.make(fit=True)
    png=BytesIO()
    qr.make_image(fill_color='#0B2545',back_color='white').save(png,format='PNG',dpi=(300,300))
    raiz=ET.fromstring(qr.make_image(image_factory=SvgPathFillImage).to_string())
    for path in raiz.iter('{http://www.w3.org/2000/svg}path'):path.set('fill','#0B2545')
    return png.getvalue(),ET.tostring(raiz,encoding='utf-8',xml_declaration=True)
