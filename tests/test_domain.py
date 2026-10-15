from datetime import date
import unittest

import pandas as pd

from mente_futuro.domain import dashboard_data, csv_bytes, money, quote_total, validate_request
from mente_futuro.presentation import quote_html


class DomainTests(unittest.TestCase):
    def test_reference_quotes_and_rounding(self):
        self.assertEqual(quote_total(4580000,15,0),3893000)
        self.assertEqual(quote_total(2650000,15,0),2252500)
        self.assertEqual(quote_total(420000,0,19),499800)
        self.assertEqual(quote_total(101,50,0),51)
        self.assertEqual(quote_total(100000,4.333,0),95670)
        self.assertEqual(money(2252500),"$2.252.500")

    def test_invalid_quote_amounts(self):
        for args in [(-1,0,0),(1,101,0),(1,0,20),(float('nan'),0,0)]:
            with self.assertRaises(ValueError): quote_total(*args)

    def test_empty_dashboard(self):
        d=dashboard_data([],[],date(2026,1,1),date(2026,3,31))
        self.assertEqual(d['total'],0)
        self.assertEqual(d['average'],0)
        self.assertEqual(d['conversion'],0)
        self.assertEqual(d['monthly'].monto_clp.tolist(),[0,0,0])

    def test_sale_dates_cancellation_and_chile_timezone(self):
        cases=[
            dict(id='old',created_at='2025-01-01T12:00:00Z',servicio='Coaching individual',tematica='Liderazgo'),
            dict(id='new',created_at='2026-01-02T12:00:00Z',servicio='Coaching individual',tematica='Comunicación'),
            dict(id='cancelled',created_at='2026-01-03T12:00:00Z',servicio='Coaching dúo',tematica='Liderazgo'),
            dict(id='boundary',created_at='2026-02-01T01:00:00Z',servicio='Coaching individual',tematica='Liderazgo'),
        ]
        sales=[
            dict(caso_id='old',fecha_venta='2026-01-10',monto_clp=100,anulada=False,estado_pago='Pagado'),
            dict(caso_id='new',fecha_venta='2026-02-10',monto_clp=200,anulada=False,estado_pago='Pendiente'),
            dict(caso_id='cancelled',fecha_venta='2026-01-10',monto_clp=999,anulada=True,estado_pago='Pendiente'),
        ]
        d=dashboard_data(cases,sales,date(2026,1,1),date(2026,1,31))
        self.assertEqual(d['total'],100)
        self.assertEqual(d['sales_count'],1)
        self.assertEqual(d['requests_count'],3)
        self.assertEqual(d['conversion'],0)
        d=dashboard_data(cases,sales,date(2026,1,1),date(2026,2,28),'Coaching individual')
        self.assertEqual(d['total'],300)
        self.assertEqual(d['conversion'],50)
        self.assertEqual(d['pending_payment'],200)

    def test_csv_formula_protection(self):
        text=csv_bytes(pd.DataFrame({'Cliente':['=1+1',' +cmd','normal']})).decode('utf-8-sig')
        self.assertIn("'=1+1",text)
        self.assertIn("' +cmd",text)

    def test_quote_export_escapes_customer_content(self):
        q=dict(numero=1,created_at='2026-01-01',snapshot={'cliente':'<script>alert(1)</script>'},fecha_emision='2026-01-01',valida_hasta='2026-02-01',detalle='<img onerror=x>',condiciones='A & B',base_clp=100,descuento_pct=0,iva_pct=0,total_clp=100)
        html=quote_html(q)
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('A &amp; B',html)

    def test_request_validation(self):
        self.assertGreaterEqual(len(validate_request({})),5)
        self.assertEqual(validate_request(dict(cliente='Empresa',contacto='Persona',email='test@example.cl',servicio='Coaching individual',tematica='Liderazgo',participantes=1,horas=1,modalidad='Online')),[])


if __name__ == '__main__': unittest.main()
