"""Subidas/SMTP simulados: no archivos de clientes, repositorios externos ni correos reales."""
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock,patch
from uuid import uuid4
from datetime import datetime,timezone
import unittest
from docx import Document
from PIL import Image
from reportlab.pdfgen import canvas
import test_app as base
from test_propuesta_documento import propuesta
from servicios.archivos_caso import validar_archivo,MAX_BYTES
from servicios.documentos_caso import DocumentosCaso
from servicios.aviso_documento import avisar_documento


def pdf_ficticio():
    salida=BytesIO();c=canvas.Canvas(salida);c.drawString(60,750,'Lista de asistencia ficticia');c.save();return salida.getvalue()


class Consulta:
    def __init__(self,servidor):self.s=servidor;self.filtros=[];self.operacion='select';self.datos=None;self.rango=None
    def select(self,*args):return self
    def eq(self,k,v):self.filtros.append((k,v));return self
    def order(self,*args,**kw):return self
    def range(self,a,b):self.rango=(a,b);return self
    def insert(self,d):self.operacion='insert';self.datos=d;return self
    def update(self,d):self.operacion='update';self.datos=d;return self
    def execute(self):
        if self.operacion=='insert':
            d=deepcopy(self.datos);d.update(estado_archivo='pendiente',fecha_subida=datetime.now(timezone.utc).isoformat(),aviso_estado='no_solicitado')
            self.s.filas.append(d);return SimpleNamespace(data=[deepcopy(d)])
        filas=[d for d in self.s.filas if all(d.get(k)==v for k,v in self.filtros)]
        if self.operacion=='update':
            for d in filas:d.update(self.datos)
        if self.rango:filas=filas[self.rango[0]:self.rango[1]+1]
        return SimpleNamespace(data=deepcopy(filas))


class Bucket:
    def __init__(self,s):self.s=s;self.uploads=0;self.fallar_tras_subir=False;self.fallar_borrado=False;self.firmas=[]
    def list(self,carpeta,opciones):return [{'name':k.split('/')[-1]} for k in self.s.objetos if k.startswith(carpeta+'/') and opciones['search'] in k]
    def upload(self,ruta,contenido,opciones):
        self.uploads+=1
        if ruta in self.s.objetos:raise RuntimeError('No sobrescribir')
        self.s.objetos[ruta]=contenido
        if self.fallar_tras_subir:self.fallar_tras_subir=False;raise ConnectionError('Respuesta perdida')
    def remove(self,rutas):
        if self.fallar_borrado:self.fallar_borrado=False;raise ConnectionError('Desconectado')
        for ruta in rutas:self.s.objetos.pop(ruta,None)
    def create_signed_url(self,ruta,segundos,opciones):
        self.firmas.append((ruta,segundos,opciones));return {'signedURL':'https://storage.example.test/temporal?token=ficticio'}


class Servidor:
    def __init__(self,repo):
        self.filas=[];self.objetos={};self.bucket=Bucket(self);self.repo=repo;self.cuenta=True
        original=repo.client.table
        repo.client.table=lambda nombre:Consulta(self) if nombre=='mf_documentos' else original(nombre)
        repo.client.storage=SimpleNamespace(from_=lambda nombre:self.bucket)
        repo.client.rpc=lambda nombre,p:SimpleNamespace(execute=lambda:SimpleNamespace(data=self.rpc(nombre,p)))
    def rpc(self,n,p):
        if n=='mf_destinatario_documentos':return {'tiene_cuenta':self.cuenta,'correo':'cliente@example.test'}
        d=next(d for d in self.filas if d['id']==p['p_id'])
        if n=='mf_confirmar_documento':
            if d['archivo_path'] not in self.objetos:raise RuntimeError('Falta el archivo')
            d['estado_archivo']='disponible';return deepcopy(d)
        if n=='mf_eliminar_documento':
            if p['p_finalizar']:
                if d['archivo_path'] in self.objetos:raise RuntimeError('Archivo presente')
                d.update(estado_archivo='eliminado',visible_cliente=False,nota='')
            else:d.update(estado_archivo='eliminando',visible_cliente=False)
            return True
        if n=='mf_reservar_aviso_documento':
            if d['aviso_estado']!='no_solicitado':return False
            d['aviso_estado']='reservado';return True
        if n=='mf_resultado_aviso_documento':d['aviso_estado']=p['p_estado'];return None
        raise AssertionError(n)


