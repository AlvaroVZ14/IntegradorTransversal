"""Cookies ficticias: no usa cuentas, tokens ni datos reales."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from servicios.sesion import leer_cookie,restaurar


class SesionTests(unittest.TestCase):
    def test_expired_malformed_and_oversized_cookies_are_rejected(self):
        for value in ['', 'x', '{}', '[]', 'a'*4000,
            json.dumps({'refresh_token':'token-ficticio','expires':100}),
            json.dumps({'refresh_token':'token-ficticio','expires':100+8*86400}),
            json.dumps({'refresh_token':'token-ficticio','expires':True})]:
            self.assertIsNone(leer_cookie(value,ahora=100))
        self.assertEqual(leer_cookie(json.dumps({'refresh_token':'token-ficticio','expires':200}),100)['expires'],200)

    def test_restore_rechecks_auth_and_admin_profile(self):
        from time import time
        cookie=json.dumps({'refresh_token':'token-ficticio','expires':time()+300})
        for role in ['admin','cliente']:
            client=Mock();client.auth.refresh_session.return_value=SimpleNamespace(session=SimpleNamespace(refresh_token='nuevo-ficticio'))
            client.auth.get_user.return_value=SimpleNamespace(user=SimpleNamespace(id='persona-ficticia'))
            client.table.return_value.select.return_value.eq.return_value.execute.return_value.data=[{'id':'persona-ficticia','rol':role}]
            result=restaurar(cookie,lambda:client)
            self.assertEqual(result is not None,role=='admin')
            client.auth.refresh_session.assert_called_once_with('token-ficticio')
            client.auth.get_user.assert_called_once()

    def test_malformed_cookie_never_contacts_auth(self):
        factory=Mock()
        self.assertIsNone(restaurar('sin-formato',factory))
        factory.assert_not_called()

    def test_active_admin_refresh_returns_to_frame_to_sync_cookie(self):
        from unittest.mock import patch
        from utils.sesion_cookie import mantener_sesion_activa
        session=SimpleNamespace(refresh_token='rotado-ficticio')
        client=SimpleNamespace(auth=SimpleNamespace(get_session=lambda:session))
        for role,expected in [('admin',1),('cliente',0)]:
            state={'auth_client':client,'_repo_actual':SimpleNamespace(profile={'rol':role}),
                '_cookie_token_confirmado':'anterior-ficticio'}
            with patch('utils.sesion_cookie.st.session_state',state),patch('utils.sesion_cookie.st.rerun') as rerun:
                mantener_sesion_activa.__wrapped__()
                self.assertEqual(rerun.call_count,expected)
                if expected:rerun.assert_called_with(scope='app')
