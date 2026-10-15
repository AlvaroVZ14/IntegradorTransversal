"""Recorridos de UI con repositorio aislado; no usa credenciales reales."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

import streamlit as st
from streamlit.testing.v1 import AppTest

from mente_futuro.domain import quote_total, today

ROOT=Path(__file__).resolve().parent.parent
(ROOT/'tmp'/'tests').mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(ROOT/'tmp'/'tests')


class Client:
    def __init__(self,owner):
        self.user=SimpleNamespace(id='owner' if owner else 'client',email='test@example.cl')
        self.profile=dict(id=self.user.id,nombre='Persona de prueba',email=self.user.email,rol='duena' if owner else 'cliente')
        self.auth=SimpleNamespace(get_user=lambda:SimpleNamespace(user=self.user),sign_out=lambda *_:None)
    def table(self,_): return self
    def select(self,*_): return self
    def eq(self,*_): return self
    def execute(self): return SimpleNamespace(data=[self.profile])


class FakeRepository:
    def __init__(self,owner=True):
        self.is_owner=owner
        self.client=Client(owner)
        self.user=self.client.user
        self.profile=self.client.profile
        self.case_rows=[]
        self.quote_rows=[]
        self.sale_rows=[]
        self.tariff_rows=[]
        self.fail_write=False
    def owner_only(self):
        if not self.is_owner: raise PermissionError('Solo dueña')
    def cases(self): return deepcopy(self.case_rows)
    def profiles(self): return [dict(id='client',nombre='Cliente',email='client@example.cl',rol='cliente')]
    def tariffs(self): return deepcopy(self.tariff_rows)
    def quotes(self,case_id): return [deepcopy(q) for q in self.quote_rows if q['caso_id']==case_id]
    def sales(self): return deepcopy(self.sale_rows)
    def create_request(self,data,request_id):
        if self.fail_write: raise ConnectionError('Simulación de fallo')
        row=dict(data,id=request_id,numero=len(self.case_rows)+1,created_at=today().isoformat()+'T12:00:00Z',estado='Solicitud',version=1)
        self.case_rows.append(row)
        return row
    def issue_quote(self,case,data,operation_id):
        row=dict(data,id=str(uuid4()),numero=len(self.quote_rows)+1,caso_id=case['id'],created_at=today().isoformat(),fecha_emision=today().isoformat(),snapshot=case,total_clp=quote_total(data['base_clp'],data['descuento_pct'],data['iva_pct']))
        self.quote_rows.insert(0,row)
        self.case_rows[0]['estado']='Cotizado'
        self.case_rows[0]['version']+=1
    def record_sale(self,case,quote,sale_date,payment):
        self.sale_rows.append(dict(id=str(uuid4()),caso_id=case['id'],cotizacion_id=quote['id'],monto_clp=quote['total_clp'],fecha_venta=sale_date.isoformat(),estado_pago=payment,anulada=False,version=1))
        self.case_rows[0]['estado']='Vendido'
        self.case_rows[0]['version']+=1
    def update_case(self,case,changes):
        self.case_rows[0].update(changes)
        self.case_rows[0]['version']+=1
    def save_tariff(self,data,tariff=None):
        self.tariff_rows.append(dict(data,id=str(uuid4()),version=1))


def by_label(elements,label):
    return next(e for e in elements if e.label==label)


class AppTests(unittest.TestCase):
    def setup_app(self,owner=True):
        repo=FakeRepository(owner)
        patcher=patch('mente_futuro.repository.Repository',return_value=repo)
        patcher.start()
        self.addCleanup(patcher.stop)
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20)
        app.session_state['auth_client']=repo.client
        return app,repo
    def assert_clean(self,app):
        self.assertEqual([e.message for e in app.exception],[])
        self.assertEqual([e.value for e in app.error],[])
    def create_request(self,app):
        by_label(app.radio,'Navegación').set_value('Nueva solicitud').run()
        by_label(app.text_input,'Nombre o empresa *').set_value('Empresa de prueba')
        by_label(app.text_input,'Persona de contacto *').set_value('Contacto prueba')
        by_label(app.text_input,'Correo de contacto *').set_value('cliente@example.cl')
        by_label(app.text_area,'¿Qué te gustaría lograr?').set_value('Desarrollar habilidades de liderazgo.')
        by_label(app.button,'Enviar solicitud').click().run()

    def test_login_and_empty_validation(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20).run()
        self.assert_clean(app)
        by_label(app.button,'Ingresar a mi espacio').click().run()
        self.assertIn('Ingresa tu correo',app.error[0].value)

    def test_client_navigation_and_own_request(self):
        app,repo=self.setup_app(False)
        app.run()
        self.assert_clean(app)
        self.assertNotIn('Dashboard',app.radio[0].options)
        self.create_request(app)
        self.assert_clean(app)
        self.assertEqual(len(repo.case_rows),1)
        self.assertEqual(app.radio[0].value,'Casos y cotizaciones')
        self.assertFalse(any(x.label=='Emitir y guardar cotización' for x in app.button))
        self.assertFalse(any(x.label=='Tarifas y servicios' for x in app.tabs))

    def test_failed_write_never_shows_success(self):
        app,repo=self.setup_app(False)
        repo.fail_write=True
        app.run()
        self.create_request(app)
        self.assertEqual(repo.case_rows,[])
        self.assertEqual(len(app.success),0)
        self.assertTrue(app.error)

    def test_owner_request_quote_sale_dashboard(self):
        app,repo=self.setup_app()
        app.run()
        self.assert_clean(app)
        self.create_request(app)
        self.assert_clean(app)
        by_label(app.number_input,'Valor base (CLP)').set_value(420000)
        by_label(app.selectbox,'Tratamiento de IVA *').set_value('Exento de IVA')
        by_label(app.button,'Emitir y guardar cotización').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.quote_rows[0]['total_clp'],420000)
        by_label(app.checkbox,'El cliente aceptó esta cotización').check()
        by_label(app.button,'Registrar venta').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.sale_rows[0]['monto_clp'],420000)
        by_label(app.radio,'Navegación').set_value('Dashboard').run()
        self.assert_clean(app)
        self.assertEqual(by_label(app.metric,'Ventas del período').value,'$420.000')
        self.assertEqual(by_label(app.metric,'Ventas cerradas').value,'1')

    def test_tariff_write(self):
        app,repo=self.setup_app()
        app.run()
        by_label(app.radio,'Navegación').set_value('Casos y cotizaciones').run()
        by_label(app.text_input,'Nombre del plan').set_value('Plan de prueba')
        by_label(app.number_input,'Valor de referencia (CLP)').set_value(420000)
        by_label(app.button,'Guardar tarifa').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.tariff_rows[0]['monto_clp'],420000)

    def test_logout_clears_session(self):
        app,repo=self.setup_app()
        app.run()
        by_label(app.button,'Cerrar sesión').click().run()
        self.assert_clean(app)
        self.assertNotIn('auth_client',app.session_state)
        self.assertTrue(any(x.label=='Ingresar a mi espacio' for x in app.button))


if __name__ == '__main__': unittest.main()
