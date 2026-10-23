"""Respaldos y monitoreo con datos ficticios; no usa la red ni secretos reales."""
import csv
import hashlib
import io
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from cryptography.exceptions import InvalidTag
from servicios.respaldos import TABLAS,zip_csv
from scripts.mantenimiento import cifrar,descifrar,comprobar_app,monitor,StreamlitRedirect
from urllib.request import Request


def snapshot_ficticio():
    tables={t:dict(columns=[dict(name='id',type='uuid',generated=False,identity=False)],rows=[]) for t in TABLAS}
    tables['mf_casos']=dict(columns=[dict(name=c,type='text',generated=False,identity=False) for c in ['id','cliente','detalle','nulo','vacio']],
        rows=[dict(id=str(i),cliente='Fundación Ficticia',detalle={'texto':'Comas, salto\n"y comillas"'},nulo=None,vacio='') for i in range(1100)])
    return dict(format=1,snapshot_at='2026-10-22T12:00:00+00:00',tables=tables)


class RespaldoTests(unittest.TestCase):
    def test_all_tables_empty_headers_and_more_than_1000_rows(self):
        with ZipFile(io.BytesIO(zip_csv(snapshot_ficticio()))) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(len(z.namelist()),len(TABLAS)+1)
            manifest=json.loads(z.read('manifest.json'))
            for name,table in manifest['tables'].items():
                data=z.read(name+'.csv')
                self.assertEqual(hashlib.sha256(data).hexdigest(),table['sha256'])
                rows=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
                self.assertEqual(len(rows),table['rows'])
            table=manifest['tables']['mf_casos']
            self.assertEqual(table['rows'],1100)
            self.assertIn([0,'nulo'],table['null_cells'])
            self.assertNotIn([0,'vacio'],table['null_cells'])
            rows=list(csv.DictReader(io.StringIO(z.read('mf_casos.csv').decode('utf-8-sig'))))
            self.assertEqual(json.loads(rows[0]['detalle']),{'texto':'Comas, salto\n"y comillas"'})

    def test_incomplete_snapshot_never_downloaded(self):
        data=snapshot_ficticio();del data['tables']['mf_ventas']
        with self.assertRaises(ValueError):zip_csv(data)
        data=snapshot_ficticio();del data['tables']['mf_casos']['rows'][0]['cliente']
        with self.assertRaises(ValueError):zip_csv(data)

    def test_encryption_recovers_zip_and_detects_wrong_key_or_tampering(self):
        data=zip_csv(snapshot_ficticio());key=bytes(range(32))
        encrypted=cifrar(data,key)
        self.assertEqual(descifrar(encrypted,key),data)
        self.assertNotEqual(encrypted,cifrar(data,key))
        self.assertNotIn(b'mf_casos.csv',encrypted)
        for damaged,k in [(encrypted[:-1]+bytes([encrypted[-1]^1]),key),(encrypted,b'x'*32)]:
            with self.assertRaises(InvalidTag):descifrar(damaged,k)

    def test_monitor_detects_sleep_even_with_http_200(self):
        with patch('scripts.mantenimiento.request',return_value=b'Streamlit has gone to sleep'):
            with self.assertRaises(RuntimeError):comprobar_app('https://ficticia.streamlit.app/')
        with patch('scripts.mantenimiento.request',side_effect=[b'<title>Streamlit</title>',b'ok']) as req:
            comprobar_app('https://ficticia.streamlit.app/')
            self.assertEqual(req.call_count,2)
        with patch('scripts.mantenimiento.request',side_effect=[b'Streamlit',b'<html>Streamlit</html>']):
            with self.assertRaises(RuntimeError):comprobar_app('https://ficticia.streamlit.app/')

    def test_monitor_checks_both_services_even_when_database_fails(self):
        with patch('scripts.mantenimiento.supabase',side_effect=ConnectionError()),patch('scripts.mantenimiento.secret',return_value='https://ficticia.streamlit.app'),patch('scripts.mantenimiento.comprobar_app') as app,patch('scripts.mantenimiento.registrar') as reg:
            with self.assertRaises(RuntimeError):monitor()
            app.assert_called_once();reg.assert_called_once_with('monitor','error')

    def test_public_cloud_redirects_allowed_but_credentials_and_other_hosts_rejected(self):
        redirect=StreamlitRedirect('ficticia.streamlit.app')
        req=Request('https://ficticia.streamlit.app/')
        for target in ['https://share.streamlit.io/-/auth/app','https://ficticia.streamlit.app/']:
            self.assertEqual(redirect.redirect_request(req,None,303,'',{},target).full_url,target)
        for target in ['http://ficticia.streamlit.app/','https://otro.example.test/',
                       'https://share.streamlit.io.ejemplo.test/','https://usuario@share.streamlit.io/']:
            with self.assertRaises(ValueError):redirect.redirect_request(req,None,303,'',{},target)
        for name in ['Authorization','apikey']:
            credential=Request('https://ficticia.streamlit.app/',headers={name:'valor-ficticio'})
            with self.assertRaises(ValueError):redirect.redirect_request(credential,None,303,'',{},'https://share.streamlit.io/')

    def test_cloud_portal_response_never_claims_form_is_healthy(self):
        shell=b'<html>Streamlit<script src="/-/build/assets/index.js"></script></html>'
        with patch('scripts.mantenimiento.request',side_effect=[shell,shell]):
            self.assertEqual(comprobar_app('https://ficticia.streamlit.app/'),'portal')
        with patch('scripts.mantenimiento.request',side_effect=[b'Streamlit',b'ok']):
            self.assertEqual(comprobar_app('https://ficticia.streamlit.app/'),'servidor')
