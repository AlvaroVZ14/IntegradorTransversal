"""Redes opcionales: validación, formulario único, persistencia y PDF ficticio."""
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
from pathlib import Path

from pypdf import PdfReader
from docx import Document
from servicios.redes_sociales import normalizar_red, normalizar_redes, REDES
from servicios.formulario import guardar, faltantes
from servicios.ficha_caso import generar_ficha_pdf
from servicios.documentos_cotizacion import generar_pdf,generar_word
from utils.formulario_config import CAMPOS
import test_app as base
from test_propuesta_documento import propuesta

TODAS=dict(instagram='@empresa_norte',linkedin='linkedin.com/company/horizonte-ficticio',
           facebook='facebook.com/horizonte-ficticio',sitio_web='empresa.example.test',otra_red='TikTok: @empresa_norte')


class RedesTests(TestCase):
    def test_formatos_opcionales_limites_y_urls_peligrosas(self):
        for valor in ('@empresa_norte','empresa_norte','https://instagram.com/empresa_norte/?igsh=abc'):
            self.assertEqual(normalizar_red('instagram',valor),'https://www.instagram.com/empresa_norte/')
        self.assertEqual(normalizar_red('sitio_web','empresa.example.test'),'https://empresa.example.test')
        self.assertEqual(normalizar_red('sitio_web','http://empresa.example.test/ruta'),'http://empresa.example.test/ruta')
        self.assertEqual(normalizar_red('otra_red','TikTok: @empresa'),'TikTok: @empresa')
        for campo in REDES:
            self.assertEqual(normalizar_red(campo,''),'')
            for valor in ('javascript:alert(1)','data:text/html,mal','file:///tmp/a','ftp://empresa.test','x'*201,'https://empresa.test/%0a','https://empresa.test/\\mal'):
                with self.subTest(campo=campo,valor=valor):
                    with self.assertRaisesRegex(ValueError,REDES[campo][0]):normalizar_red(campo,valor)
        for valor in ('no es un enlace','https://a..test','https://user:password@example.test','https://empresa.test:0'):
            with self.assertRaises(ValueError):normalizar_red('sitio_web',valor)
        with self.assertRaises(ValueError):normalizar_red('instagram','https://instagram.com.evil.test/empresa')
        self.assertEqual(normalizar_red('otra_red','á'*200),'á'*200)

    def test_pdf_ficha_enlaces_textos_largos_y_cotizacion_sin_redes(self):
        caso,_,q=propuesta();caso['created_at']='2026-11-02T15:00:00Z';caso['redes_sociales']=normalizar_redes(TODAS)
        caso['redes_sociales']['sitio_web']='https://empresa.example.test/'+'a'*160
        caso['detalle']=('Detalle ficticio de capacitación y acompañamiento. '*120)+' FIN DEL DETALLE'
        pdf=generar_ficha_pdf(caso);reader=PdfReader(BytesIO(pdf))
        texto='\n'.join(p.extract_text() for p in reader.pages)
        for etiqueta in ('Redes sociales','Instagram','LinkedIn','Facebook','Sitio web','Otra red','FIN DEL DETALLE'):
            self.assertIn(etiqueta,' '.join(texto.split()))
        enlaces=[a.get_object().get('/A',{}).get('/URI') for p in reader.pages for a in p.get('/Annots',[])]
        for k,v in caso['redes_sociales'].items():
            if v.startswith('https://'):self.assertIn(v,enlaces)
        q['snapshot']['redes_sociales']=caso['redes_sociales']
        for contenido in ('\n'.join(p.extract_text() for p in PdfReader(BytesIO(generar_pdf(q))).pages),
                          '\n'.join(p.text for p in Document(BytesIO(generar_word(q))).paragraphs)):
            self.assertNotIn('empresa.example.test',contenido);self.assertNotIn('empresa_norte',contenido)
        caso['redes_sociales']={}
        self.assertIn('Sin redes registradas','\n'.join(p.extract_text() for p in PdfReader(BytesIO(generar_ficha_pdf(caso))).pages))


