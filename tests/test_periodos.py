"""Fechas de borde y totales ficticios del Dashboard; sin servicios externos."""
from datetime import date, timedelta
from unittest import TestCase
from unittest.mock import patch
import test_app as base
from test_dashboard import caso, venta
from servicios.periodos import (AGRUPACIONES, inicio_periodo, fin_periodo, mover_periodo,
    periodo_vigente, periodo_anterior, navegar_periodo, puede_avanzar, etiqueta_rango,
    fecha_chile, validar_rango)
from servicios.dashboard import datos_dashboard


class PeriodosTests(TestCase):
    def test_calendario_noviembre_y_etiquetas_exactas(self):
        hoy=date(2026,11,3)
        esperados=[(date(2026,11,1),date(2026,11,30),'Mes: noviembre 2026'),
            (date(2026,10,1),date(2026,12,31),'Trimestre 4 de 2026'),
            (date(2026,7,1),date(2026,12,31),'Semestre 2 de 2026'),
            (date(2026,1,1),date(2026,12,31),'Año 2026')]
        for grupo,(desde,hasta,nombre) in zip(AGRUPACIONES,esperados):
            self.assertEqual(periodo_vigente(grupo,hoy),(desde,hasta))
            self.assertEqual(etiqueta_rango(desde,hasta,grupo),f'{nombre} · {desde:%d/%m/%Y} – {hasta:%d/%m/%Y}')

    def test_febrero_bisiesto_y_no_bisiesto(self):
        self.assertEqual(fin_periodo(date(2024,2,1),'Mensual'),date(2024,2,29))
        self.assertEqual(fin_periodo(date(2026,2,28),'Mensual'),date(2026,2,28))
        self.assertEqual(mover_periodo(date(2024,2,29),1,'Anual'),date(2025,2,28))
        self.assertEqual(periodo_anterior(date(2024,3,1),date(2024,3,31)),(date(2024,1,30),date(2024,2,29)))

    def test_primer_ultimo_dia_trimestre_y_cambio_de_anio(self):
        for primero,ultimo in [(date(2026,1,1),date(2026,3,31)),(date(2026,4,1),date(2026,6,30)),
                               (date(2026,7,1),date(2026,9,30)),(date(2026,10,1),date(2026,12,31))]:
            for fecha in (primero,ultimo):
                self.assertEqual(inicio_periodo(fecha,'Trimestral'),primero)
                self.assertEqual(fin_periodo(fecha,'Trimestral'),ultimo)
        self.assertEqual(navegar_periodo(date(2026,1,1),'Trimestral',-1,date(2026,11,3)),
                         (date(2025,10,1),date(2025,12,31)))
        self.assertEqual(navegar_periodo(date(2026,1,1),'Mensual',-1,date(2026,11,3)),
                         (date(2025,12,1),date(2025,12,31)))

    def test_no_navega_a_periodos_futuros_pero_completa_el_actual(self):
        hoy=date(2026,11,3)
        for grupo in AGRUPACIONES:
            inicio,fin=periodo_vigente(grupo,hoy)
            self.assertFalse(puede_avanzar(inicio,grupo,hoy))
            with self.assertRaises(ValueError):navegar_periodo(inicio,grupo,1,hoy)
            anterior=navegar_periodo(inicio,grupo,-1,hoy)
            self.assertTrue(puede_avanzar(anterior[0],grupo,hoy))
            self.assertEqual(navegar_periodo(anterior[0],grupo,1,hoy),(inicio,fin))

    def test_comparacion_contigua_de_igual_numero_de_dias(self):
        for desde,hasta in [(date(2026,11,1),date(2026,11,30)),(date(2026,12,31),date(2026,12,31)),
                            (date(2024,1,1),date(2024,12,31)),(date(2023,12,30),date(2026,1,3))]:
            a,b=periodo_anterior(desde,hasta)
            self.assertEqual(hasta-desde,b-a);self.assertEqual(b+timedelta(days=1),desde)
        with self.assertRaises(ValueError):validar_rango(date(2026,4,1),date(2026,3,31))
        self.assertEqual(fecha_chile('2026-04-01T01:00:00Z'),date(2026,3,31))

    def test_totales_inclusivos_ventas_anuladas_ceros_y_desglose(self):
        for grupo in AGRUPACIONES:
            desde,hasta=periodo_vigente(grupo,date(2026,11,3))
            fechas=[desde-timedelta(days=1),desde,hasta,hasta+timedelta(days=1)]
            casos=[caso(str(i),fecha=f'{d}T12:00:00Z') for i,d in enumerate(fechas)]
            ventas=[venta(str(i),str(d),100*(i+1)) for i,d in enumerate(fechas)]
            ventas.append(venta('1',str(desde),999999,anulada=True))
            data=datos_dashboard(casos,ventas,desde,hasta,grupo)
            self.assertEqual(data['total'],500);self.assertEqual(data['requests_count'],2)
            self.assertEqual(data['series'].total.sum(),500);self.assertEqual(data['evolution'].total.sum(),500)
            self.assertEqual(data['evolution'].solicitudes.sum(),2)
            self.assertEqual(data['evolution_grouping'],'Semanal' if grupo=='Mensual' else 'Mensual')
            self.assertGreater(len(data['evolution']),1)
            vacio=datos_dashboard([],[],desde,hasta,grupo)
            self.assertEqual(vacio['evolution'].total.sum(),0);self.assertGreater(len(vacio['evolution']),1)
            self.assertIsNone(vacio['variations']['total'])
        un_dia=datos_dashboard([caso()],[venta()],date(2026,1,15),date(2026,1,15))
        self.assertEqual(un_dia['total'],1250000)
        self.assertEqual(un_dia['previous_range'],(date(2026,1,14),date(2026,1,14)))

    def test_comparacion_usa_las_ventas_del_bloque_exactamente_indicado(self):
        dias=['2026-10-01','2026-10-02','2026-10-31','2026-11-01','2026-11-30']
        casos=[caso(str(i),fecha=d+'T12:00:00Z') for i,d in enumerate(dias)]
        ventas=[venta(str(i),d,monto) for i,(d,monto) in enumerate(zip(dias,[900,100,100,300,100]))]
        data=datos_dashboard(casos,ventas,date(2026,11,1),date(2026,11,30))
        self.assertEqual(data['previous_range'],(date(2026,10,2),date(2026,10,31)))
        self.assertEqual(data['total'],400);self.assertEqual(data['previous']['total'],200)
        self.assertEqual(data['variations']['total'],100)
        for grupo in AGRUPACIONES:
            varios=datos_dashboard(casos,ventas,date(2025,1,1),date(2027,12,31),grupo)
            self.assertEqual(varios['evolution_grouping'],grupo)
            self.assertEqual(varios['evolution'].total.sum(),varios['total'])
            self.assertEqual(varios['series'].total.sum(),1500)


