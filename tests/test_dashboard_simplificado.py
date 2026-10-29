"""Valores históricos de una muestra ficticia, conservados al reubicar tarjetas."""
from datetime import date
import unittest
from streamlit.testing.v1 import AppTest
import test_app as base
from datos_dashboard_ficticios import datos_ficticios


class DashboardSimplificadoTests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_admin_values_and_comparisons_survive_new_session(self):
        app,repo=self.setup_app()
        repo.case_rows,repo.sale_rows=datos_ficticios()
        filtros=dict(dash_agrupacion='Mensual',dash_rango='Personalizado',dash_desde=date(2026,5,1),
            dash_hasta=date(2026,10,21),dash_servicio='Todos',dash_tematica='Todas')
        esperados={'Total vendido':'$7.460.000','Cantidad de ventas':'6',
            'Solicitudes recibidas en el período':'12','Venta promedio':'$1.243.333',
            'Solicitudes que se vendieron':'50,0%','Ventas con pago pendiente':'$2.160.000'}
        for intento in range(2):
            if intento:
                app=AppTest.from_file(str(base.ROOT/'app.py'),default_timeout=20)
                app.session_state['auth_client']=repo.client
            for k,v in filtros.items():app.session_state[k]=v
            app.run();base.ir_a(app,'Dashboard');self.assert_clean(app)
            self.assertEqual([m.label for m in app.metric],['Total vendido','Venta promedio',
                'Solicitudes que se vendieron','Ventas con pago pendiente'])
            for label,valor in esperados.items():
                self.assertEqual(base.fila_indicador(app,label)['Valor'],valor)
            self.assertEqual(base.fila_indicador(app,'Cantidad de ventas')['Variación'],'Sin comparación previa')
            self.assertTrue(any('6 ventas registradas' in c.value for c in app.caption))
            self.assertIn('no casos en estado Cerrada',base.by_label(app.metric,'Total vendido').help)
            self.assertEqual(len(app.get('plotly_chart')),9)
            self.assertTrue(any(b.label=='Exportar resumen por período' for b in app.get('download_button')))
