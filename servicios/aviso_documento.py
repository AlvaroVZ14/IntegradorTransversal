"""Aviso explícito al subir: sin adjuntos, archivos, enlaces firmados ni datos del caso."""
from email.message import EmailMessage
from email.utils import formatdate,make_msgid
import re
from servicios.envio_cotizacion import entregar_mensaje


def avisar_documento(documentos,documento,settings,destinatario):
    documentos.repo.owner_only()
    if not documento['visible_cliente'] or documento['estado_archivo']!='disponible':return 'no_solicitado'
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',destinatario or '') or any(c in destinatario for c in '\r\n'):return 'fallido'
    if not documentos.reservar_aviso(documento['id']):return 'ya_reservado'
    try:
        mensaje=EmailMessage();mensaje['From']=settings.get('remitente','');mensaje['To']=destinatario
        mensaje['Subject']='Tienes un nuevo documento en Mente y Futuro'
        mensaje['Date']=formatdate(localtime=True);mensaje['Message-ID']=make_msgid()
        mensaje.set_content('Hola,\n\nTienes un nuevo documento en Mente y Futuro.\n\nMente y Futuro')
        entregar_mensaje(mensaje,settings)
    except Exception:
        # SMTP puede aceptar un mensaje y perderse su respuesta. No reenviar a ciegas.
        try:documentos.resultado_aviso(documento['id'],'incierto')
        except Exception:pass
        return 'incierto'
    try:documentos.resultado_aviso(documento['id'],'enviado')
    except Exception:return 'enviado_sin_registro'
    return 'enviado'


def avisar_socia(documentos, documento_id, settings):
    """Un aviso genérico al correo de contacto guardado; nunca al que el cliente elija."""
    try:
        reserva = documentos.reservar_aviso_socia(documento_id)
        if not reserva:
            return 'ya_reservado'
        destinatario = reserva.get('correo', '')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', destinatario) or any(c in destinatario for c in '\r\n'):
            documentos.resultado_aviso_socia(documento_id, 'fallido')
            return 'fallido'
        mensaje = EmailMessage()
        mensaje['From'] = settings.get('remitente', '')
        mensaje['To'] = destinatario
        mensaje['Subject'] = 'Tienes un nuevo documento en Mente y Futuro'
        mensaje['Date'] = formatdate(localtime=True)
        mensaje['Message-ID'] = make_msgid()
        mensaje.set_content('Hola,\n\nRecibiste un nuevo documento en Mente y Futuro. Ingresa a la aplicación para revisarlo.\n')
        entregar_mensaje(mensaje, settings)
    except Exception:
        try:documentos.resultado_aviso_socia(documento_id, 'incierto')
        except Exception:pass
        return 'incierto'
    try:documentos.resultado_aviso_socia(documento_id, 'enviado')
    except Exception:return 'enviado_sin_registro'
    return 'enviado'
