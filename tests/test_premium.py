"""Presentación con datos ficticios: accesibilidad, escape y límites de las series."""
from datetime import date
from xml.etree import ElementTree
import unittest
from utils.componentes import sparkline_svg,html_chips_vidrio
from utils.metricas_visuales import ingresos_seis_meses
from utils.metricas_visuales import contexto_cohortes


class PresentacionPremium(unittest.TestCase):
    def test_sparkline_preserves_gaps_zeroes_and_escapes_labels(self):
        svg=sparkline_svg([0,None,5,float('nan'),2,3],['<script>falso</script>','b','c','d','e','f'],'<key>')
        raiz=ElementTree.fromstring(svg)
        self.assertEqual(len(raiz.findall('circle')),4)
        self.assertEqual(len(raiz.findall('polyline')),3)
        self.assertIn('&lt;script&gt;',svg)
        self.assertNotIn('<script>',svg)
        self.assertNotIn('nan',svg)

    def test_no_history_is_invented_for_missing_data(self):
        self.assertEqual(sparkline_svg([None,None]),'')
        self.assertIn('0',sparkline_svg([0,0,0]))
        puntos,meses=ingresos_seis_meses([{'created_at':'2026-10-01T01:00:00Z'},
                                       {'created_at':'2026-10-22T15:00:00Z'},
                                       {'created_at':'2025-01-01'},{'created_at':None}],date(2026,10,23))
        self.assertEqual(meses,['05/2026','06/2026','07/2026','08/2026','09/2026','10/2026'])
        self.assertEqual(puntos,[0,0,0,0,1,1])
        self.assertIn('$1.250.000',sparkline_svg([1250000],formato='moneda'))
        self.assertIn('33,3%',sparkline_svg([100/3],formato='porcentaje'))

    def test_glass_chips_never_render_data_as_markup(self):
        html=html_chips_vidrio([('<img>','<script>ficticio</script>')])
        self.assertNotIn('<img>',html);self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)

    def test_context_graphs_use_same_sales_and_cohort_rules_as_existing_kpis(self):
        from datos_dashboard_ficticios import datos_ficticios
        from servicios.dashboard import datos_dashboard
        casos,ventas=datos_ficticios()
        data=datos_dashboard(casos,ventas,date(2026,5,1),date(2026,10,21))
        series=contexto_cohortes(data,ventas,date(2026,10,21))
        self.assertEqual(sum(series['pending_payment']),data['pending_payment'])
        self.assertEqual(len(series['conversion']),6)
        self.assertEqual(data['requests_count'],len(data['requests']))
