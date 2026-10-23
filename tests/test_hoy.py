"""Seis categorías y acciones con registros ficticios; no se contacta a nadie."""
from copy import deepcopy
from datetime import datetime,timedelta
from unittest.mock import Mock
import unittest

import test_app as base
from test_app import by_label,ir_a
from servicios.hoy import CHILE,configuracion_hoy,pendientes,mensaje_listo,saludo
from utils.validaciones import validar_campo


def datos(ahora=None):
    ahora=ahora or datetime.now(CHILE)
    def c(n,estado='Solicitud',dias=10,**extra):
        return dict(dict(id='caso-'+str(n),numero=n,created_at=(ahora-timedelta(days=dias)).isoformat(),version=1,
            cliente='Fundación Horizonte '+str(n),contacto='Daniela Soto',email='daniela@example.test',telefono='912345678',
            servicio='Coaching individual',tematica='Liderazgo',participantes=12,horas=2.0,modalidad='Online',
            lugar='Antofagasta',detalle='Desarrollar habilidades.',estado=estado,fecha_preferida=None,fecha_realizacion=None),**extra)
    casos=[c(1),c(2,dias=20),c(3,'Cotizado'),c(4,'En ejecución',email='incorrecto',modalidad='Por definir'),
        c(5,'En ejecución'),c(6,'En ejecución',fecha_realizacion=(ahora.date()-timedelta(days=1)).isoformat()),c(7,'Finalizado')]
    def q(n):return dict(id='quote-'+str(n),caso_id='caso-'+str(n),numero=n,created_at=(ahora-timedelta(days=6)).isoformat(),
        fecha_emision=(ahora.date()-timedelta(days=6)).isoformat(),valida_hasta=(ahora.date()+timedelta(days=20)).isoformat(),
        total_clp=420000,base_clp=420000,descuento_pct=0,iva_pct=0,detalle='Programa ficticio',condiciones='Prueba',snapshot=deepcopy(casos[n-1]),
        documento=dict(textos=dict(descripcion='Texto ajustado ficticio',objetivos='Colaborar mejor',metodologia='Actividad práctica',dirigido_a='Equipo',incluye='Dos horas'),mostrar={}))
    quotes=[q(3),q(5),q(6),q(7)]
    ventas=[dict(id='venta-5',caso_id='caso-5',monto_clp=420000,estado_pago='Abono recibido',anulada=False,version=1,cotizacion_id='quote-5',fecha_venta=ahora.date().isoformat()),
        dict(id='venta-6',caso_id='caso-6',monto_clp=420000,estado_pago='Pagado',anulada=False,version=1,cotizacion_id='quote-6',fecha_venta=ahora.date().isoformat())]
    envios=[dict(id='envio-7',caso_id='caso-7',cotizacion_id='quote-7',estado='incierto',canal='correo',destinatario='daniela@example.test',created_at=ahora.isoformat())]
    return casos,quotes,ventas,[],envios


