"""Transferencias solo en documentos administrativos. Datos del ejemplo ficticio."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock,patch
import tomllib
import unittest
from docx import Document
from pypdf import PdfReader
import test_app as base
from test_propuesta_documento import propuesta
from servicios.documentos_cotizacion import generar_pdf,generar_word
from servicios.cotizacion_asistida import datos_emision
from servicios.pago_cotizacion import (CAMPOS_PAGO,normalizar_pago,leer_pago_secrets,pago_para_documento)
from servicios.propuesta_documento import modelo


def pago_ficticio():
    return tomllib.loads((base.ROOT/'secrets.toml.example').read_text(encoding='utf-8'))['pago']


def muestras_pago():
    _,_,q=propuesta();q['documento'].update(pago=pago_ficticio(),incluir_pago=True)
    sin=deepcopy(q);sin['documento'].pop('pago')
    apagado=deepcopy(q);apagado['documento']['incluir_pago']=False
    distinto=deepcopy(q);distinto['numero']=7;distinto['documento']['pago']['numero_cuenta']='9999999999'
    salto=deepcopy(q);salto['numero']=8
    salto['condiciones']='\n'.join(f'Condición ficticia {i+1}: Coordinar la jornada con el equipo.' for i in range(18))+'\nFIN DE CONDICIONES'
    return [('con-pago',q),('sin-pago',sin),('pago-apagado',apagado),('pago-particular',distinto),('pago-pagina-siguiente',salto)]


def texto_word(word):
    return '\n'.join(p.text for p in word.paragraphs)+'\n'+'\n'.join(c.text for t in word.tables for r in t.rows for c in r.cells)


class PagoDocumentoTests(unittest.TestCase):
    def test_complete_missing_off_and_per_quote_in_pdf_and_word(self):
        for nombre,q in muestras_pago():
            with self.subTest(nombre=nombre):
                original=deepcopy(q)
                with patch('servicios.pago_cotizacion.leer_pago_secrets',side_effect=AssertionError('No leer secretos al regenerar')):
                    pdf=PdfReader(BytesIO(generar_pdf(q)));word=Document(BytesIO(generar_word(q)))
                texto='\n'.join(p.extract_text() for p in pdf.pages);wtexto=texto_word(word)
                presente=nombre not in ('sin-pago','pago-apagado')
                for contenido in (texto,wtexto):
                    self.assertEqual('Datos para el pago' in contenido,presente)
                    if presente:
                        for clave,valor in q['documento']['pago'].items():self.assertIn(valor,contenido)
                        self.assertIn('Indicar el N° de cotización en el asunto',contenido)
                        self.assertLess(contenido.index('Condiciones generales'),contenido.index('Datos para el pago'))
                    else:self.assertNotIn('Banco Ficticio',contenido)
                if presente:
                    pagina=next(p.extract_text() for p in pdf.pages if 'Datos para el pago' in p.extract_text())
                    for valor in q['documento']['pago'].values():self.assertIn(valor,pagina)
                    self.assertIn('Indicar el N° de cotización en el asunto',pagina)
                    tabla=word.tables[-1]
                    self.assertEqual(len(tabla.rows),6);self.assertEqual(len(tabla.columns),2)
                    for row in tabla.rows:
                        self.assertTrue(row._tr.xpath('./w:trPr/w:cantSplit'))
                        self.assertTrue(all(p.paragraph_format.keep_with_next for c in row.cells for p in c.paragraphs))
                if nombre=='pago-pagina-siguiente':
                    paginas=[p.extract_text() for p in pdf.pages]
                    self.assertNotEqual(next(i for i,t in enumerate(paginas) if 'FIN DE CONDICIONES' in t),next(i for i,t in enumerate(paginas) if 'Datos para el pago' in t))
                self.assertEqual(q,original)
        # La impresión no depende de la etapa comercial del caso.
        q=muestras_pago()[0][1]
        for estado in ('Solicitud','Cotizado','Vendido','En ejecución','Finalizado','Cancelado'):
            q['snapshot']['estado']=estado
            self.assertEqual(modelo(q)['pago'],pago_ficticio())

    def test_partial_malformed_and_absent_secrets_never_block_documents(self):
        _,_,q=propuesta()
        for datos in ({},None,'incorrecto',{**pago_ficticio(),'banco':''},{**pago_ficticio(),'titular':'x'*1000}):
            with self.subTest(tipo=type(datos).__name__):
                q['documento'].update(pago=datos,incluir_pago=True)
                self.assertFalse(pago_para_documento(q['documento']))
                self.assertNotIn('Datos para el pago','\n'.join(p.extract_text() for p in PdfReader(BytesIO(generar_pdf(q))).pages))
                self.assertNotIn('Datos para el pago',texto_word(Document(BytesIO(generar_word(q)))))
        with patch('streamlit.secrets',{'pago':pago_ficticio()}):self.assertEqual(leer_pago_secrets(),pago_ficticio())
        with patch('streamlit.secrets',{}):self.assertFalse(any(leer_pago_secrets().values()))
        with patch('streamlit.secrets',Mock(get=Mock(side_effect=FileNotFoundError))):self.assertFalse(any(leer_pago_secrets().values()))


class PagoEditorTests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_preload_edit_reload_snapshot_and_independent_next_quote(self):
        app,repo=self.setup_app()
        with patch('paginas.cotizador.leer_pago_secrets',return_value=pago_ficticio()) as secretos:
            app.run();base.AppTests.create_request(self,app)
            self.assertTrue(base.by_label(app.toggle,'Incluir datos de pago').value)
            self.assertEqual(base.by_label(app.text_input,'Banco').value,pago_ficticio()['banco'])
            base.by_label(app.text_input,'N° de cuenta').set_value('9999999999').run()
            base.by_label(app.number_input,'Valor base (CLP)').set_value(1000000).run()
            self.assertEqual(secretos.call_count,1)
        cid=repo.case_rows[0]['id']
        with patch('paginas.cotizador.leer_pago_secrets',side_effect=AssertionError('No reemplazar un borrador existente')):
            fresh=base.AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
            fresh.session_state['auth_client']=repo.client;fresh.run();base.ir_a(fresh,'Casos y cotizaciones')
            base.by_label(fresh.selectbox,'Abrir detalle').set_value(cid).run()
            self.assertEqual(base.by_label(fresh.text_input,'N° de cuenta').value,'9999999999')
            base.by_label(fresh.button,'Generar cotización').click().run();self.assert_clean(fresh)
        emitida=deepcopy(repo.quote_rows[0])
        self.assertEqual(emitida['documento']['pago']['numero_cuenta'],'9999999999')
        base.by_label(fresh.text_input,'N° de cuenta').set_value('8888888888').run()
        self.assertEqual(repo.quote_rows[0],emitida)
        self.assertEqual(pago_ficticio()['numero_cuenta'],'0000000000')
        # Otro caso obtiene una copia nueva, sin tocar los secretos ni la versión.
        nuevo=deepcopy(repo.case_rows[0]);nuevo.update(id='caso-ficticio-2',numero=2,estado='Solicitud')
        repo.case_rows.append(nuevo)
        with patch('paginas.cotizador.leer_pago_secrets',return_value=pago_ficticio()):
            fresh.session_state['dashboard_revision']=fresh.session_state.get('dashboard_revision',0)+1
            fresh.run()
            base.by_label(fresh.selectbox,'Abrir detalle').set_value(nuevo['id']).run()
            self.assertEqual(base.by_label(fresh.text_input,'N° de cuenta').value,'0000000000')
            base.by_label(fresh.toggle,'Incluir datos de pago').set_value(False).run()
            self.assertFalse(repo.draft_rows[nuevo['id']]['datos']['incluir_pago'])

    def test_public_and_client_form_never_show_payment_fields(self):
        for cliente in (True,False):
            app,repo=self.setup_app(owner=not cliente)
            if not cliente:app.query_params['vista']='solicitud'
            app.run();self.assert_clean(app)
            contenido=' '.join(e.value for e in app.markdown)
            self.assertNotIn('Datos para el pago',contenido)
            self.assertFalse(any(e.label in CAMPOS_PAGO.values() for e in app.text_input))
            self.assertFalse(any(e.label=='Incluir datos de pago' for e in app.toggle))


if __name__=='__main__':
    out=Path('output/pago-cotizacion');out.mkdir(parents=True,exist_ok=True)
    for nombre,q in muestras_pago():
        (out/(nombre+'.pdf')).write_bytes(generar_pdf(q))
        (out/(nombre+'.docx')).write_bytes(generar_word(q))
    print('Cinco muestras con datos ficticios generadas.')
