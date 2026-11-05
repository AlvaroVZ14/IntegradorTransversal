"""Copia de informes con datos ficticios, sin conexiones ni credenciales reales."""
from copy import deepcopy
from datetime import date
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock
from servicios.hoja_columnas import COLUMNAS,CLAVES
from servicios.hoja_formato import formulas_resumen,preparar,MARCA
from servicios.hoja_sync import matrices,fusionar,procesar,reintentar,FalloHoja,GoogleHoja,configuracion,avisar

def datos():
    fila={c:None for c in COLUMNAS['Casos']}
    fila.update(codigo='MF-2026-0001',fecha_solicitud='2026-11-05',empresa='Empresa ficticia',participantes=4,monto_vendido=100000,tematica='Liderazgo\n de equipos')
    return {'Casos':[fila],'Cotizaciones':[],'Ventas':[]}

class Base:
    def __init__(self):self.lote={'completo':False,'codigos':['MF-2026-0001'],'datos':datos()};self.confirmaciones=[]
    def tomar(self,*args):return deepcopy(self.lote)
    def renovar(self,*args):pass
    def finalizar(self,token,error,filas):self.confirmaciones.append(error)
class Hoja:
    def __init__(self):self.tablas={h:[list(COLUMNAS[h])] for h in CLAVES};self.registros=[]
    def preparar(self):pass
    def leer(self):return deepcopy(self.tablas)
    def escribir(self,tablas,anteriores,validar):validar();self.tablas=deepcopy(tablas)
    def registro(self,filas,validar):validar();self.registros+=filas