class HoyRulesTests(unittest.TestCase):
    def setUp(self):
        self.ahora=datetime(2026,10,22,12,tzinfo=CHILE)
        self.datos=datos(self.ahora);self.config=configuracion_hoy()

    def test_each_card_and_oldest_first_without_mutations(self):
        copia=deepcopy(self.datos)
        grupos=pendientes(*self.datos,self.config,self.ahora)
        self.assertEqual([i['caso']['id'] for i in grupos['solicitudes']],['caso-2','caso-1'])
        self.assertEqual([i['dias'] for i in grupos['solicitudes']],[20,10])
        self.assertEqual([len(grupos[k]) for k in ('seguimientos','datos','pagos','cierres','correos')],[1,1,1,1,1])
        self.assertIn('Correo',grupos['datos'][0]['faltantes'])
        self.assertEqual(self.datos,copia)

    def test_followup_cooldown_is_for_current_quote_and_configurable(self):
        casos,quotes,ventas,eventos,envios=deepcopy(self.datos)
        eventos.append(dict(caso_id='caso-3',cotizacion_id='quote-3',tipo='seguimiento',datos=dict(tipo_mensaje='seguimiento'),created_at=(self.ahora-timedelta(days=1)).isoformat()))
        self.assertFalse(pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)['seguimientos'])
        eventos[0]['created_at']=(self.ahora-timedelta(days=3)).isoformat()
        self.assertEqual(len(pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)['seguimientos']),1)
        config={**self.config,'dias_sin_respuesta':10}
        self.assertFalse(pendientes(casos,quotes,ventas,eventos,envios,config,self.ahora)['seguimientos'])

    def test_preferred_date_is_not_proof_and_annulled_sale_is_excluded(self):
        casos,quotes,ventas,eventos,envios=deepcopy(self.datos)
        casos[5]['fecha_realizacion']=None;casos[5]['fecha_preferida']='2026-10-01'
        grupos=pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)
        self.assertFalse(grupos['cierres'])
        self.assertTrue(any(i['caso']['id']=='caso-6' for i in grupos['datos']))
        ventas[0]['anulada']=True
        self.assertFalse(pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)['pagos'])
        self.assertIsNotNone(validar_campo('fecha_realizacion','2099-01-01'))

    def test_email_failure_review_does_not_change_send(self):
        casos,quotes,ventas,eventos,envios=deepcopy(self.datos)
        eventos.append(dict(caso_id='caso-7',tipo='correo_revisado',datos=dict(envio_id='envio-7',estado='incierto')))
        self.assertFalse(pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)['correos'])
        envios[0]['estado']='error'
        self.assertEqual(len(pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)['correos']),1)

    def test_chile_dates_greeting_and_template_variables(self):
        casos,quotes,ventas,_,_=self.datos
        casos=deepcopy(casos[:1]);casos[0]['created_at']='2026-10-22T01:00:00Z'
        grupo=pendientes(casos,[],[],[],[],self.config,self.ahora)
        self.assertEqual(grupo['solicitudes'][0]['dias'],1)
        asunto,texto=mensaje_listo('seguimiento',self.datos[0][2],quotes[0],None,self.config)
        self.assertIn('Daniela Soto',texto);self.assertIn('COT-2026-0003',texto)
        self.assertNotIn('{contacto}',texto)
        self.assertEqual([saludo(h) for h in (8,15,21)],['Buenos días','Buenas tardes','Buenas noches'])

    def test_accepted_without_sale_is_actionable_and_sale_uses_accepted_quote(self):
        casos,quotes,ventas,eventos,envios=deepcopy(self.datos)
        casos[4]['estado']='Vendido'
        grupos=pendientes(casos,quotes,[],eventos,envios,self.config,self.ahora)
        self.assertTrue(any('Venta por registrar' in t['faltantes'] for t in grupos['datos']))
        nueva={**quotes[1],'id':'quote-nueva','numero':99,'fecha_emision':'2026-10-22','created_at':self.ahora.isoformat()}
        quotes.append(nueva)
        grupos=pendientes(casos,quotes,ventas,eventos,envios,self.config,self.ahora)
        self.assertEqual(grupos['pagos'][0]['cotizacion']['id'],'quote-5')


