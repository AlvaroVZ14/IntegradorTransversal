"""Atribución declarada en el enlace; nunca determina identidad ni permisos."""
from collections import Counter

CANALES = {
    'instagram': ('Instagram', ':material/photo_camera:', 'Úsalo en la biografía y en el sticker de enlace de tus historias. En las publicaciones, el enlace no es clicable.'),
    'facebook': ('Facebook', ':material/groups:', 'Pégalo en el botón de tu página o en una publicación.'),
    'whatsapp': ('WhatsApp', ':material/chat:', 'Compártelo en una conversación o en tu estado.'),
    'sitio_web': ('Sitio web', ':material/language:', 'Úsalo en el botón de contacto o de solicitud de tu sitio.'),
    'qr': ('Código QR', ':material/qr_code_2:', 'Imprime este QR en tarjetas, afiches o material de tus actividades.'),
    'directo': ('Directo', ':material/link:', 'Envía este enlace cuando no necesites identificar una red específica.'),
}

def normalizar_canal(valor):
    return valor if isinstance(valor, str) and valor in (*CANALES, 'otro') else 'otro'

def etiqueta_canal(valor):
    if valor is None or valor == '':return 'Sin canal registrado'
    valor = normalizar_canal(valor)
    return CANALES[valor][0] if valor in CANALES else 'Otro'

def conteo_canales(casos):
    return dict(Counter(etiqueta_canal(c.get('canal_captacion')) for c in casos))
