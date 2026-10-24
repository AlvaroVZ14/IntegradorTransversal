"""Flujos con AppTest y cambios externos ficticios, sin Supabase real."""
import unittest
from unittest.mock import Mock, patch
import test_app as base


class EnVivoUI(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def test_dashboard_external_request_filters_failure_and_recovery(self):
        app,repo=self.setup_app()
        repo.live_snapshot=Mock(wraps=repo.live_snapshot)
        with patch('servicios.en_vivo.time',return_value=120) as clock:
            app.run();base.ir_a(app,'Dashboard')
            base.by_label(app.selectbox,'Temática').set_value('Liderazgo').run()
            base.by_label(app.selectbox,'Agrupar por').set_value('Semanal').run()
            self.assertEqual(repo.live_snapshot.call_count,2) # Hoy + Dashboard.
            repo.case_rows=[dict(id='empresa-ficticia',numero=1,cliente='Empresa Ficticia',servicio='Coaching individual',
                tematica='Liderazgo',estado='Solicitud',created_at=base.today().isoformat()+'T12:00:00Z',origen='Formulario web',modalidad='Online')]
            clock.return_value=180;app.run()
            self.assert_clean(app)
            self.assertEqual(base.by_label(app.metric,'Nuevas solicitudes').value,'1')
            self.assertEqual(base.by_label(app.selectbox,'Temática').value,'Liderazgo')
            self.assertEqual(base.by_label(app.selectbox,'Agrupar por').value,'Semanal')
            self.assertFalse(any(b.label=='Actualizar' for b in app.button))
            repo.live_snapshot.side_effect=ConnectionError('Fallo ficticio');clock.return_value=240;app.run()
            self.assert_clean(app)
            self.assertEqual(base.by_label(app.metric,'Nuevas solicitudes').value,'1')
            self.assertFalse(app.session_state['en_vivo']['dashboard']['conectado'])
            repo.live_snapshot.side_effect=None;clock.return_value=300;app.run()
            self.assert_clean(app)
            self.assertTrue(app.session_state['en_vivo']['dashboard']['conectado'])

    def test_list_selection_is_explicit_and_can_return_without_losing_filter(self):
        app,repo=self.setup_app();app.run()
        base.AppTests.create_request(self,app)
        self.assertTrue(any(b.label=='Volver al listado' for b in app.button))
        base.by_label(app.button,'Volver al listado').click().run()
        self.assert_clean(app)
        self.assertIsNone(base.by_label(app.selectbox,'Abrir detalle').value)
        self.assertFalse(any(x.label=='Contacto' for x in app.text_input))
        base.by_label(app.selectbox,'Abrir detalle').set_value(repo.case_rows[0]['id']).run()
        self.assert_clean(app)
        self.assertTrue(any(x.label=='Contacto' for x in app.text_input))


if __name__=='__main__':unittest.main()