class HoyUITests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def preparar(self):
        app,repo=self.setup_app()
        repo.case_rows,repo.quote_rows,repo.sale_rows,repo.event_rows,repo.email_rows=datos()
        return app,repo

    def test_admin_starts_on_today_and_client_cannot_open_it(self):
        app,repo=self.setup_app();app.run()
        self.assert_clean(app)
        self.assertEqual(app.session_state['navigation'],'Hoy')
        self.assertTrue(any('Todo al día. Buen trabajo' in s.value for s in app.success))
        cliente,r=self.setup_app(False)
        r.all_quotes=Mock(side_effect=AssertionError('No debe consultar'))
        cliente.query_params['pagina']='Hoy';cliente.run()
        self.assert_clean(cliente);self.assertEqual(cliente.session_state['navigation'],'Nueva solicitud')
        r.all_quotes.assert_not_called()

    def test_login_redirects_to_today_even_from_an_old_dashboard_url(self):
        app,repo=self.setup_app()
        app.query_params['pagina']='Dashboard'
        app.session_state['inicio_tras_login']=True
        app.run();self.assert_clean(app)
        self.assertEqual(app.session_state['navigation'],'Hoy')
        ir_a(app,'Dashboard');self.assert_clean(app)
        self.assertEqual(app.session_state['navigation'],'Dashboard')

    def test_cards_are_read_only_and_shortcuts_reach_the_selected_case(self):
        app,repo=self.preparar();antes=deepcopy(repo.case_rows);app.run()
        self.assert_clean(app);self.assertEqual(repo.case_rows,antes);self.assertFalse(repo.event_rows)
        for label in ('Cotizar','Hacer seguimiento','Completar','Registrar pago','Cerrar caso','Revisar envío'):
            self.assertTrue(any(b.label==label for b in app.button),label)
        primero=next(b for b in app.button if b.label=='Cotizar')
        primero.click().run()
        self.assert_clean(app);self.assertEqual(app.session_state['selected_case'],'caso-2')
        self.assertEqual(app.session_state['navigation'],'Casos y cotizaciones')

    def test_followup_preview_does_not_log_until_explicit_action(self):
        app,repo=self.preparar();app.run()
        by_label(app.button,'Hacer seguimiento').click().run()
        self.assert_clean(app);self.assertFalse(repo.event_rows)
        self.assertIn('Daniela Soto',by_label(app.text_area,'Mensaje').value)
        by_label(app.button,'Registrar seguimiento realizado').click().run()
        self.assert_clean(app);self.assertEqual(len(repo.event_rows),1)
        self.assertFalse(any(b.label=='Hacer seguimiento' for b in app.button))
        self.assertEqual(repo.case_rows[2]['estado'],'Cotizado')

    def test_close_undo_and_cycle_suggestions(self):
        app,repo=self.preparar();app.run()
        by_label(app.button,'Cerrar caso').click().run()
        self.assert_clean(app);self.assertEqual(repo.case_rows[5]['estado'],'Finalizado')
        self.assertTrue(any(b.label=='Preparar agradecimiento' for b in app.button))
        self.assertTrue(any(b.label=='Guardar como plantilla' for b in app.button))
        by_label(app.button,'Deshacer').click().run()
        self.assert_clean(app);self.assertEqual(repo.case_rows[5]['estado'],'En ejecución')
        self.assertEqual(len(repo.sale_rows),2)

    def test_configuration_preserves_issuer_and_quote_settings(self):
        app,repo=self.setup_app();app.run();ir_a(app,'Casos y cotizaciones')
        emisor=deepcopy(repo.settings_row['datos']['emisor'])
        by_label(app.number_input,'Días sin respuesta para sugerir seguimiento').set_value(8)
        by_label(app.button,'Guardar avisos y mensajes').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.settings_row['datos']['hoy']['dias_sin_respuesta'],8)
        self.assertEqual(repo.settings_row['datos']['emisor'],emisor)
        by_label(app.button,'Guardar configuración').click().run()
        self.assert_clean(app);self.assertEqual(repo.settings_row['datos']['hoy']['dias_sin_respuesta'],8)

    def test_payment_and_missing_data_shortcuts_and_email_review(self):
        app,repo=self.preparar();app.run()
        by_label(app.button,'Registrar pago').click().run()
        self.assert_clean(app);self.assertEqual(app.session_state['selected_case'],'caso-5')
        self.assertTrue(any(t.label=='Venta' for t in app.tabs))
        ir_a(app,'Hoy')
        by_label(app.button,'Marcar revisado').click().run()
        self.assert_clean(app);self.assertFalse(any(b.label=='Revisar envío' for b in app.button))
        self.assertEqual(repo.email_rows[0]['estado'],'incierto')
