"""Jobs privados, sin imprimir respuestas, claves, correos ni datos de clientes."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from servicios.respaldos import zip_csv

HEADER=b'MFYB1'
MAX_RESPONSE=55*1024*1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def request(url,headers=None,payload=None,max_bytes=MAX_RESPONSE):
    data=None if payload is None else json.dumps(payload).encode()
    req=Request(url,data=data,headers=dict(headers or {},**{'User-Agent':'MenteFuturo-Mantenimiento/1','Content-Type':'application/json'}))
    # No reenviar credenciales a otro host mediante una redirección.
    with build_opener(NoRedirect).open(req,timeout=60) as response:
        body=response.read(max_bytes+1)
        if len(body)>max_bytes:raise ValueError('Respuesta demasiado grande')
        return body


def secret(name):
    value=os.environ.get(name,'').strip()
    if not value:raise ValueError('Falta configurar un secreto de mantenimiento')
    return value


def supabase(path,payload=None):
    url=secret('SUPABASE_URL').rstrip('/')
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.supabase.co') or parsed.path or parsed.username:
        raise ValueError('URL de Supabase inválida')
    key=secret('SUPABASE_SERVER_KEY')
    headers={'apikey':key}
    if not key.startswith('sb_secret_'):headers['Authorization']='Bearer '+key
    return json.loads(request(url+'/rest/v1/'+path,headers,payload) or 'null')


def run_url():
    repo=secret('GITHUB_REPOSITORY');run=secret('GITHUB_RUN_ID')
    if not re.fullmatch(r'[\w.-]+/[\w.-]+',repo) or not run.isdigit():raise ValueError('Ejecución inválida')
    return f'https://github.com/{repo}/actions/runs/{run}'


def registrar(tipo,estado,artifact=None,digest=None):
    supabase('mf_mantenimiento',dict(tipo=tipo,estado=estado,run_url=run_url(),artefacto_id=artifact,sha256=digest))


def comprobar_app(url):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname or not parsed.hostname.endswith('.streamlit.app') or parsed.username or parsed.query or parsed.fragment:
        raise ValueError('URL pública inválida')
    root=url.rstrip('/')
    html=request(root+'/',max_bytes=2*1024*1024).decode('utf-8',errors='replace').lower()
    dormida=('has gone to sleep','get this app back up','app is sleeping','app is in the oven')
    if any(t in html for t in dormida):raise RuntimeError('App dormida')
    if 'streamlit' not in html:raise RuntimeError('Página no reconocida')
    health=request(root+'/_stcore/health',max_bytes=1024).decode().strip().lower()
    if health not in ('ok','healthy'):raise RuntimeError('Salud no confirmada')
    # HTTP + salud no equivalen a completar un formulario con Auth/WebSocket.


def monitor():
    errores=[]
    try:supabase('mf_casos?select=id&limit=1')
    except Exception:errores.append('Supabase')
    try:comprobar_app(secret('APP_URL'))
    except Exception:errores.append('Streamlit')
    try:
        from datetime import datetime,timezone
        rows=supabase('mf_mantenimiento?select=created_at&tipo=eq.respaldo&estado=eq.ok&order=created_at.desc&limit=1')
        if not rows or (datetime.now(timezone.utc)-datetime.fromisoformat(rows[0]['created_at'].replace('Z','+00:00'))).total_seconds()>9*86400:
            errores.append('Respaldo ausente o antiguo')
    except Exception:errores.append('Registro de respaldos')
    try:registrar('monitor','error' if errores else 'ok')
    except Exception:errores.append('Registro del monitor')
    if errores:
        print('Comprobaciones pendientes: '+', '.join(errores))
        raise RuntimeError('Comprobación incompleta')
    print('Consulta, respuesta HTTP, salud y antigüedad del respaldo comprobadas; no garantiza disponibilidad del formulario.')


def clave():
    key=base64.b64decode(secret('BACKUP_ENCRYPTION_KEY'),validate=True)
    if len(key)!=32:raise ValueError('La clave debe representar 32 bytes aleatorios')
    return key


def cifrar(data,key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce=os.urandom(12)
    return HEADER+nonce+AESGCM(key).encrypt(nonce,data,HEADER)


def descifrar(data,key):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not data.startswith(HEADER) or len(data)<33:raise ValueError('Formato cifrado inválido')
    return AESGCM(key).decrypt(data[5:17],data[17:],HEADER)


def respaldar():
    key=clave()  # Validar antes de leer información privada.
    snapshot=supabase('rpc/mf_exportar_respaldo',{})
    data=zip_csv(snapshot)
    encrypted=cifrar(data,key)
    # Verifica el cifrado antes de subir; el ZIP plano solo existe en memoria.
    if descifrar(encrypted,key)!=data:raise RuntimeError('No se verificó el cifrado')
    path=Path('backup-encrypted');path.mkdir(exist_ok=True)
    (path/'respaldo.mfy').write_bytes(encrypted)
    digest=hashlib.sha256(encrypted).hexdigest()
    output=secret('GITHUB_OUTPUT')
    with open(output,'a',encoding='utf-8') as stream:stream.write('sha256='+digest+'\n')
    print('Respaldo comercial completo verificado y cifrado. Pendiente de confirmar almacenamiento.')


def avisar(tipo,fallo):
    """Una issue por tipo; no incluir excepciones técnicas ni datos privados."""
    repo=secret('GITHUB_REPOSITORY');url=run_url()
    headers={'Authorization':'Bearer '+secret('GH_TOKEN'),'Accept':'application/vnd.github+json'}
    api='https://api.github.com/repos/'+repo+'/issues'
    title='[Mantenimiento] Revisar '+tipo
    issues=json.loads(request(api+'?state=open&per_page=100',headers))
    current=next((i for i in issues if i.get('title')==title and 'pull_request' not in i),None)
    if fallo:
        body='Una comprobación automática requiere atención. Revisa esta ejecución privada: '+url+'\nGuía: docs/mantenimiento.md. No compartas claves ni datos de clientes.'
        if current:request(api+'/'+str(current['number'])+'/comments',headers,{'body':body})
        else:request(api,headers,{'title':title,'body':body})
    elif current:
        # Cerrar la alerta existente solo después de una ejecución correcta.
        request(api+'/'+str(current['number'])+'/comments',headers,{'body':'Comprobación recuperada: '+url})
        req=Request(api+'/'+str(current['number']),data=json.dumps({'state':'closed'}).encode(),headers=dict(headers,**{'Content-Type':'application/json'}),method='PATCH')
        with build_opener(NoRedirect).open(req,timeout=30) as response:response.read(1024)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['monitor','backup','confirm','failure','issue','decrypt'])
    parser.add_argument('--kind',choices=['monitor','respaldo'],default='monitor')
    parser.add_argument('--failed',action='store_true')
    parser.add_argument('--artifact');parser.add_argument('--sha256')
    parser.add_argument('--input');parser.add_argument('--output')
    args=parser.parse_args()
    try:
        if args.action=='monitor':monitor()
        elif args.action=='backup':respaldar()
        elif args.action=='confirm':
            if not args.artifact or not args.artifact.isdigit() or not re.fullmatch('[a-f0-9]{64}',args.sha256 or ''):raise ValueError('Artefacto no confirmado')
            registrar('respaldo','ok',args.artifact,args.sha256)
        elif args.action=='failure':registrar(args.kind,'error')
        elif args.action=='issue':avisar(args.kind,args.failed)
        elif args.action=='decrypt':
            # No sobrescribir una copia existente. No usa Supabase ni GitHub.
            data=descifrar(Path(args.input).read_bytes(),clave())
            with open(args.output,'xb') as stream:stream.write(data)
            print('ZIP recuperado. Mantén este archivo en un lugar privado.')
    except Exception as error:
        # Nunca imprimir el cuerpo HTTP o el mensaje de una librería: podría
        # contener datos, cabeceras o URLs con credenciales.
        print('Mantenimiento no completado ('+type(error).__name__+'). Revisa secretos, disponibilidad y docs/mantenimiento.md.',file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
