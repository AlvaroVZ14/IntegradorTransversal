"""Datos ficticios: enlaces, UI por rol, atribución y archivos QR."""
from copy import deepcopy
from datetime import date
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch,Mock
from urllib.parse import urlsplit,parse_qs
from xml.etree import ElementTree as ET
from PIL import Image
from streamlit.testing.v1 import AppTest
from servicios.compartir import url_base,resolver_url,es_local,enlace_canal,texto_listo,archivos_qr,TEXTOS
from utils.canales import CANALES,normalizar_canal,conteo_canales
from servicios.dashboard import datos_dashboard
from servicios.formulario import guardar
from utils.formulario_config import valores_iniciales
from test_app import ROOT,FakeRepository,menu_visible
from mente_futuro.domain import SERVICES,TOPICS

BASE='https://portal.example.test/'
CAT=dict(servicios=list(SERVICES),tematicas=list(TOPICS),version=3,pendiente=False)

class CompartirTests(TestCase):
    def test_url_de_configuracion_prevalece_sin_parametros_ni_datos_personales(self):
        self.assertEqual(resolver_url({'url_publica':BASE+'?email=privado@example.test#token'},'https://detectado.example.test/compartir'),(BASE,False))
        self.assertEqual(resolver_url({},BASE+'compartir'),(BASE,True))
        self.assertEqual(url_base(BASE+'~/+/compartir'),BASE)
        for url in ['javascript:alert(1)','//portal.example.test','https://user:pass@portal.example.test','https://portal.example.test\nBcc:x','https://portal.example.test:abc','https://portal.example.test\\@evil.example.test']:
            self.assertEqual(url_base(url),'',url)
        self.assertTrue(es_local('http://127.0.0.1:8501/'));self.assertTrue(es_local('http://localhost:8501/'))
        for canal in CANALES:
            link=enlace_canal(BASE,canal)
            self.assertEqual(parse_qs(urlsplit(link).query),{'vista':['solicitud'],'canal':[canal]})
            self.assertNotIn('@',link)
        self.assertEqual(normalizar_canal('hola'),'otro');self.assertEqual(normalizar_canal(None),'otro')
        self.assertEqual(texto_listo('Texto {enlace} {otro}',BASE),'Texto '+BASE+' {otro}')

    def test_png_svg_alta_resolucion_mismos_modulos_y_colores(self):
        png,svg=archivos_qr(enlace_canal(BASE,'qr'))
        im=Image.open(BytesIO(png)).convert('RGB')
        self.assertGreaterEqual(im.width,1000);self.assertEqual(im.width,im.height)
        self.assertEqual(set(im.get_flattened_data()),{(11,37,69),(255,255,255)})
        self.assertEqual(im.getpixel((0,0)),(255,255,255))
        root=ET.fromstring(svg);paths=list(root.iter('{http://www.w3.org/2000/svg}path'))
        self.assertTrue(paths);self.assertTrue(all(p.attrib['fill']=='#0B2545' for p in paths))

    def test_lector_qr_independiente_recupera_los_seis_enlaces(self):
        import sys
        sys.path.insert(0,str(ROOT/'tmp'/'qr-decoder'))
        try:import zxingcpp
        except ImportError:self.skipTest('Lector opcional de QA: instalar zxing-cpp en tmp/qr-decoder.')
        for canal in CANALES:
            enlace=enlace_canal(BASE,canal);png,_=archivos_qr(enlace)
            im=Image.open(BytesIO(png))
            for imagen in (im,im.resize((280,280),Image.Resampling.NEAREST)):
                resultado=zxingcpp.read_barcode(imagen)
                self.assertIsNotNone(resultado,canal);self.assertEqual(resultado.text,enlace)

    def test_serie_canales_respeta_fechas_chile_servicio_tematica_sin_tocar_indicadores(self):
        base=dict(id='1',estado='Solicitud',created_at='2026-03-01T03:30:00Z',servicio=SERVICES[0],tematica=TOPICS[0],canal_captacion='instagram')
        casos=[base,{**base,'id':'2','created_at':'2026-03-02T12:00:00Z','canal_captacion':'facebook'},
            {**base,'id':'3','created_at':'2026-02-28T03:30:00Z'},
            {**base,'id':'4','servicio':SERVICES[1]},
            {**base,'id':'5','tematica':TOPICS[1]},
            {**base,'id':'6','canal_captacion':None}]
        d=datos_dashboard(casos,[],date(2026,3,1),date(2026,3,31),'Mensual',SERVICES[0],TOPICS[0])
        self.assertEqual(d['requests_count'],3)
        ids=set(d['requests'].id)
        self.assertEqual(conteo_canales([c for c in casos if c['id'] in ids]),{'Instagram':1,'Facebook':1,'Sin canal registrado':1})
        self.assertEqual(d['total'],0);self.assertEqual(conteo_canales([]),{})

    def test_guardado_externo_envia_canal_validado_e_interno_no(self):
        repo=FakeRepository(False)
        v=dict(valores_iniciales(),cliente='Empresa ficticia',contacto='Camila Ficticia',email='camila@example.test',servicio=SERVICES[0],tematicas=[TOPICS[0]])
        b=dict(id='ficticio',token='ficticio',values=v,canal_captacion='hola',canal_explicito=True)
        guardar(b,'cliente',repo,True,'',CAT)
        self.assertEqual(repo.case_rows[0]['canal_captacion'],'otro')
        admin=FakeRepository();guardar(b,'interno',admin,False,'',CAT)
        self.assertNotIn('canal_captacion',admin.case_rows[0])
        with self.assertRaises(ValueError):guardar(b,'cliente',repo,True,'',{**CAT,'version':2})

