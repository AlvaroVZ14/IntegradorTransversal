"""Contrato de las dos entradas; Auth y datos completamente ficticios."""
import json
from time import time
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch,Mock
from streamlit.testing.v1 import AppTest
from mente_futuro.domain import SERVICES,TOPICS
from servicios.formulario_publico import configuracion_visible
from utils.navegacion import rutas_para_perfil,PAGINAS
from test_app import ROOT,FakeRepository,by_label,menu_visible
from test_recarga import recargar

class EntradasTests(TestCase):
    def setUp(self):
        self.repo=FakeRepository()
        p=patch('servicios.repositorio.Repository',side_effect=lambda *_:self.repo)
        self.repository=p.start();self.addCleanup(p.stop)
        for target,value in [('servicios.formulario.catalogo_publico',dict(servicios=SERVICES,tematicas=TOPICS,version=3,pendiente=False)),
            ('paginas.formulario.configuracion_publica',configuracion_visible({})),
            ('utils.sesion_cookie.cookie_inicial',''),('utils.sesion_cookie.puente_cookie',True)]:
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)

    def app(self,rol=None):
        self.repo=FakeRepository(rol!='cliente')
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        if rol:app.session_state['auth_client']=self.repo.client
        return app

    def limpio(self,app):
        self.assertFalse(app.exception);self.assertFalse(app.error)

    def test_01_principal_anonimo_login_recarga_y_boton_sin_cuenta(self):
        app=self.app();self.assertEqual(recargar(app,''),0);self.limpio(app)
        self.assertTrue(any(t.label=='Crear cuenta de cliente' for t in app.tabs))
        self.assertTrue(any(b.label=='Ingresar a mi espacio' for b in app.button))
        self.assertEqual(recargar(app,''),0);self.limpio(app)
        by_label(app.button,'Enviar solicitud sin cuenta').click().run()
        self.assertEqual(app.query_params['vista'],'solicitud')
        self.assertTrue(any(b.label=='Siguiente' for b in app.button));self.assertFalse(app.sidebar.children)

    def test_02_03_cookie_recupera_rol_real_en_sesion_nueva_y_recarga(self):
        for rol,esperada in [('admin','Hoy'),('cliente','Nueva solicitud')]:
            app=self.app(rol);del app.session_state['auth_client']
            session=SimpleNamespace(refresh_token='rotado-ficticio-'+rol)
            self.repo.client.auth.refresh_session=Mock(return_value=SimpleNamespace(session=session))
            self.repo.client.auth.get_session=lambda:session
            valor=json.dumps({'refresh_token':'cookie-ficticia-'+rol,'expires':time()+600})
            with patch('utils.sesion_cookie.cookie_inicial',return_value=valor),patch('servicios.repositorio.public_client',return_value=self.repo.client):
                self.assertEqual(recargar(app,''),0);self.limpio(app)
            self.assertEqual(app.session_state['navigation'],esperada)
            self.assertFalse(any(b.label=='Ingresar a mi espacio' for b in app.button))
            self.repo.client.auth.refresh_session.assert_called_once()
            self.assertEqual(recargar(app,PAGINAS[esperada][1]),0);self.limpio(app)
            if rol=='cliente':
                self.assertFalse(app.sidebar.children)
                self.assertTrue(app.text_input(key='request_contacto').disabled)
                self.assertTrue(app.text_input(key='request_email').disabled)

    def test_04_publico_ignora_auth_de_todos_los_roles_incluso_al_recargar(self):
        for rol in (None,'admin','cliente'):
            app=self.app(rol)
            self.repo.client.auth.get_user=Mock(side_effect=AssertionError('El formulario público no debe consultar Auth'))
            self.repository.reset_mock()
            app.query_params.update(vista='solicitud',canal='instagram',pagina='Dashboard',modo='interno')
            self.assertEqual(recargar(app,'dashboard'),0);self.limpio(app)
            self.assertEqual(recargar(app,'dashboard'),0);self.limpio(app)
            self.assertFalse(app.sidebar.children);self.assertFalse(menu_visible(app))
            self.assertFalse(app.text_input(key='publico_contacto').disabled)
            self.assertEqual(app.text_input(key='publico_email').value,'')
            self.assertNotIn('_repo_actual',app.session_state)
            self.assertFalse(any(s.label=='Origen de la solicitud' for s in app.selectbox))
            self.assertEqual(app.session_state['formularios']['publico:visitante']['canal_captacion'],'instagram')
            self.repo.client.auth.get_user.assert_not_called();self.repository.assert_not_called()
            if rol:self.assertTrue(any(b.label=='Volver a la app' for b in app.button))

    def test_05_destinos_ejecutables_cliente_excluyen_admin_y_url_no_carga_datos(self):
        self.assertEqual(list(rutas_para_perfil({'rol':'cliente'},{**PAGINAS,'Inicio':None})),['Nueva solicitud'])
        for titulo in ('Hoy','Casos y cotizaciones','Compartir','Dashboard','Estado'):
            app=self.app('cliente')
            self.repo.live_snapshot=Mock(side_effect=AssertionError('No debe consultar datos administrativos'))
            self.assertEqual(recargar(app,PAGINAS[titulo][1]),0);self.limpio(app)
            self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
            self.repo.live_snapshot.assert_not_called()

    def test_06_envio_publico_solo_rpc_anonima_no_crea_cuenta_ni_sesion(self):
        app=self.app();app.query_params.update(vista='solicitud',canal='whatsapp');app.run()
        api=Mock();api.rpc.return_value.execute.return_value=SimpleNamespace(data={'codigo':'MF-2026-0042'})
        app.text_input(key='publico_contacto').set_value('Camila Ficticia')
        app.text_input(key='publico_email').set_value('camila@example.test')
        by_label(app.button,'Siguiente').click().run();by_label(app.button,'Siguiente').click().run()
        app.checkbox(key='publico_consentimiento').check()
        with patch('servicios.formulario_publico.cliente_publico',return_value=api):
            by_label(app.button,'Enviar solicitud').click().run()
        self.limpio(app);self.assertNotIn('auth_client',app.session_state)
        self.assertTrue(any('MF-2026-0042' in x.value for x in app.markdown))
        self.assertEqual(api.rpc.call_count,1)
        nombre,parametros=api.rpc.call_args.args
        self.assertEqual(nombre,'registrar_solicitud_publica');self.assertEqual(parametros['p_datos']['canal_captacion'],'whatsapp')
        api.auth.sign_up.assert_not_called();api.auth.sign_in_with_password.assert_not_called()
        self.repository.assert_not_called()

    def test_cookie_expirada_invalida_revocada_y_logout_vuelven_a_login(self):
        for cookie in ('malformada',json.dumps({'refresh_token':'ficticio-vencido','expires':time()-1}),
            json.dumps({'refresh_token':'ficticio-revocado','expires':time()+300})):
            app=self.app()
            self.repo.client.auth.refresh_session=Mock(side_effect=PermissionError('Revocado ficticio'))
            with patch('utils.sesion_cookie.cookie_inicial',return_value=cookie),patch('servicios.repositorio.public_client',return_value=self.repo.client):
                self.assertEqual(recargar(app,'dashboard'),0);self.limpio(app)
            self.assertTrue(any(b.label=='Ingresar a mi espacio' for b in app.button))
            self.assertNotIn('auth_client',app.session_state)
            self.assertEqual(app.session_state['_cookie_command']['action'],'clear')
        app=self.app('cliente');app.run();app.switch_page('paginas/nueva_solicitud.py')
        by_label(app.button,'Cerrar sesión').click().run();self.limpio(app)
        self.assertNotIn('auth_client',app.session_state)
        self.assertEqual(app.session_state['_cookie_command']['action'],'clear')

    def test_acceso_directo_login_y_volver_desde_publico(self):
        app=self.app('admin');app.query_params['vista']='acceso';app.run();self.limpio(app)
        self.assertTrue(any(b.label=='Ingresar a mi espacio' for b in app.button))
        app.query_params['vista']='solicitud';app.run()
        by_label(app.button,'Volver a la app').click().run();self.limpio(app)
        self.assertEqual(app.session_state['navigation'],'Hoy')

    def test_evento_tardio_del_formulario_no_reabre_datos_tras_logout(self):
        from paginas.formulario import Formulario
        borrador={'values':{'cliente':'Empresa ficticia'}}
        evento=SimpleNamespace(prefix='request_',scope='cliente:ficticio',b=borrador)
        for estado in ({},{'request_cliente':'Evento anterior','formularios':{}}):
            with patch('paginas.formulario.st.session_state',estado):
                Formulario.cambio(evento,'cliente')
            self.assertEqual(borrador['values']['cliente'],'Empresa ficticia')

    def test_callback_con_copia_del_borrador_actual_guarda_en_el_vigente(self):
        from paginas.formulario import Formulario
        anterior={'id':'ficticio','values':{'cliente':'Antes'}}
        vigente={'id':'ficticio','values':{'cliente':'Antes'},'tocados':[]}
        evento=SimpleNamespace(prefix='publico_',scope='publico:visitante',b=anterior)
        estado={'publico_cliente':'Empresa ficticia','formularios':{'publico:visitante':vigente}}
        with patch('paginas.formulario.st.session_state',estado):Formulario.cambio(evento,'cliente')
        self.assertEqual(vigente['values']['cliente'],'Empresa ficticia')
        self.assertEqual(anterior['values']['cliente'],'Antes')
