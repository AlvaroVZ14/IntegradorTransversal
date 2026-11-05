"""Informe privado: dominios, carga bajo demanda, roles y Dashboard intacto."""
import unittest
from unittest.mock import patch
import test_app as base
from servicios.informe_avanzado import validar_url, fecha_sincronizacion

URL = 'https://lookerstudio.google.com/embed/reporting/informe-ficticio-pruebas/page/resumen'


class Informe39Tests(unittest.TestCase):
    setup_app = base.AppTests.setup_app
    assert_clean = base.AppTests.assert_clean

    def test_enlace_privado_validado_sin_peticiones_externas(self):
        self.assertIsNone(validar_url(''))
        self.assertIsNone(validar_url(None))
        self.assertEqual(validar_url(URL)['abrir'], URL.replace('/embed/', '/'))
        for u in ['http://lookerstudio.google.com/embed/reporting/prueba-ficticia',
                  'javascript:alert(1)', 'https://lookerstudio.google.com.ejemplo.test/embed/reporting/prueba-ficticia',
                  'https://usuario:clave@lookerstudio.google.com/embed/reporting/prueba-ficticia',
                  'https://lookerstudio.google.com:443/embed/reporting/prueba-ficticia',
                  'https://lookerstudio.google.com/reporting/prueba-ficticia',
                  URL+'?url=https://ejemplo.test', URL+'#externo', '<iframe src="'+URL+'">', 123]:
            with self.subTest(u=u),self.assertRaises(ValueError):validar_url(u)
        with self.assertRaisesRegex(ValueError, 'Revisa el enlace'):
            validar_url('https://[invalido/embed/reporting/prueba-ficticia')

    def test_hora_de_chile_y_sin_datos(self):
        self.assertIn('05/11/2026 a las 14:00',fecha_sincronizacion('2026-11-05T17:00:00Z'))
        self.assertIn('Aún no hay',fecha_sincronizacion(None))
        self.assertIn('No pudimos',fecha_sincronizacion('incorrecta'))

    def test_sin_url_conserva_dashboard_sin_iframe_ni_pestana(self):
        with patch('servicios.informe_avanzado.leer_informe',return_value=None),patch('paginas.informe_avanzado.iframe') as iframe:
            app,repo=self.setup_app();app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertNotIn('Informe avanzado',[t.label for t in app.tabs]);iframe.assert_not_called()
            self.assertTrue(any(b.label=='Limpiar' for b in app.button))

    def test_iframe_solo_al_abrir_pestana_y_filtros_persisten(self):
        with patch('servicios.informe_avanzado.leer_informe',return_value=validar_url(URL)),patch('paginas.informe_avanzado.iframe') as iframe:
            app,repo=self.setup_app();app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertIn('Informe avanzado',[t.label for t in app.tabs]);iframe.assert_not_called()
            rango=app.session_state['dash_aplicado']
            app.session_state['dashboard_vista']='Informe avanzado';app.run();self.assert_clean(app)
            iframe.assert_called_once_with(URL,height=720,scrolling=True)
            self.assertEqual(app.session_state['dash_aplicado'],rango)
            self.assertFalse(any(b.label=='Limpiar' for b in app.button))
            self.assertTrue(any('Cómo leer este informe' in m.value for m in app.markdown))
            self.assertTrue(any('sincronización' in c.value for c in app.caption))
            app.session_state['dashboard_vista']='Dashboard';app.run();self.assert_clean(app)
            self.assertEqual(app.session_state['dash_aplicado'],rango)
            self.assertTrue(any(b.label=='Limpiar' for b in app.button))
            self.assertEqual(iframe.call_count,1)

    def test_cliente_no_lee_url_ni_carga_informe(self):
        with patch('servicios.informe_avanzado.leer_informe') as leer,patch('paginas.informe_avanzado.iframe') as iframe:
            app,repo=self.setup_app(False);app.query_params['pagina']='Dashboard';app.run();self.assert_clean(app)
            self.assertEqual(app.session_state['navigation'],'Mis documentos')
            leer.assert_not_called();iframe.assert_not_called()

    def test_url_invalida_avisa_y_conserva_tablero(self):
        with patch('servicios.informe_avanzado.leer_informe',side_effect=ValueError('Revisa el enlace del informe.')):
            app,repo=self.setup_app();app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertTrue(any('Revisa el enlace' in w.value for w in app.warning))
            self.assertTrue(any(b.label=='Limpiar' for b in app.button))


if __name__=='__main__':unittest.main()
