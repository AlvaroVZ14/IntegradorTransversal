"""Hoy y Registro: filtros, navegación y límites con casos ficticios."""
from copy import deepcopy
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch
import test_app as base
from test_hoy import datos
from servicios.hoy import CHILE, configuracion_hoy, pendientes, casos_por_accion


class HoyRegistroTests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def preparar(self):
        app,repo=self.setup_app()
        repo.case_rows,repo.quote_rows,repo.sale_rows,repo.event_rows,repo.email_rows=datos()
        return app,repo

    def tabla(self,app):
        return next(m.value for m in app.markdown if '<table' in m.value)

    def test_tres_tarjetas_sin_total_ni_contadores_de_cabecera(self):
        app,repo=self.preparar();antes=deepcopy(repo.case_rows);app.run();self.assert_clean(app)
        for key,label,valor in [('solicitudes','Por cotizar',2),('pagos','Pagos por registrar',1),
                                ('seguimientos','Cotizaciones sin respuesta',1)]:
            tarjeta=app.button(key='hoy_tarjeta_'+key)
            self.assertEqual(tarjeta.label,f'**{valor}**\n\n{label}')
            self.assertTrue(tarjeta.help)
        self.assertFalse(app.metric)
        contenido=' '.join(x.value for x in app.markdown)
        self.assertNotIn('<div class="mfy-glass-chips"',contenido);self.assertNotIn('Acciones pendientes',contenido)
        self.assertFalse(any('·' in s.value for s in app.subheader))
        self.assertEqual(repo.case_rows,antes)

    def test_cada_tarjeta_abre_registro_con_el_grupo_exacto(self):
        for key,label,esperados,excluidos in [
            ('solicitudes','Por cotizar',[1,2],[3,4,5,6,7]),
            ('pagos','Pagos por registrar',[5],[1,2,3,4,6,7]),
            ('seguimientos','Cotizaciones sin respuesta',[3],[1,2,4,5,6,7])]:
            with self.subTest(label=label):
                app,repo=self.preparar();app.run();antes=deepcopy(repo.case_rows)
                # La tarjeta debe limpiar búsquedas/detalles y la pestaña anterior.
                app.session_state['casos_busqueda']='No coincide'
                app.session_state['caso_abierto']='caso-7'
                app.session_state['casos_pestana']='Tarifas y servicios'
                app.button(key='hoy_tarjeta_'+key).click().run();self.assert_clean(app)
                self.assertEqual(app.session_state['navigation'],'Casos y cotizaciones')
                self.assertEqual(base.by_label(app.selectbox,'Filtrar estado').value,label)
                self.assertEqual(app.session_state['casos_pestana'],'Registro de casos')
                self.assertIsNone(base.by_label(app.selectbox,'Abrir detalle').value)
                tabla=self.tabla(app)
                for n in esperados:self.assertIn('Fundación Horizonte '+str(n),tabla)
                for n in excluidos:self.assertNotIn('Fundación Horizonte '+str(n),tabla)
                self.assertEqual(repo.case_rows,antes)

    def test_cinco_solicitudes_mas_antiguas_y_ver_todas(self):
        app,repo=self.preparar()
        ahora=datetime.now(CHILE)
        repo.quote_rows=[];repo.sale_rows=[];repo.event_rows=[];repo.email_rows=[]
        original=deepcopy(repo.case_rows[0])
        repo.case_rows=[{**original,'id':f'nueva-{i}','numero':i,'cliente':f'Empresa ficticia {i}',
                        'created_at':(ahora-timedelta(days=i)).isoformat()} for i in range(1,9)]
        app.run();self.assert_clean(app)
        cotizar=[b for b in app.button if b.label=='Cotizar']
        self.assertEqual(len(cotizar),5)
        nombres=' '.join(x.value for x in app.markdown if 'mfy-task-person' in x.value)
        self.assertIn('Empresa ficticia 8',nombres);self.assertNotIn('Empresa ficticia 1',nombres)
        base.by_label(app.button,'Ver todas').click().run();self.assert_clean(app)
        tabla=self.tabla(app)
        for i in range(1,9):self.assertIn(f'Empresa ficticia {i}',tabla)

    def test_chips_y_selector_sincronizados_y_buscador_conservado(self):
        app,repo=self.preparar();app.run();base.ir_a(app,'Casos y cotizaciones')
        grupos=app.get('button_group')
        chip=next(x for x in grupos if x.key=='casos_chips_estados')
        chip.set_value('Cotizado').run();self.assert_clean(app)
        self.assertEqual(base.by_label(app.selectbox,'Filtrar estado').value,'Cotizado')
        self.assertIn('Fundación Horizonte 3',self.tabla(app))
        self.assertNotIn('Fundación Horizonte 1',self.tabla(app))
        base.by_label(app.text_input,'Buscar un caso').set_value('Horizonte 3').run()
        self.assertIn('Fundación Horizonte 3',self.tabla(app))
        base.by_label(app.selectbox,'Filtrar estado').set_value('Solicitud').run();self.assert_clean(app)
        self.assertEqual(app.session_state['casos_chips_estados'],'Solicitud')
        self.assertEqual(base.by_label(app.text_input,'Buscar un caso').value,'Horizonte 3')
        self.assertFalse(app.metric)
        self.assertFalse(any('Solicitudes sin cotizar' in x.value for x in app.subheader))

    def test_mas_de_cinco_dias_y_mismas_reglas_en_registro(self):
        ahora=datetime(2026,11,3,12,tzinfo=CHILE)
        casos,q,v,e,env=datos(ahora)
        q[0]['fecha_emision']=(ahora.date()-timedelta(days=5)).isoformat()
        configuracion=configuracion_hoy()
        self.assertFalse(pendientes(casos,q,v,e,env,configuracion,ahora)['seguimientos'])
        q[0]['fecha_emision']=(ahora.date()-timedelta(days=6)).isoformat()
        snapshot=dict(casos=casos,cotizaciones=q,ventas=v,eventos=e,envios=env,configuracion={})
        for filtro,grupo in [('Por cotizar','solicitudes'),('Pagos por registrar','pagos'),('Cotizaciones sin respuesta','seguimientos')]:
            esperado=[i['caso'] for i in pendientes(casos,q,v,e,env,configuracion,ahora)[grupo]]
            self.assertEqual(casos_por_accion(snapshot,filtro,ahora),esperado)

    def test_compartir_compacto_reutiliza_url_sin_otra_consulta(self):
        app,repo=self.preparar();repo.settings_row['datos']['url_publica']='https://portal.example.test/'
        with patch('paginas.compartir.copiar_mensaje') as copiar:
            app.run();self.assert_clean(app)
            copiar.assert_called_once()
            self.assertEqual(copiar.call_args.args[0],'https://portal.example.test/?vista=solicitud&canal=directo')
            self.assertEqual(copiar.call_args.kwargs['etiqueta'],'Copiar enlace')
            self.assertTrue(any(p.label=='Más opciones' for p in app.get('page_link')))
