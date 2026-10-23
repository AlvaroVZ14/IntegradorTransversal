"""Datos ficticios: asistentes de registro y recorridos de Administración/Cliente."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
import unittest

from streamlit.testing.v1 import AppTest
from servicios.solicitud_rapida import (cuenta_por_correo, clientes_existentes, duplicados,
    errores_adicionales, formatear_rut, normalizar_telefono, sugerencias, sugerir_correo)
import test_app as base
from test_app import by_label, ir_a


def caso(**cambios):
    return dict(dict(id=str(uuid4()),numero=7,cliente='Fundación Horizonte',contacto='Camila Rojas',
        email='client@example.cl',telefono='+56 9 1234 5678',rut='12.345.678-5',cargo='Coordinadora',
        servicio='Coaching individual',tematica='Liderazgo',participantes=12,horas=3.0,
        modalidad='Online',lugar='Antofagasta',detalle='Desarrollar habilidades.',version=1,
        estado='Solicitud',created_at=(datetime.now(timezone.utc)-timedelta(days=45)).isoformat(),
        fecha_preferida=None,cliente_id=None,origen='Correo'),**cambios)


class AyudasTests(unittest.TestCase):
    def test_rut_and_three_phone_formats(self):
        self.assertEqual(formatear_rut('123456785'),'12.345.678-5')
        self.assertEqual(errores_adicionales(dict(rut='12.345.678-5')),[])
        self.assertTrue(errores_adicionales(dict(rut='12.345.678-9')))
        self.assertTrue(errores_adicionales(dict(rut='12A3456785')))
        for telefono in ('912345678','+56912345678','9 1234 5678'):
            self.assertEqual(normalizar_telefono(telefono),'+56 9 1234 5678')
        self.assertTrue(errores_adicionales(dict(telefono='no es un teléfono')))

    def test_email_suggestion_is_not_automatic_and_roles_are_filtered(self):
        self.assertEqual(sugerir_correo('camila@gmial.com'),'camila@gmail.com')
        self.assertIsNone(sugerir_correo('camila@ejemplo.cl'))
        perfiles=[dict(id='1',rol='cliente',email='camila@example.cl'),dict(id='2',rol='admin',email='admin@example.cl')]
        self.assertEqual(cuenta_por_correo(' CAMILA@EXAMPLE.CL ',perfiles)['id'],'1')
        self.assertIsNone(cuenta_por_correo('admin@example.cl',perfiles))
        self.assertIsNone(cuenta_por_correo('camila@example.cl',perfiles+[perfiles[0]]))
        self.assertEqual(cuenta_por_correo('contacto@fundacion.test',perfiles,
            [dict(email='contacto@fundacion.test',cliente_id='1')])['id'],'1')
        self.assertIsNone(cuenta_por_correo('contacto@fundacion.test',perfiles,
            [dict(email='contacto@fundacion.test',cliente_id='2')]))

    def test_recent_open_duplicates_and_timezone(self):
        ahora=datetime(2026,10,22,12,tzinfo=timezone.utc)
        datos=caso()
        recientes=[caso(id='reciente',created_at=(ahora-timedelta(days=2)).isoformat()),
            caso(id='cerrado',estado='Finalizado',created_at=ahora.isoformat()),
            caso(id='antiguo',created_at=(ahora-timedelta(days=31)).isoformat()),
            caso(id='otro',tematica='Trabajo en equipo',created_at=ahora.isoformat())]
        self.assertEqual([c['id'] for c in duplicados(datos,recientes,ahora)],['reciente'])

    def test_catalog_keeps_latest_and_suggestions_do_not_change_values(self):
        viejo=caso(horas=1,participantes=10)
        nuevo=caso(horas=3,participantes=20,created_at=datetime.now(timezone.utc).isoformat())
        self.assertEqual(clientes_existentes([viejo,nuevo])[0]['id'],nuevo['id'])
        copia=deepcopy([viejo,nuevo])
        valores,fuente=sugerencias('Liderazgo','Coaching individual',copia,[])
        self.assertEqual(valores,dict(horas=2.0,participantes=15))
        self.assertEqual(copia,[viejo,nuevo])
        valores,fuente=sugerencias('Otro','Coaching individual',[],[dict(servicio='Coaching individual',horas=2,participantes=8,activa=True)])
        self.assertEqual(valores['participantes'],8)
        self.assertIn('sin temática',fuente)


class SolicitudUITests(unittest.TestCase):
    assert_clean=base.AppTests.assert_clean

    def setup_app(self,owner=True):
        app,repo=base.AppTests.setup_app(self,owner)
        return app,repo

    def llenar(self,app,correo='client@example.cl'):
        ir_a(app,'Nueva solicitud')
        by_label(app.text_input,'Nombre o empresa *').set_value('Fundación Horizonte')
        by_label(app.text_input,'Persona de contacto *').set_value('Camila Rojas')
        by_label(app.text_input,'Correo de contacto *').set_value(correo)
        app.run()

    def test_existing_company_autofill_and_manual_link_override(self):
        app,repo=self.setup_app()
        existente=caso()
        repo.case_rows=[existente]
        app.run()
        ir_a(app,'Nueva solicitud')
        by_label(app.selectbox,'Buscar empresa o cliente existente').set_value(existente['id']).run()
        self.assert_clean(app)
        for label,valor in [('Nombre o empresa *','Fundación Horizonte'),('RUT (opcional)','12.345.678-5'),
                            ('Persona de contacto *','Camila Rojas'),('Cargo (opcional)','Coordinadora')]:
            self.assertEqual(by_label(app.text_input,label).value,valor)
        enlace=by_label(app.selectbox,'Vincular a una cuenta de cliente')
        self.assertEqual(enlace.value,'client')
        enlace.set_value(None).run()
        by_label(app.text_input,'Lugar o ciudad').set_value('Calama').run()
        self.assertIsNone(by_label(app.selectbox,'Vincular a una cuenta de cliente').value)
        self.assertTrue(by_label(app.text_input,'Nombre o empresa *').value)
        by_label(app.text_input,'Correo de contacto *').set_value('otra@example.cl').run()
        by_label(app.text_input,'Correo de contacto *').set_value('client@example.cl').run()
        self.assertEqual(by_label(app.selectbox,'Vincular a una cuenta de cliente').value,'client')

    def test_new_customer_with_account_and_keep_origin_for_next(self):
        app,repo=self.setup_app()
        app.run()
        self.llenar(app)
        self.assertEqual(by_label(app.selectbox,'Vincular a una cuenta de cliente').value,'client')
        by_label(app.selectbox,'Origen de la solicitud').set_value('Referido por colega').run()
        by_label(app.button,'Guardar y registrar otra').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.case_rows[0]['cliente_id'],'client')
        self.assertEqual(repo.case_rows[0]['origen'],'Referido por colega')
        self.assertEqual(by_label(app.text_input,'Nombre o empresa *').value,'')
        self.assertEqual(by_label(app.selectbox,'Origen de la solicitud').value,'Referido por colega')
        self.assertEqual(app.session_state['navigation'],'Nueva solicitud')

    def test_inline_validation_and_optional_email_correction(self):
        app,repo=self.setup_app()
        app.run()
        self.llenar(app,'camila@gmial.com')
        self.assertEqual(by_label(app.text_input,'Correo de contacto *').value,'camila@gmial.com')
        by_label(app.button,'Usar camila@gmail.com').click().run()
        self.assertEqual(by_label(app.text_input,'Correo de contacto *').value,'camila@gmail.com')
        by_label(app.text_input,'RUT (opcional)').set_value('123456789').run()
        self.assertTrue(any('verificador' in e.value for e in app.error))
        by_label(app.button,'Enviar solicitud').click().run()
        self.assertEqual(repo.case_rows,[])
        by_label(app.text_input,'RUT (opcional)').set_value('123456785').run()
        for telefono in ('912345678','+56912345678','9 1234 5678'):
            by_label(app.text_input,'Teléfono').set_value(telefono).run()
            self.assertEqual(by_label(app.text_input,'Teléfono').value,'+56 9 1234 5678')
        self.assert_clean(app)

    def test_duplicate_requires_deliberate_override_and_can_open(self):
        app,repo=self.setup_app()
        existente=caso(created_at=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat())
        repo.case_rows=[existente]
        app.run()
        self.llenar(app)
        self.assertTrue(any('misma solicitud' in w.value for w in app.warning))
        by_label(app.button,'Guardar y registrar otra').click().run()
        self.assertEqual(len(repo.case_rows),1)
        abrir=next(b for b in app.button if b.label.startswith('Abrir MF-'))
        abrir.click().run()
        self.assert_clean(app)
        self.assertEqual(app.session_state['selected_case'],existente['id'])
        ir_a(app,'Nueva solicitud')
        by_label(app.checkbox,'Crear otra solicitud de todas formas').check()
        by_label(app.button,'Guardar y registrar otra').click().run()
        self.assert_clean(app)
        self.assertEqual(len(repo.case_rows),2)

    def test_saved_draft_restores_after_new_session_without_trusting_client_identity(self):
        app,repo=self.setup_app(False)
        entrada=dict(id=str(uuid4()),values=dict(cliente='Fundación Horizonte',rut='12.345.678-5',cargo='Coordinadora',
            email='otro@example.cl',contacto='Persona ajena',cliente_id='owner',origen='Reunión',
            telefono='912345678',detalle='Borrador ficticio',horas=4.0,participantes=15))
        with patch('utils.solicitud_borrador.component',return_value=lambda **kw:SimpleNamespace(recovered=entrada)):
            app.run()
        self.assert_clean(app)
        self.assertEqual(by_label(app.text_area,'¿Qué te gustaría lograr?').value,'Borrador ficticio')
        self.assertEqual(by_label(app.text_input,'Correo de contacto *').value,repo.user.email)
        self.assertTrue(by_label(app.text_input,'Correo de contacto *').disabled)
        self.assertEqual(by_label(app.text_input,'Persona de contacto *').value,repo.profile['nombre'])
        self.assertFalse(app.checkbox[0].value)
        self.assertEqual(app.session_state['request_id'],entrada['id'])
        self.assertFalse(any(s.label=='Buscar empresa o cliente existente' for s in app.selectbox))

    def test_quote_shortcut_and_suggestions_stay_editable(self):
        app,repo=self.setup_app()
        repo.tariff_rows=[dict(id='tarifa',servicio='Coaching individual',nombre='Coaching',horas=2,participantes=8,activa=True,monto_clp=100000,tratamiento_iva='Exento',detalle='Sesión ficticia',fuente='',version=1)]
        app.run()
        self.llenar(app)
        by_label(app.button,'Aplicar sugerencia').click().run()
        self.assertEqual(by_label(app.number_input,'Participantes *').value,8)
        by_label(app.number_input,'Participantes *').set_value(10).run()
        by_label(app.button,'Guardar y cotizar ahora').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.case_rows[0]['participantes'],10)
        self.assertEqual(app.session_state['navigation'],'Casos y cotizaciones')
        self.assertTrue(any(b.label=='Emitir y guardar cotización' for b in app.button))

    def test_lost_response_retry_uses_same_uuid_not_duplicate_warning(self):
        app,repo=self.setup_app()
        original=repo.create_request
        intentos=[]
        def perdida(data,request_id):
            intentos.append(request_id)
            if len(intentos)==1:
                original(data,request_id)
                raise ConnectionError('Respuesta perdida ficticia')
            return next(c for c in repo.case_rows if c['id']==request_id)
        repo.create_request=perdida
        app.run()
        self.llenar(app)
        by_label(app.button,'Guardar y registrar otra').click().run()
        self.assertTrue(app.error)
        by_label(app.button,'Guardar y registrar otra').click().run()
        self.assert_clean(app)
        self.assertEqual(len(repo.case_rows),1)
        self.assertEqual(intentos[0],intentos[1])