class ArchivosTests(unittest.TestCase):
    def test_types_content_size_and_names(self):
        pdf=pdf_ficticio();self.assertEqual(validar_archivo('../../Nombre Persona.pdf',pdf).mime,'application/pdf')
        with self.assertRaises(ValueError):validar_archivo('archivo.pdf',b'<html>falso</html>')
        with self.assertRaises(ValueError):validar_archivo('archivo.svg',b'<svg/>')
        with self.assertRaises(ValueError):validar_archivo('archivo.pdf',b'x'*(MAX_BYTES+1))
        with self.assertRaises(ValueError):validar_archivo('archivo.pdf',b'')
        salida=BytesIO();Document().save(salida)
        self.assertTrue(validar_archivo('cualquiera.docx',salida.getvalue()))
        with self.assertRaises(ValueError):validar_archivo('cualquiera.xlsx',salida.getvalue())
        from zipfile import ZipFile
        salida=BytesIO()
        with ZipFile(salida,'w') as z:
            z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>')
            z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>')
        self.assertTrue(validar_archivo('archivo.xlsx',salida.getvalue()))
        salida=BytesIO();Image.new('RGB',(5,5),'white').save(salida,'PNG')
        self.assertTrue(validar_archivo('imagen.png',salida.getvalue()))
        with self.assertRaises(ValueError):validar_archivo('imagen.jpg',salida.getvalue())


class DocumentosTests(unittest.TestCase):
    def preparar(self):
        repo=base.FakeRepository();s=Servidor(repo);return DocumentosCaso(repo),s
    def test_upload_retry_visibility_signing_delete_and_opaque_filename(self):
        docs,s=self.preparar();caso=str(uuid4());id=str(uuid4());s.bucket.fallar_tras_subir=True
        with self.assertRaises(ConnectionError):docs.subir(caso,'Lista de asistencia','Nombre_Apellido.pdf',pdf_ficticio(),documento_id=id)
        self.assertEqual(len(s.filas),1);self.assertEqual(s.filas[0]['estado_archivo'],'pendiente')
        # Reutilizar exactamente los bytes evita incluir la hora de otro PDF.
        contenido=next(iter(s.objetos.values()))
        d=docs.subir(caso,'Lista de asistencia','Nombre_Apellido.pdf',contenido,documento_id=id)
        self.assertEqual(s.bucket.uploads,1);self.assertTrue(d['visible_cliente'])
        self.assertNotIn('Nombre',d['nombre']);self.assertNotIn('Apellido',d['archivo_path'])
        docs.enlace(id);self.assertEqual(s.bucket.firmas[0][1],600)
        docs.visibilidad(id,False);self.assertFalse(s.filas[0]['visible_cliente'])
        s.bucket.fallar_borrado=True
        with self.assertRaises(ConnectionError):docs.eliminar(id)
        self.assertEqual(s.filas[0]['estado_archivo'],'eliminando');self.assertFalse(s.filas[0]['visible_cliente'])
        with self.assertRaises(PermissionError):docs.enlace(id)
        docs.eliminar(id);self.assertFalse(s.objetos);self.assertEqual(s.filas[0]['estado_archivo'],'eliminado')
    def test_auto_quote_is_private_unique_and_never_restored_after_delete(self):
        docs,s=self.preparar();caso,_,q=propuesta();q['id']=str(uuid4())
        a=docs.sincronizar_cotizacion(caso,q);b=docs.sincronizar_cotizacion(caso,q)
        self.assertEqual(a['id'],b['id']);self.assertFalse(a['visible_cliente']);self.assertEqual(len(s.filas),1)
        docs.eliminar(a['id']);docs.sincronizar_cotizacion(caso,q)
        self.assertEqual(s.filas[0]['estado_archivo'],'eliminado');self.assertFalse(s.objetos)
    def test_client_cannot_write_and_missing_document_cannot_be_signed(self):
        docs,s=self.preparar();docs.repo.is_owner=False
        for accion in (lambda:docs.subir(str(uuid4()),'Informe','x.pdf',pdf_ficticio()),lambda:docs.visibilidad(str(uuid4()),True),lambda:docs.eliminar(str(uuid4()))):
            with self.assertRaises(PermissionError):accion()
        with self.assertRaises(PermissionError):docs.enlace(str(uuid4()))
        self.assertFalse(s.bucket.firmas)
    def test_notice_is_generic_without_attachments_once_and_failure_does_not_erase_upload(self):
        docs,s=self.preparar();d=docs.subir(str(uuid4()),'Informe','Dato_personal.pdf',pdf_ficticio(),nota='NOTA SENSIBLE FICTICIA')
        with patch('servicios.aviso_documento.entregar_mensaje') as smtp:
            self.assertEqual(avisar_documento(docs,d,{},'cliente@example.test'),'enviado')
            mensaje=smtp.call_args.args[0]
            self.assertEqual(list(mensaje.iter_attachments()),[])
            self.assertNotIn('NOTA SENSIBLE',str(mensaje));self.assertNotIn('Dato_personal',str(mensaje))
            self.assertEqual(avisar_documento(docs,d,{},'cliente@example.test'),'ya_reservado');self.assertEqual(smtp.call_count,1)
        segundo=docs.subir(str(uuid4()),'Material','x.pdf',pdf_ficticio())
        with patch('servicios.aviso_documento.entregar_mensaje',side_effect=ConnectionError):
            self.assertEqual(avisar_documento(docs,segundo,{},'cliente@example.test'),'incierto')
        self.assertEqual(s.filas[-1]['estado_archivo'],'disponible');self.assertEqual(s.filas[-1]['aviso_estado'],'incierto')


