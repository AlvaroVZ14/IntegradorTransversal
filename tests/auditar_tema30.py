from pathlib import Path
import sys,json,time,unittest
from unittest.mock import Mock
sys.path[:0]=[str(Path.cwd()),str(Path.cwd()/'tests')]
import streamlit
import test_app as base
from utils.estilos import ESTILOS_BASE,CSS_COPIAR,CSS_EN_VIVO
from mente_futuro.presentation import LOGO,FAVICON

resultados=[]
for rol,pagina in [('admin',p) for p in ('Hoy','Nueva solicitud','Casos y cotizaciones','Compartir','Dashboard')]+[('cliente','Solicitar servicio'),('cliente','Mis documentos'),('publico','Formulario'),('publico','Login')]:
    prueba=base.AppTests()
    app,repo=prueba.setup_app(rol=='admin')
    contadores={}
    for nombre in ('live_snapshot','profiles','tariffs','cases','sales','quote_settings','templates','sharing_settings'):
        if hasattr(repo,nombre):
            m=Mock(wraps=getattr(repo,nombre));setattr(repo,nombre,m);contadores[nombre]=m
    repo.client.rpc=Mock(wraps=repo.client.rpc)
    repo.client.execute=Mock(wraps=repo.client.execute)
    if rol=='publico':
        app=base.AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=30)
        app.query_params['vista']='solicitud' if pagina=='Formulario' else 'acceso'
    t=time.perf_counter();app.run()
    if rol!='publico' and pagina!=app.session_state['navigation']:base.ir_a(app,pagina)
    primera=time.perf_counter()-t
    for m in contadores.values():m.reset_mock()
    repo.client.rpc.reset_mock();repo.client.execute.reset_mock()
    t=time.perf_counter();app.run();repetida=time.perf_counter()-t
    resultados.append(dict(rol=rol,pagina=pagina,primera_s=round(primera,3),repetida_s=round(repetida,3),
        llamadas_repo={k:v.call_count for k,v in contadores.items() if v.call_count},
        rpc_cliente=repo.client.rpc.call_count,lectura_perfil=repo.client.execute.call_count,
        errores=[x.message for x in app.exception]+[x.value for x in app.error],
        css_emitido_bytes=sum(len(m.value.encode()) for m in app.markdown if '<style' in m.value)))
    prueba.doCleanups()
salida=dict(streamlit=streamlit.__version__,css_bytes=len(ESTILOS_BASE.encode()),
    componentes_css_bytes=len(CSS_COPIAR.encode())+len(CSS_EN_VIVO.encode()),
    logo_bytes=LOGO.stat().st_size,favicon_bytes=FAVICON.stat().st_size,pantallas=resultados,
    metodologia='AppTest local, repositorio simulado. No mide red, SQL interno ni tiempo del navegador; primera incluye marco y navegación. Caché calentado al repetir.')
p=Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(salida,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(salida,ensure_ascii=False,indent=2))
