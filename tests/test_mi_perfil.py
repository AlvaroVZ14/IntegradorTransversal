"""Mi perfil: cuentas ficticias y consultas simuladas; no accede a Supabase real."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
import test_app as base
from servicios.perfil_cliente import PerfilCliente,actualizar_borrador_perfil
from utils.formulario_config import valores_iniciales


def perfil_ficticio(repo):
    return dict(id='perfil-ficticio',version=1,empresa='Empresa Horizonte Ficticia',nombre=repo.profile['nombre'],
                correo=repo.user.email,telefono='+56 9 1234 5678',cargo='Coordinadora',
                redes_sociales={'instagram':'https://www.instagram.com/empresa_ficticia/'})


class PerfilTests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def preparar(self):
        app,repo=self.setup_app(False);perfil=perfil_ficticio(repo)
        def rpc(nombre,parametros):
            if nombre=='mf_mis_documentos':datos=[]
            elif nombre=='mf_mi_perfil':datos=deepcopy(perfil)
            elif nombre=='mf_guardar_mi_perfil':
                d=parametros['p_datos'];perfil.update(telefono=d['telefono'],cargo=d['cargo'],
                    redes_sociales={k:v for k,v in d.items() if k not in ('telefono','cargo') and v},version=perfil['version']+1)
                datos=deepcopy(perfil)
            else:raise AssertionError(nombre)
            return SimpleNamespace(execute=lambda:SimpleNamespace(data=datos))
        repo.client.rpc=Mock(side_effect=rpc)
        return app,repo,perfil

    def test_tarjeta_solo_dentro_mis_documentos_dos_secciones_y_sin_rut(self):
        app,repo,_=self.preparar();app.run();base.ir_a(app,'Mis documentos');self.assert_clean(app)
        self.assertEqual(base.menu_visible(app),['Solicitar servicio','Mis documentos'])
        self.assertTrue(any(x.label=='Mi perfil' for x in app.expander))
        for label in ('Empresa','Nombre de contacto','Correo'):self.assertTrue(base.by_label(app.text_input,label).disabled)
        self.assertFalse(any('RUT' in x.label for x in app.text_input))
        self.assertTrue(any('Es el correo de tu cuenta' in x.value for x in app.caption))
        self.assertEqual(sum(x.label=='Guardar cambios' for x in app.button),1)

    def test_guardar_normaliza_actualiza_y_precarga_sin_cambiar_identidad(self):
        app,repo,perfil=self.preparar();app.run();base.ir_a(app,'Mis documentos')
        base.by_label(app.text_input,'Teléfono').set_value('912345678')
        base.by_label(app.text_input,'Instagram').set_value('@nueva_red')
        base.by_label(app.text_input,'Cargo').set_value('Encargada')
        base.by_label(app.button,'Guardar cambios').click().run();self.assert_clean(app)
        self.assertEqual(perfil['telefono'],'+56 9 1234 5678')
        self.assertEqual(perfil['redes_sociales']['instagram'],'https://www.instagram.com/nueva_red/')
        self.assertTrue(any(x.value=='Listo, actualizamos tus datos' for x in app.success))
        consulta=next(c for c in repo.client.rpc.call_args_list if c.args[0]=='mf_guardar_mi_perfil')
        self.assertFalse(set(consulta.args[1]['p_datos'])&{'rut','correo','empresa','estado','nombre'})
        from mente_futuro.domain import SERVICES,TOPICS
        with patch('servicios.formulario.catalogo_publico',return_value=dict(servicios=SERVICES,tematicas=TOPICS,version=5,pendiente=False)):
            base.ir_a(app,'Solicitar servicio');self.assert_clean(app)
        self.assertEqual(app.text_input(key='request_telefono').value,perfil['telefono'])
        self.assertEqual(app.text_input(key='request_cargo').value,'Encargada')
        self.assertEqual(app.text_input(key='request_instagram').value,perfil['redes_sociales']['instagram'])
        self.assertTrue(app.text_input(key='request_email').disabled)

    def test_error_campo_no_guarda_y_red_no_pierde_lo_escrito(self):
        app,repo,_=self.preparar();app.run();base.ir_a(app,'Mis documentos')
        base.by_label(app.text_input,'Instagram').set_value('javascript:alert(1)')
        base.by_label(app.button,'Guardar cambios').click().run()
        self.assertTrue(any('Instagram' in x.value for x in app.error))
        self.assertFalse(any(c.args[0]=='mf_guardar_mi_perfil' for c in repo.client.rpc.call_args_list))
        self.assertEqual(base.by_label(app.text_input,'Instagram').value,'javascript:alert(1)')
        base.by_label(app.text_input,'Instagram').set_value('@corregida')
        original=repo.client.rpc.side_effect
        repo.client.rpc.side_effect=lambda n,p:(_ for _ in ()).throw(ConnectionError('Traza privada')) if n=='mf_guardar_mi_perfil' else original(n,p)
        base.by_label(app.button,'Guardar cambios').click().run()
        self.assertFalse(app.exception);self.assertTrue(app.warning)
        self.assertEqual(base.by_label(app.text_input,'Instagram').value,'@corregida')

    def test_sin_registro_y_sin_confirmar_o_admin(self):
        app,repo,perfil=self.preparar();perfil.update(id=None,version=0,empresa='',telefono='',cargo='',redes_sociales={})
        app.run();base.ir_a(app,'Mis documentos');self.assert_clean(app)
        self.assertEqual(base.by_label(app.text_input,'Empresa').value,'')
        base.by_label(app.text_input,'Cargo').set_value('Primer perfil')
        base.by_label(app.button,'Guardar cambios').click().run();self.assert_clean(app)
        self.assertEqual(perfil['cargo'],'Primer perfil')
        repo.user.email_confirmed_at=None
        with self.assertRaises(PermissionError):PerfilCliente(repo)
        repo.user.email_confirmed_at='2026-01-01';repo.profile['rol']='admin'
        with self.assertRaises(PermissionError):PerfilCliente(repo)

    def test_borrador_conserva_campos_editados_y_servicio(self):
        repo=base.FakeRepository(False);perfil=perfil_ficticio(repo)
        valores={**valores_iniciales(),'cliente':perfil['empresa'],'telefono':'Dato manual','detalle':'Detalle manual','cargo':'Antes'}
        estado={'formularios':{'cliente:'+repo.user.id:{'values':valores,'tocados':['telefono','detalle']}},'request_cargo':'Antes'}
        cambios=actualizar_borrador_perfil(estado,repo.user.id,perfil)
        self.assertNotIn('telefono',cambios);self.assertEqual(valores['telefono'],'Dato manual')
        self.assertEqual(valores['detalle'],'Detalle manual');self.assertEqual(valores['cargo'],perfil['cargo'])
        self.assertNotIn('request_cargo',estado)

    def test_whitelist_cliente_antes_rpc(self):
        _,repo,_=self.preparar()
        with self.assertRaisesRegex(ValueError,'Solo puedes editar'):
            PerfilCliente(repo).guardar(perfil_ficticio(repo),{'rut':'12.345.678-5'})
        repo.client.rpc.assert_not_called()
