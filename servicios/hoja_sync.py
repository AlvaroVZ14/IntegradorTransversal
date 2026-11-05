"""Procesador de informes: único lugar que abre conexiones con secretos.

No se llama desde pantallas de cliente. No escribe en tablas comerciales.
No imprime respuestas, DSN, JSON de Google ni excepciones de proveedores.
"""
from copy import deepcopy
from datetime import date,datetime,timezone
import json
import os
import random
import re
import threading
import time
from uuid import uuid4
from servicios.hoja_columnas import COLUMNAS,CLAVES,FECHAS

_lock=threading.Lock()
_evento=threading.Event()
_trabajador=None
_reconstruir=False
_estado_local={'configurada':False,'aviso':False}

class FalloHoja(RuntimeError):
    def __init__(self):super().__init__('No pudimos actualizar la hoja. Tus datos están a salvo; lo reintentamos solos.')


def configuracion(entorno=None):
    """CLI usa variables; solo Administración puede solicitar secrets de la app."""
    env=os.environ if entorno is None else entorno
    if env.get('HOJA_DATABASE_URL'):
        datos=dict(activada=env.get('HOJA_SYNC_ENABLED','false').lower()=='true',database_url=env.get('HOJA_DATABASE_URL'),
                   id=env.get('HOJA_ID',''),url=env.get('HOJA_URL',''),google=json.loads(env.get('HOJA_GOOGLE_JSON','{}')))
    elif entorno is None:
        import streamlit as st
        try:datos=deepcopy(dict(st.secrets.get('hoja',{})))
        except Exception:datos={}
        if isinstance(datos.get('google'),str):datos['google']=json.loads(datos['google'])
        elif datos.get('google'):datos['google']=dict(datos['google'])
    else:datos={}
    if not datos.get('activada'):return None
    if not datos.get('database_url') or not re.fullmatch(r'[\w-]{10,200}',str(datos.get('id',''))) or not datos.get('google'):
        raise FalloHoja()
    # El enlace visible se deriva del ID; no se publica un destino arbitrario.
    datos['url']='https://docs.google.com/spreadsheets/d/'+datos['id']+'/edit'
    return datos


class BaseReportes:
    def __init__(self,dsn):self.dsn=dsn
    def _consulta(self,sql,args):
        import psycopg
        with psycopg.connect(self.dsn,connect_timeout=8,sslmode='require',prepare_threshold=None) as conn:
            with conn.cursor() as cur:
                cur.execute(sql,args);return cur.fetchone()[0]
    def tomar(self,token,completo=False):return self._consulta('select reportes.tomar(%s,%s)',(str(token),completo))
    def renovar(self,token):
        if not self._consulta('select reportes.renovar(%s)',(str(token),)):raise FalloHoja()
    def finalizar(self,token,error,filas):
        if not self._consulta('select reportes.finalizar(%s,%s,%s::jsonb)',(str(token),error,json.dumps(filas))):raise FalloHoja()


def _celda(valor,columna):
    if valor is None:return ''
    if columna in FECHAS:
        fecha=date.fromisoformat(str(valor)[:10])
        return (fecha-date(1899,12,30)).days
    if isinstance(valor,str):return re.sub(r'\s+',' ',valor).strip()
    if isinstance(valor,(int,float,bool)):return valor
    raise FalloHoja()


def matrices(datos):
    """Falla cerrado si el contrato SQL incluyera una columna nueva/sensible."""
    if set(datos)!=set(CLAVES):raise FalloHoja()
    resultado={}
    for hoja,columnas_clave in CLAVES.items():
        filas=datos[hoja]
        if not isinstance(filas,list) or any(set(f)!=set(COLUMNAS[hoja]) for f in filas):raise FalloHoja()
        vistos=set();tabla=[]
        for fila in filas:
            clave=tuple(str(fila[c]) for c in columnas_clave)
            if clave in vistos:raise FalloHoja()
            vistos.add(clave)
            tabla.append([_celda(fila[c],c) for c in COLUMNAS[hoja]])
        resultado[hoja]=tabla
    return resultado


