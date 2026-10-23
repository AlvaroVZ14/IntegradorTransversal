"""Cotizaciones y SMTP simulados, sin consultar Supabase ni enviar correos reales."""
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from datetime import datetime,timezone
from uuid import uuid4
import unittest

from docx import Document
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest
import test_app as base
from test_app import by_label,ir_a,ROOT
from datos_cotizacion_ficticios import ejemplo
from servicios.cotizacion_asistida import recomendar_tarifa,prellenar,configuracion,faltantes,mensaje_cliente
from servicios.documentos_cotizacion import generar_word,generar_pdf
from servicios.envio_cotizacion import enviar_correo,enlace_whatsapp


class CotizadorTests(unittest.TestCase):
    def test_documents_same_content_escape_and_optional_sections(self):
        caso,d,q=ejemplo();q['documento']['textos']['metodologia']='Texto oculto ficticio'
        q['documento']['mostrar']['metodologia']=False
        q['documento']['textos']['descripcion']='Aprender <colaborando> & escuchando'
        word=Document(BytesIO(generar_word(q)))
        texto='\n'.join(p.text for p in word.paragraphs)
        self.assertIn('Aprender <colaborando> & escuchando',texto)
        self.assertNotIn('Texto oculto ficticio',texto)
        self.assertNotIn('{{',texto)
        reader=PdfReader(BytesIO(generar_pdf(q)))
        pdf='\n'.join(p.extract_text() for p in reader.pages)
        self.assertIn('Aprender <colaborando> & escuchando',pdf)
        self.assertNotIn('Texto oculto ficticio',pdf)
        self.assertIn('$1.125.000',pdf)

    def test_recommendation_favors_topic_and_missing_issuer_is_explicit(self):
        caso,d,q=ejemplo()
        tarifas=[dict(id='general',servicio=caso['servicio'],horas=4,participantes=20,activa=True,monto_clp=100),
            dict(id='tema',servicio=caso['servicio'],tematica=caso['tematica'],horas=5,participantes=25,activa=True,monto_clp=200)]
        self.assertEqual(recomendar_tarifa(caso,tarifas)['id'],'tema')
        nuevo=prellenar(caso,tarifas,[],configuracion())
        self.assertTrue(any(label=='Razón social' for label,_ in faltantes(caso,nuevo)))
        self.assertEqual(nuevo['base_clp'],200) # No escala automáticamente el precio.
        self.assertNotIn('{horas}',nuevo['textos']['incluye'])

    def test_smtp_requires_confirmation_and_prevents_repeat(self):
        _,_,q=ejemplo();repo=MagicMock();repo.prepare_quote_send.return_value={'nuevo':True,'envio':{'estado':'preparado'}}
        settings=dict(host='smtp.example.test',usuario='test',password='ficticia',remitente='emisor@example.test')
        adjuntos=[('propuesta.pdf',b'%PDF prueba','application/pdf')]
        with patch('servicios.envio_cotizacion.smtplib.SMTP') as smtp:
            smtp.return_value.__enter__.return_value.send_message.return_value={}
            with self.assertRaises(PermissionError):enviar_correo(repo,q,'operacion','cliente@example.test','Propuesta','Hola',adjuntos,settings)
            smtp.assert_not_called();repo.prepare_quote_send.assert_not_called()
            self.assertEqual(enviar_correo(repo,q,'operacion','cliente@example.test','Propuesta','Hola',adjuntos,settings,True),'enviado')
            smtp.return_value.__enter__.return_value.starttls.assert_called_once()
            mensaje=smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
            self.assertEqual(len(list(mensaje.iter_attachments())),1)
            repo.prepare_quote_send.return_value={'nuevo':False,'envio':{'estado':'enviado'}}
            enviar_correo(repo,q,'operacion','cliente@example.test','Propuesta','Hola',adjuntos,settings,True)
            self.assertEqual(smtp.call_count,1)

    def test_smtp_uncertain_does_not_retry_and_whatsapp_has_no_send_side_effect(self):
        _,_,q=ejemplo();repo=MagicMock();repo.prepare_quote_send.return_value={'nuevo':True,'envio':{}}
        settings=dict(host='smtp.example.test',usuario='test',password='ficticia',remitente='emisor@example.test')
        with patch('servicios.envio_cotizacion.smtplib.SMTP',side_effect=TimeoutError()):
            with self.assertRaises(ValueError):enviar_correo(repo,q,'operacion','cliente@example.test','Propuesta','Hola',[('p.pdf',b'pdf','application/pdf')],settings,True)
        repo.confirm_quote_send.assert_called_with('operacion','incierto')
        self.assertTrue(enlace_whatsapp('912345678','Hola Daniela').startswith('https://wa.me/56912345678'))
        self.assertIsNone(enlace_whatsapp('','Hola'))
        asunto,texto=mensaje_cliente(q)
        self.assertIn('Daniela Soto',texto);self.assertIn('COT-',asunto)


