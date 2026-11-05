"""Regresión: las acciones de cotización no se superponen al formulario."""
import re
import unittest
import test_app as base
import test_cotizador as editor
from ui.tema import ESTILOS_BASE


class PanelCotizacionTests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean
    abrir=editor.EditorUITests.abrir

    def test_cerrar_aviso_conserva_version_y_borrador(self):
        app,repo=self.abrir()
        base.by_label(app.text_area,'Objetivo general').set_value('Objetivo ficticio que se conserva.').run()
        base.by_label(app.button,'Generar cotización').click().run()
        self.assert_clean(app)
        cid=repo.case_rows[0]['id'];qid=repo.quote_rows[0]['id']
        self.assertEqual(app.session_state['cotizacion_lista'],qid)
        aviso=next(c for c in app.get('flex_container') if c.key=='mfy_quote_downloads')
        cerrar=next(b for b in aviso.button if b.label=='Cerrar aviso')
        self.assertEqual(cerrar.key,'close_ready_'+qid)
        cerrar.click().run();self.assert_clean(app)
        self.assertNotIn('cotizacion_lista',app.session_state)
        self.assertEqual(len(repo.quote_rows),1)
        self.assertEqual(repo.draft_rows[cid]['datos']['textos']['objetivos'],'Objetivo ficticio que se conserva.')
        self.assertTrue(any(b.label=='Descargar Word' for b in app.get('download_button')))
        self.assertTrue(any(b.label=='Descargar PDF' for b in app.get('download_button')))
        self.assertFalse(any(b.label=='Cerrar aviso' for b in app.button))

    def test_paneles_en_flujo_no_crean_capas_fijas(self):
        # Evalúa las declaraciones de cada selector, incluidas reglas compartidas.
        for selector in ('.st-key-mfy_generate','.st-key-mfy_quote_downloads'):
            bloques=[body for nombres,body in re.findall(r'([^{}]+)\{([^{}]*)\}',ESTILOS_BASE) if selector in nombres.split(',')]
            self.assertTrue(bloques)
            self.assertFalse(any(re.search(r'position\s*:\s*(fixed|sticky)',b) for b in bloques))
            self.assertFalse(any('overflow-y:auto' in b for b in bloques))
        self.assertNotIn('.stMainBlockContainer:has(.mfy-quote-total){padding-bottom:180px}',ESTILOS_BASE)


if __name__=='__main__':unittest.main()