def fusionar(hoja,existentes,nuevas,codigos,completo=False):
    columnas=COLUMNAS[hoja];ancho=len(columnas)
    if not completo and existentes and tuple(existentes[0])!=columnas:raise FalloHoja()
    guardadas=[] if completo else [list(f)+['']*max(0,ancho-len(f)) for f in existentes[1:] if any(v!='' for v in f)]
    ix=columnas.index('codigo' if hoja=='Casos' else 'codigo_caso')
    guardadas=[f[:ancho] for f in guardadas if str(f[ix]) not in set(codigos)]
    datos={}
    for fila in guardadas+nuevas:
        clave=tuple(str(fila[columnas.index(c)]) for c in CLAVES[hoja])
        datos[clave]=fila
    return [list(columnas)]+[datos[k] for k in sorted(datos)]


def temporal(error):
    respuesta=getattr(error,'response',None)
    codigo=getattr(respuesta,'status_code',None)
    return codigo in (408,429,500,502,503,504) or isinstance(error,(TimeoutError,ConnectionError)) or type(error).__name__ in ('Timeout','ReadTimeout','ConnectTimeout','ConnectionError')


def reintentar(funcion,*,dormir=time.sleep,aleatorio=random.random,intentos=6):
    for intento in range(intentos):
        try:return funcion()
        except Exception as error:
            if not temporal(error) or intento==intentos-1:raise FalloHoja() from None
            # 429 espera el siguiente minuto; los otros fallos usan backoff.
            codigo=getattr(getattr(error,'response',None),'status_code',None)
            dormir(max(60 if codigo==429 else 0,min(2**intento,32))+aleatorio())


