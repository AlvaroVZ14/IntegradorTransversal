"""Tablero simple con demostración ficticia; sin escrituras ni llamadas externas."""
from copy import deepcopy
from datetime import date
from unittest import TestCase
from unittest.mock import Mock
import test_app as base
from servicios.dashboard_demo import datos_demo
from servicios.dashboard import datos_dashboard, ventas_por_dimension
from utils.graficos_dashboard import barras_ventas
from utils.estilos import ESTILOS_BASE


class DashboardSimpleTests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_demo_coherente_y_distribuciones_conservan_total(self):
        desde,hasta=date(2026,11,1),date(2026,11,30)
        casos,ventas=datos_demo(desde,hasta)
        data=datos_dashboard(casos,ventas,desde,hasta)
        self.assertEqual(data['total'],4080000)
        self.assertEqual(data['sales_count'],8);self.assertEqual(data['average'],510000)
        self.assertAlmostEqual(data['conversion'],100*8/12)
        self.assertEqual(data['pending_payment'],2040000)
        for dimension in ('tematica','servicio'):
            totales=ventas_por_dimension(casos,data['sales'].to_dict('records'),dimension)
            self.assertEqual(sum(totales.values()),data['total'])
            fig=barras_ventas(totales)
            self.assertEqual(sum(fig.data[0].x),data['total'])
            self.assertEqual(fig.layout.xaxis.tickprefix,'$')
            self.assertNotIn('solicitudes',fig.data[0].hovertemplate)

    def test_tematica_principal_caso_antiguo_y_anulacion(self):
        casos=[dict(id='a',created_at='2020-01-01',tematica='Liderazgo',tematicas=['Liderazgo','Otra'],servicio='Taller')]
        ventas=[dict(caso_id='a',monto_clp=100,anulada=False),dict(caso_id='a',monto_clp=999,anulada=True),
                dict(caso_id='sin-referencia',monto_clp=50,anulada=False)]
        self.assertEqual(ventas_por_dimension(casos,ventas,'tematica'),{'Liderazgo':100,'Sin información':50})
        self.assertIsNone(barras_ventas({}));self.assertIsNone(barras_ventas({'Taller':0}))

    def test_modo_demo_muestra_cinco_graficos_y_vuelve_a_datos_reales(self):
        app,repo=self.setup_app();app.run();base.ir_a(app,'Dashboard')
        antes=deepcopy((repo.case_rows,repo.sale_rows))
        repo.live_snapshot=Mock(wraps=repo.live_snapshot)
        base.by_label(app.toggle,'Ver datos de prueba').set_value(True).run();self.assert_clean(app)
        repo.live_snapshot.assert_not_called()
        self.assertEqual((repo.case_rows,repo.sale_rows),antes)
        self.assertEqual([m.label for m in app.metric],['Total vendido','Venta promedio','Conversión','Pago pendiente'])
        self.assertTrue(all(m.help for m in app.metric))
        self.assertEqual(base.by_label(app.metric,'Total vendido').value,'$4.080.000')
        self.assertEqual(len(app.get('plotly_chart')),5)
        self.assertEqual([s.value for s in app.subheader],['Ventas por período','Ventas por temática',
            'Ventas por tipo de servicio','Embudo de casos por estado','Origen de las solicitudes'])
        self.assertTrue(any('No son ventas reales' in i.value for i in app.info))
        self.assertFalse(any(e.label=='Reportes por período' for e in app.expander))
        base.by_label(app.toggle,'Ver datos de prueba').set_value(False).run();self.assert_clean(app)
        self.assertEqual(base.by_label(app.metric,'Total vendido').value,'$0')
        self.assertEqual(len(app.get('plotly_chart')),0)
        self.assertTrue(any(e.label=='Reportes por período' for e in app.expander))

    def test_grid_responsive_aislado_y_sin_datos(self):
        self.assertIn('.st-key-mfy_dashboard_kpis',ESTILOS_BASE)
        self.assertIn('calc(50% - 4px)',ESTILOS_BASE)
        self.assertIn('min-height:138px',ESTILOS_BASE)
        app,_=self.setup_app();app.session_state['dashboard_mobile']=True
        app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
        self.assertEqual(len(app.metric),4);self.assertFalse(app.get('plotly_chart'))
        self.assertTrue(any('Aún no hay ventas' in m.value for m in app.markdown))
