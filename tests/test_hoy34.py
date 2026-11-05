"""Hoy compacto: datos ficticios, sin red, archivos de cliente ni correos reales."""
from copy import deepcopy
from datetime import datetime,timedelta
from unittest import TestCase
from unittest.mock import Mock,patch
from types import SimpleNamespace
import test_app as base
from test_hoy import datos
from servicios.hoy import CHILE,pendientes,configuracion_hoy,casos_por_accion
from servicios.hoy_vista import fecha_larga,para_hacer_ahora,actividad_reciente,hace_cuanto,avisos_automatizacion


class HoyVistaTests(TestCase):
    def setUp(self):self.ahora=datetime(2026,11,3,12,tzinfo=CHILE)

    def test_fecha_larga_y_relativos_sin_inventar_hora(self):
        self.assertEqual(fecha_larga(self.ahora),'martes 3 de noviembre')
        for segundos,texto in [(12,'Ahora'),(60,'Hace 1 minuto'),(7200,'Hace 2 horas'),(86400,'Hace 1 día')]:
            self.assertEqual(hace_cuanto((self.ahora-timedelta(seconds=segundos)).isoformat(),self.ahora),texto)
        self.assertEqual(hace_cuanto('2026-11-03',self.ahora),'Hoy')

    def test_lista_unica_urgente_limite_y_filtro_completo(self):
        c,q,v,e,env=datos(self.ahora)
        c += [dict(c[0],id='extra-'+str(i),numero=10+i,created_at=(self.ahora-timedelta(days=i)).isoformat()) for i in range(8)]
        snapshot=dict(casos=c,cotizaciones=q,ventas=v,eventos=e,envios=env,configuracion={})
        grupos=pendientes(c,q,v,e,env,configuracion_hoy(),self.ahora)
        antes=deepcopy(grupos)
        lista=para_hacer_ahora(grupos)
        self.assertEqual(len(lista),5)
        self.assertEqual([i['dias'] for i in lista],sorted([i['dias'] for i in lista],reverse=True))
        self.assertEqual(casos_por_accion(snapshot,'Para hacer ahora',self.ahora),[i['caso'] for i in para_hacer_ahora(grupos,None)])
        self.assertEqual(grupos,antes)

    def test_actividad_cinco_eventos_venta_sin_duplicado_documentos_cliente(self):
        c,q,v,_,env=datos(self.ahora)
        evento=dict(id='evento-venta',caso_id=v[0]['caso_id'],tipo='vender',created_at=(self.ahora-timedelta(minutes=3)).isoformat())
        snapshot=dict(casos=c,cotizaciones=q,ventas=v,eventos=[evento],envios=env,
            documentos=[dict(id='doc-a',caso_id=c[0]['id'],origen='cliente',fecha_subida=(self.ahora-timedelta(minutes=1)).isoformat()),
                        dict(id='doc-b',caso_id=c[0]['id'],origen='socia',fecha_subida=self.ahora.isoformat()),
                        dict(id='doc-c',caso_id=c[0]['id'],origen='cliente',estado_archivo='eliminado',fecha_subida=self.ahora.isoformat())])
        antes=deepcopy(snapshot);actividad=actividad_reciente(snapshot,self.ahora)
        self.assertEqual(len(actividad),5);self.assertEqual(actividad[0]['id'],'documento:doc-a')
        self.assertEqual(sum(e['texto']=='Venta registrada' and e['caso_id']==v[0]['caso_id'] for e in actividad),1)
        self.assertFalse(any(e['id'] in ('documento:doc-b','documento:doc-c') for e in actividad))
        self.assertEqual(snapshot,antes)
        snapshot['eventos']=[dict(evento,tipo='aceptar',deshecho_en=self.ahora.isoformat())]
        self.assertFalse(any(e['texto']=='Propuesta aceptada' for e in actividad_reciente(snapshot,self.ahora)))

    def test_hoja_ausente_sana_y_desactualizada(self):
        self.assertEqual(avisos_automatizacion({},self.ahora),[])
        def ejemplo(**campos):return dict(automatizaciones=dict(hoja_calculo=dict(integrada=True,**campos)))
        self.assertEqual(avisos_automatizacion(ejemplo(ultima_sincronizacion=self.ahora.isoformat()),self.ahora),[])
        self.assertEqual(len(avisos_automatizacion(ejemplo(ultima_sincronizacion=(self.ahora-timedelta(days=2)).isoformat(),estado_correo='error'),self.ahora)),2)