class DocumentosUITests(unittest.TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean
    def app_documentos(self):
        _,repo=self.setup_app();caso,_,_=propuesta();repo.case_rows=[caso];s=Servidor(repo)
        app=base.AppTest.from_string('''
from servicios.repositorio import Repository
from paginas.documentos_caso import documentos_caso
repo=Repository(None,None,None)
documentos_caso(repo,repo.case_rows[0],repo.quote_rows)
''',default_timeout=20)
        return app,repo,s
    def test_upload_default_visibility_notice_failure_and_confirmed_delete(self):
        app,repo,s=self.app_documentos()
        archivo=SimpleNamespace(name='Apellido Privado.pdf',getvalue=pdf_ficticio)
        with patch('streamlit.file_uploader',return_value=[archivo]),patch('streamlit.secrets',{'smtp':{}}),patch('paginas.documentos_caso.avisar_documento',return_value='incierto'):
            app.run();self.assertTrue(base.by_label(app.toggle,'Avisar al cliente por correo').value)
            base.by_label(app.button,'Subir documentos').click().run();self.assert_clean(app)
            self.assertTrue(s.filas[0]['visible_cliente']);self.assertEqual(s.filas[0]['tipo'],'Lista de asistencia')
            self.assertTrue(any('El cliente ya puede verlo' in x.value for x in app.success))
            self.assertTrue(any('quedó guardado' in x.value for x in app.warning))
            self.assertTrue(base.by_label(app.button,'Eliminar documento').disabled)
            base.by_label(app.checkbox,'Confirmo eliminar este documento').set_value(True).run()
            base.by_label(app.button,'Eliminar documento').click().run();self.assert_clean(app)
            self.assertEqual(s.filas[0]['estado_archivo'],'eliminado')
    def test_account_pending_and_ui_role_guard(self):
        app,repo,s=self.app_documentos();s.cuenta=False
        with patch('streamlit.file_uploader',return_value=[SimpleNamespace(name='x.pdf',getvalue=pdf_ficticio)]),patch('streamlit.secrets',{}):
            app.run();base.by_label(app.toggle,'Avisar al cliente por correo').set_value(False)
            base.by_label(app.button,'Subir documentos').click().run()
            self.assertTrue(any('cuando cree su cuenta' in x.value for x in app.success))
        from paginas.documentos_caso import documentos_caso
        repo.profile['rol']='cliente'
        with self.assertRaises(PermissionError):documentos_caso(repo,repo.case_rows[0],[])


if __name__=='__main__':unittest.main()