class GoogleHoja:
    def __init__(self,config):
        import gspread
        from google.oauth2.service_account import Credentials
        credenciales=Credentials.from_service_account_info(config['google'],scopes=['https://www.googleapis.com/auth/spreadsheets'])
        cliente=gspread.authorize(credenciales)
        cliente.set_timeout(30)
        self.libro=cliente.open_by_key(config['id'])
        self.correo=config['google']['client_email'];self.preparada=False;self.propiedades={}
    def preparar(self):
        from servicios.hoja_formato import preparar
        if not self.preparada:
            self.propiedades=preparar(self.libro,self.correo);self.preparada=True
    def leer(self):
        from servicios.hoja_formato import letra
        respuesta=reintentar(lambda:self.libro.values_batch_get(["'"+h+"'!A:"+letra(len(COLUMNAS[h])) for h in CLAVES],params={'valueRenderOption':'UNFORMATTED_VALUE','dateTimeRenderOption':'SERIAL_NUMBER'}))
        return {h:r.get('values',[]) for h,r in zip(CLAVES,respuesta['valueRanges'])}
    def escribir(self,tablas,anteriores,validar):
        from servicios.hoja_formato import letra
        crecimiento=[]
        for h,t in tablas.items():
            p=self.propiedades[h]
            if len(t)>p['gridProperties']['rowCount']:
                cantidad=((len(t)+999)//1000)*1000
                crecimiento.append({'updateSheetProperties':{'properties':{'sheetId':p['sheetId'],'gridProperties':{'rowCount':cantidad}},'fields':'gridProperties.rowCount'}})
                p['gridProperties']['rowCount']=cantidad
        if crecimiento:validar();reintentar(lambda:self.libro.batch_update({'requests':crecimiento}))
        # Rangos absolutos y RAW: repetir el lote no duplica ni ejecuta fórmulas.
        partes=[]
        for hoja,tabla in tablas.items():
            ancho=len(COLUMNAS[hoja]);alto=max(len(tabla),len(anteriores.get(hoja,[])))
            for inicio in range(0,alto,200):
                filas=[tabla[i] if i<len(tabla) else ['']*ancho for i in range(inicio,min(inicio+200,alto))]
                partes.append({'range':f"'{hoja}'!A{inicio+1}:{letra(ancho)}{inicio+len(filas)}",'values':filas})
        grupo=[];tamano=0
        def enviar(lote):
            def escribir():
                validar();return self.libro.values_batch_update({'valueInputOption':'RAW','data':lote})
            reintentar(escribir)
        for parte in partes:
            peso=len(json.dumps(parte,ensure_ascii=False).encode())
            if grupo and (tamano+peso>900000 or len(grupo)>=8):
                enviar(grupo);time.sleep(1.1);grupo=[];tamano=0
            grupo.append(parte);tamano+=peso
        if grupo:enviar(grupo)
    def registro(self,filas,validar):
        validar()
        respuesta=reintentar(lambda:self.libro.values_get("'Registro'!A2:E501"))
        existentes=respuesta.get('values',[])
        nuevas=(existentes+filas)[-500:]
        nuevas += [['']*5 for _ in range(500-len(nuevas))]
        reintentar(lambda:self.libro.values_update("'Registro'!A2:E501",params={'valueInputOption':'RAW'},body={'values':nuevas}))


def procesar(base,hoja,*,completo=False,token=None):
    token=token or uuid4();lote=base.tomar(token,completo)
    if lote is None:return False
    filas={h:0 for h in CLAVES}
    try:
        base.renovar(token)
        if callable(hoja):hoja=hoja()
        reintentar(hoja.preparar)
        nuevas=matrices(lote['datos'])
        anteriores=hoja.leer()
        tablas={h:fusionar(h,anteriores[h],nuevas[h],lote['codigos'],lote['completo']) for h in CLAVES}
        filas={h:len(t)-1 for h,t in tablas.items()}
        validar=lambda:base.renovar(token)
        hoja.escribir(tablas,anteriores,validar)
        fecha=_celda(datetime.now(timezone.utc).date().isoformat(),'fecha')
        hoja.registro([[fecha,h,filas[h],'Correcto',''] for h in CLAVES],validar)
        base.finalizar(token,None,filas)
        return True
    except Exception:
        try:base.finalizar(token,'error',filas)
        except Exception:pass # Lease expira; la cola permanece pendiente.
        raise FalloHoja() from None


def _ciclo(config):
    global _reconstruir
    base=BaseReportes(config['database_url']);google=None;fallos=0
    while True:
        _evento.wait(20);_evento.clear()
        time.sleep(7) # Junta cambios de edición rápida.
        with _lock:
            completo=_reconstruir;_reconstruir=False
            try:
                def conectar():
                    nonlocal google
                    if google is None:google=GoogleHoja(config)
                    return google
                if procesar(base,conectar,completo=completo):_estado_local['aviso']=False
                elif completo:_reconstruir=True
                fallos=0
            except Exception:
                _estado_local['aviso']=True
                google=None;fallos+=1
                if completo:_reconstruir=True
        if fallos:time.sleep(min(2**min(fallos,8),300))


def avisar(*,admin=False,reconstruir=False):
    """Devuelve al instante: nunca espera al candado, PostgreSQL ni Google."""
    global _trabajador,_reconstruir
    if not admin:return
    if reconstruir:_reconstruir=True
    if _trabajador is not None and _trabajador.is_alive():_evento.set();return
    try:config=configuracion()
    except Exception:_estado_local['aviso']=True;return
    if not config:return
    _estado_local.update(configurada=True,url=config['url'])
    # Protección de arranque separada del candado ocupado durante una escritura.
    with _inicio:
        if _trabajador is None or not _trabajador.is_alive():
            _trabajador=threading.Thread(target=_ciclo,args=(config,),name='mfy-hoja',daemon=True);_trabajador.start()
    _evento.set()

_inicio=threading.Lock()

def estado_local():
    return {k:v for k,v in _estado_local.items() if k in ('configurada','aviso','url')}


def ejecutar_cli(*,preparar=False):
    config=configuracion(os.environ)
    if config is None:raise FalloHoja()
    base=BaseReportes(config['database_url'])
    for intento in range(13):
        if procesar(base,lambda:GoogleHoja(config),completo=True):return True
        if intento<12:time.sleep(10)
    raise FalloHoja()
