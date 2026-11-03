"""Archivos y correos ficticios. No se envía correo ni se usa Supabase real."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import uuid4
import test_app as base
from test_documentos_caso import Servidor, pdf_ficticio
from servicios.archivos_caso import MAX_BYTES
from servicios.mis_documentos import MisDocumentos
from servicios.documentos_caso import DocumentosCaso
from servicios.aviso_documento import avisar_socia


class ServidorCliente(Servidor):
    def rpc(self, n, p):
        if n == 'mf_mis_documentos':
            return [dict(id=self.caso, numero=1, cliente='Empresa ficticia', servicio='Taller ficticio',
                created_at='2026-11-03T12:00:00Z', puede_enviar=self.abierto,
                documentos=[{**d, 'es_mio':True} for d in self.filas if d['estado_archivo']!='eliminado'])]
        if n == 'mf_preparar_documento_cliente':
            d=next((d for d in self.filas if d['id']==p['p_id']), None)
            if not d:
                id=p['p_id'];d=dict(id=id,caso_id=p['p_caso_id'],tipo=p['p_tipo'],nota=p['p_nota'],
                    nombre='Documento_'+id.replace('-','')+'.'+p['p_extension'],
                    archivo_path=f"{p['p_caso_id']}/cliente/{id}.{p['p_extension']}",tamano=p['p_tamano'],
                    tipo_mime=p['p_mime'],origen='cliente',subido_por=self.repo.user.id,
                    estado_archivo='pendiente',visible_cliente=False,fecha_subida='2026-11-03T12:00:00Z',aviso_estado='no_solicitado')
                self.filas.append(d)
            return deepcopy(d)
        if n == 'mf_aviso_documento_cliente':
            d=next(d for d in self.filas if d['id']==p['p_id'])
            if 'p_resultado' in p:d['aviso_estado']=p['p_resultado'];return {}
            if d['aviso_estado']!='no_solicitado':return {}
            d['aviso_estado']='reservado';return {'correo':'socia@example.test'}
        if n == 'mf_eliminar_documento_cliente':
            d=next(d for d in self.filas if d['id']==p['p_id'])
            if p['p_finalizar']:
                if d['archivo_path'] in self.objetos:raise RuntimeError('Aún hay archivo')
                d['estado_archivo']='eliminado'
            else:d['estado_archivo']='eliminando'
            return {'archivo_path':d['archivo_path']}
        return super().rpc(n,p)


class DocumentosClienteTests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def preparar(self):
        _,repo=self.setup_app(False);s=ServidorCliente(repo);s.caso=str(uuid4());s.abierto=True
        return MisDocumentos(repo),s,repo

    def test_valida_antes_de_reservar_y_no_guarda_nombre_original(self):
        docs,s,_=self.preparar()
        for nombre,contenido in [('mal.exe',pdf_ficticio()),('mal.pdf',b'no es PDF'),('grande.pdf',b'x'*(MAX_BYTES+1))]:
            with self.assertRaises(ValueError):docs.subir(s.caso,'Requerimientos',nombre,contenido)
        with self.assertRaises(ValueError):docs.subir(s.caso,'Informe','a.pdf',pdf_ficticio())
        self.assertFalse(s.filas);self.assertFalse(s.objetos)
        d=docs.subir(s.caso,'Requerimientos','Nombre_Personal.pdf',pdf_ficticio())
        self.assertIn('/cliente/',d['archivo_path']);self.assertNotIn('Personal',str(d));self.assertNotIn('Nombre',str(d))
        self.assertEqual(d['estado_archivo'],'disponible')

    def test_reintento_de_respuesta_perdida_no_duplica_y_borrado_recuperable(self):
        docs,s,_=self.preparar();id=uuid4();contenido=pdf_ficticio();s.bucket.fallar_tras_subir=True
        with self.assertRaises(ConnectionError):docs.subir(s.caso,'Otro','x.pdf',contenido,documento_id=id)
        docs.subir(s.caso,'Otro','x.pdf',contenido,documento_id=id)
        self.assertEqual(s.bucket.uploads,1);self.assertEqual(len(s.filas),1)
        s.bucket.fallar_borrado=True
        with self.assertRaises(ConnectionError):docs.eliminar(str(id))
        self.assertEqual(s.filas[0]['estado_archivo'],'eliminando')
        docs.eliminar(str(id));self.assertFalse(s.objetos);self.assertEqual(s.filas[0]['estado_archivo'],'eliminado')

    def test_aviso_generico_una_vez_y_smtp_no_bloquea(self):
        docs,s,_=self.preparar();d=docs.subir(s.caso,'Otro','Privado.pdf',pdf_ficticio(),nota='NOTA PRIVADA FICTICIA')
        with patch('servicios.aviso_documento.entregar_mensaje') as smtp:
            self.assertEqual(avisar_socia(docs,d['id'],{}),'enviado')
            mensaje=smtp.call_args.args[0]
            self.assertEqual(mensaje['To'],'socia@example.test');self.assertFalse(list(mensaje.iter_attachments()))
            for dato in ('PRIVADA','Privado.pdf',s.caso,d['archivo_path']):self.assertNotIn(dato,str(mensaje))
            self.assertEqual(avisar_socia(docs,d['id'],{}),'ya_reservado');self.assertEqual(smtp.call_count,1)
        segundo=docs.subir(s.caso,'Otro','otro.pdf',pdf_ficticio())
        with patch('servicios.aviso_documento.entregar_mensaje',side_effect=ConnectionError):
            self.assertEqual(avisar_socia(docs,segundo['id'],{}),'incierto')
        self.assertEqual(s.filas[-1]['estado_archivo'],'disponible')

    def app_cliente(self):
        docs,s,repo=self.preparar()
        app=base.AppTest.from_string('''
from servicios.repositorio import Repository
from paginas.mis_documentos import mis_documentos
mis_documentos(Repository(None,None,None))
''',default_timeout=20)
        return app,docs,s,repo

    def test_caso_sin_documentos_permite_subir_y_descargar_el_propio(self):
        app,_,s,_=self.app_cliente();pdf=pdf_ficticio()
        with patch('paginas.mi_perfil.mi_perfil'),patch('streamlit.secrets',{}),patch('streamlit.file_uploader',
            return_value=[SimpleNamespace(name='Empresa privada.pdf',getvalue=lambda:pdf)]),patch('paginas.mis_documentos.avisar_socia'):
            app.run();self.assert_clean(app)
            self.assertTrue(any('No subas claves' in x.value for x in app.caption))
            base.by_label(app.button,'Enviar documentos').click().run();self.assert_clean(app)
            self.assertTrue(any('Recibimos tu documento' in x.value for x in app.success))
            self.assertTrue(any('Documentos que enviaste' in x.value for x in app.markdown))
            self.assertEqual(len(app.get('download_button')),1)
            self.assertTrue(base.by_label(app.button,'Eliminar documento').disabled)
            base.by_label(app.checkbox,'Confirmo eliminar este documento').set_value(True).run()
            base.by_label(app.button,'Eliminar documento').click().run();self.assert_clean(app)
            self.assertEqual(s.filas[0]['estado_archivo'],'eliminado')

    def test_cerrada_no_permite_subir_o_eliminar_pero_si_descargar(self):
        app,docs,s,_=self.app_cliente();docs.subir(s.caso,'Otro','x.pdf',pdf_ficticio());s.abierto=False
        with patch('paginas.mi_perfil.mi_perfil'):
            app.run();self.assert_clean(app)
            self.assertFalse(app.get('file_uploader'));self.assertFalse(app.button)
            self.assertEqual(len(app.get('download_button')),1)

    def test_administracion_ve_origen_filtra_y_cambia_tipo(self):
        docs,s,repo=self.preparar();d=docs.subir(s.caso,'Otro','x.pdf',pdf_ficticio())
        repo.is_owner=True;repo.profile['rol']='admin'
        repo.case_rows=[{'id':s.caso}]
        app=base.AppTest.from_string('''
from servicios.repositorio import Repository
from paginas.documentos_caso import documentos_caso
repo=Repository(None,None,None)
documentos_caso(repo,repo.case_rows[0],[])
''',default_timeout=20)
        with patch('streamlit.secrets',{}):
            app.run();self.assert_clean(app)
            self.assertTrue(any('Enviado por el cliente' in x.value for x in app.caption))
            campos=[x for x in app.selectbox if x.label=='Tipo de documento']
            campos[-1].set_value('Nómina de participantes')
            base.by_label(app.button,'Cambiar tipo').click().run();self.assert_clean(app)
            self.assertEqual(s.filas[0]['tipo'],'Nómina de participantes')
            base.by_label(app.selectbox,'Origen de los documentos').set_value('Enviados por la socia').run()
            self.assertFalse(any('Enviado por el cliente' in x.value for x in app.caption))
            self.assertTrue(any('No hay documentos de este origen' in x.value for x in app.info))
