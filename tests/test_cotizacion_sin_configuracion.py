"""Emisión y descarga con ajustes ausentes o inaccesibles; datos ficticios."""
from copy import deepcopy
from datetime import date,timedelta
from io import BytesIO
from unittest.mock import Mock
import unittest

from docx import Document
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest
import test_app as base
from datos_cotizacion_ficticios import ejemplo
from servicios.cotizacion_asistida import prellenar,faltantes,datos_emision
from servicios.cotizacion_defaults import (CONDICIONES_DEFAULT,NOMBRE_ARCHIVO_DEFAULT,VIGENCIA_DIAS_DEFAULT,
    RESERVA_PCT_DEFAULT,REMUNERACION_PCT_DEFAULT)
from servicios.documentos_cotizacion import generar_pdf,nombre_archivo
from mente_futuro.domain import today


class DefaultsTests(unittest.TestCase):
    def test_defaults_are_local_copies_and_only_minimal_fields_are_required(self):
        caso,_,_=ejemplo()
        caso.update(contacto='',email='',detalle='',datos_incompletos=True)
        d=prellenar(caso,[],[])
        self.assertEqual(d['condiciones'],CONDICIONES_DEFAULT)
        self.assertEqual(d['nombre_archivo'],NOMBRE_ARCHIVO_DEFAULT)
        self.assertEqual(d['iva_pct'],0)
        self.assertEqual(date.fromisoformat(d['valida_hasta']),today()+timedelta(days=VIGENCIA_DIAS_DEFAULT))
        self.assertEqual(faltantes(caso,d),[('Un ítem con valor mayor a cero','importes')])
        d.update(base_clp=250000,condiciones='',detalle='')
        d['textos']={k:'' for k in d['textos']}
        self.assertFalse(faltantes(caso,d))
        payload=datos_emision(d)
        self.assertGreaterEqual(len(payload['detalle'].strip()),2) # Restricción SQL existente.
        self.assertEqual(payload['condiciones'],'')
        d['textos']['incluye']='Edición particular'
        nuevo=prellenar(caso,[],[])
        self.assertNotEqual(nuevo['textos']['incluye'],'Edición particular')
        self.assertEqual(nuevo['condiciones'],CONDICIONES_DEFAULT)

    def test_missing_minimums_are_specific_without_settings_reference(self):
        caso,_,_=ejemplo();d=prellenar(caso,[],[])
        d.update(cliente='',servicio='',detalle_modalidad='')
        destinos={dest for _,dest in faltantes(caso,d)}
        self.assertEqual(destinos,{'cliente','servicio','detalle_modalidad','importes'})

    def test_filename_and_optional_program_are_taken_from_quote(self):
        caso,d,q=ejemplo()
        q['documento']['nombre_archivo']='Propuesta_{folio}_{cliente}'
        self.assertTrue(nombre_archivo(q).startswith('Propuesta_COT-'))
        q['documento']['cliente']='Cliente ficticio alternativo'
        q['documento']['servicio']='Servicio ficticio alternativo'
        q['documento']['detalle_modalidad']='Online: dos sesiones de una hora'
        q['documento']['emisor']={}
        q['documento']['textos']={k:'' for k in q['documento']['textos']}
        q['condiciones']=''
        pdf=generar_pdf(q)
        texto='\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
        self.assertIn('Cliente ficticio alternativo',texto)
        self.assertIn('Online: dos sesiones de una hora',texto)


class FlujoSinConfiguracionTests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_new_case_no_settings_generate_download_edit_and_reload(self):
        app,repo=self.setup_app()
        repo.settings_row['datos']={}
        repo.quote_settings=Mock(side_effect=AssertionError('No debe leer ajustes'))
        repo.save_quote_settings=Mock(side_effect=AssertionError('No debe escribir ajustes'))
        app.run();base.AppTests.create_request(self,app)
        base.by_label(app.number_input,'Valor base (CLP)').set_value(250000).run()
        self.assertFalse(any(t.label=='Configuración' for t in app.tabs))
        self.assertEqual(base.by_label(app.text_area,'Condiciones comerciales').value,CONDICIONES_DEFAULT)
        self.assertIn('Reunión diagnóstica',base.by_label(app.text_area,'Qué incluye').value)
        base.by_label(app.text_area,'Condiciones comerciales').set_value('Acuerdo exclusivo ficticio').run()
        for label in ('Objetivo general','Frase introductoria de metodología','Descripción del servicio','Dirigido a','Qué incluye'):
            base.by_label(app.text_area,label).set_value('').run()
        cid=repo.case_rows[0]['id']
        fresh=AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
        fresh.session_state['auth_client']=repo.client;fresh.run();base.ir_a(fresh,'Casos y cotizaciones')
        base.by_label(fresh.selectbox,'Abrir detalle').set_value(cid).run()
        self.assertEqual(base.by_label(fresh.text_area,'Condiciones comerciales').value,'Acuerdo exclusivo ficticio')
        base.by_label(fresh.button,'Generar cotización').click().run()
        self.assert_clean(fresh)
        self.assertEqual(len(repo.quote_rows),1)
        self.assertEqual(repo.quote_rows[0]['total_clp'],250000)
        self.assertTrue(any(b.label=='Descargar PDF' for b in fresh.get('download_button')))
        self.assertTrue(any(b.label=='Descargar Word' for b in fresh.get('download_button')))
        from paginas.acciones_cotizacion import archivos
        word,pdf=archivos(repo,repo.quote_rows[0])
        self.assertTrue(pdf.startswith(b'%PDF'))
        self.assertTrue(Document(BytesIO(word)).paragraphs)
        repo.quote_settings.assert_not_called();repo.save_quote_settings.assert_not_called()
        # La edición no cambia los valores iniciales de la cotización siguiente.
        self.assertEqual(prellenar(repo.case_rows[0],[],[])['condiciones'],CONDICIONES_DEFAULT)

    def test_sale_percentages_are_visible_local_editable_and_sum_to_100(self):
        app,repo=self.setup_app()
        repo.quote_settings=Mock(side_effect=AssertionError('No debe leer ajustes'))
        app.run();base.AppTests.create_request(self,app)
        base.by_label(app.number_input,'Valor base (CLP)').set_value(200000).run()
        base.by_label(app.button,'Generar cotización').click().run()
        self.assertEqual(base.by_label(app.number_input,'Reserva (%)').value,RESERVA_PCT_DEFAULT)
        self.assertEqual(base.by_label(app.number_input,'Remuneración (%)').value,REMUNERACION_PCT_DEFAULT)
        base.by_label(app.number_input,'Reserva (%)').set_value(30.0)
        base.by_label(app.number_input,'Remuneración (%)').set_value(60.0)
        base.by_label(app.button,'Registrar venta').click().run()
        self.assertFalse(repo.sale_rows)
        self.assertTrue(any('sumar 100%' in e.value for e in app.error))
        base.by_label(app.number_input,'Remuneración (%)').set_value(70.0)
        base.by_label(app.button,'Registrar venta').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.sale_rows[0]['reserva_clp'],60000)
        self.assertEqual(repo.sale_rows[0]['remuneracion_clp'],140000)
        repo.quote_settings.assert_not_called()
        base.by_label(app.button,'Deshacer').click().run()
        self.assert_clean(app);self.assertFalse(repo.sale_rows)
