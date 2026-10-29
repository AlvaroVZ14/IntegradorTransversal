"""Reproduce el módulo antiguo que causa ImportError durante actualizaciones."""
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

import test_recarga as base


class ArranqueCloudTests(unittest.TestCase):
    app=base.RecargaTests.app

    def test_old_cached_navigation_reproduces_import_error(self):
        anterior=ModuleType('utils.navegacion')
        anterior.crear_paginas=lambda:None
        with patch.dict(sys.modules,{'utils.navegacion':anterior}):
            with self.assertRaises(ImportError):
                exec('from utils.navegacion import registrar_navegacion',{})

    def test_login_and_public_form_start_with_old_module_loaded(self):
        for publico in (False,True):
            with self.subTest(publico=publico):
                app,_=self.app()
                if publico:app.query_params['vista']='solicitud'
                anterior=ModuleType('utils.navegacion')
                with patch.dict(sys.modules,{'utils.navegacion':anterior}):
                    app.run()
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
                labels=[b.label for b in app.button]
                self.assertIn('Siguiente' if publico else 'Ingresar a mi espacio',labels)

    def test_admin_and_client_routes_survive_stale_module_and_reload(self):
        for rol in ('admin','cliente'):
            with self.subTest(rol=rol):
                app,_=self.app(rol)
                with patch.dict(sys.modules,{'utils.navegacion':ModuleType('utils.navegacion')}):
                    self.assertEqual(base.recargar(app,'dashboard'),0)
                    self.assertFalse(app.exception)
                    self.assertFalse(app.error)
                    self.assertEqual(app.session_state['navigation'],'Dashboard' if rol=='admin' else 'Nueva solicitud')
                    self.assertEqual(base.recargar(app,'dashboard'),0)
                    self.assertFalse(app.exception)
