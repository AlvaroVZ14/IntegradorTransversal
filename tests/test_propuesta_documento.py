"""Contrato de documento v2, listas y persistencia. Todos los datos son ficticios."""
from copy import deepcopy
from datetime import date,timedelta
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from docx import Document
from pypdf import PdfReader
import test_app as base
from datos_cotizacion_ficticios import ejemplo
from servicios.propuesta_documento import ampliar_borrador,modelo,folio
from servicios.cotizacion_asistida import datos_emision
from servicios.documentos_cotizacion import generar_pdf,generar_word,nombre_archivo
from mente_futuro.domain import quote_total
from mente_futuro.domain import today
from servicios.repositorio import Repository


def propuesta():
    caso,d,q=ejemplo();ampliar_borrador(d,caso)
    d.update(fecha_emision='2026-11-02',valida_hasta='2026-12-02',modalidad='Híbrida',
        jornadas_duracion='2 jornadas de 3 horas cada una',participantes=18,
        item_descripcion='Programa de colaboración, seis horas',base_clp=1000000,
        descuento_pct=0,descuento_motivo='')
    d['textos'].update(objetivos='Construir acuerdos prácticos de colaboración y comunicación para el equipo.',
        metodologia='La jornada se desarrolla en tres momentos participativos.',dirigido_a='',
        descripcion='Programa práctico con ejercicios de comunicación y acuerdos de colaboración.')
    d['objetivos_especificos']=[{'id':str(i),'texto':x} for i,x in enumerate([
        'Identificar oportunidades de coordinación entre áreas.',
        'Ensayar conversaciones para resolver diferencias.',
        'Construir acuerdos verificables de colaboración.',
        'Definir compromisos para las próximas semanas.'])]
    d['momentos']=[{'id':str(i),'etiqueta':a,'descripcion':b} for i,(a,b) in enumerate([
        ('Conectar','Conversación inicial y reconocimiento de experiencias del equipo.'),
        ('Practicar','Ejercicios en grupos pequeños con retroalimentación entre participantes.'),
        ('Acordar','Síntesis compartida y compromisos de aplicación cotidiana.')])]
    q.update(datos_emision(d));q.update(numero=4,fecha_emision=d['fecha_emision'],total_clp=1000000)
    return caso,d,q


def muestras():
    _,_,q=propuesta()
    largo=deepcopy(q);largo['numero']=5;largo['descuento_pct']=15;largo['descuento_motivo']='Convenio ficticio'
    largo['documento']['descuento_periodo']='del 1 al 30 de noviembre'
    largo['iva_pct']=19;largo['total_clp']=quote_total(1000000,15,19)
    largo['documento']['objetivos_especificos']=[{'texto':f'{i+1}. Acuerdo ficticio de coordinación y revisión de compromisos del equipo.'} for i in range(45)]
    largo['condiciones']='\n'.join(f'Condición {i+1}: Los horarios y espacios se acuerdan entre las partes antes de la jornada.' for i in range(35))+'\nFIN DE CONDICIONES'
    reducido=deepcopy(q);reducido['numero']=6;reducido['documento']['mostrar'].update(objetivos=False,metodologia=False,descripcion=False)
    return [('propuesta-ficticia',q),('propuesta-extensa',largo),('propuesta-sin-programa',reducido)]


class PropuestaTests(unittest.TestCase):
    def test_pdf_two_pages_and_required_structure(self):
        _,d,q=propuesta();reader=PdfReader(BytesIO(generar_pdf(q)))
        self.assertEqual(len(reader.pages),2)
        a,b=[p.extract_text() for p in reader.pages]
        for x in ('COTIZACIÓN DE SERVICIOS','2 de noviembre 2026','1. Objetivos','Objetivos específicos','2. Metodología','Conectar:'):self.assertIn(x,a)
        for x in ('3. Detalle del servicio','4. Valor del servicio','5. Condiciones generales','Híbrida','2 jornadas de 3 horas','$1.000.000.-','TOTAL'):self.assertIn(x,b)
        self.assertNotIn('Por definir',b)
        self.assertEqual(folio(q),'MF-2026-0004')
        self.assertTrue(nombre_archivo(q).startswith('Cotizacion_MF-2026-0004_'))

    def test_optional_sections_numbering_totals_and_long_content(self):
        for nombre,q in muestras():
            pdf=PdfReader(BytesIO(generar_pdf(q)))
            texto='\n'.join(p.extract_text() for p in pdf.pages)
            if nombre=='propuesta-extensa':
                self.assertGreater(len(pdf.pages),2)
                for x in ('15%','del 1 al 30 de noviembre','IVA 19%','$1.011.500','FIN DE CONDICIONES','45. Acuerdo'):self.assertIn(x,texto)
            if nombre=='propuesta-sin-programa':
                self.assertNotIn('Objetivo general',texto)
                self.assertNotIn('Programa práctico',texto)
                self.assertIn('1. Detalle del servicio',texto)
                self.assertEqual(len(pdf.pages),1)
            word=Document(BytesIO(generar_word(q)))
            contenido='\n'.join(p.text for p in word.paragraphs)+'\n'+'\n'.join(c.text for t in word.tables for r in t.rows for c in r.cells)
            self.assertIn('COTIZACIÓN DE SERVICIOS',contenido)
            self.assertIn('TOTAL',contenido)
            self.assertNotIn('{{',contenido)
        _,_,q=propuesta();original=deepcopy(q);generar_pdf(q);generar_word(q);self.assertEqual(q,original)


