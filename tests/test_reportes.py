"""Límites inclusivos y calendario chileno, con registros exclusivamente ficticios."""
from datetime import date
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest

from servicios.reportes import AGRUPACIONES,INDICADORES,fecha_chile,reporte_periodos,totales_reporte,exportar_reporte
from mente_futuro.domain import dashboard_data


def muestra():
    fechas=['2024-01-01T03:00:00Z','2024-03-31T23:00:00-03:00','2024-04-01T02:59:59Z',
            '2024-07-01T04:00:00Z','2024-12-31T23:59:59-03:00','2025-01-01T03:00:00Z',
            '2024-01-01T02:59:59Z']
    casos=[dict(id=str(i),numero=i+1,cliente='Empresa ficticia',servicio='Coaching individual',
        tematica='Liderazgo',estado='Solicitud',created_at=f) for i,f in enumerate(fechas)]
    dias=['2024-01-01','2024-03-31','2024-04-01','2024-07-01','2024-12-31','2025-01-01','2023-12-31']
    quotes=[dict(id='q'+str(i),caso_id=str(i),fecha_emision=f) for i,f in enumerate(dias)]
    quotes.append(dict(id='q-version',caso_id='2',created_at='2024-04-01T02:59:59Z'))
    ventas=[dict(caso_id=str(i),fecha_venta=f,monto_clp=(i+1)*100000,anulada=False,
        estado_pago='Pagado' if i in (1,4) else 'Abono recibido' if i==2 else 'Pendiente')
        for i,f in enumerate(dias)]
    ventas.append(dict(caso_id='0',fecha_venta='2024-06-01',monto_clp=999999,anulada=True,estado_pago='Pendiente'))
    return casos,quotes,ventas


class ReportesTests(unittest.TestCase):
    def test_four_groupings_preserve_range_totals_and_dashboard_definitions(self):
        casos,quotes,ventas=muestra()
        esperado={'Solicitudes':5,'Cotizaciones emitidas':6,'Ventas cerradas':5,
                  'Total vendido (CLP)':1500000,'Ventas con pago pendiente (CLP)':800000}
        for grupo in AGRUPACIONES:
            with self.subTest(grupo=grupo):
                frame=reporte_periodos(casos,quotes,ventas,date(2024,1,1),date(2024,12,31),grupo)
                self.assertEqual(totales_reporte(frame),esperado)
                domain=dashboard_data(casos,ventas,date(2024,1,1),date(2024,12,31))
                self.assertEqual(frame['Total vendido (CLP)'].sum(),domain['total'])
                self.assertEqual(frame['Solicitudes'].sum(),domain['requests_count'])
                self.assertEqual(frame['Ventas cerradas'].sum(),domain['sales_count'])
                self.assertEqual(frame['Ventas con pago pendiente (CLP)'].sum(),domain['pending_payment'])

    def test_calendar_quarters_semesters_and_zero_months(self):
        datos=muestra()
        args=(*datos,date(2024,1,1),date(2024,12,31))
        mensual=reporte_periodos(*args,'Mensual')
        self.assertEqual(len(mensual),12)
        self.assertEqual(mensual.iloc[1][list(INDICADORES)].tolist(),[0]*5)
        trimestre=reporte_periodos(*args,'Trimestral')
        self.assertEqual(trimestre['Desde'].tolist(),[date(2024,m,1) for m in (1,4,7,10)])
        self.assertEqual(trimestre['Total vendido (CLP)'].tolist(),[300000,300000,400000,500000])
        semestre=reporte_periodos(*args,'Semestral')
        self.assertEqual(semestre['Total vendido (CLP)'].tolist(),[600000,900000])

    def test_single_day_includes_start_end_and_chile_midnight(self):
        for grupo in AGRUPACIONES:
            frame=reporte_periodos(*muestra(),date(2024,3,31),date(2024,3,31),grupo)
            self.assertEqual(len(frame),1)
            self.assertEqual(frame.iloc[0]['Desde'],date(2024,3,31))
            self.assertEqual(frame.iloc[0]['Hasta'],date(2024,3,31))
            self.assertEqual(totales_reporte(frame),{'Solicitudes':2,'Cotizaciones emitidas':2,
                'Ventas cerradas':1,'Total vendido (CLP)':200000,'Ventas con pago pendiente (CLP)':0})

    def test_multi_year_and_partial_periods(self):
        datos=muestra()
        totales=[]
        for grupo in AGRUPACIONES:
            frame=reporte_periodos(*datos,date(2023,12,31),date(2025,1,1),grupo)
            totales.append(totales_reporte(frame))
            self.assertEqual(frame.iloc[0]['Desde'],date(2023,12,31))
            self.assertEqual(frame.iloc[-1]['Hasta'],date(2025,1,1))
        self.assertTrue(all(t==totales[0] for t in totales))
        self.assertEqual(totales[0]['Total vendido (CLP)'],2800000)

    def test_empty_range_has_every_period_and_csv_is_excel_readable(self):
        for grupo,n in zip(AGRUPACIONES,(36,12,6,3)):
            frame=reporte_periodos([],[],[],date(2023,1,1),date(2025,12,31),grupo)
            self.assertEqual(len(frame),n)
            self.assertFalse(any(totales_reporte(frame).values()))
        frame=reporte_periodos(*muestra(),date(2024,1,1),date(2024,12,31))
        csv=exportar_reporte(frame)
        self.assertTrue(csv.startswith(b'\xef\xbb\xbf'))
        read=pd.read_csv(BytesIO(csv),sep=';',encoding='utf-8-sig')
        self.assertEqual(read['Total vendido (CLP)'].sum(),1500000)
        self.assertEqual(read.iloc[0]['Desde'],'01/01/2024')

    def test_invalid_range_and_unsupported_group_rejected(self):
        with self.assertRaisesRegex(ValueError,'Elige Desde y Hasta'):
            reporte_periodos([],[],[],None,date(2024,1,1))
        with self.assertRaisesRegex(ValueError,'Desde no puede'):
            reporte_periodos([],[],[],date(2024,2,1),date(2024,1,1))
        with self.assertRaises(ValueError):reporte_periodos([],[],[],date(2024,1,1),date(2024,2,1),'Semanal')
        self.assertEqual(fecha_chile('2024-04-01T02:59:59Z'),date(2024,3,31))
        self.assertEqual(fecha_chile('2024-04-01'),date(2024,4,1))


