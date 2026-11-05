"""Redes públicas de marca: datos ficticios, sin enviar solicitudes reales."""
from unittest import TestCase
from unittest.mock import patch
from xml.etree import ElementTree as ET
from streamlit.testing.v1 import AppTest
import test_app as base
from servicios import marca
from ui.tema import redes_marca

REDES={red:'https://social.example.test/'+red for red in ('instagram','facebook','youtube','linkedin')}


class MarcaTests(TestCase):
    def test_sin_url_no_hay_icono_y_no_se_ejecutan_esquemas_peligrosos(self):
        with patch.object(marca,'REDES',{**REDES,'facebook':'','youtube':'javascript:alert(1)','linkedin':'https://user:password@social.example.test/'}):
            datos=marca.datos_publicos()
            self.assertEqual(list(datos['redes']),['instagram'])
            self.assertEqual(marca.redes_pendientes(),('facebook','youtube','linkedin'))
            raiz=ET.fromstring(redes_marca(datos))
            self.assertEqual(len(raiz.findall('.//svg')),1)
            self.assertNotIn('javascript:',ET.tostring(raiz,encoding='unicode'))

    def test_cuatro_enlaces_accesibles_inline_y_sin_contenido_remoto(self):
        with patch.object(marca,'REDES',REDES),patch.object(marca,'NOMBRE','Consultora Ficticia'):
            datos=marca.datos_publicos()
        for lugar in ('encabezado','pie','confirmacion'):
            html=redes_marca(datos,ubicacion=lugar)
            raiz=ET.fromstring(html)
            enlaces=raiz.findall('.//a')
            self.assertEqual(len(enlaces),4)
            self.assertEqual({a.get('href') for a in enlaces},set(REDES.values()))
            for a in enlaces:
                self.assertEqual(a.get('target'),'_blank')
                self.assertEqual(a.get('rel'),'noopener noreferrer')
                self.assertIn('Consultora Ficticia',a.get('aria-label'))
                self.assertEqual(a.get('aria-label'),a.get('title'))
                self.assertIsNotNone(a.find('svg'))
            for prohibido in ('<script','<iframe','<img','<image','<use','src=','@import','url('):
                self.assertNotIn(prohibido,html)
        self.assertEqual(redes_marca({'nombre':'Ficticia','redes':{}}),'')
        for url in ('http://social.example.test/','https://social.example.test/?tracking=1','https://social.example.test/#rastro','https://social.example.test/\n'):
            self.assertEqual(marca._url_segura(url),'')


class FormularioMarcaTests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def setUp(self):
        for target,valor in [('servicios.marca.NOMBRE','Consultora Ficticia'),
                             ('servicios.marca.SITIO_WEB','https://empresa.example.test/'),
                             ('servicios.marca.CORREO_CONTACTO','contacto@example.test'),
                             ('servicios.marca.REDES',REDES)]:
            parche=patch(target,valor);parche.start();self.addCleanup(parche.stop)

    def lugares(self,app):
        return [lugar for lugar in ('encabezado','pie','confirmacion')
                for m in app.markdown if 'mfy-brand-networks-'+lugar+'"' in m.value]

    def test_publico_tiene_encabezado_pie_y_confirmacion_sin_iniciar_sesion(self):
        app,repo=self.setup_app()
        app=AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
        app.query_params['vista']='solicitud';app.run()
        self.assert_clean(app);self.assertEqual(self.lugares(app),['encabezado','pie'])
        self.assertFalse(app.sidebar.children)
        app.text_input(key='publico_contacto').set_value('Contacto Ficticio')
        app.text_input(key='publico_email').set_value('cliente@example.test')
        app.button(key='publico_siguiente').click().run()
        app.button(key='publico_siguiente').click().run()
        app.checkbox(key='publico_consentimiento').check()
        with patch('servicios.formulario.guardar',return_value={'codigo':'MF-2026-0042','caso':None}):
            app.button(key='publico_siguiente').click().run()
        self.assert_clean(app)
        self.assertEqual(self.lugares(app),['encabezado','pie','confirmacion'])
        self.assertNotIn('auth_client',app.session_state)
        self.assertTrue(any('48 horas hábiles' in m.value for m in app.markdown))

    def test_interno_solo_pie_y_cuenta_cliente_mismos_enlaces(self):
        for owner in (True,False):
            with self.subTest(admin=owner):
                app,repo=self.setup_app(owner);app.run()
                base.ir_a(app,'Nueva solicitud' if owner else 'Solicitar servicio')
                self.assert_clean(app)
                self.assertEqual(self.lugares(app),['pie'] if owner else ['encabezado','pie'])
                html=''.join(m.value for m in app.markdown if 'mfy-brand-networks' in m.value)
                for url in REDES.values():self.assertIn(url,html)
                self.assertTrue(any(e.value=='Redes sociales de la empresa (opcional)' for e in app.subheader))
