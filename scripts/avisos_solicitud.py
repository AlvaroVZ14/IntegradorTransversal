"""Worker SMTP de servidor. Sin datos personales en logs, archivos o artefactos."""
from email.message import EmailMessage
from email.utils import formatdate
import os,re,smtplib,ssl,json
from urllib.request import Request,urlopen

def rpc(nombre,datos):
    clave=os.environ['SUPABASE_SERVER_KEY']
    req=Request(os.environ['SUPABASE_URL'].rstrip('/')+'/rest/v1/rpc/'+nombre,
        data=json.dumps(datos).encode(),headers={'apikey':clave,'Authorization':'Bearer '+clave,'Content-Type':'application/json'})
    with urlopen(req,timeout=20) as r:return json.load(r)

def correo_valido(valor):return isinstance(valor,str) and len(valor)<=254 and bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',valor))

def enviar(aviso,settings,conexion=None):
    if not correo_valido(aviso.get('destinatario')) or not correo_valido(settings.get('remitente')):return 'error'
    msg=EmailMessage();msg['From']=settings['remitente'];msg['To']=aviso['destinatario']
    msg['Subject']='Nueva solicitud · '+aviso['codigo'];msg['Date']=formatdate(localtime=False)
    msg['Message-ID']='<solicitud-'+str(aviso['id'])+'@'+settings['remitente'].split('@')[1]+'>'
    msg.set_content('Recibiste una nueva solicitud.\n\n'+'\n'.join(
        label+': '+str(aviso.get(k) or 'Por definir') for k,label in [('codigo','Número'),('cliente','Empresa'),
        ('contacto','Contacto'),('email','Correo'),('telefono','Teléfono'),('servicio','Servicio'),('fecha_preferida','Fecha preferida')])
        +'\n\nAbre Casos y cotizaciones para revisar la solicitud. Este aviso no cambia el estado del caso.')
    enviando=False
    try:
        puerto=int(settings.get('puerto',587));seguro=puerto==465
        conexion=conexion or (smtplib.SMTP_SSL if seguro else smtplib.SMTP)
        opciones={'timeout':20}
        if seguro:opciones['context']=ssl.create_default_context()
        with conexion(settings['host'],puerto,**opciones) as smtp:
            if not seguro:smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
            smtp.login(settings['usuario'],settings['password'])
            enviando=True
            rechazados=smtp.send_message(msg)
            if rechazados:raise smtplib.SMTPRecipientsRefused(rechazados)
        return 'enviado'
    except (smtplib.SMTPRecipientsRefused,smtplib.SMTPSenderRefused,smtplib.SMTPDataError):return 'error'
    except Exception:return 'incierto' if enviando else 'error'

def procesar(settings,api=rpc,mailer=enviar):
    resultados={k:0 for k in ('enviado','error','incierto')}
    for aviso in api('mf_tomar_avisos_solicitud',{}):
        estado=mailer(aviso,settings)
        # Si falla esta confirmación tras SMTP, la reserva se vuelve incierta;
        # no se vuelve a enviar ciegamente tras perder la respuesta.
        api('mf_confirmar_aviso_solicitud',dict(p_id=aviso['id'],p_lease=aviso['lease'],p_estado=estado))
        resultados[estado]+=1
    return resultados

def main():
    requeridos=('SUPABASE_URL','SUPABASE_SERVER_KEY','SMTP_HOST','SMTP_USER','SMTP_PASSWORD','SMTP_FROM')
    if any(not os.environ.get(k) for k in requeridos):raise RuntimeError('Faltan secretos para los avisos.')
    settings=dict(host=os.environ['SMTP_HOST'],puerto=int(os.environ.get('SMTP_PORT') or '587'),
        usuario=os.environ['SMTP_USER'],password=os.environ['SMTP_PASSWORD'],remitente=os.environ['SMTP_FROM'])
    print('Resumen de avisos:',json.dumps(procesar(settings)))

if __name__=='__main__':
    try:main()
    except Exception:
        print('No se completó la revisión de avisos. Revisa la configuración y el estado en Supabase.')
        raise SystemExit(1) from None
