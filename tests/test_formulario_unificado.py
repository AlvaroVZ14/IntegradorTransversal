"""Contrato entre modos, entrada, identidad y atajos con datos ficticios."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch,Mock
from streamlit.testing.v1 import AppTest
from mente_futuro.domain import SERVICES,TOPICS
from servicios.formulario import modo_servidor,datos_normalizados,errores
from servicios.formulario_publico import configuracion_visible
from utils.formulario_config import CAMPOS,MODOS,DIFERENCIAS_INTENCIONALES,contrato,valores_iniciales
from test_app import ROOT,FakeRepository,by_label,paso,menu_visible,PAGINAS

CATALOGO=dict(servicios=list(SERVICES),tematicas=list(TOPICS),version=2,pendiente=False)
CONFIG=configuracion_visible(dict(politica_privacidad='https://empresa.example.test/privacidad'))

class ContratoTests(TestCase):
    def test_diferencias_de_campos_y_etiquetas_solo_si_estan_declaradas(self):
        contratos={m:contrato(m) for m in MODOS}
        todos=set().union(*(set(c) for c in contratos.values()))
        for campo in todos:
            presentes=[c[campo] for c in contratos.values() if campo in c]
            self.assertTrue(all(c==presentes[0] for c in presentes),campo)
            if len(presentes)!=3:self.assertIn(campo,DIFERENCIAS_INTENCIONALES)
        for campo in ('cliente','contacto','email','rut','cargo','telefono','servicio','tematicas','modalidad','participantes','horas','dirigido_a','lugar','fecha_preferida','detalle'):
            self.assertTrue(all(campo in c for c in contratos.values()),campo)

    def test_identidad_y_modo_no_se_toman_del_navegador(self):
        repo=FakeRepository(False)
        datos=datos_normalizados(dict(valores_iniciales(),contacto='Nombre falso',email='otro@example.test',cliente_id='owner',origen='Correo',referido_por='Colega',servicio=SERVICES[0],tematicas=TOPICS[:2]),'cliente',repo)
        self.assertEqual(datos['contacto'],repo.profile['nombre']);self.assertEqual(datos['email'],repo.user.email)
        for k in ('cliente_id','origen','referido_por'):self.assertNotIn(k,datos)
        self.assertEqual(datos['tematica'],TOPICS[0])
        self.assertEqual(modo_servidor(repo),'cliente');self.assertEqual(modo_servidor(None),'publico')
        self.assertFalse(errores(valores_iniciales(),'interno'))
        self.assertTrue(errores(valores_iniciales(),'interno',completo=True))


class FormularioUITests(TestCase):
    def setUp(self):
        for target,value in [('servicios.formulario.catalogo_publico',CATALOGO),('paginas.formulario.configuracion_publica',CONFIG),
            ('utils.sesion_cookie.puente_cookie',True),('utils.sesion_cookie.cookie_inicial','')]:
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)

    def app(self,modo='publico'):
        repo=FakeRepository(modo=='interno')
        p=patch('servicios.repositorio.Repository',return_value=repo);p.start();self.addCleanup(p.stop)
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        if modo!='publico':app.session_state['auth_client']=repo.client
        else:app.query_params['vista']='solicitud'
        return app,repo

    def assert_limpio(self,app):
        self.assertFalse(app.exception);self.assertFalse(app.error)

    def test_entrada_publica_acceso_opcional_y_ataques_url(self):
        app,_=self.app();app.query_params.update(modo='interno',vista='solicitud',pagina='Dashboard');app.run()
        self.assert_limpio(app);self.assertFalse(menu_visible(app));self.assertFalse(app.dataframe)
        self.assertFalse(any(s.label=='Origen de la solicitud' for s in app.selectbox))
        self.assertTrue(any(b.label=='Siguiente' for b in app.button))
        by_label(app.button,'Acceso del equipo y cuentas').click().run()
        self.assertEqual(app.query_params['vista'],'acceso')
        self.assertTrue(any(b.label=='Ingresar a mi espacio' for b in app.button))

    def test_raiz_admin_va_hoy_cliente_sin_lateral_y_no_puede_elegir_modo(self):
        admin,_=self.app('interno');admin.run();self.assertEqual(admin.session_state['navigation'],'Hoy')
        cliente,repo=self.app('cliente');cliente.query_params.update(modo='interno',vista='hoy',pagina='Dashboard');cliente.run()
        self.assert_limpio(cliente);self.assertFalse(cliente.sidebar.children)
        self.assertEqual(cliente.session_state['navigation'],'Nueva solicitud')
        self.assertEqual(cliente.text_input(key='request_email').value,repo.user.email)
        self.assertTrue(cliente.text_input(key='request_contacto').disabled)
        from paginas.formulario import formulario
        with self.assertRaises(PermissionError):formulario('interno',repo)

    def test_campos_y_etiquetas_reales_comparten_tres_pasos(self):
        observados={}
        for modo in MODOS:
            app,repo=self.app(modo)
            if modo=='interno':app.query_params['pagina']='Nueva solicitud'
            app.run();self.assert_limpio(app)
            if modo!='publico':app.switch_page(PAGINAS[app.session_state['navigation']][0])
            if modo=='publico':
                app.text_input(key='publico_contacto').set_value('Camila Ficticia')
                app.text_input(key='publico_email').set_value('camila@example.test');app.run()
            comun=set()
            for n in (1,2,3):
                if n>1:
                    if modo=='interno':paso(app,n)
                    else:by_label(app.button,'Siguiente').click().run()
                self.assert_limpio(app)
                labels={e.label for tipo in ('text_input','text_area','date_input','number_input','button_group') for e in app.get(tipo)}
                for k,c in CAMPOS.items():
                    if len(c.modos)==3 and c.paso==n:
                        self.assertIn(c.etiqueta,labels,(modo,k,n));comun.add((k,c.etiqueta,c.paso))
            observados[modo]=comun
        self.assertEqual(observados['publico'],observados['cliente']);self.assertEqual(observados['cliente'],observados['interno'])

    def test_guardar_incompleto_referido_y_exito_con_atajos(self):
        app,repo=self.app('interno');app.query_params['pagina']='Nueva solicitud';app.run()
        app.switch_page(PAGINAS['Nueva solicitud'][0])
        app.text_input(key='request_cliente').set_value('Empresa por completar')
        by_label(app.selectbox,'Origen de la solicitud').set_value('Referido por colega').run()
        app.text_input(key='request_referido_por').set_value('Colega Ficticia')
        by_label(app.button,'Guardar').click().run()
        self.assert_limpio(app);self.assertEqual(len(repo.case_rows),1)
        self.assertIsNone(repo.case_rows[0]['email']);self.assertEqual(repo.case_rows[0]['referido_por'],'Colega Ficticia')
        self.assertTrue(repo.case_rows[0]['datos_incompletos']);self.assertTrue(by_label(app.button,'Cotizar').disabled)
        self.assertTrue(any('Faltan datos' in e.value for e in app.info))
        by_label(app.button,'Registrar otra solicitud').click().run();self.assert_limpio(app)
        self.assertEqual(by_label(app.selectbox,'Origen de la solicitud').value,'Referido por colega')

    def test_registro_con_sesion_confirmada_llega_a_cliente(self):
        app,repo=self.app('cliente');del app.session_state['auth_client'];app.query_params['vista']='acceso'
        repo.client.auth.sign_up=Mock(return_value=SimpleNamespace(session=SimpleNamespace(refresh_token='ficticio')))
        with patch('mente_futuro.ui.public_client',return_value=repo.client):
            app.run()
            for label,valor in [('Nombre completo','Camila Ficticia'),('Tu correo','camila@example.test'),('Crea una contraseña','Clave-Ficticia-123!'),('Repite la contraseña','Clave-Ficticia-123!')]:by_label(app.text_input,label).set_value(valor)
            by_label(app.button,'Crear mi cuenta').click().run()
        self.assert_limpio(app);self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
        self.assertTrue(app.text_input(key='request_email').disabled)
        self.assertEqual(repo.client.auth.sign_up.call_args.args[0]['options']['data'],{'nombre':'Camila Ficticia'})

    def test_correo_ya_registrado_ofrece_ingreso_y_fallo_smtp_no_crea_sesion(self):
        for fallo in (False,True):
            app,repo=self.app('cliente');del app.session_state['auth_client'];app.query_params['vista']='acceso'
            repo.client.auth.sign_up=Mock(side_effect=ConnectionError('SMTP ficticio') if fallo else None,
                return_value=SimpleNamespace(session=None,user=SimpleNamespace(identities=[])))
            with patch('mente_futuro.ui.public_client',return_value=repo.client):
                app.run()
                for label,valor in [('Nombre completo','Camila Ficticia'),('Tu correo','camila@example.test'),('Crea una contraseña','Clave-Ficticia-123!'),('Repite la contraseña','Clave-Ficticia-123!')]:by_label(app.text_input,label).set_value(valor)
                by_label(app.button,'Crear mi cuenta').click().run()
                self.assertNotIn('auth_client',app.session_state)
                if fallo:self.assertTrue(app.warning)
                else:
                    self.assertTrue(any('ya tenías una cuenta' in e.value for e in app.info))
                    by_label(app.button,'Iniciar sesión con este correo').click().run()
                    self.assertEqual(app.text_input(key='login_correo').value,'camila@example.test')

    def test_confirmacion_enlace_se_borra_de_url_y_auth_verifica_antes_de_ingresar(self):
        app,repo=self.app('cliente');del app.session_state['auth_client']
        token='a'*64;app.query_params.update(token_hash=token,type='email',vista='acceso')
        repo.client.auth.verify_otp=Mock(return_value=SimpleNamespace(session=SimpleNamespace(refresh_token='ficticio')))
        with patch('servicios.acceso.public_client',return_value=repo.client):
            app.run();self.assertNotIn('token_hash',app.query_params)
            self.assertNotIn('auth_client',app.session_state)
            by_label(app.button,'Confirmar correo y continuar').click().run()
        repo.client.auth.verify_otp.assert_called_once_with({'token_hash':token,'type':'email'})
        self.assertEqual(app.session_state['navigation'],'Nueva solicitud');self.assert_limpio(app)
