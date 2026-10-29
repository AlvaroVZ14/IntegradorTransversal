"""Documentos con datos ficticios, sin leer clientes ni configuración reales."""
from copy import deepcopy
from io import BytesIO
import unittest
from pypdf import PdfReader
from datos_cotizacion_ficticios import ejemplo
from servicios.documentos_cotizacion import generar_pdf,documento_descarga,nombre_archivo
from mente_futuro.domain import quote_total


def ejemplos_pdf():
    _,_,uno=ejemplo()
    uno['documento']['marca']={'nombre':'Consultora Horizonte SpA','sitio_web':'https://example.test',
                              'correo_contacto':'contacto@example.test'}
    uno.update(descuento_pct=0,descuento_motivo='',total_clp=1250000)
    uno['documento'].update(descuento_pct=0,descuento_motivo='')
    varios=deepcopy(uno)
    varios.update(numero=2,detalle='1. Taller de colaboración: 4 horas para 20 participantes.\n'
        '2. Charla de comunicación: 1 hora para 20 participantes.\n'
        '3. Sesión de seguimiento: 1 hora para 4 representantes.\n'
        'El valor corresponde al programa completo; no hay precios individuales acordados.')
    varios['documento']['horas']=6.0
    largo=deepcopy(uno)
    largo.update(numero=3,descuento_pct=15,descuento_motivo='Convenio institucional ficticio',
                 iva_pct=19,total_clp=quote_total(1250000,15,19))
    largo['documento'].update(descuento_pct=15,descuento_motivo=largo['descuento_motivo'],iva_pct=19)
    largo['documento']['textos']['objetivos']='\n'.join(
        f'{i+1}. Fortalecer la colaboración mediante actividades prácticas, reflexión guiada y acuerdos del equipo.'
        for i in range(35))+'\nFIN DE OBJETIVOS EXTENSOS'
    largo['condiciones']='\n'.join(
        f'Cláusula {i+1}: La organización coordinará los espacios, materiales y horarios con la facilitadora. '
        'Cualquier ajuste de alcance debe acordarse antes de la jornada.' for i in range(24))+'\nFIN DE CONDICIONES EXTENSAS'
    return [('un_servicio',uno),('varios_componentes',varios),('descuento_notas_largas',largo)]


class DocumentosPDFTests(unittest.TestCase):
    def test_three_documents_include_amounts_dates_and_full_long_text(self):
        for nombre,q in ejemplos_pdf():
            with self.subTest(nombre=nombre):
                reader=PdfReader(BytesIO(generar_pdf(q)))
                text='\n'.join(page.extract_text() for page in reader.pages)
                for value in ('Fundación Horizonte Norte','Daniela Soto','DIRIGIDO A','INVERSIÓN',
                              'CONDICIONES COMERCIALES','Consultora Horizonte SpA','contacto@example.test'):
                    self.assertIn(value,text)
                self.assertNotIn('{{',text)
                self.assertRegex(text,r'\d{2}/\d{2}/\d{4}')
                for i,page in enumerate(reader.pages):self.assertIn(f'Página {i+1}',page.extract_text())
                if nombre=='varios_componentes':
                    for value in ('Taller de colaboración','Charla de comunicación','Sesión de seguimiento'):
                        self.assertIn(value,text)
                if nombre=='descuento_notas_largas':
                    self.assertIn('$1.264.375',text)
                    self.assertIn('15%',text)
                    self.assertIn('FIN DE OBJETIVOS EXTENSOS',text)
                    self.assertIn('FIN DE CONDICIONES EXTENSAS',text)
                    self.assertGreater(len(reader.pages),2)

    def test_historical_configuration_fallback_never_changes_stored_quote(self):
        _,_,q=ejemplo();q['documento']={}
        original=deepcopy(q)
        config={'emisor':{'razon_social':'Emisor ficticio'},'nombre':'Marca ficticia',
                'condiciones':'Nuevas condiciones generales'}
        preparado=documento_descarga(q,config)
        self.assertEqual(q,original)
        self.assertEqual(preparado['documento']['emisor'],config['emisor'])
        self.assertEqual(preparado['condiciones'],original['condiciones'])
        preparado['documento']['emisor']['razon_social']='Otra razón social'
        self.assertEqual(config['emisor']['razon_social'],'Emisor ficticio')

    def test_filename_cannot_contain_paths(self):
        _,_,q=ejemplo();q['snapshot']['cliente']='Fundación / Norte: <demo> \\ prueba'
        nombre=nombre_archivo(q)
        self.assertTrue(nombre.startswith('Cotizacion_COT-'))
        self.assertTrue(nombre.endswith('.pdf'))
        self.assertNotRegex(nombre,r'[<>:/\\]')


if __name__=='__main__':unittest.main()
