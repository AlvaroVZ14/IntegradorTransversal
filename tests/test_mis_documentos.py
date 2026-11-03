"""Portal cliente con cuentas y documentos ficticios, sin llamadas externas."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from servicios.mis_documentos import MisDocumentos
from servicios.autoguardado import preparar, editar, guardar
from utils.permisos import allowed_pages, guard_route
import test_app as base
from test_app import by_label, ir_a, menu_visible
from test_recarga import recargar


def caso_cliente():
    return dict(id='caso-ficticio', numero=42, created_at='2026-11-02T02:30:00Z',
                cliente='Empresa Horizonte Ficticia', servicio='Taller de trabajo en equipo', documentos=[
                    dict(id='documento-ficticio', tipo='Lista de asistencia', nombre='Documento_ficticio.pdf',
                         fecha_subida='2026-11-02T15:00:00Z', tipo_mime='application/pdf')])


class MisDocumentosTests(TestCase):
    setup_app = base.AppTests.setup_app
    assert_clean = base.AppTests.assert_clean

    def test_dos_destinos_y_guardia_incluso_urls_desconocidas(self):
        self.assertEqual(allowed_pages({'rol': 'cliente'}), ['Solicitar servicio', 'Mis documentos'])
        for ruta in ('Hoy', 'Dashboard', 'Estado', 'Compartir', 'Nueva solicitud', 'no-existe'):
            app, repo = self.setup_app(False)
            self.assertEqual(guard_route(repo.profile, ruta), 'Mis documentos')
            self.assertEqual(recargar(app, {'Nueva solicitud': 'nueva-solicitud'}.get(ruta, ruta.lower())), 0)
            self.assert_clean(app)
            self.assertEqual(app.session_state['navigation'], 'Mis documentos')
            self.assertEqual(menu_visible(app), ['Solicitar servicio', 'Mis documentos'])
            self.assertFalse(app.dataframe)

    def test_documentos_agrupados_descarga_diferida_sin_datos_internos(self):
        app, repo = self.setup_app(False)
        repo.client.rpc = Mock(return_value=SimpleNamespace(execute=lambda: SimpleNamespace(data=[caso_cliente()])))
        app.run(); ir_a(app, 'Mis documentos'); self.assert_clean(app)
        self.assertIn('Empresa Horizonte Ficticia', ' '.join(e.value for e in app.markdown))
        self.assertIn('MF-2026-0042', ' '.join(e.value for e in app.subheader))
        self.assertIn('01/11/2026', ' '.join(e.value for e in app.caption))  # Fecha Chile.
        self.assertEqual(len(app.get('download_button')), 1)
        repo.client.rpc.assert_called_with('mf_mis_documentos', {'p_desde': 0})
        self.assertFalse(app.dataframe); self.assertFalse(app.metric)
        self.assertFalse(any(s.label in ('Estado', 'Monto', 'Nota') for s in app.text_input))
        self.assertFalse(any('archivo_path' in e.value or 'storage/v1' in e.value for e in app.markdown))
        self.assertEqual(recargar(app, 'mis-documentos'), 0); self.assert_clean(app)

    def test_vacio_y_fallo_de_red_no_muestran_datos_ajenos(self):
        app, repo = self.setup_app(False); app.run(); ir_a(app, 'Mis documentos')
        self.assertTrue(any('Cuando la socia comunitaria' in e.value for e in app.info))
        repo.client.rpc = Mock(side_effect=ConnectionError('RUTA-INTERNA-SECRETA'))
        app.run(); self.assert_clean(app)
        self.assertTrue(app.warning); self.assertFalse(app.get('download_button'))
        self.assertNotIn('RUTA-INTERNA-SECRETA', str(app))

    def test_descarga_verifica_permiso_al_pulsar_y_no_devuelve_url(self):
        _, repo = self.setup_app(False)
        repo.client.rpc = Mock(return_value=SimpleNamespace(execute=lambda: SimpleNamespace(data={
            'archivo_path': 'uuid-caso/uuid-documento.pdf', 'nombre': 'Documento_ficticio.pdf', 'tipo_mime': 'application/pdf'})))
        bucket = Mock(); bucket.create_signed_url.return_value = {'signedURL': 'https://storage.example.test/uuid?token=ficticio'}
        repo.client.storage = SimpleNamespace(from_=lambda _: bucket)
        respuesta = Mock(); respuesta.__enter__ = Mock(return_value=respuesta); respuesta.__exit__ = Mock(return_value=False)
        respuesta.read.return_value = b'%PDF-ficticio'
        with patch('servicios.mis_documentos.urlopen', return_value=respuesta) as peticion:
            self.assertEqual(MisDocumentos(repo).descargar('documento-ficticio'), b'%PDF-ficticio')
            bucket.create_signed_url.assert_called_once_with('uuid-caso/uuid-documento.pdf', 600)
            peticion.assert_called_once()
        repo.client.rpc.return_value.execute = lambda: SimpleNamespace(data=None)
        with patch('servicios.mis_documentos.urlopen') as peticion:
            with self.assertRaisesRegex(RuntimeError, 'Vuelve a abrir Mis documentos'):
                MisDocumentos(repo).descargar('documento-revocado')
            peticion.assert_not_called()

    def test_paginacion_sin_cache_compartido_y_admin_rechazado(self):
        _, repo = self.setup_app(False)
        paginas = [[caso_cliente()] * 100, [caso_cliente()]]
        repo.client.rpc = Mock(side_effect=lambda *args: SimpleNamespace(execute=lambda: SimpleNamespace(data=paginas.pop(0))))
        self.assertEqual(len(MisDocumentos(repo).listar()), 101)
        self.assertEqual(repo.client.rpc.call_args.args[1], {'p_desde': 100})
        repo.profile['rol'] = 'admin'
        with self.assertRaises(PermissionError): MisDocumentos(repo)

    def test_correos_adicionales_validacion_autoguardado_y_recarga(self):
        app, repo = self.setup_app(); app.run(); base.AppTests.create_request(self, app)
        caso = repo.case_rows[0]; caso['correos_documentos'] = []
        app.run()
        label = 'Correos adicionales con acceso a los documentos (opcional)'
        by_label(app.text_area, label).set_value('Encargada@Example.Test; otro@example.test').run()
        self.assert_clean(app)
        self.assertEqual(caso['correos_documentos'], ['encargada@example.test', 'otro@example.test'])
        by_label(app.text_area, label).set_value('invalido').run()
        self.assertTrue(app.error); self.assertEqual(len(caso['correos_documentos']), 2)
        borrador = preparar({}, caso)
        editar(borrador, 'correos_documentos', '')
        self.assertTrue(guardar(repo, borrador, campos=['correos_documentos']))
        self.assertEqual(caso['correos_documentos'], [])
