"""Una llamada por ciclo, aislamiento, fallos y recuperación con datos ficticios."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from servicios import en_vivo


class LecturasTest(unittest.TestCase):
    def setUp(self):
        self.state={}
        self.st=patch.object(en_vivo.st,'session_state',self.state)
        self.st.start();self.addCleanup(self.st.stop)
        self.clock=patch.object(en_vivo,'time',return_value=120)
        self.now=self.clock.start();self.addCleanup(self.clock.stop)
        # No runtime de Streamlit: el caché real se comprueba en AppTest.
        self.fetch=patch.object(en_vivo,'_consultar',side_effect=lambda *a:(a[-1].live_snapshot(a[1]),self.now()))
        self.fetch.start();self.addCleanup(self.fetch.stop)
        self.repo=SimpleNamespace(owner_only=Mock(),live_snapshot=Mock(return_value={'casos':[],'ventas':[]}))

    def test_one_query_per_cycle_and_invalidation(self):
        en_vivo.cargar(self.repo,'dashboard');en_vivo.cargar(self.repo,'dashboard')
        self.assertEqual(self.repo.live_snapshot.call_count,1)
        self.now.return_value=180
        en_vivo.cargar(self.repo,'dashboard')
        self.assertEqual(self.repo.live_snapshot.call_count,2)
        self.state['dashboard_revision']=1
        en_vivo.cargar(self.repo,'dashboard')
        self.assertEqual(self.repo.live_snapshot.call_count,3)

    def test_disconnect_retains_last_data_and_timestamp_then_recovers(self):
        self.repo.live_snapshot.return_value={'casos':[{'id':'ficticio'}],'ventas':[]}
        first=en_vivo.cargar(self.repo,'dashboard')
        self.now.return_value=180;self.repo.live_snapshot.side_effect=ConnectionError('Ficticio')
        failed=en_vivo.cargar(self.repo,'dashboard')
        self.assertFalse(failed['conectado']);self.assertEqual(failed['datos'],first['datos'])
        self.assertEqual(failed['fecha'],120)
        en_vivo.cargar(self.repo,'dashboard');self.assertEqual(self.repo.live_snapshot.call_count,2)
        self.now.return_value=240;self.repo.live_snapshot.side_effect=None
        self.repo.live_snapshot.return_value={'casos':[{'id':'otra'}],'ventas':[]}
        recovered=en_vivo.cargar(self.repo,'dashboard')
        self.assertTrue(recovered['conectado']);self.assertEqual(recovered['fecha'],240)

    def test_initial_failure_does_not_invent_empty_business_data(self):
        self.repo.live_snapshot.side_effect=ConnectionError()
        self.assertNotIn('datos',en_vivo.cargar(self.repo,'hoy'))

    def test_partial_response_never_replaces_good_snapshot(self):
        primero=en_vivo.cargar(self.repo,'dashboard')
        self.now.return_value=180
        self.repo.live_snapshot.return_value={'casos':[]}
        ultimo=en_vivo.cargar(self.repo,'dashboard')
        self.assertFalse(ultimo['conectado'])
        self.assertEqual(ultimo['datos'],primero['datos'])

    def test_client_or_revoked_permission_never_receives_stale_data(self):
        en_vivo.cargar(self.repo,'casos');self.now.return_value=180
        self.repo.owner_only.side_effect=PermissionError()
        with self.assertRaises(PermissionError):en_vivo.cargar(self.repo,'casos')

    def test_missing_sql_legacy_bootstrap_is_not_repeated_by_timer(self):
        class FaltaSQL(Exception):code='PGRST202'
        self.repo.live_snapshot.side_effect=FaltaSQL()
        self.repo.cases=Mock(return_value=[]);self.repo.sales=Mock(return_value=[])
        a=en_vivo.cargar(self.repo,'dashboard');self.assertTrue(a['falta_sql'])
        self.now.return_value=180;en_vivo.cargar(self.repo,'dashboard')
        self.repo.cases.assert_called_once();self.repo.sales.assert_called_once()


if __name__=='__main__':unittest.main()
