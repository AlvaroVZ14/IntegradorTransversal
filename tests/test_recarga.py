"""Reproduce la intención de URL que envía un navegador al recargar."""
import importlib
import json
from pathlib import Path
from time import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock
from streamlit.testing.v1 import AppTest
from streamlit.runtime.pages_manager import PagesManager
from test_app import FakeRepository,menu_visible,TODAS_PAGINAS

ROOT=Path(__file__).resolve().parent.parent
NAV=importlib.import_module('streamlit.commands.navigation')


def recargar(app,ruta):
    original=PagesManager.set_script_intent
    primera=True
    def intent(manager,page_hash,page_name):
        nonlocal primera
        if primera:
            primera=False
            return original(manager,'',ruta)
        return original(manager,page_hash,page_name)
    with patch.object(PagesManager,'set_script_intent',intent),patch.object(NAV,'send_page_not_found',wraps=NAV.send_page_not_found) as dialogo:
        app.run()
        return dialogo.call_count


class RecargaTests(unittest.TestCase):
    def app(self,rol=None):
        repo=FakeRepository(rol!='cliente')
        for target,value in [('servicios.repositorio.Repository',repo),('utils.sesion_cookie.puente_cookie',True),('utils.sesion_cookie.cookie_inicial','')]:
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)
        from mente_futuro.domain import SERVICES,TOPICS
        from servicios.formulario_publico import configuracion_visible
        for target,value in [('servicios.formulario.catalogo_publico',dict(servicios=SERVICES,tematicas=TOPICS,version=2,pendiente=False)),('paginas.formulario.configuracion_publica',configuracion_visible({}))]:
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=25)
        if rol:app.session_state['auth_client']=repo.client
        return app,repo

    def test_reproduce_old_registration_failure(self):
        app=AppTest.from_string("import streamlit as st\nst.navigation([st.Page(lambda:st.write('Ingreso'),title='Ingresar',default=True)],position='hidden').run()",default_timeout=25)
        self.assertGreater(recargar(app,'dashboard'),0)

    def test_each_url_without_session_shows_login_and_remembers_destination(self):
        for path,title in [('hoy','Hoy'),('nueva-solicitud','Nueva solicitud'),('casos','Casos y cotizaciones'),('compartir','Compartir'),('dashboard','Dashboard'),('estado','Estado')]:
            app,_=self.app()
            self.assertEqual(recargar(app,path),0)
            self.assertFalse(app.exception);self.assertFalse(app.error)
            self.assertEqual(app.session_state['destino_tras_login'],title)
            self.assertTrue(any(b.label=='Ingresar a mi espacio' for b in app.button))
            self.assertFalse(menu_visible(app))

    def test_each_url_admin_and_client_and_unknown_paths(self):
        for rol in ['admin','cliente']:
            for path in ['hoy','nueva-solicitud','casos','compartir','dashboard','estado','no-existe','ruta/anidada']:
                app,_=self.app(rol)
                self.assertEqual(recargar(app,path),0,(rol,path))
                self.assertFalse(app.exception);self.assertFalse(app.error)
                self.assertEqual(list(p['page_name'] for p in app._registered_pages.values()),TODAS_PAGINAS)
                if rol=='cliente':
                    self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
                    self.assertEqual(menu_visible(app),[])
                    self.assertFalse(app.dataframe);self.assertFalse(app.metric)
                elif path in ['no-existe','ruta/anidada']:
                    self.assertEqual(app.session_state['navigation'],'Hoy')

    def test_admin_cookie_restores_direct_dashboard_without_login_flash(self):
        app,repo=self.app()
        session=SimpleNamespace(refresh_token='nuevo-refresh-ficticio')
        repo.client.auth.refresh_session=Mock(return_value=SimpleNamespace(session=session))
        repo.client.auth.get_session=lambda:session
        cookie=json.dumps({'refresh_token':'refresh-ficticio','expires':time()+300})
        with patch('utils.sesion_cookie.cookie_inicial',return_value=cookie),patch('servicios.repositorio.public_client',return_value=repo.client):
            self.assertEqual(recargar(app,'dashboard'),0)
        self.assertEqual(app.session_state['navigation'],'Dashboard')
        self.assertFalse(any(b.label=='Ingresar a mi espacio' for b in app.button))
        repo.client.auth.refresh_session.assert_called_once_with('refresh-ficticio')

    def test_client_cookie_restores_only_client_form(self):
        app,repo=self.app('cliente')
        del app.session_state['auth_client']
        repo.client.auth.refresh_session=Mock(return_value=SimpleNamespace(session=SimpleNamespace(refresh_token='ficticio')))
        cookie=json.dumps({'refresh_token':'refresh-ficticio','expires':time()+300})
        with patch('utils.sesion_cookie.cookie_inicial',return_value=cookie),patch('servicios.repositorio.public_client',return_value=repo.client):
            self.assertEqual(recargar(app,'dashboard'),0)
        self.assertIn('auth_client',app.session_state)
        self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
        self.assertTrue(any(b.label=='Siguiente' for b in app.button))

    def test_network_error_during_restore_keeps_loading_and_cookie(self):
        app,_=self.app()
        cookie=json.dumps({'refresh_token':'refresh-ficticio','expires':time()+300})
        with patch('utils.sesion_cookie.cookie_inicial',return_value=cookie),patch('servicios.sesion.restaurar',side_effect=ConnectionError('Error ficticio')):
            self.assertEqual(recargar(app,'dashboard'),0)
        self.assertTrue(app.warning)
        self.assertFalse(any(b.label=='Ingresar a mi espacio' for b in app.button))
        self.assertFalse(app.session_state['_restauracion_intentada'])

    def test_public_link_without_login_or_page_dialog(self):
        app,_=self.app()
        app.query_params['vista']='solicitud'
        with patch('servicios.formulario_publico.configuracion_publica',return_value={'sitio_web':'','redes':{},'correo_contacto':''}):
            self.assertEqual(recargar(app,''),0)
        self.assertEqual(app.query_params['vista'],'solicitud')
        self.assertFalse(any(b.label=='Ingresar a mi espacio' for b in app.button))
        self.assertTrue(any(b.label=='Siguiente' for b in app.button))
        self.assertFalse(menu_visible(app));self.assertFalse(app.error);self.assertFalse(app.exception)