class EditorUITests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def abrir(self):
        app,repo=self.setup_app();app.run();base.AppTests.create_request(self,app)
        return app,repo

    def test_generate_one_click_and_draft_survives_new_session(self):
        app,repo=self.abrir()
        self.assertTrue(any('Prellenado automáticamente' in i.value for i in app.info))
        by_label(app.text_area,'Objetivos').set_value('Objetivos ficticios editados.').run()
        self.assertEqual(len(repo.quote_rows),0)
        cid=repo.case_rows[0]['id']
        self.assertEqual(repo.draft_rows[cid]['datos']['textos']['objetivos'],'Objetivos ficticios editados.')
        fresh=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20)
        fresh.session_state['auth_client']=repo.client;fresh.run();ir_a(fresh,'Casos y cotizaciones')
        self.assert_clean(fresh)
        self.assertEqual(by_label(fresh.text_area,'Objetivos').value,'Objetivos ficticios editados.')
        by_label(fresh.button,'Generar cotización').click().run()
        self.assert_clean(fresh)
        self.assertEqual(len(repo.quote_rows),1)
        self.assertEqual(repo.case_rows[0]['estado'],'Cotizado')
        self.assertTrue(any(b.label=='Descargar Word' for b in fresh.get('download_button')))
        self.assertTrue(any(b.label=='Descargar PDF' for b in fresh.get('download_button')))
        self.assertTrue(any('Cotización lista' in x.value for x in fresh.markdown))

    def test_discount_reason_and_reset_are_manual(self):
        app,repo=self.abrir()
        by_label(app.number_input,'Descuento (%)').set_value(15.0).run()
        by_label(app.button,'Generar cotización').click().run()
        self.assertFalse(repo.quote_rows)
        self.assertTrue(any('Motivo del descuento' in w.value for w in app.warning))
        by_label(app.text_input,'Motivo del descuento').set_value('Convenio ficticio').run()
        by_label(app.text_area,'Objetivos').set_value('Cambio temporal').run()
        reset=next(b for b in app.button if b.key=='reset_'+repo.case_rows[0]['id']+'objetivos')
        reset.click().run()
        self.assertEqual(by_label(app.text_area,'Objetivos').value,repo.case_rows[0]['detalle'])
        by_label(app.button,'Generar cotización').click().run()
        self.assert_clean(app);self.assertEqual(repo.quote_rows[0]['descuento_motivo'],'Convenio ficticio')

    def test_accept_sell_dialog_and_undo(self):
        app,repo=self.abrir()
        def decide(caso,q,datos,op):
            anterior=deepcopy(repo.case_rows[0]);venta=None
            if datos['accion']=='vender':
                reserva=round(datos['monto_clp']*datos['reserva_pct']/100)
                venta=dict(id=str(uuid4()),caso_id=caso['id'],cotizacion_id=q['id'],monto_clp=datos['monto_clp'],fecha_venta=datos['fecha'],estado_pago=datos['estado_pago'],anulada=False,version=1,
                    reserva_pct=datos['reserva_pct'],remuneracion_pct=datos['remuneracion_pct'],reserva_clp=reserva,remuneracion_clp=datos['monto_clp']-reserva,documento_numero=datos['documento_numero'])
                repo.sale_rows.append(venta)
            row=repo.update_case(caso,{'estado':'En ejecución' if venta else 'Vendido'})
            e=dict(id=str(uuid4()),caso_id=caso['id'],tipo=datos['accion'],datos={},created_at=datetime.now(timezone.utc).isoformat(),antes=anterior,deshecho_en=None)
            repo.event_rows.append(e)
            return dict(caso=row,venta=venta,evento=e)
        def undo(eid):
            e=next(e for e in repo.event_rows if e['id']==eid)
            repo.sale_rows=[];e['deshecho_en']='ahora'
            return repo.update_case(repo.case_rows[0],{'estado':e['antes']['estado']})
        repo.decide_quote=decide;repo.undo_quote_decision=undo
        by_label(app.number_input,'Valor base (CLP)').set_value(420000).run()
        by_label(app.button,'Generar cotización').click().run()
        by_label(app.button,'Marcar como aceptada').click().run()
        self.assertEqual(by_label(app.number_input,'Monto de la venta (CLP)').value,420000)
        by_label(app.button,'Aceptar y registrar venta').click().run()
        self.assert_clean(app);self.assertEqual(repo.case_rows[0]['estado'],'En ejecución');self.assertEqual(len(repo.sale_rows),1)
        self.assertEqual(by_label(app.metric,'Reserva').value,'$126.000')
        self.assertEqual(by_label(app.metric,'Remuneración').value,'$294.000')
        by_label(app.button,'Deshacer').click().run()
        self.assert_clean(app);self.assertEqual(repo.case_rows[0]['estado'],'Cotizado');self.assertFalse(repo.sale_rows)

    def test_client_never_gets_editor_or_configuration(self):
        app,repo=self.setup_app(False);app.run()
        self.assertFalse(any(t.label=='Configuración' for t in app.tabs))
        self.assertFalse(any(b.label=='Generar cotización' for b in app.button))
