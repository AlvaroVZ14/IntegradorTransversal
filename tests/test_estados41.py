"""Datos ficticios. No hay consultas ni envíos reales."""
from datetime import date,timedelta
from copy import deepcopy
import json
import unittest
from xml.etree import ElementTree
import pandas as pd
import test_app as base
from test_tema30 import contraste
from ui.estados import (CATALOGO,color_estado,chip_estado,chip_antiguedad,
                        estado_cotizacion,vigencia_cotizacion,mapa_colores,clase_estado,html_correo,TEXTO_GRAFICOS)
from ui.tema import html_tabla_registros
from utils.graficos_dashboard import embudo_estados


class EstadosTests(unittest.TestCase):
    def test_catalogo_serializable_completo_y_contraste(self):
        json.dumps(CATALOGO)
        for tipo,grupo in CATALOGO.items():
            for e in grupo.values():
                with self.subTest(tipo=tipo,estado=e['clave']):
                    self.assertGreaterEqual(contraste(e['texto'],e['fondo']),4.5)
                    self.assertGreaterEqual(contraste(TEXTO_GRAFICOS,e['solido']),4.5)
                    self.assertTrue(e['icono']);self.assertTrue(e['ayuda']);self.assertTrue(e['borde'])
                    chip=chip_estado(e['clave'],tipo)
                    self.assertIn(e['etiqueta'],chip);self.assertIn(e['icono'],chip)

    def test_alias_no_cambia_datos_y_chips_escapan_html(self):
        for viejo,nuevo in [('En revisión','Solicitud'),('Cotizado','Cotizada'),('Vendido','Aceptada'),('En ejecución','En seguimiento'),('Finalizado','Cerrada'),('Cancelado','Rechazada')]:
            self.assertEqual(color_estado(viejo)['etiqueta'],nuevo)
            self.assertEqual(clase_estado(viejo),clase_estado(nuevo))
        self.assertEqual(color_estado('Abono recibido','pago')['etiqueta'],'Anticipo pagado')
        self.assertIn('&lt;script&gt;',chip_estado('<script>'))

    def test_limites_antiguedad(self):
        for dias,clave in [(0,'reciente'),(1,'reciente'),(2,'atencion'),(5,'atencion'),(6,'demorada')]:
            self.assertIn(clase_estado(clave,'antiguedad'),chip_antiguedad(dias))
            self.assertIn(str(dias),chip_antiguedad(dias))

    def test_cotizacion_fechas_limites_deshecho_y_version_ajena(self):
        hoy=date(2026,11,5)
        q=dict(id='cotizacion-a',fecha_emision=hoy.isoformat(),valida_hasta=(hoy+timedelta(days=30)).isoformat())
        original=deepcopy(q)
        self.assertIsNone(estado_cotizacion(q,hoy=hoy))
        envio=dict(cotizacion_id=q['id'],tipo='envio',created_at='2026-11-05T12:00:00Z')
        self.assertEqual(estado_cotizacion(q,eventos=[envio],hoy=hoy),'enviada')
        for dias,esperado in [(5,None),(6,'sin_respuesta'),(30,'sin_respuesta'),(31,'vencida')]:
            caso=dict(q,fecha_emision=(hoy-timedelta(days=dias)).isoformat())
            self.assertEqual(estado_cotizacion(caso,hoy=hoy),esperado)
        self.assertEqual(estado_cotizacion(dict(q,valida_hasta=(hoy-timedelta(days=1)).isoformat()),hoy=hoy),'vencida')
        self.assertEqual(estado_cotizacion(dict(q,estado='Borrador'),hoy=hoy),'borrador')
        decision=dict(envio,tipo='aceptar')
        self.assertEqual(estado_cotizacion(q,eventos=[decision],hoy=hoy),'aceptada')
        self.assertIsNone(estado_cotizacion(q,eventos=[dict(decision,cotizacion_id='cotizacion-b')],hoy=hoy))
        self.assertIsNone(estado_cotizacion(q,eventos=[dict(decision,deshecho_en='2026-11-05T12:00:05Z')],hoy=hoy))
        self.assertEqual(estado_cotizacion(q,eventos=[dict(decision,tipo='rechazar')],hoy=hoy),'rechazada')
        self.assertEqual(q,original)
        self.assertEqual(vigencia_cotizacion(q,hoy),'Vence en 30 días')
        self.assertEqual(vigencia_cotizacion(dict(q,valida_hasta=str(hoy)),hoy),'Vence hoy')

    def test_tabla_conserva_filas_orden_y_textos(self):
        frame=pd.DataFrame([{'Caso':'MF-2026-0002','Estado':'Cotizada'},{'Caso':'MF-2026-0001','Estado':'Solicitud'}])
        tabla=ElementTree.fromstring(html_tabla_registros(frame))
        filas=tabla.findall('.//tbody/tr')
        self.assertEqual(len(filas),2)
        self.assertEqual(filas[0].attrib['class'],clase_estado('Cotizada'))
        self.assertIn('MF-2026-0002',''.join(filas[0].itertext()))
        self.assertEqual(frame.iloc[0]['Estado'],'Cotizada')

    def test_embudo_orden_y_colores_explicitos_incluso_con_ceros(self):
        colores=mapa_colores()
        frame=pd.DataFrame([{'estado':e,'Casos':1} for e in reversed(colores)])
        fig=embudo_estados(frame)
        etapas=list(colores)[:-1]
        self.assertEqual(list(fig.data[0].y),etapas)
        self.assertEqual(list(fig.data[0].marker.color),[colores[e] for e in etapas])
        self.assertEqual(sum(fig.data[0].x),5)
        self.assertIsNone(embudo_estados(pd.DataFrame(columns=['estado','Casos'])))

    def test_correo_html_escapado_mismos_colores(self):
        html=html_correo('<script>dato ficticio</script>','Solicitud')
        self.assertNotIn('<script>',html)
        for k in ('texto','fondo','borde'):self.assertIn(color_estado('Solicitud')[k],html)


class RecorridoEstadosTests(unittest.TestCase):
    def setUp(self):
        self.base=base.AppTests();self.addCleanup(self.base.doCleanups)

    def test_filtros_conteos_csv_leyenda_sin_mutar_estados(self):
        app,repo=self.base.setup_app();app.run();self.base.create_request(app)
        from mente_futuro.domain import STATES
        original=deepcopy(repo.case_rows[0])
        repo.case_rows=[dict(original,id=f'ficticio-{i}',numero=i+1,estado=e) for i,e in enumerate(STATES)]
        app.session_state['dashboard_revision']+=1
        app.session_state['selected_case']=None;app.session_state['caso_abierto']=None
        app.run();self.base.assert_clean(app)
        self.assertTrue(any(e.label=='¿Qué significa cada color?' for e in app.expander))
        html=next(m.value for m in app.markdown if '<table' in m.value)
        for e in CATALOGO['caso'].values():self.assertIn(e['etiqueta'],html);self.assertIn(e['icono'],html)
        self.assertTrue(app.get('download_button'))
        self.assertEqual([c['estado'] for c in repo.case_rows],STATES)


if __name__=='__main__':unittest.main()
