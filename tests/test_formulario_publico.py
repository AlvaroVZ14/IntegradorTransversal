"""Recorrido público aislado, sin cuentas, correos ni escrituras reales."""
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock,patch
from streamlit.testing.v1 import AppTest
from servicios import formulario_publico as servicio
from utils.solicitud_borrador import DEFAULTS
from test_app import ROOT

VACIA=servicio.configuracion_visible({})


class ServicioPublicoTests(TestCase):
    def test_configuracion_whitelist_y_urls_seguras(self):
        datos=servicio.configuracion_visible(dict(sitio_web='empresa.example.test',
            redes={'facebook':'javascript:alert(1)','instagram':'https://social.example.test/perfil','otra':'https://otro.example.test'},
            correo_contacto='contacto@example.test',smtp_password='secreto-ficticio',emisor={'rut':'privado'}))
        self.assertEqual(datos['sitio_web'],'https://empresa.example.test')
        self.assertEqual(datos['redes']['facebook'],'')
        self.assertNotIn('smtp_password',datos);self.assertNotIn('otra',datos['redes'])
        for url in ['//malicioso.example.test','https://user:password@example.test','javascript:alert(1)','https://example.test\nBcc:otro@example.test']:
            self.assertEqual(servicio.url_publica(url),'')
        self.assertEqual(servicio.configuracion_visible(None),VACIA)

    def test_validacion_normaliza_telefono_rut_y_rechaza_consentimiento_y_honeypot(self):
        valores=dict(DEFAULTS,contacto='Camila Ficticia',email='camila@example.test',rut='123456785')
        for telefono in ['912345678','+56912345678','9 1234 5678']:
            datos=servicio.datos_solicitud(dict(valores,telefono=telefono))
            self.assertEqual(datos['telefono'],'+56 9 1234 5678')
            self.assertEqual(datos['rut'],'12.345.678-5')
            self.assertEqual(datos['cliente'],'Camila Ficticia')
        self.assertIn('rut',servicio.errores_paso(dict(valores,rut='12.345.678-9'),1))
        borrador={'id':'ficticio','token':'ficticio','values':valores}
        with patch.object(servicio,'cliente_publico') as cliente:
            for consentimiento,trampa in [(False,''),(True,'robot')]:
                with self.assertRaises(ValueError):servicio.enviar(borrador,consentimiento,trampa)
            cliente.assert_not_called()


class PublicoUITests(TestCase):
    def setUp(self):
        from mente_futuro.domain import SERVICES,TOPICS
        p=patch('paginas.formulario.configuracion_publica',return_value=VACIA);p.start();self.addCleanup(p.stop)
        p=patch('servicios.formulario.catalogo_publico',return_value=dict(servicios=SERVICES,tematicas=TOPICS,version=2,pendiente=False));p.start();self.addCleanup(p.stop)
        self.envio=patch('servicios.formulario.guardar',return_value=dict(codigo='MF-2026-0042',caso=None)).start()
        self.addCleanup(patch.stopall)
        self.app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        self.app.query_params['vista']='solicitud';self.app.run()

    def contacto(self):
        for campo,valor in [('cliente','Empresa Ficticia'),('contacto','Camila Ficticia'),('email','camila@example.test')]:
            self.app.text_input(key='publico_'+campo).set_value(valor)
        self.app.button(key='publico_siguiente').click().run()

    def paso3(self):
        self.contacto();self.app.button(key='publico_siguiente').click().run()

    def borrador(self):return self.app.session_state['formularios']['publico:visitante']

    def test_publico_no_consulta_auth_ni_muestra_menu_y_conserva_al_volver(self):
        self.assertFalse(self.app.sidebar.children);self.assertNotIn('auth_client',self.app.session_state)
        self.contacto()
        self.assertEqual(self.borrador()['step'],2)
        self.assertEqual(self.borrador()['values']['horas'],1.0)
        self.app.button(key='publico_atras').click().run()
        self.assertEqual(self.app.text_input(key='publico_contacto').value,'Camila Ficticia')
        self.assertEqual(self.app.text_input(key='publico_email').value,'camila@example.test')
        self.assertFalse(self.app.exception);self.assertFalse(self.app.error)

    def test_rut_invalido_impide_avanzar_y_envio_sin_consentimiento_no_escribe(self):
        self.app.text_input(key='publico_rut').set_value('12.345.678-9')
        self.contacto()
        self.assertEqual(self.borrador()['step'],1)
        self.assertTrue(any('dígito verificador' in m.value for m in self.app.markdown))
        self.app.text_input(key='publico_rut').set_value('12.345.678-5')
        self.app.button(key='publico_siguiente').click().run()
        self.app.button(key='publico_siguiente').click().run()
        self.app.button(key='publico_siguiente').click().run()
        self.envio.assert_not_called()
        self.assertTrue(self.borrador()['error_consentimiento'])

    def test_envio_confirmado_recibo_sin_datos_privados_y_no_reenvia(self):
        self.paso3()
        self.app.checkbox(key='publico_consentimiento').check()
        self.app.button(key='publico_siguiente').click().run()
        self.envio.assert_called_once()
        self.assertTrue(any('MF-2026-0042' in m.value and '48 horas hábiles' in m.value for m in self.app.markdown))
        self.assertFalse(self.app.text_input);self.assertFalse(self.app.exception)
        self.app.run();self.envio.assert_called_once()

    def test_red_fallida_conserva_borrador_id_y_reintento(self):
        self.envio.side_effect=[ConnectionError('fallo ficticio'),dict(codigo='MF-2026-0042',caso=None)]
        self.paso3();ident=self.borrador()['id']
        self.app.checkbox(key='publico_consentimiento').check()
        self.app.button(key='publico_siguiente').click().run()
        self.assertTrue(self.app.error)
        self.assertEqual(self.borrador()['id'],ident)
        self.assertEqual(self.borrador()['values']['email'],'camila@example.test')
        self.app.button(key='publico_siguiente').click().run()
        self.assertEqual(self.app.session_state['formulario_recibos']['publico:visitante']['codigo'],'MF-2026-0042')
