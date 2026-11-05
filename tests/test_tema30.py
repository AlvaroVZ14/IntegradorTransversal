"""Presupuestos y regresiones del sistema visual; datos exclusivamente ficticios."""
from pathlib import Path
import unittest
from unittest.mock import Mock
from xml.etree import ElementTree
import test_app as base
from servicios.imagenes import ICONO_PORTAL,LOGO_DOCUMENTOS,LOGO_PORTAL,ILUSTRACIONES
from ui import tema


def contraste(a,b):
    def luminancia(color):
        rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
        linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        return sum(c*p for c,p in zip(linear,(.2126,.7152,.0722)))
    luces=sorted((luminancia(a),luminancia(b)))
    return (luces[1]+.05)/(luces[0]+.05)


class TemaTests(unittest.TestCase):
    def test_presupuesto_css_e_imagenes_sin_recursos_externos(self):
        # Presupuesto de 20 KiB, incluidos los estilos nuevos de estados.
        self.assertLess(sum(len(s.encode()) for s in (tema.ESTILOS_BASE,tema.CSS_COPIAR,tema.CSS_EN_VIVO)),20*1024)
        for ruta in (ICONO_PORTAL,LOGO_PORTAL,*ILUSTRACIONES.values()):
            with self.subTest(ruta=ruta.name):
                self.assertLess(ruta.stat().st_size,10000)
                xml=ElementTree.fromstring(ruta.read_text(encoding='utf-8'))
                self.assertEqual(xml.tag,'{http://www.w3.org/2000/svg}svg')
                self.assertNotIn('<script',ruta.read_text(encoding='utf-8'))
                self.assertNotIn('href=',ruta.read_text(encoding='utf-8'))
        self.assertEqual(LOGO_DOCUMENTOS.name,'logo-mente-y-futuro.jpeg')

    def test_contraste_aa_textos_estados_y_degradado(self):
        pares=[('#FFFFFF','#315BBC'),('#FFFFFF','#6D38B6'),('#FFFFFF','#1B2F6B'),
               ('#5B6B82','#FFFFFF'),('#0B2545','#EAF1FF'),('#6533A8','#F1ECFF')]
        pares += [(fg,bg) for _,bg,fg in tema.ESTADOS_COLORES.values()]
        for fg,bg in pares:
            with self.subTest(fg=fg,bg=bg):self.assertGreaterEqual(contraste(fg,bg),4.5)

    def test_sin_fuentes_pesadas_ni_animacion_continua(self):
        for prohibido in ('@import','backdrop-filter','filter:blur','infinite'):
            self.assertNotIn(prohibido,tema.ESTILOS_BASE)
        for esperado in ('max-width:1200px','max-width:767px','max-width:1023px',
                         'prefers-reduced-motion','prefers-reduced-data','data-mfy-light=true'):
            self.assertIn(esperado,tema.ESTILOS_BASE)

    def test_adaptadores_y_html_seguro(self):
        from utils.componentes import encabezado_pagina
        from utils.estilos import ESTILOS_BASE
        self.assertIs(encabezado_pagina,tema.encabezado_pagina)
        self.assertIs(ESTILOS_BASE,tema.ESTILOS_BASE)
        html=tema.html_contenido_encabezado('<script>','<img>','MENTE Y FUTURO · CLIENTES','')
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;img&gt;',html)
        self.assertEqual(html.count('MENTE Y FUTURO'),1)


class GuiaTests(unittest.TestCase):
    def setUp(self):
        self.base=base.AppTests()
        self.addCleanup(self.base.doCleanups)

    def test_guia_admin_oculta_y_modo_ligero_sin_escrituras(self):
        app,repo=self.base.setup_app(True)
        repo.live_snapshot=Mock(wraps=repo.live_snapshot)
        app.run()
        self.assertEqual(base.menu_visible(app),['Hoy','Nueva solicitud','Casos y cotizaciones','Compartir','Dashboard'])
        self.assertTrue(any(p.label=='Guía de estilo' for p in app.get('page_link')))
        n=repo.live_snapshot.call_count
        base.by_label(app.toggle,'Modo ligero').set_value(True).run()
        self.base.assert_clean(app)
        self.assertTrue(app.session_state['tema_modo_ligero'])
        self.assertEqual(n,repo.live_snapshot.call_count)
        base.ir_a(app,'Guía de estilo');self.base.assert_clean(app)
        self.assertEqual(repo.case_rows,[])
        self.assertTrue(any(b.label=='Guardar ejemplo' for b in app.button))

    def test_cliente_no_accede_guia_ni_cambia_su_menu(self):
        app,_=self.base.setup_app(False)
        app.session_state['pending_navigation']='Guía de estilo'
        app.run();self.base.assert_clean(app)
        self.assertEqual(app.session_state['navigation'],'Mis documentos')
        self.assertEqual(base.menu_visible(app),['Solicitar servicio','Mis documentos'])
        self.assertFalse(any(p.label=='Guía de estilo' for p in app.get('page_link')))


if __name__=='__main__':unittest.main()
