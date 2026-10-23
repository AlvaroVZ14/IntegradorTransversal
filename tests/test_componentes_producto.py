"""Comprueba escape de datos en los nuevos componentes HTML, sin cuentas reales."""
from datetime import date
import unittest

import pandas as pd

from utils.componentes import html_tabla_registros, badge_estado, html_contenido_encabezado


class SeguridadPresentacionTests(unittest.TestCase):
    def test_table_escapes_untrusted_content_and_preserves_chilean_date(self):
        frame=pd.DataFrame([{'Cliente':'<script>alert(1)</script>',
            'Estado':'<img src=x onerror=alert(2)>', 'Fecha':date(2026,10,22)}])
        html=html_tabla_registros(frame,'<b>Título</b>')
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('&lt;b&gt;Título&lt;/b&gt;',html)
        self.assertIn('22/10/2026',html)
        self.assertIn('data-label="Cliente"',html)

    def test_review_substage_has_official_badge_without_changing_stored_value(self):
        self.assertIn('>Solicitud</span>',badge_estado('En revisión'))
        self.assertIn('title="Solicitud en revisión"',badge_estado('En revisión'))
        self.assertIn('>Cotizada</span>',badge_estado('Cotizado'))

    def test_shared_header_escapes_every_text_argument(self):
        html=html_contenido_encabezado('<script>titulo</script>', '<img src=x>',
                                      '<b>solicitudes</b>', '<svg onload=alert(1)>')
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img',html)
        self.assertNotIn('<svg',html)
        self.assertIn('&lt;script&gt;titulo&lt;/script&gt;',html)
        self.assertIn('aria-hidden="true"',html)