class PeriodosUITests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_filtros_navegacion_personalizado_y_error_no_aplica(self):
        app,repo=self.setup_app()
        with patch('paginas.dashboard.today',return_value=date(2026,11,3)):
            app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertEqual(base.by_label(app.selectbox,'Agrupar por').options,list(AGRUPACIONES))
            self.assertFalse(any(x.label in ('Rango rápido','Servicio','Temática') for x in app.selectbox))
            self.assertTrue(base.by_label(app.button,'Siguiente').disabled)
            base.by_label(app.selectbox,'Agrupar por').set_value('Trimestral').run();self.assert_clean(app)
            self.assertEqual(app.session_state['dash_aplicado'][:2],(date(2026,10,1),date(2026,12,31)))
            self.assertIn('Trimestre 4 de 2026',' '.join(x.value for x in app.markdown))
            base.by_label(app.button,'Anterior').click().run()
            self.assertEqual(app.session_state['dash_aplicado'][:2],(date(2026,7,1),date(2026,9,30)))
            base.by_label(app.button,'Siguiente').click().run()
            base.by_label(app.date_input,'Desde').set_value(date(2026,10,2)).run()
            self.assertIn('Rango personalizado',' '.join(x.value for x in app.markdown))
            aplicado=app.session_state['dash_aplicado']
            base.by_label(app.date_input,'Hasta').set_value(date(2026,10,1)).run();self.assert_clean(app)
            self.assertEqual(app.session_state['dash_aplicado'],aplicado)
            self.assertTrue(any('Desde no puede ser posterior' in x.value for x in app.warning))
            base.by_label(app.button,'Limpiar').click().run();self.assert_clean(app)
            self.assertFalse(app.warning);self.assertFalse(app.session_state['dash_aplicado'][3])
            self.assertEqual(base.by_label(app.selectbox,'Agrupar por').value,'Trimestral')
            self.assertTrue(any('Sin datos del período anterior' in x.value for x in app.caption))
            self.assertTrue(all(not m.delta for m in app.metric))

    def test_rango_sobrevive_refresco_y_cambio_de_pagina(self):
        app,repo=self.setup_app()
        with patch('paginas.dashboard.today',return_value=date(2026,11,3)):
            app.session_state['dashboard_mobile']=True
            app.run();base.ir_a(app,'Dashboard')
            base.by_label(app.selectbox,'Agrupar por').set_value('Semestral').run()
            base.by_label(app.button,'Anterior').click().run()
            aplicado=app.session_state['dash_aplicado']
            app.run();self.assertEqual(app.session_state['dash_aplicado'],aplicado)
            base.ir_a(app,'Hoy');base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertEqual(app.session_state['dash_aplicado'],aplicado)
            self.assertEqual(base.by_label(app.date_input,'Desde').value,aplicado[0])
            self.assertEqual(base.by_label(app.selectbox,'Agrupar por').value,'Semestral')
            self.assertTrue(any(x.label=='Filtros' for x in app.expander))

    def test_filtros_retirados_no_dejan_restricciones_ocultas(self):
        app,repo=self.setup_app()
        repo.case_rows=[caso('a',fecha='2026-11-02T12:00:00Z'),
            caso('b',fecha='2026-11-03T12:00:00Z',servicio='Coaching dúo',tematica='Comunicación efectiva')]
        repo.sale_rows=[venta('a','2026-11-02',100),venta('b','2026-11-03',200)]
        app.session_state['dash_servicio']='Coaching individual'
        app.session_state['dash_tematica']='Liderazgo'
        with patch('paginas.dashboard.today',return_value=date(2026,11,3)):
            app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertEqual(base.by_label(app.metric,'Total vendido').value,'$300')
            self.assertEqual(base.fila_indicador(app,'Solicitudes recibidas en el período')['Valor'],'2')
            self.assertNotIn('dash_servicio',app.session_state)
            self.assertNotIn('dash_tematica',app.session_state)