class EditorPropuestaTests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_lists_reorder_remove_reload_generate_and_preview(self):
        app,repo=self.setup_app();app.run();base.AppTests.create_request(self,app)
        base.by_label(app.number_input,'Valor base (CLP)').set_value(1000000).run()
        base.by_label(app.toggle,'Exento de IVA').set_value(False).run()
        self.assertEqual(base.by_label(app.metric,'Total de la propuesta (CLP)').value,'$1.190.000')
        self.assertTrue(base.by_label(app.text_area,'Condiciones comerciales').value.startswith('Valor neto más IVA 19%.'))
        base.by_label(app.toggle,'Exento de IVA').set_value(True).run()
        base.by_label(app.date_input,'Fecha de emisión').set_value(date(2026,1,10)).run()
        base.by_label(app.button,'Agregar objetivo específico').click().run()
        base.by_label(app.text_area,'Objetivo específico 1').set_value('Primer objetivo ficticio').run()
        base.by_label(app.button,'Agregar objetivo específico').click().run()
        base.by_label(app.text_area,'Objetivo específico 2').set_value('Segundo objetivo ficticio').run()
        next(b for b in app.button if b.label=='↑ Subir' and not b.disabled).click().run()
        self.assertEqual(base.by_label(app.text_area,'Objetivo específico 1').value,'Segundo objetivo ficticio')
        base.by_label(app.button,'Agregar momento').click().run()
        base.by_label(app.text_input,'Etiqueta 1').set_value('Practicar').run()
        base.by_label(app.text_area,'Descripción del momento 1').set_value('Ejercicio ficticio').run()
        cid=repo.case_rows[0]['id']
        datos=repo.draft_rows[cid]['datos']
        self.assertEqual(datos['objetivos_especificos'][0]['texto'],'Segundo objetivo ficticio')
        self.assertEqual(datos['momentos'][0]['etiqueta'],'Practicar')
        primero=next(b for b in app.button if b.label=='Quitar');primero.click().run()
        self.assertEqual(len(repo.draft_rows[cid]['datos']['objetivos_especificos']),1)
        fresh=base.AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
        fresh.session_state['auth_client']=repo.client;fresh.run();base.ir_a(fresh,'Casos y cotizaciones')
        base.by_label(fresh.selectbox,'Abrir detalle').set_value(cid).run()
        self.assertEqual(base.by_label(fresh.text_area,'Objetivo específico 1').value,'Primer objetivo ficticio')
        self.assertTrue(any(e.label=='Vista previa del documento' for e in fresh.expander))
        base.by_label(fresh.button,'Generar cotización').click().run();self.assert_clean(fresh)
        self.assertEqual(repo.quote_rows[0]['documento']['momentos'][0]['etiqueta'],'Practicar')
        self.assertEqual(repo.quote_rows[0]['fecha_emision'],'2026-01-10')
        self.assertTrue(any(b.label=='Redactar correo' for b in fresh.get('link_button')))


class CompatibilidadRPC(unittest.TestCase):
    def test_fallback_only_for_missing_rpc_and_today_without_retrying_other_errors(self):
        class ErrorRPC(Exception):pass
        caso={'id':'ficticio','version':1}
        for fecha,codigo,permitido in [(today().isoformat(),'PGRST202',True),('2020-01-01','PGRST202',False),(today().isoformat(),'42501',False),(today().isoformat(),'40001',False)]:
            with self.subTest(fecha=fecha,codigo=codigo):
                error=ErrorRPC();error.code=codigo
                client=Mock();client.rpc.return_value.execute.side_effect=[error,SimpleNamespace(data={'id':'version-ficticia'})]
                repo=Repository(client,SimpleNamespace(id='admin-ficticia'),{'rol':'admin'})
                datos={'fecha_emision':fecha,'documento':{'formato_version':2}}
                if permitido:
                    self.assertEqual(repo.issue_quote(caso,datos,'op-ficticia')['id'],'version-ficticia')
                    self.assertEqual([x.args[0] for x in client.rpc.call_args_list],['mf_emitir_propuesta_v2','mf_emitir_cotizacion'])
                else:
                    with self.assertRaises(ErrorRPC):repo.issue_quote(caso,datos,'op-ficticia')
                    self.assertEqual(client.rpc.call_count,1)


if __name__=='__main__':
    carpeta=Path('output/propuesta19');carpeta.mkdir(parents=True,exist_ok=True)
    for nombre,q in muestras():
        (carpeta/(nombre+'.pdf')).write_bytes(generar_pdf(q))
        (carpeta/(nombre+'.docx')).write_bytes(generar_word(q))
    print('Tres muestras ficticias generadas.')