class HoyUITests(TestCase):
    setup_app=base.AppTests.setup_app
    assert_clean=base.AppTests.assert_clean

    def setUp(self):
        reloj=patch('servicios.en_vivo.time',return_value=120)
        reloj.start();self.addCleanup(reloj.stop)

    def test_cero_uno_diez_orden_de_pantalla_y_lista_cinco(self):
        for cantidad in (0,1,10):
            with self.subTest(cantidad=cantidad):
                app,repo=self.setup_app()
                original=datos()[0][0]
                repo.case_rows=[dict(original,id='ficticio-'+str(i),numero=i+1,cliente='Empresa ficticia '+str(i),
                    created_at=(datetime.now(CHILE)-timedelta(days=i+1)).isoformat()) for i in range(cantidad)]
                repo.live_snapshot=Mock(wraps=repo.live_snapshot)
                app.run();self.assert_clean(app)
                self.assertEqual(repo.live_snapshot.call_count,1)
                self.assertEqual(len([b for b in app.button if b.label=='Cotizar']),min(cantidad,5))
                self.assertEqual([s.value for s in app.subheader][:2],['Para hacer ahora','Actividad reciente'])
                self.assertEqual(app.button(key='hoy_tarjeta_solicitudes').label,f'**{cantidad}**\n\nPor cotizar')
                self.assertFalse(any('mfy-glass-chips' in m.value for m in app.markdown if '<style' not in m.value))
                self.assertTrue(any(p.label=='Más opciones' for p in app.get('page_link')))
                antes=repo.live_snapshot.call_count;app.run();self.assert_clean(app)
                self.assertEqual(repo.live_snapshot.call_count,antes)
                if cantidad:
                    revision=app.session_state.get('dashboard_revision',0)
                    repo.case_rows.append(dict(original,id='nueva',numero=99))
                    app.session_state['dashboard_revision']=revision+1
                    app.run();self.assert_clean(app)
                    self.assertEqual(app.button(key='hoy_tarjeta_solicitudes').label,f'**{cantidad+1}**\n\nPor cotizar')

    def test_atajo_nueva_solicitud_y_union_seguimientos(self):
        app,repo=self.setup_app()
        repo.case_rows,repo.quote_rows,repo.sale_rows,repo.event_rows,repo.email_rows=datos()
        app.run();self.assert_clean(app)
        self.assertTrue(any(b.label=='Hacer seguimiento' for b in app.button))
        base.by_label(app.button,'Ver todas').click().run();self.assert_clean(app)
        self.assertEqual(base.by_label(app.selectbox,'Filtrar estado').value,'Para hacer ahora')
        base.ir_a(app,'Hoy')
        app.button(key='hoy_nueva').click().run();self.assert_clean(app)
        self.assertEqual(app.session_state['navigation'],'Nueva solicitud')

    def test_copia_manual_muestra_siempre_el_texto_actual(self):
        puente=lambda **kwargs:SimpleNamespace(copiado=False,fallo=True)
        with patch('utils.mensaje_listo.component',return_value=puente):
            app=base.AppTest.from_string('''
import streamlit as st
from utils.mensaje_listo import copiar_mensaje
copiar_mensaje(st.session_state.get('texto','Primer mensaje ficticio'),'prueba_manual')
''').run()
            self.assert_clean(app)
            self.assertEqual(app.text_area[0].value,'Primer mensaje ficticio')
            app.session_state['texto']='Segundo mensaje ficticio'
            app.run();self.assert_clean(app)
            self.assertEqual(app.text_area[0].value,'Segundo mensaje ficticio')
