"""Flujo guiado y registro, solo repositorios y clientes ficticios."""
from copy import deepcopy
from datetime import date
from unittest.mock import patch
import unittest
from streamlit.testing.v1 import AppTest
import test_app as base
from datos_cotizacion_ficticios import ejemplo
from servicios.flujo_cotizaciones import (filtrar_registro,fecha_local,duplicar_borrador,
    comparar_versiones,siguiente_paso,PASOS,MOTIVOS_RECHAZO)


class PresentacionTests(unittest.TestCase):
    def test_fechas_filtros_orden_y_sin_importe(self):
        casos=[dict(id=str(i),created_at='2026-11-01T02:00:00Z',tematica='Liderazgo',importe_registro=m)
               for i,m in enumerate((None,0,100,200))]
        self.assertEqual(fecha_local(casos[0]['created_at']),date(2026,10,31))
        self.assertEqual(fecha_local('2026-11-01'),date(2026,11,1))
        self.assertEqual([c['importe_registro'] for c in filtrar_registro(casos,{},orden='Monto menor')],[0,100,200,None])
        self.assertEqual([c['importe_registro'] for c in filtrar_registro(casos,{},orden='Monto mayor')],[200,100,0,None])
        self.assertFalse(filtrar_registro(casos,{},desde=date(2026,11,1)))
        self.assertEqual(len(filtrar_registro(casos,{'tematica':['Liderazgo']},date(2026,10,31),date(2026,10,31))),4)
        self.assertFalse(filtrar_registro(casos,{'tematica':['Otro']}))

    def test_duplicar_conserva_vigencia_y_no_modifica_version(self):
        caso,d,q=ejemplo();d.update(fecha_emision='2026-11-05',valida_hasta='2026-12-05')
        original=deepcopy(q);q['documento']['textos']['objetivos']='Objetivo anterior ficticio'
        copia=duplicar_borrador(d,q)
        self.assertEqual(copia['fecha_emision'],'2026-11-05')
        self.assertEqual(copia['valida_hasta'],'2026-12-05')
        self.assertEqual(copia['textos']['objetivos'],'Objetivo anterior ficticio')
        copia['textos']['objetivos']='Nueva edición'
        self.assertNotEqual(copia['textos'],q['documento']['textos'])
        delta,items=comparar_versiones(q,original)
        self.assertEqual(delta,0);self.assertFalse(items)
        nuevo=deepcopy(q);nuevo['total_clp']+=10000;nuevo['documento']['item_descripcion']='Otro ítem'
        self.assertEqual(comparar_versiones(nuevo,q),(10000,['item_descripcion']))
        self.assertIn('Sin presupuesto',MOTIVOS_RECHAZO)
        self.assertEqual(siguiente_paso('Vendido')[:2],('Registrar venta','Venta'))


class FlujoUITests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def abrir(self):
        app,repo=self.setup_app();app.run();base.AppTests.create_request(self,app)
        base.by_label(app.number_input,'Valor base (CLP)').set_value(450000).run()
        return app,repo

    def test_asistente_atras_siguiente_y_rapida_sin_generacion_anticipada(self):
        with patch('paginas.cotizador.generar_pdf') as pdf,patch('paginas.cotizador.generar_word') as word:
            app,repo=self.abrir();cid=repo.case_rows[0]['id']
            pdf.assert_not_called();word.assert_not_called()
            self.assertTrue(all(any(t.label==p for t in app.tabs) for p in PASOS))
            base.by_label(app.button,'Siguiente').click().run()
            self.assertEqual(app.session_state['cot_tabs_'+cid],'Detalle')
            base.by_label(app.button,'Atrás').click().run()
            self.assertEqual(app.session_state['cot_tabs_'+cid],'Programa')
            base.by_label(app.button,'Cotización rápida').click().run()
            self.assertEqual(app.session_state['cot_tabs_'+cid],'Revisar y generar')
            self.assert_clean(app);self.assertFalse(repo.quote_rows)
        base.by_label(app.button,'Generar cotización').click().run()
        self.assert_clean(app);self.assertEqual(len(repo.quote_rows),1)
        with patch('paginas.acciones_cotizacion._archivos') as archivos:
            app.run();archivos.assert_not_called() # Historial diferido, no regenera al dibujar.
        self.assert_clean(app)

    def test_duplicacion_y_borrador_sin_red_se_recuperan(self):
        app,repo=self.abrir();cid=repo.case_rows[0]['id']
        base.by_label(app.button,'Generar cotización').click().run()
        base.by_label(app.text_area,'Objetivo general').set_value('Edición nueva ficticia').run()
        base.by_label(app.button,'Duplicar una cotización anterior').click().run()
        self.assertEqual(base.by_label(app.text_area,'Objetivo general').value,repo.quote_rows[0]['documento']['textos']['objetivos'])
        original=repo.save_quote_draft
        repo.save_quote_draft=lambda *args:(_ for _ in ()).throw(ConnectionError('Fallo ficticio'))
        base.by_label(app.text_area,'Objetivo general').set_value('Texto conservado sin red').run()
        self.assertEqual(app.session_state['cotizadores'][cid]['datos']['textos']['objetivos'],'Texto conservado sin red')
        repo.save_quote_draft=original
        app.session_state['cotizadores'][cid]['reintento']=0
        app.run();self.assert_clean(app)
        self.assertEqual(repo.draft_rows[cid]['datos']['textos']['objetivos'],'Texto conservado sin red')
        fresh=AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
        fresh.session_state['auth_client']=repo.client;fresh.run();base.ir_a(fresh,'Casos y cotizaciones')
        base.by_label(fresh.selectbox,'Abrir detalle').set_value(cid).run()
        self.assert_clean(fresh)
        self.assertEqual(base.by_label(fresh.text_area,'Objetivo general').value,'Texto conservado sin red')

    def test_paginacion_20_y_atajo_conserva_filtro(self):
        app,repo=self.abrir();caso=deepcopy(repo.case_rows[0])
        repo.case_rows=[{**caso,'id':str(i),'numero':i,'cliente':f'Empresa ficticia {i}'} for i in range(1,24)]
        app.session_state['selected_case']=None;app.session_state['caso_abierto']=None
        app.session_state['dashboard_revision']=100
        app.run();self.assert_clean(app)
        self.assertEqual(len([b for b in app.button if b.label=='Ver']),20)
        base.by_label(app.number_input,'Página').set_value(2).run()
        self.assertEqual(len([b for b in app.button if b.label=='Ver']),3)
        next(b for b in app.button if b.label=='Ver').click().run()
        self.assert_clean(app);self.assertTrue(app.session_state['caso_abierto'])
        base.by_label(app.button,'Volver al listado').click().run()
        self.assertEqual(base.by_label(app.number_input,'Página').value,2)
