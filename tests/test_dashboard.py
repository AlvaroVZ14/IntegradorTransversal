from datetime import date
import unittest

import pandas as pd

from servicios.dashboard import (AGRUPACIONES, ajustar_rango, agrupar_por_periodo, datos_dashboard,
                                etiqueta_periodo, inicio_periodo, rango_anterior, rango_rapido, variacion)


def caso(id="a",fecha="2026-01-02T12:00:00Z",servicio="Coaching individual",tematica="Liderazgo",estado="Cotizado"):
    return dict(id=id,numero=1,cliente="Empresa ficticia",created_at=fecha,servicio=servicio,tematica=tematica,estado=estado)


def venta(id="a",fecha="2026-01-15",monto=1250000,anulada=False,pago="Pendiente"):
    return dict(caso_id=id,fecha_venta=fecha,monto_clp=monto,anulada=anulada,estado_pago=pago)


class DashboardTests(unittest.TestCase):
    def test_empty_range_includes_every_period(self):
        expected={"Semanal":53,"Mensual":12,"Trimestral":4,"Semestral":2,"Anual":1}
        for grouping,n in expected.items():
            data=datos_dashboard([],[],date(2026,1,1),date(2026,12,31),grouping)
            self.assertEqual(len(data['series']),n)
            self.assertEqual(data['series'].total.sum(),0)
            self.assertIsNone(data['average'])
            self.assertIsNone(data['conversion'])

    def test_one_sale_conserves_amount_and_zero_periods(self):
        for grouping in AGRUPACIONES:
            data=datos_dashboard([caso()],[venta()],date(2026,1,1),date(2026,12,31),grouping)
            self.assertEqual(data['total'],1250000)
            self.assertEqual(data['average'],1250000)
            self.assertEqual(data['sales_count'],1)
            self.assertEqual(data['series'].total.sum(),1250000)
            self.assertEqual(data['series'].cantidad.sum(),1)
            self.assertEqual((data['series'].total>0).sum(),1)

    def test_iso_week_monday_and_year_boundary(self):
        self.assertEqual(inicio_periodo(date(2026,10,18),'Semanal'),date(2026,10,12))
        self.assertEqual(etiqueta_periodo(date(2026,10,12),'Semanal'),'Sem 42 · 12–18 oct')
        df=pd.DataFrame([venta(fecha='2021-01-01'),venta(fecha='2021-01-04')])
        series=agrupar_por_periodo(df,'Semanal',date(2020,12,28),date(2021,1,10))
        self.assertEqual(series.cantidad.tolist(),[1,1])
        self.assertTrue(series.periodo.iloc[0].startswith('Sem 53'))
        self.assertTrue(series.periodo.iloc[1].startswith('Sem 01'))

    def test_quarter_semester_and_year_boundaries(self):
        df=pd.DataFrame([venta(fecha=d,monto=100) for d in ['2026-03-31','2026-04-01','2026-06-30','2026-07-01']])
        self.assertEqual(agrupar_por_periodo(df,'Trimestral',date(2026,1,1),date(2026,12,31)).total.tolist(),[100,200,100,0])
        self.assertEqual(agrupar_por_periodo(df,'Semestral',date(2026,1,1),date(2026,12,31)).total.tolist(),[300,100])
        self.assertEqual(agrupar_por_periodo(df,'Anual',date(2025,1,1),date(2027,12,31)).total.tolist(),[0,400,0])

    def test_creation_chile_dates_and_sales_acceptance_are_separate(self):
        cases=[caso(fecha='2026-02-01T01:00:00Z')]
        data=datos_dashboard(cases,[venta(fecha='2026-02-10')],date(2026,1,1),date(2026,2,28))
        self.assertEqual(data['series'].solicitudes.tolist(),[1,0])
        self.assertEqual(data['series'].cantidad.tolist(),[0,1])
        self.assertEqual(data['conversion'],100)

    def test_cancelled_sales_and_future_cohort_sale_excluded(self):
        data=datos_dashboard([caso()],[venta(anulada=True)],date(2026,1,1),date(2026,1,31))
        self.assertEqual(data['total'],0)
        self.assertEqual(data['conversion'],0)
        self.assertIsNone(data['average'])
        data=datos_dashboard([caso()],[venta(fecha='2026-02-01')],date(2026,1,1),date(2026,1,31))
        self.assertEqual(data['conversion'],0)

    def test_filters_apply_to_both_current_and_previous(self):
        cases=[caso(),caso('b',servicio='Coaching dúo',tematica='Comunicación efectiva'),caso('c',tematica='Comunicación efectiva')]
        sales=[venta('a',monto=100),venta('b',monto=200),venta('c',monto=300)]
        data=datos_dashboard(cases,sales,date(2026,1,1),date(2026,3,31),'Mensual','Coaching individual','Comunicación efectiva')
        self.assertEqual(data['total'],300)
        self.assertEqual(data['requests_count'],1)
        self.assertEqual(data['pending_payment'],300)

    def test_zero_denominator_variations(self):
        self.assertEqual(variacion(150,100),50)
        self.assertEqual(variacion(50,100),-50)
        self.assertIsNone(variacion(100,0))
        self.assertIsNone(variacion(None,100))
        self.assertEqual(variacion(0,0),0)

    def test_previous_block_depends_on_grouping(self):
        self.assertEqual(rango_anterior(date(2026,7,1),date(2026,12,31),'Mensual'),(date(2026,1,1),date(2026,6,30)))
        self.assertEqual(rango_anterior(date(2026,7,1),date(2026,12,31),'Trimestral'),(date(2026,1,1),date(2026,6,30)))
        self.assertEqual(rango_anterior(date(2026,7,1),date(2026,12,31),'Anual'),(date(2025,1,1),date(2025,12,31)))

    def test_variation_against_previous_sales(self):
        cases=[caso('a',fecha='2025-12-01T12:00:00Z'),caso('b')]
        data=datos_dashboard(cases,[venta('a','2025-12-20',100),venta('b','2026-01-15',150)],date(2026,1,1),date(2026,1,31))
        self.assertEqual(data['variations']['total'],50)
        self.assertEqual(data['previous']['total'],100)

    def test_quick_ranges_and_minimum_visible_periods(self):
        today=date(2026,10,21)
        self.assertEqual(rango_rapido('Últimos 6 meses',today),(date(2026,5,1),today))
        self.assertEqual(rango_rapido('Últimas 8 semanas',today),(date(2026,8,31),today))
        self.assertEqual(rango_rapido('Año anterior',today),(date(2025,1,1),date(2025,12,31)))
        start,end,message=ajustar_rango(date(2026,10,20),today,'Semanal')
        self.assertEqual(start,date(2026,9,28));self.assertEqual(end,today);self.assertTrue(message)
        start,end,message=ajustar_rango(today,today,'Trimestral')
        self.assertEqual(start,date(2026,7,1));self.assertTrue(message)

    def test_two_argument_aggregation_with_explicit_frame_range(self):
        df=pd.DataFrame(columns=['fecha_venta','monto_clp'])
        df.attrs.update(desde=date(2026,1,1),hasta=date(2026,3,31))
        self.assertEqual(len(agrupar_por_periodo(df,'Mensual')),3)
        with self.assertRaises(ValueError): agrupar_por_periodo(df,'Diaria')

    def test_states_use_consistent_labels(self):
        data=datos_dashboard([caso()],[],date(2026,1,1),date(2026,2,28))
        self.assertEqual(data['states'].estado.tolist(),['Cotizada'])

    def test_chart_count_axes_use_integer_ticks(self):
        from paginas.dashboard import grafico_conteos,grafico_periodos
        spec=grafico_conteos(pd.DataFrame({'estado':['Cotizada'],'Casos':[1]}),'estado','Casos').to_plotly_json()
        self.assertEqual(spec['layout']['xaxis']['tickformat'],',d')
        self.assertEqual(spec['layout']['xaxis']['dtick'],1)
        data=datos_dashboard([caso()],[venta()],date(2026,1,1),date(2026,3,31))
        spec=grafico_periodos(data['series'],solicitudes=True).to_plotly_json()
        self.assertEqual(spec['layout']['yaxis']['dtick'],1)

    def test_adjust_reversed_dates(self):
        start,end,message=ajustar_rango(date(2026,3,31),date(2026,1,1),'Mensual')
        self.assertEqual((start,end),(date(2026,1,1),date(2026,3,31)))
        self.assertTrue(message)