class CompartirUITests(TestCase):
    def setUp(self):
        def elevar(error,*_):raise error
        p=patch('mente_futuro.ui.show_error',side_effect=elevar);p.start();self.addCleanup(p.stop)
        self.repo=FakeRepository(True)
        self.repo.settings_row['datos'].update(url_publica=BASE,compartir={k:'Mensaje ficticio {enlace}' for k in TEXTOS})
        for target,value in [('servicios.repositorio.Repository',self.repo),('servicios.formulario.catalogo_publico',CAT),
            ('paginas.formulario.configuracion_publica',{'redes':{},'sitio_web':'','correo_contacto':'','politica_privacidad':''}),('utils.sesion_cookie.puente_cookie',True),('utils.sesion_cookie.cookie_inicial','')]:
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)

    def app(self,rol=None):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        if rol:
            self.repo.profile['rol']=rol;self.repo.is_owner=rol=='admin'
            app.session_state['auth_client']=self.repo.client
        app.query_params['pagina']='Compartir'
        return app.run()

    def test_admin_ve_seis_canales_qr_textos_y_los_guarda_sin_perder_configuracion(self):
        app=self.app('admin');self.assertFalse(app.exception);self.assertFalse(app.error)
        self.assertIn('Compartir',menu_visible(app));self.assertEqual(app.session_state['navigation'],'Compartir')
        self.assertEqual(len([c for c in app.code if '?vista=solicitud&canal=' in c.value]),11)
        self.assertEqual(len(app.get('download_button')),2)
        # AppTest conserva el hash de la pantalla de inicio: fijarlo como el navegador.
        app.switch_page('paginas/compartir.py')
        app.text_area(key='compartir_texto_whatsapp').set_value('Hola, revisa {enlace}')
        next(b for b in app.button if b.label=='Guardar textos para compartir').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(self.repo.settings_row['datos']['compartir']['whatsapp'],'Hola, revisa {enlace}')
        self.assertIn('emisor',self.repo.settings_row['datos'])

    def test_visitante_y_cliente_no_ven_herramientas_aunque_forcen_la_url(self):
        for rol in (None,'cliente'):
            app=self.app(rol)
            self.assertFalse(app.exception);self.assertFalse(app.error);self.assertFalse(app.get('download_button'))
            self.assertNotIn('Compartir',menu_visible(app))
            self.assertTrue(any(b.label==('Ingresar a mi espacio' if rol is None else 'Siguiente') for b in app.button))

    def test_canal_no_da_privilegios_y_se_conserva_en_los_pasos(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        app.query_params.update(vista='solicitud',canal='instagram',modo='interno');app.run()
        app.text_input(key='publico_contacto').set_value('Camila Ficticia')
        app.text_input(key='publico_email').set_value('camila@example.test')
        app.button(key='publico_siguiente').click().run()
        self.assertEqual(app.session_state['formularios']['publico:visitante']['canal_captacion'],'instagram')
        self.assertEqual(app.session_state['formularios']['publico:visitante']['step'],2)
        self.assertFalse(any(s.label=='Origen de la solicitud' for s in app.selectbox))

    def test_cliente_con_sesion_conserva_canal_al_cambiar_a_ruta_del_formulario(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        self.repo.profile['rol']='cliente';self.repo.is_owner=False
        app.session_state['auth_client']=self.repo.client
        app.query_params.update(vista='solicitud',canal='whatsapp',modo='interno');app.run()
        self.assertFalse(app.exception);self.assertFalse(app.error)
        self.assertEqual(app.session_state['formularios']['publico:visitante']['canal_captacion'],'whatsapp')
        self.assertFalse(app.sidebar.children)
        self.assertFalse(app.text_input(key='publico_contacto').disabled)
