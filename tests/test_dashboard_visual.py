from datetime import date
import unittest

import pandas as pd

from datos_dashboard_ficticios import datos_ficticios
from servicios.dashboard import datos_dashboard
from utils.estilos import AMARILLO, AZUL
from utils.graficos_dashboard import (dona, embudo_estados, modalidades, origenes, reparto,
                                     solicitudes_vs_ventas, tematicas_dona, ventas_por_periodo)


class VisualDashboardTests(unittest.TestCase):
    def setUp(self):
        self.casos,self.ventas=datos_ficticios()
        self.data=datos_dashboard(self.casos,self.ventas,date(2026,5,1),date(2026,10,21))

    def test_sales_keep_zero_points_and_highlight(self):
        fig=ventas_por_periodo(self.data['series'])
        self.assertIn(0,list(fig.data[0].y))
        self.assertEqual(fig.data[0].line.color,AZUL)
        self.assertEqual(fig.data[2].marker.color,AMARILLO)
        self.assertEqual(fig.data[0].fill,'tozeroy')
        self.assertEqual(fig.layout.template.layout.separators,',.')
        self.assertEqual(sum(fig.data[0].y),self.data['total'])

    def test_empty_figures_have_no_axes(self):
        empty=datos_dashboard([],[],date(2026,5,1),date(2026,10,21))
        self.assertIsNone(ventas_por_periodo(empty['series']))
        self.assertIsNone(solicitudes_vs_ventas(empty['series']))
        self.assertIsNone(tematicas_dona(empty['topics']))
        self.assertIsNone(embudo_estados(empty['states']))
        self.assertIsNone(origenes([]))
        self.assertIsNone(modalidades([]))
        self.assertIsNone(reparto([]))

    def test_topics_preserve_total_and_group_other(self):
        frame=pd.DataFrame({'tematica':[f'Tema ficticio {i}' for i in range(7)],'Solicitudes':[7,6,5,4,3,2,1]})
        fig=tematicas_dona(frame)
        self.assertIn('Otras',fig.data[0].labels)
        self.assertEqual(sum(fig.data[0].values),28)
        self.assertEqual(len(fig.data[0].labels),6)

    def test_referral_and_unknown_modality_are_not_lost(self):
        self.assertIn('Referido por colega',origenes(self.casos).data[0].y)
        fig=modalidades(self.casos)
        self.assertIn('Por definir',fig.data[0].labels)
        self.assertIn('Híbrida',fig.data[0].labels)
        self.assertEqual(sum(fig.data[0].values),len(self.casos))

    def test_partition_requires_real_fields(self):
        self.assertIsNone(reparto([{'monto_clp':1000}]))
        self.assertIsNone(reparto([{'reserva_clp':None,'remuneracion_clp':1000}]))
        fig=reparto(self.ventas)
        self.assertEqual(sum(fig.data[0].values),sum(v['monto_clp'] for v in self.ventas))

    def test_reduced_motion_and_funnel_labels(self):
        fig=ventas_por_periodo(self.data['series'],reduced_motion=True)
        self.assertEqual(fig.layout.transition.duration,0)
        self.assertEqual(embudo_estados(self.data['states']).data[0].y,('Solicitud','Cotizada','Aceptada','En seguimiento','Cerrada'))
