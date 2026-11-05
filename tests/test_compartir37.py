"""Canales cortos, resumen y rutas públicas con datos ficticios."""
from datetime import date
from io import BytesIO
from urllib.parse import parse_qs,urlsplit
from unittest import TestCase
from unittest.mock import patch
from PIL import Image
from streamlit.testing.v1 import AppTest
import test_app as base
from utils.canales import CODIGOS,canal_entrada
from servicios.compartir import enlace_canal,enlaces_compartir,resumen_canales,archivos_qr

BASE='https://portal.example.test/'

class Compartir37Tests(TestCase):
    def test_enlaces_por_canal_y_destinos_compartir(self):
        for codigo,canal in CODIGOS.items():
            enlace=enlace_canal(BASE,canal)
            query=parse_qs(urlsplit(enlace).query)
            self.assertEqual(query,{'vista':['solicitud'],'c':[codigo]})
            self.assertEqual(canal_entrada({'c':codigo}),canal)
        self.assertEqual(canal_entrada({}),'directo')
        self.assertEqual(canal_entrada({'c':'hola','canal':'instagram'}),'directo')
        self.assertEqual(canal_entrada({'canal':'facebook'}),'facebook')
        destinos=enlaces_compartir(BASE)
        for canal,campo in [('facebook','u'),('linkedin','url')]:
            self.assertEqual(parse_qs(urlsplit(destinos[canal]).query)[campo],[enlace_canal(BASE,canal)])
        self.assertIn(enlace_canal(BASE,'whatsapp'),parse_qs(urlsplit(destinos['whatsapp']).query)['text'][0])
        self.assertIn(enlace_canal(BASE,'correo'),parse_qs(urlsplit(destinos['correo']).query)['body'][0])
        self.assertEqual(destinos['instagram'],enlace_canal(BASE,'instagram'))

    def test_resumen_90_dias_inclusivo_y_hora_chile(self):
        casos=[dict(created_at=f,canal_captacion=c) for f,c in [('2026-11-05T12:00:00Z','instagram'),
            ('2026-08-08T12:00:00Z','qr'),('2026-08-07T12:00:00Z','facebook'),
            ('2026-11-06T12:00:00Z','whatsapp'),('2026-11-05T12:00:00Z',None)]]
        self.assertEqual(resumen_canales(casos,date(2026,11,5)),{'Instagram':1,'Código QR':1})

    def test_qr_160_pixeles_y_cache(self):
        import sys
        sys.path.insert(0,str(base.ROOT/'tmp'/'qr-decoder'))
        import zxingcpp
        for canal in ('qr','directo'):
            enlace=enlace_canal(BASE,canal)
            png,svg=archivos_qr(enlace)
            self.assertEqual((png,svg),archivos_qr(enlace))
            imagen=Image.open(BytesIO(png)).resize((160,160),Image.Resampling.NEAREST)
            self.assertEqual(zxingcpp.read_barcode(imagen).text,enlace)


class Entrada37Tests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_dashboard_muestra_canales_solo_en_el_rango_elegido(self):
        app,repo=self.setup_app();app.run();base.AppTests.create_request(self,app)
        repo.case_rows[0]['canal_captacion']='instagram'
        app.session_state['dashboard_revision']=100
        base.ir_a(app,'Dashboard');self.assert_clean(app)
        self.assertTrue(any('Solicitudes por canal' in m.value for m in app.subheader))
        repo.case_rows[0]['created_at']='2000-01-01T12:00:00Z'
        app.session_state['dashboard_revision']=101
        app.run();self.assert_clean(app)
        self.assertFalse(any('Solicitudes por canal' in m.value for m in app.subheader))

    def test_todos_los_codigos_abren_formulario_sin_login_y_persisten(self):
        self.setup_app() # Activa repositorios y catálogos ficticios.
        for codigo,canal in [*CODIGOS.items(),('hola','directo'),(None,'directo')]:
            with self.subTest(codigo=codigo):
                app=AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
                if codigo is not None:app.query_params['c']=codigo
                else:app.query_params['vista']='solicitud'
                app.run();self.assert_clean(app)
                borrador=app.session_state['formularios']['publico:visitante']
                self.assertEqual(borrador['canal_captacion'],canal)
                self.assertFalse(any(b.label=='Ingresar a mi espacio' for b in app.button))
                app.text_input(key='publico_contacto').set_value('Contacto Ficticio')
                app.text_input(key='publico_email').set_value('persona@example.test')
                app.button(key='publico_siguiente').click().run()
                self.assertEqual(app.session_state['formularios']['publico:visitante']['canal_captacion'],canal)
                app.run();self.assert_clean(app)
                self.assertEqual(app.session_state['formularios']['publico:visitante']['canal_captacion'],canal)
                self.assertNotIn('auth_client',app.session_state)
