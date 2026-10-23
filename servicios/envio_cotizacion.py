"""Envío explícito con TLS y reserva persistida para evitar reenvíos automáticos."""
from email.message import EmailMessage
from email.utils import formatdate,make_msgid
import re
import smtplib
import ssl

from mente_futuro.domain import code
from servicios.cotizacion_asistida import mensaje_cliente


def enlace_whatsapp(telefono,texto):
    from urllib.parse import quote
    from servicios.solicitud_rapida import normalizar_telefono
    numero=re.sub(r'\D','',normalizar_telefono(telefono))
    if not 10<=len(numero)<=15:return None
    return f'https://wa.me/{numero}?text={quote(texto)}'


def enviar_correo(repo,cotizacion,operation_id,destinatario,asunto,cuerpo,adjuntos,settings,confirmado=False):
    repo.owner_only()
    if not confirmado:raise PermissionError('Confirma el envío antes de continuar.')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',destinatario) or any('\n' in s or '\r' in s for s in (destinatario,asunto)):
        raise ValueError('Revisa destinatario y asunto.')
    if not adjuntos:raise ValueError('Selecciona al menos un adjunto.')
    if not all(settings.get(k) for k in ('host','usuario','password','remitente')):raise ValueError('Configura SMTP en st.secrets antes de enviar.')
    if sum(len(b) for _,b,_ in adjuntos)>15_000_000:raise ValueError('Los adjuntos superan 15 MB.')
    mensaje=EmailMessage();mensaje['From']=settings['remitente'];mensaje['To']=destinatario;mensaje['Subject']=asunto
    mensaje['Date']=formatdate(localtime=True);mensaje['Message-ID']=make_msgid()
    mensaje.set_content(cuerpo)
    for nombre,contenido,mime in adjuntos:
        principal,subtipo=mime.split('/',1)
        mensaje.add_attachment(contenido,maintype=principal,subtype=subtipo,filename=nombre)
    reserva=repo.prepare_quote_send(cotizacion['id'],operation_id,'correo',destinatario)
    if not reserva['nuevo']:
        if reserva['envio']['estado']=='enviado':return 'enviado'
        raise ValueError('Este intento ya comenzó. Revisa el correo antes de preparar otro envío; no se reenvió automáticamente.')
    try:
        contexto=ssl.create_default_context()
        puerto=int(settings.get('puerto',465 if settings.get('ssl',False) else 587))
        conexion=smtplib.SMTP_SSL(settings['host'],puerto,context=contexto,timeout=20) if settings.get('ssl',False) else smtplib.SMTP(settings['host'],puerto,timeout=20)
        with conexion as smtp:
            if not settings.get('ssl',False):smtp.ehlo();smtp.starttls(context=contexto);smtp.ehlo()
            smtp.login(settings['usuario'],settings['password'])
            rechazados=smtp.send_message(mensaje)
            if rechazados:raise smtplib.SMTPRecipientsRefused(rechazados)
    except Exception:
        try:repo.confirm_quote_send(operation_id,'incierto')
        except Exception:pass
        raise ValueError('No pudimos confirmar el envío. Revisa tu correo antes de intentar de nuevo; no se reenvió automáticamente.') from None
    try:
        repo.confirm_quote_send(operation_id,'enviado')
        return 'enviado'
    except Exception:
        return 'aceptado_smtp_sin_registro'