class ReportesUITests(unittest.TestCase):
    def test_admin_generates_table_graph_csv_and_reload(self):
        app=AppTest.from_string('''
from paginas.reportes import contenido_reportes
from test_reportes import muestra
from test_app import FakeRepository
repo=FakeRepository(True)
casos,repo.quote_rows,ventas=muestra()
contenido_reportes(repo,casos,ventas)
''',default_timeout=20)
        for k,v in dict(reporte_desde=date(2024,1,1),reporte_hasta=date(2024,12,31)).items():app.session_state[k]=v
        for _ in range(2):
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.dataframe[0].value),13)
            self.assertEqual(app.dataframe[0].value.iloc[-1]['Total vendido (CLP)'],'$1.500.000')
            self.assertEqual(len(app.get('plotly_chart')),1)
            self.assertEqual(app.get('download_button')[0].label,'Descargar reporte CSV')
        next(x for x in app.date_input if x.key=='reporte_desde').set_value(date(2025,1,1))
        app.button[0].click().run()
        self.assertTrue(any('Desde no puede' in w.value for w in app.warning))
        self.assertFalse(app.dataframe)

    def test_dashboard_opens_report_panel_only_for_admin(self):
        from test_app import AppTests,ir_a
        caso=AppTests()
        self.addCleanup(caso.doCleanups)
        app,repo=caso.setup_app()
        repo.case_rows,repo.quote_rows,repo.sale_rows=muestra()
        app.run();ir_a(app,'Dashboard')
        self.assertFalse(app.dataframe)
        app.session_state['reportes_panel']=True
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe),1)
        self.assertEqual(app.get('download_button')[-1].label,'Descargar reporte CSV')

    def test_client_cannot_render_or_query_report(self):
        from paginas.reportes import contenido_reportes
        repo=SimpleNamespace(profile={'rol':'cliente'},all_quotes=Mock())
        with self.assertRaises(PermissionError):contenido_reportes(repo,[],[])
        repo.all_quotes.assert_not_called()