class RedesUITests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def catalogo(self):
        from mente_futuro.domain import SERVICES,TOPICS
        return dict(servicios=SERVICES,tematicas=TOPICS,version=4,pendiente=False)

    def test_formulario_publico_interno_y_cliente_mismos_cinco_campos_sin_pasos_extra(self):
        for modo in ('interno','cliente','publico'):
            app,repo=self.setup_app(modo=='interno')
            if modo=='publico':app.query_params['vista']='solicitud'
            elif modo=='interno':app.query_params['pagina']='Nueva solicitud'
            with patch('servicios.formulario.catalogo_publico',return_value=self.catalogo()),patch('servicios.redes_sociales.precargar_redes',return_value={}):
                app.run()
                if modo!='publico':base.ir_a(app,'Nueva solicitud' if modo=='interno' else 'Solicitar servicio')
                self.assert_clean(app)
                for campo in REDES:
                    base.by_label(app.text_input,CAMPOS[campo].etiqueta).set_value(TODAS[campo])
                app.run();self.assert_clean(app)
                prefijo='publico_' if modo=='publico' else 'request_'
                self.assertEqual(app.text_input(key=prefijo+'instagram').value,'https://www.instagram.com/empresa_norte/')
                self.assertTrue(any('Nos ayuda a conocer mejor' in c.value for c in app.caption))
                app.text_input(key=prefijo+'sitio_web').set_value('javascript:alert(1)').run()
                self.assertTrue(any('Revisa Sitio web' in c.value for c in app.markdown))
                self.assertEqual(app.text_input(key=prefijo+'sitio_web').value,'javascript:alert(1)')

    def test_precarga_cliente_y_guardado_sin_redes_no_son_faltantes(self):
        app,repo=self.setup_app(False)
        perfil={'empresa':'Empresa del perfil ficticia','redes_sociales':normalizar_redes(TODAS)}
        with patch('servicios.formulario.catalogo_publico',return_value=self.catalogo()),patch('servicios.redes_sociales.precargar_redes',return_value=perfil):
            app.run();self.assert_clean(app)
            self.assertEqual(app.text_input(key='request_instagram').value,perfil['redes_sociales']['instagram'])
            self.assertTrue(app.text_input(key='request_email').disabled)
            self.assertFalse(app.text_input(key='request_instagram').disabled)
            otra={'empresa':'Otra empresa ficticia','redes_sociales':{'instagram':'https://www.instagram.com/otra_empresa/'}}
            with patch('servicios.redes_sociales.precargar_redes',return_value=otra):
                app.text_input(key='request_cliente').set_value(otra['empresa']).run();self.assert_clean(app)
            self.assertEqual(app.text_input(key='request_instagram').value,otra['redes_sociales']['instagram'])
        from utils.formulario_config import valores_iniciales
        datos=valores_iniciales()
        pendientes=faltantes(datos)
        self.assertFalse(set(REDES)&set(pendientes))
        datos.update(cliente='Empresa ficticia',contacto='Persona ficticia',email='persona@example.test',servicio='Coaching individual',tematicas=['Liderazgo'])
        self.assertFalse(faltantes(datos))

    def test_guardado_envia_json_y_base_antigua_no_descarta_redes(self):
        from utils.formulario_config import valores_iniciales
        repo=base.FakeRepository(False);repo.create_request=Mock(return_value={'codigo':'MF-2026-0042'})
        valores={**valores_iniciales(),**TODAS,'cliente':'Empresa ficticia','servicio':'Coaching individual','tematicas':['Liderazgo']}
        borrador={'id':'ficticio','values':valores}
        guardar(borrador,'cliente',repo,True,'',self.catalogo())
        enviados=repo.create_request.call_args.args[0]
        self.assertEqual(enviados['redes_sociales'],normalizar_redes(TODAS))
        self.assertFalse(set(REDES)&set(enviados))
        with self.assertRaisesRegex(ValueError,'guardado de redes'):guardar(borrador,'cliente',repo,True,'',{**self.catalogo(),'version':3})

    def test_edicion_caso_autoguarda_y_mantiene_texto_invalido(self):
        app,repo=self.setup_app();app.run();base.AppTests.create_request(self,app)
        caso=repo.case_rows[0];caso['redes_sociales']={};app.run();self.assert_clean(app)
        self.assertTrue(any('Sin redes registradas' in c.value for c in app.caption))
        app.text_input(key=f"red_caso_{caso['id']}_instagram").set_value('@posterior').run();self.assert_clean(app)
        self.assertEqual(caso['redes_sociales']['instagram'],'https://www.instagram.com/posterior/')
        self.assertTrue(any(x.label=='Instagram' for x in app.get('link_button')))
        app.text_input(key=f"red_caso_{caso['id']}_sitio_web").set_value('javascript:alert(1)').run()
        self.assertTrue(app.error);self.assertNotIn('sitio_web',caso['redes_sociales'])
        app.text_input(key=f"red_caso_{caso['id']}_sitio_web").set_value('empresa.example.test').run();self.assert_clean(app)
        self.assertEqual(caso['redes_sociales']['sitio_web'],'https://empresa.example.test')
        self.assertTrue(any(x.label=='Descargar ficha del caso' for x in app.get('download_button')))

    def test_respaldo_incluye_registro_reutilizable_sin_romper_respaldo_anterior(self):
        from test_mantenimiento import snapshot_ficticio
        from servicios.respaldos import zip_csv
        from zipfile import ZipFile
        snapshot=snapshot_ficticio()
        snapshot['tables']['mf_empresas_redes']={'columns':[dict(name='id',type='uuid',generated=False,identity=False)],'rows':[{'id':'empresa-ficticia'}]}
        with ZipFile(BytesIO(zip_csv(snapshot))) as archivo:
            self.assertIn('mf_empresas_redes.csv',archivo.namelist())