class Hoja38Tests(unittest.TestCase):
    def test_secciones_reales_de_streamlit_sin_deepcopy(self):
        from streamlit.runtime.secrets import AttrDict
        original=AttrDict({'hoja':{'activada':True,'database_url':'conexion_ficticia','id':'ID_FICTICIO_12345',
            'google':{'client_email':'informes@example.test','private_key':'CLAVE_FICTICIA'}}})
        with patch.dict('os.environ',{},clear=True),patch('streamlit.secrets',original):
            resultado=configuracion()
        self.assertTrue(resultado['activada'])
        self.assertIsInstance(resultado['google'],dict)
        self.assertEqual(resultado['google']['private_key'],'CLAVE_FICTICIA')
        resultado['google']['private_key']='MODIFICADA'
        self.assertEqual(original['hoja']['google']['private_key'],'CLAVE_FICTICIA')

    def test_contrato_privado_falla_cerrado(self):
        d=datos();d['Casos'][0]['rut']='12.345.678-5'
        with self.assertRaises(FalloHoja):matrices(d)
        with self.assertRaises(FalloHoja):matrices({})
    def test_fechas_numeros_textos_y_claves(self):
        fila=matrices(datos())['Casos'][0];cols=COLUMNAS['Casos']
        self.assertEqual(fila[cols.index('fecha_solicitud')],(date(2026,11,5)-date(1899,12,30)).days)
        self.assertEqual(fila[cols.index('monto_vendido')],100000)
        self.assertEqual(fila[cols.index('tematica')],'Liderazgo de equipos')
        d=datos();d['Casos']*=2
        with self.assertRaises(FalloHoja):matrices(d)
    def test_repetir_editar_eliminar_reconstruir(self):
        b,h=Base(),Hoja();procesar(b,h);original=deepcopy(h.tablas)
        procesar(b,h);self.assertEqual(h.tablas,original)
        b.lote['datos']['Casos'][0]['participantes']=12;procesar(b,h)
        self.assertEqual(h.tablas['Casos'][1][COLUMNAS['Casos'].index('participantes')],12)
        b.lote['datos']['Casos']=[];procesar(b,h);self.assertEqual(len(h.tablas['Casos']),1)
        b.lote['completo']=True;b.lote['datos']=datos();procesar(b,h,completo=True)
        primero=deepcopy(h.tablas);procesar(b,h,completo=True);self.assertEqual(h.tablas,primero)
        self.assertTrue(all(e is None for e in b.confirmaciones))
    def test_google_caido_conserva_cola_y_no_expone_error(self):
        b,h=Base(),Hoja();h.escribir=Mock(side_effect=RuntimeError('CLAVE_SECRETA'))
        with self.assertRaises(FalloHoja) as e:procesar(b,h)
        self.assertNotIn('CLAVE_SECRETA',str(e.exception));self.assertEqual(b.confirmaciones,['error']);self.assertIsNotNone(b.lote)
        with self.assertRaises(FalloHoja):procesar(b,Mock(side_effect=ValueError('SECRETO')))
        self.assertEqual(b.confirmaciones,['error','error'])
    def test_cuota_backoff_y_errores_permanentes(self):
        error=RuntimeError();error.response=SimpleNamespace(status_code=429)
        llamada=Mock(side_effect=[error,error,'bien']);esperas=[]
        self.assertEqual(reintentar(llamada,dormir=esperas.append,aleatorio=lambda:0),'bien')
        self.assertEqual(esperas,[60,60])
        permanente=Mock(side_effect=ValueError('credencial'))
        with self.assertRaises(FalloHoja):reintentar(permanente,dormir=esperas.append)
        self.assertEqual(permanente.call_count,1)
    def test_borrados_limpian_filas_y_texto_no_se_ejecuta(self):
        h=object.__new__(GoogleHoja);h.libro=Mock();h.propiedades={x:{'sheetId':i,'gridProperties':{'rowCount':1000}} for i,x in enumerate(CLAVES)}
        d=datos();d['Casos'][0]['empresa']='=IMPORTXML("URL_FICTICIA")'
        tablas={x:[list(COLUMNAS[x])]+filas for x,filas in matrices(d).items()}
        anteriores={x:tablas[x]+[['antiguo']] for x in CLAVES};validar=Mock()
        h.escribir(tablas,anteriores,validar)
        solicitud=h.libro.values_batch_update.call_args.args[0]
        self.assertEqual(solicitud['valueInputOption'],'RAW');self.assertNotIn('Resumen',str(solicitud))
        self.assertEqual(solicitud['data'][0]['values'][-1],['']*len(COLUMNAS['Casos']))
        self.assertTrue(validar.called)
    def test_registro_con_maximo_500(self):
        h=object.__new__(GoogleHoja);h.libro=Mock();h.libro.values_get.return_value={'values':[[n] for n in range(500)]}
        h.registro([[500,'Casos',1,'Correcto','']],lambda:None)
        filas=h.libro.values_update.call_args.kwargs['body']['values']
        self.assertEqual(len(filas),500);self.assertEqual(filas[0],[1]);self.assertEqual(filas[-1][0],500)
    def test_formulas_solo_propias_y_no_ocultan_error_de_consulta(self):
        for formula in formulas_resumen().values():
            self.assertIn('QUERY(',formula);self.assertIn('Sin datos',formula);self.assertNotIn('IFERROR',formula)
    def test_preparacion_respeta_resumen_ya_existente(self):
        libro=Mock();libro.fetch_sheet_metadata.return_value={'sheets':[{'properties':{'title':h,'sheetId':i},'developerMetadata':[{'metadataKey':MARCA}]} for i,h in enumerate(COLUMNAS)]}
        libro.values_get.return_value={'values':[['=FORMULA_PROPIA()']]}
        preparar(libro,'informes@example.test');libro.values_batch_update.assert_not_called();libro.batch_update.assert_not_called()
    def test_no_admin_no_lee_credenciales(self):
        with patch('servicios.hoja_sync.configuracion') as c:avisar(admin=False);c.assert_not_called()
        self.assertIsNone(configuracion({}))
    def test_encabezado_incompatible_solo_reconstruccion(self):
        with self.assertRaises(FalloHoja):fusionar('Casos',[['alterado']],[],[],False)
        self.assertEqual(fusionar('Casos',[['alterado']],[],[],True),[list(COLUMNAS['Casos'])])
    def test_no_se_pierde_error_por_finalizacion_fallida(self):
        b=Base();b.finalizar=Mock(side_effect=RuntimeError('DSN_SECRETO'))
        with self.assertRaises(FalloHoja) as e:procesar(b,Hoja())
        self.assertNotIn('DSN_SECRETO',str(e.exception))

if __name__=='__main__':unittest.main()
