"""Recorridos de UI con repositorio aislado; no usa credenciales reales."""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
from streamlit.util import calc_hash

import streamlit as st
from streamlit.testing.v1 import AppTest

from mente_futuro.domain import quote_total, today
from utils.navegacion import PAGINAS

ROOT=Path(__file__).resolve().parent.parent
(ROOT/'tmp'/'tests').mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(ROOT/'tmp'/'tests')


class Client:
    def __init__(self,owner):
        self.user=SimpleNamespace(id='owner' if owner else 'client',email='test@example.cl')
        self.profile=dict(id=self.user.id,nombre='Camila Rojas' if owner else 'Valentina Soto',email=self.user.email,rol='admin' if owner else 'cliente')
        self.auth=SimpleNamespace(get_user=lambda:SimpleNamespace(user=self.user),sign_out=lambda *_:None)
    def table(self,_): return self
    def select(self,*_): return self
    def eq(self,*_): return self
    def execute(self): return SimpleNamespace(data=[self.profile])


class FakeRepository:
    def __init__(self,owner=True):
        self.is_owner=owner
        self.client=Client(owner)
        self.user=self.client.user
        self.profile=self.client.profile
        self.case_rows=[]
        self.quote_rows=[]
        self.sale_rows=[]
        self.tariff_rows=[]
        self.fail_write=False
        self.draft_rows={}
        self.template_rows=[]
        self.event_rows=[]
        self.email_rows=[]
        self.settings_row=dict(version=1,datos=dict(emisor=dict(razon_social='Consultora Horizonte SpA',rut='12.345.678-5',giro='Capacitación',direccion='Calle Ficticia 123',comuna='Antofagasta',correo='emisor@example.test',telefono='+56 9 1234 5678',representante='Camila Rojas',cuenta_bancaria='Banco ficticio · Cuenta 123'),reserva_pct=30.0,remuneracion_pct=70.0))
    def create_request_legacy(self,data,request_id):return self.create_request(data,request_id)
    def request_notifications(self):return []
    def owner_only(self):
        if not self.is_owner: raise PermissionError('Solo dueña')
    def cases(self): return deepcopy(self.case_rows)
    def live_snapshot(self,vista):
        self.owner_only()
        data={'casos':deepcopy(self.case_rows)}
        if vista in ('dashboard','hoy'):data['ventas']=deepcopy(self.sale_rows)
        if vista=='hoy':data.update(cotizaciones=deepcopy(self.quote_rows),eventos=deepcopy(self.event_rows),
            envios=deepcopy(self.email_rows),configuracion=deepcopy(self.settings_row['datos']))
        return data
    def profiles(self): return [dict(id='client',nombre='Cliente',email='client@example.cl',rol='cliente')]
    def tariffs(self): return deepcopy(self.tariff_rows)
    def quotes(self,case_id): return [deepcopy(q) for q in self.quote_rows if q['caso_id']==case_id]
    def sales(self): return deepcopy(self.sale_rows)
    def create_request(self,data,request_id):
        if self.fail_write: raise ConnectionError('Simulación de fallo')
        row=dict(data,id=request_id,numero=len(self.case_rows)+1,created_at=today().isoformat()+'T12:00:00Z',estado='Solicitud',version=1,fecha_realizacion=None)
        if self.is_owner:
            row['datos_pendientes']=[k for k in ('cliente','contacto','email','servicio','tematica','modalidad','participantes','horas') if row.get(k) is None or row.get(k)=='']
            row['datos_incompletos']=bool(row['datos_pendientes'])
        self.case_rows.append(row)
        return row if self.is_owner else {'codigo': 'MF-2026-0001'}
    def issue_quote(self,case,data,operation_id):
        row=dict(deepcopy(data),id=str(uuid4()),operacion_id=operation_id,version_cotizacion=len(self.quote_rows)+1,numero=len(self.quote_rows)+1,caso_id=case['id'],created_at=today().isoformat(),fecha_emision=today().isoformat(),snapshot=deepcopy(case),total_clp=quote_total(data['base_clp'],data['descuento_pct'],data['iva_pct']))
        self.quote_rows.insert(0,row)
        self.case_rows[0]['estado']='Cotizado'
        self.case_rows[0]['version']+=1
        return row
    def record_sale(self,case,quote,sale_date,payment):
        self.sale_rows.append(dict(id=str(uuid4()),caso_id=case['id'],cotizacion_id=quote['id'],monto_clp=quote['total_clp'],fecha_venta=sale_date.isoformat(),estado_pago=payment,anulada=False,version=1,
            created_at=datetime.now(timezone.utc).isoformat(),estado_caso_anterior=case['estado'],caso_version_aceptada=case['version']+1))
        self.case_rows[0]['estado']='Vendido'
        self.case_rows[0]['version']+=1
        return deepcopy(self.sale_rows[-1])
    def undo_acceptance(self,sale_id,version):
        sale=next(s for s in self.sale_rows if s['id']==sale_id)
        case=self.get_case(sale['caso_id'])
        if case['version']!=version:raise ValueError('Conflicto')
        result=self.update_case(case,{'estado':sale['estado_caso_anterior']})
        self.sale_rows=[s for s in self.sale_rows if s['id']!=sale_id]
        return result
    def update_case(self,case,changes):
        if self.fail_write:raise ConnectionError('Fallo de escritura ficticio')
        row=next(c for c in self.case_rows if c['id']==case['id'])
        row.update(changes)
        row['version']+=1
        from servicios.dashboard_cache import invalidar_dashboard
        invalidar_dashboard()
        return deepcopy(row)
    def get_case(self,case_id):
        self.owner_only()
        return deepcopy(next(c for c in self.case_rows if c['id']==case_id))
    def update_sale(self,sale,payment,annulled):
        row=next(s for s in self.sale_rows if s['id']==sale['id'])
        row.update(estado_pago=payment,anulada=annulled,version=row['version']+1)
        return deepcopy(row)
    def save_tariff(self,data,tariff=None):
        self.tariff_rows.append(dict(data,id=str(uuid4()),version=1))
    def quote_settings(self):return deepcopy(self.settings_row)
    def save_quote_settings(self,data,version):
        self.settings_row=dict(datos=deepcopy(data),version=version+1)
        return deepcopy(self.settings_row)
    def program_templates(self):return deepcopy(self.template_rows)
    def save_program_template(self,data):self.template_rows.append(dict(data,id=str(uuid4()),activa=True))
    def quote_draft(self,case_id):return deepcopy(self.draft_rows.get(case_id))
    def save_quote_draft(self,case_id,data,version):
        if self.fail_write:raise ConnectionError('Fallo ficticio')
        row=dict(id=case_id,datos=deepcopy(data),version=version+1)
        self.draft_rows[case_id]=row
        return deepcopy(row)
    def quote_events(self,case_id):return [deepcopy(e) for e in self.event_rows if e['caso_id']==case_id]
    def today_ready(self):return True
    def all_quotes(self):return deepcopy(self.quote_rows)
    def today_events(self):return deepcopy(self.event_rows)
    def email_attempts(self):return deepcopy(self.email_rows)
    def maintenance_latest(self,tipo,solo_ok=False):return None
    def connection_check(self):self.owner_only();return True
    def latest_case(self):return max(self.case_rows,key=lambda c:c['created_at']) if self.case_rows else None
    def record_today_contact(self,case_id,quote_id,kind,operation_id,data=None):
        existente=next((e for e in self.event_rows if e.get('operacion_id')==operation_id),None)
        if existente:return deepcopy(existente)
        e=dict(id=str(uuid4()),operacion_id=operation_id,caso_id=case_id,cotizacion_id=quote_id,
            tipo='correo_revisado' if kind=='correo_revisado' else 'seguimiento',datos=dict(data or {},tipo_mensaje=kind),
            created_at=datetime.now(timezone.utc).isoformat(),deshecho_en=None)
        self.event_rows.append(e)
        from servicios.dashboard_cache import invalidar_dashboard
        invalidar_dashboard()
        return deepcopy(e)
    def close_case_today(self,case,sale,operation_id):
        anterior=case['estado'];row=self.update_case(case,dict(estado='Finalizado'))
        e=dict(id=str(uuid4()),caso_id=case['id'],tipo='cierre',datos=dict(estado_anterior=anterior),
            created_at=datetime.now(timezone.utc).isoformat(),deshecho_en=None)
        self.event_rows.append(e)
        return dict(caso=row,evento=e)
    def undo_close_today(self,event_id):
        e=next(e for e in self.event_rows if e['id']==event_id)
        row=self.update_case(self.get_case(e['caso_id']),dict(estado=e['datos']['estado_anterior']))
        e['deshecho_en']='ahora'
        return row


def by_label(elements,label):
    return next(e for e in elements if e.label==label)


def paginas_registradas(app):
    return [p['page_name'] for p in app._registered_pages.values()]


TODAS_PAGINAS=['Inicio',*PAGINAS]


def menu_visible(app):
    return [x.label for x in app.sidebar.get('page_link')]


def paso(app,n):
    app.get('button_group')[0].set_value(n).run()
    return app


def ir_a(app, pagina):
    return app.switch_page(PAGINAS[pagina][0]).run()


class AppTests(unittest.TestCase):
    def setup_app(self,owner=True):
        repo=FakeRepository(owner)
        patcher=patch('servicios.repositorio.Repository',return_value=repo)
        patcher.start()
        self.addCleanup(patcher.stop)
        cookies=patch('utils.sesion_cookie.puente_cookie',return_value=True)
        cookies.start();self.addCleanup(cookies.stop)
        from mente_futuro.domain import SERVICES,TOPICS
        from servicios.formulario_publico import configuracion_visible
        for target,value in [('servicios.formulario.catalogo_publico',dict(servicios=SERVICES,tematicas=TOPICS,version=2,pendiente=False)),('paginas.formulario.configuracion_publica',configuracion_visible({}))]:
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20)
        app.session_state['auth_client']=repo.client
        # AppTest no actualiza su hash al seguir un switch_page del marco.
        # Las recargas reales y la raíz se verifican aparte en test_recarga.py.
        app._page_hash=calc_hash('hoy' if owner else 'nueva-solicitud')
        return app,repo
    def assert_clean(self,app):
        self.assertEqual([e.message for e in app.exception],[])
        self.assertEqual([e.value for e in app.error],[])
    def create_request(self,app):
        ir_a(app,'Nueva solicitud')
        interno=not by_label(app.text_input,'Nombre y apellido').disabled
        if interno:
            by_label(app.text_input,'Empresa o institución').set_value('Fundación Horizonte Norte')
            by_label(app.text_input,'Nombre y apellido').set_value('Valentina Soto')
            by_label(app.text_input,'Correo electrónico').set_value('cliente@example.cl')
            app.run()
            paso(app,3)
        else:
            by_label(app.button,'Siguiente').click().run()
            by_label(app.button,'Siguiente').click().run()
            by_label(app.checkbox,'Autorizo a Mente y Futuro a utilizar mis datos para gestionar esta solicitud y contactarme.').check()
        by_label(app.text_area,'Comentarios y objetivos (opcional)').set_value('Desarrollar habilidades de liderazgo.')
        by_label(app.button,'Guardar y cotizar ahora' if interno else 'Enviar solicitud').click().run()
        app.switch_page(PAGINAS[app.session_state['navigation']][0])

    def test_login_and_empty_validation(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20)
        app.query_params['vista']='acceso';app.run()
        self.assert_clean(app)
        by_label(app.button,'Ingresar a mi espacio').click().run()
        self.assertIn('Ingresa tu correo',app.error[0].value)

    def test_private_status_route_and_backup_card(self):
        app,repo=self.setup_app(True)
        app.run();ir_a(app,'Estado');self.assert_clean(app)
        self.assertEqual(app.session_state['navigation'],'Estado')
        self.assertTrue(any('Conexión a Supabase disponible' in x.value for x in app.success))
        self.assertTrue(any('Aún no hay solicitudes' in x.value for x in app.info))
        self.assertTrue(any('Sin registros de correos' in x.value for x in app.info))
        self.assertTrue(app.get('download_button'))
        ir_a(app,'Casos y cotizaciones');self.assert_clean(app)
        self.assertTrue(app.get('download_button'))

    def test_client_cannot_register_status_route(self):
        app,repo=self.setup_app(False)
        app.query_params['pagina']='Estado';app.session_state['pending_navigation']='Estado'
        app.run();self.assert_clean(app)
        self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
        self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
        self.assertFalse(app.get('download_button'))

    def test_client_navigation_and_own_request(self):
        app,repo=self.setup_app(False)
        app.run()
        self.assert_clean(app)
        self.assertNotIn('Dashboard',menu_visible(app))
        self.create_request(app)
        self.assert_clean(app)
        self.assertEqual(len(repo.case_rows),1)
        self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
        self.assertTrue(any('48 horas' in x.value for x in app.markdown))
        self.assertFalse(app.dataframe)
        self.assertFalse(any(x.label=='Emitir y guardar cotización' for x in app.button))
        self.assertFalse(any(x.label=='Tarifas y servicios' for x in app.tabs))

    def test_failed_write_never_shows_success(self):
        app,repo=self.setup_app(False)
        repo.fail_write=True
        app.run()
        self.create_request(app)
        self.assertEqual(repo.case_rows,[])
        self.assertEqual(len(app.success),0)
        self.assertTrue(app.error)

    def test_client_identity_consent_and_route_guards(self):
        app,repo=self.setup_app(False)
        app.query_params['pagina']='Dashboard'
        app.session_state['navigation']='Casos y cotizaciones'
        app.run()
        self.assert_clean(app)
        self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
        self.assertFalse(app.query_params)
        self.assertTrue(by_label(app.text_input,'Correo electrónico').disabled)
        self.assertTrue(by_label(app.text_input,'Nombre y apellido').disabled)
        self.assertFalse(any(x.label=='Vincular a una cuenta de cliente' for x in app.selectbox))
        by_label(app.button,'Siguiente').click().run()
        by_label(app.button,'Siguiente').click().run()
        by_label(app.button,'Enviar solicitud').click().run()
        self.assertEqual(repo.case_rows,[])
        self.assertTrue(any('autorizar' in e.value for e in app.error))
        for route in ['Casos y cotizaciones','Dashboard','Tarifas','Tarifas y servicios']:
            app.query_params['pagina']=route
            app.session_state['pending_navigation']=route
            app.run()
            self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
            self.assertFalse(app.dataframe)

    def test_client_success_cannot_open_listing_and_new_form_is_empty(self):
        app,repo=self.setup_app(False)
        app.run()
        self.create_request(app)
        self.assertTrue(any('48 horas' in m.value for m in app.markdown))
        self.assertFalse(app.dataframe)
        self.assertEqual(repo.case_rows[0]['contacto'],repo.profile['nombre'])
        self.assertEqual(repo.case_rows[0]['email'],repo.user.email)
        by_label(app.button,'Enviar otra solicitud').click().run()
        self.assert_clean(app)
        by_label(app.button,'Siguiente').click().run()
        by_label(app.button,'Siguiente').click().run()
        self.assertFalse(app.checkbox[0].value)

    def test_private_pages_reject_client_before_loading_data(self):
        from paginas.gestion import cases_page,dashboard_page,tariffs_content,cases_content
        repo=FakeRepository(False)
        for page in [cases_page,dashboard_page,tariffs_content,cases_content]:
            with self.assertRaises(PermissionError): page(repo)

    def test_login_copy_matches_request_only_portal(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20)
        app.query_params['vista']='acceso';app.run()
        content=' '.join(x.value for x in app.markdown)
        self.assertIn('Revisamos tu solicitud',content)
        self.assertIn('Te enviamos una propuesta a tu medida',content)
        self.assertNotIn('Revisa tus solicitudes y cotizaciones',content)

    def test_owner_request_quote_sale_dashboard(self):
        app,repo=self.setup_app()
        app.run()
        self.assert_clean(app)
        self.create_request(app)
        self.assert_clean(app)
        by_label(app.number_input,'Valor base (CLP)').set_value(420000)
        by_label(app.selectbox,'Tratamiento de IVA *').set_value('Exento de IVA')
        by_label(app.button,'Emitir y guardar cotización').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.quote_rows[0]['total_clp'],420000)
        by_label(app.checkbox,'El cliente aceptó esta cotización').check()
        by_label(app.button,'Registrar venta').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.sale_rows[0]['monto_clp'],420000)
        ir_a(app,'Dashboard')
        self.assert_clean(app)
        self.assertEqual(by_label(app.metric,'Ventas del período').value,'$420.000')
        self.assertEqual(by_label(app.metric,'Ventas cerradas').value,'1')

    def test_dashboard_empty_metrics_and_no_sales_message(self):
        app,repo=self.setup_app()
        app.run()
        ir_a(app,'Dashboard')
        self.assert_clean(app)
        self.assertEqual(by_label(app.metric,'Venta promedio').value,'—')
        self.assertEqual(by_label(app.metric,'Solicitudes que se vendieron').value,'—')
        self.assertTrue(any('Aún no hay ventas' in x.value for x in app.markdown))
        self.assertNotIn('Diaria',by_label(app.selectbox,'Agrupar por').options)

    def test_dashboard_filter_callbacks_and_reset(self):
        from servicios.dashboard import rango_rapido
        from datetime import timedelta
        app,repo=self.setup_app()
        app.run()
        ir_a(app,'Dashboard')
        by_label(app.selectbox,'Rango rápido').set_value('Año anterior').run()
        self.assert_clean(app)
        expected=rango_rapido('Año anterior',today())
        self.assertEqual(by_label(app.date_input,'Desde').value,expected[0])
        self.assertEqual(by_label(app.date_input,'Hasta').value,expected[1])
        by_label(app.date_input,'Desde').set_value(expected[0]+timedelta(days=1)).run()
        self.assertEqual(by_label(app.selectbox,'Rango rápido').value,'Personalizado')
        by_label(app.selectbox,'Servicio').set_value('Coaching dúo').run()
        by_label(app.selectbox,'Temática').set_value('Trabajo en equipo').run()
        by_label(app.button,'Limpiar').click().run()
        self.assert_clean(app)
        self.assertEqual(by_label(app.selectbox,'Agrupar por').value,'Mensual')
        self.assertEqual(by_label(app.selectbox,'Servicio').value,'Todos')
        self.assertEqual(by_label(app.selectbox,'Temática').value,'Todas')
        self.assertEqual(by_label(app.selectbox,'Rango rápido').value,'Últimos 6 meses')

    def test_dashboard_minimum_range_and_mobile_expander(self):
        app,repo=self.setup_app()
        app.session_state['dashboard_mobile']=True
        app.run()
        ir_a(app,'Dashboard')
        self.assert_clean(app)
        self.assertTrue(any(e.label=='Filtros' for e in app.expander))
        by_label(app.selectbox,'Agrupar por').set_value('Semanal').run()
        by_label(app.date_input,'Desde').set_value(today()).run()
        self.assert_clean(app)
        self.assertTrue(any('Ampliamos el rango' in x.value for x in app.info))
        self.assertEqual(by_label(app.selectbox,'Rango rápido').value,'Personalizado')

    def test_dashboard_every_group_renders(self):
        from servicios.dashboard import AGRUPACIONES
        app,repo=self.setup_app()
        app.run()
        ir_a(app,'Dashboard')
        for group in AGRUPACIONES:
            by_label(app.selectbox,'Agrupar por').set_value(group).run()
            self.assert_clean(app)

    def test_dashboard_refresh_invalidates_session_cache(self):
        from unittest.mock import Mock
        app,repo=self.setup_app()
        repo.live_snapshot=Mock(wraps=repo.live_snapshot)
        app.run()
        ir_a(app,'Dashboard')
        self.assertEqual(repo.live_snapshot.call_count,2)
        by_label(app.selectbox,'Temática').set_value('Liderazgo').run()
        self.assertEqual(repo.live_snapshot.call_count,2)
        app.session_state['dashboard_revision']=1
        app.run()
        self.assert_clean(app)
        self.assertEqual(repo.live_snapshot.call_count,3)

    def test_dashboard_visual_has_secondary_charts_and_truthful_partition(self):
        app,repo=self.setup_app()
        app.run()
        ir_a(app,'Dashboard')
        self.assert_clean(app)
        self.assertTrue(any(e.label=='Ver más gráficos' for e in app.expander))
        content=' '.join(x.value for x in app.markdown)
        self.assertIn('El reparto de reserva y remuneración aún no está registrado',content)
        self.assertEqual(len(app.metric),6)

    def test_tariff_write(self):
        app,repo=self.setup_app()
        app.run()
        ir_a(app,'Casos y cotizaciones')
        by_label(app.text_input,'Nombre del plan').set_value('Liderazgo para equipos comunitarios')
        by_label(app.number_input,'Valor de referencia (CLP)').set_value(420000)
        by_label(app.button,'Guardar tarifa').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.tariff_rows[0]['monto_clp'],420000)

    def test_logout_clears_session(self):
        app,repo=self.setup_app()
        app.run()
        by_label(app.button,'Cerrar sesión').click().run()
        self.assert_clean(app)
        self.assertNotIn('auth_client',app.session_state)
        self.assertTrue(any(x.label=='Siguiente' for x in app.button))

    def test_product_navigation_identity_and_footer(self):
        for owner,role in [(True,'Administración'),(False,'Cliente')]:
            app,repo=self.setup_app(owner)
            app.run()
            self.assert_clean(app)
            content=' '.join(x.value for x in app.markdown)
            self.assertIn(repo.profile['nombre'],content)
            if owner:
                self.assertIn(role,content)
                self.assertIn('Mente y Futuro · Sistema de gestión',content)
            self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
            self.assertEqual(menu_visible(app),['Hoy','Nueva solicitud','Casos y cotizaciones','Dashboard'] if owner else [])
            self.assertEqual((app.sidebar.button if owner else app.button)[-1 if owner else 0].label,'Cerrar sesión')
            self.assertFalse(app.radio)
            self.assertFalse(any(b.label=='Actualizar información' for b in app.button))
            for info in app._registered_pages.values():
                if info['page_name']!='Inicio':self.assertEqual(info['icon'],PAGINAS[info['page_name']][2])

    def test_case_kpis_count_real_states_and_badges(self):
        from mente_futuro.domain import STATES
        app,repo=self.setup_app()
        app.run()
        self.create_request(app)
        original=deepcopy(repo.case_rows[0])
        repo.case_rows=[dict(original,id=f'ficticio-{i}',numero=i+1,estado=s) for i,s in enumerate(STATES)]
        app.session_state['dashboard_revision']=app.session_state['dashboard_revision']+1
        app.session_state['selected_case']=None
        app.session_state['caso_abierto']=None
        app.run()
        self.assert_clean(app)
        self.assertEqual(by_label(app.metric,'Por revisar').value,'2')
        self.assertEqual(by_label(app.metric,'En desarrollo').value,'2')
        self.assertIn('cotizados',by_label(app.metric,'Por revisar').help)
        self.assertIn('Aceptada',by_label(app.metric,'En desarrollo').help)
        table=next(x.value for x in app.markdown if '<table' in x.value)
        for label in ['Solicitud','Cotizada','Aceptada','En seguimiento','Cerrada','Rechazada']:
            self.assertIn(label,table)
        self.assertEqual([c['estado'] for c in repo.case_rows],STATES)

    def test_technical_failure_is_friendly_and_session_can_exit(self):
        app,repo=self.setup_app()
        repo.live_snapshot=lambda _: (_ for _ in ()).throw(RuntimeError('SELECT secret FROM mf_casos; backend stacktrace'))
        app.run()
        ir_a(app,'Dashboard')
        self.assertFalse(app.exception)
        self.assertTrue(any('Aún no pudimos conectar' in x.value for x in app.info))
        visible=' '.join(x.value for x in app.markdown)+ ' '.join(x.value for x in app.error)
        self.assertNotIn('SELECT secret',visible)
        self.assertTrue(any(x.label=='Cerrar sesión' for x in app.button))

    def test_each_private_page_has_one_shared_header(self):
        app,repo=self.setup_app()
        app.run()
        for page,section in [('Nueva solicitud','SOLICITUDES'),
                             ('Casos y cotizaciones','SEGUIMIENTO'),('Dashboard','DASHBOARD')]:
            ir_a(app,page)
            self.assert_clean(app)
            headers=[x.value for x in app.markdown if '<div class="mfy-hero-copy">' in x.value]
            self.assertEqual(len(headers),1)
            self.assertIn(f'MENTE Y FUTURO · {section}',headers[0])
            self.assertFalse(any('class="banner"' in x.value for x in app.markdown))

    def test_request_sections_keep_one_submission_and_client_identity(self):
        app,repo=self.setup_app(False)
        app.run()
        self.assert_clean(app)
        sections=[x.value for x in app.markdown if '<div class="mfy-section-title">' in x.value]
        self.assertEqual(len(sections),1)
        self.assertEqual(len([b for b in app.button if b.label=='Siguiente']),1)
        self.assertTrue(by_label(app.text_input,'Correo electrónico').disabled)
        self.create_request(app)
        self.assert_clean(app)
        self.assertEqual(len(repo.case_rows),1)
        self.assertTrue(any('48 horas' in m.value for m in app.markdown))

    def test_client_cannot_select_private_native_pages_even_with_admin_route_hash(self):
        admin,_=self.setup_app()
        admin.run()
        private_hashes=[key for key,info in admin._registered_pages.items() if info['page_name']!='Nueva solicitud']
        app,repo=self.setup_app(False)
        app.run()
        for page in ['Casos y cotizaciones','Dashboard']:
            ir_a(app,page)
            self.assert_clean(app)
            self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
            self.assertFalse(app.dataframe)
        for page_hash in private_hashes:
            app._page_hash=page_hash  # Simula un enlace directo de otra cuenta.
            app.run()
            self.assert_clean(app)
            self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
            self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
            self.assertFalse(app.metric)

    def test_role_downgrade_removes_private_pages_before_loading_data(self):
        from unittest.mock import Mock
        app,repo=self.setup_app()
        app.run()
        ir_a(app,'Casos y cotizaciones')
        repo.profile['rol']='cliente'
        repo.is_owner=False
        repo.cases=Mock(side_effect=AssertionError('No debe leer casos'))
        repo.sales=Mock(side_effect=AssertionError('No debe leer ventas'))
        repo.profiles=Mock(side_effect=AssertionError('No debe leer otros perfiles'))
        app.run()
        self.assert_clean(app)
        self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
        self.assertEqual(app.session_state['navigation'],'Nueva solicitud')
        repo.cases.assert_not_called()
        repo.sales.assert_not_called()
        repo.profiles.assert_not_called()

    def test_logout_hides_native_navigation_and_only_dashboard_has_refresh(self):
        app,_=self.setup_app()
        app.run()
        ir_a(app,'Dashboard')
        self.assertEqual(len([b for b in app.button if b.label=='Actualizar']),0)
        ir_a(app,'Nueva solicitud')
        self.assertFalse(any(b.label in ['Actualizar','Actualizar información'] for b in app.button))
        by_label(app.button,'Cerrar sesión').click().run()
        self.assert_clean(app)
        self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
        self.assertFalse(app.sidebar.button)

    def test_failed_profile_check_removes_previous_private_navigation(self):
        app,repo=self.setup_app()
        app.run()
        repo.client.execute=lambda: (_ for _ in ()).throw(ConnectionError('Fallo de perfil ficticio'))
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        self.assertEqual(paginas_registradas(app),TODAS_PAGINAS)
        self.assertNotIn('_repo_actual',app.session_state)
        self.assertFalse(app.sidebar.button)

    def test_autosave_keeps_invalid_field_and_saves_other_field(self):
        app,repo=self.setup_app();app.run();self.create_request(app)
        by_label(app.text_input,'Correo').set_value('incompleto').run()
        self.assertEqual(by_label(app.text_input,'Correo').value,'incompleto')
        self.assertEqual(repo.case_rows[0]['email'],'cliente@example.cl')
        by_label(app.text_input,'Contacto').set_value('Daniela Fuentes').run()
        self.assertEqual(repo.case_rows[0]['contacto'],'Daniela Fuentes')
        self.assertTrue(app.error)
        self.assertEqual(by_label(app.text_input,'Correo').value,'incompleto')

    def test_autosave_retry_undo_and_dashboard(self):
        app,repo=self.setup_app();app.run();self.create_request(app)
        repo.fail_write=True
        by_label(app.text_input,'Lugar').set_value('Antofagasta').run()
        self.assertEqual(by_label(app.text_input,'Lugar').value,'Antofagasta')
        self.assertNotEqual(repo.case_rows[0]['lugar'],'Antofagasta')
        repo.fail_write=False
        app.session_state['borradores_casos'][repo.case_rows[0]['id']]['reintento']=0
        app.run()
        self.assert_clean(app)
        self.assertEqual(repo.case_rows[0]['lugar'],'Antofagasta')
        by_label(app.selectbox,'Estado del caso').set_value('En revisión').run()
        self.assertEqual(repo.case_rows[0]['estado'],'En revisión')
        by_label(app.button,'Deshacer').click().run()
        self.assert_clean(app)
        self.assertEqual(repo.case_rows[0]['estado'],'Solicitud')
        ir_a(app,'Dashboard')
        self.assert_clean(app)
        self.assertEqual(by_label(app.metric,'Nuevas solicitudes').value,'1')

    def test_autosave_does_not_reset_quote_draft(self):
        app,repo=self.setup_app();app.run();self.create_request(app)
        by_label(app.number_input,'Valor base (CLP)').set_value(980000).run()
        by_label(app.text_area,'Condiciones comerciales').set_value('Propuesta ficticia con dos sesiones.').run()
        by_label(app.text_input,'Contacto').set_value('Daniela Fuentes').run()
        self.assert_clean(app)
        self.assertEqual(by_label(app.number_input,'Valor base (CLP)').value,980000)
        self.assertEqual(by_label(app.text_area,'Condiciones comerciales').value,'Propuesta ficticia con dos sesiones.')

    def test_sale_annul_requires_explicit_confirmation(self):
        app,repo=self.setup_app();app.run();self.create_request(app)
        repo.case_rows[0]['estado']='Vendido'
        repo.sale_rows=[dict(id='venta-ficticia',caso_id=repo.case_rows[0]['id'],monto_clp=420000,
            fecha_venta=today().isoformat(),estado_pago='Pendiente',anulada=False,version=1)]
        app.run()
        by_label(app.checkbox,'Venta anulada').check()
        by_label(app.button,'Guardar estado de la venta').click().run()
        self.assertFalse(repo.sale_rows[0]['anulada'])
        self.assertTrue(app.error)
        by_label(app.checkbox,'Confirmo anular esta venta').check()
        by_label(app.button,'Guardar estado de la venta').click().run()
        self.assert_clean(app)
        self.assertTrue(repo.sale_rows[0]['anulada'])

    def test_saved_field_survives_a_new_streamlit_session(self):
        app,repo=self.setup_app();app.run();self.create_request(app)
        by_label(app.text_input,'Contacto').set_value('Daniela Fuentes').run()
        fresh=AppTest.from_file(str(ROOT/'app.py'),default_timeout=20)
        fresh.session_state['auth_client']=repo.client
        fresh.run();ir_a(fresh,'Casos y cotizaciones')
        by_label(fresh.selectbox,'Abrir detalle').set_value(repo.case_rows[0]['id']).run()
        self.assert_clean(fresh)
        self.assertEqual(by_label(fresh.text_input,'Contacto').value,'Daniela Fuentes')

    def test_acceptance_can_be_undone_with_backend_support(self):
        app,repo=self.setup_app();app.run();self.create_request(app)
        by_label(app.number_input,'Valor base (CLP)').set_value(420000)
        by_label(app.selectbox,'Tratamiento de IVA *').set_value('Exento de IVA')
        by_label(app.button,'Emitir y guardar cotización').click().run()
        by_label(app.button,'Registrar venta').click().run()
        self.assert_clean(app)
        self.assertEqual(len(repo.sale_rows),1)
        by_label(app.button,'Deshacer').click().run()
        self.assert_clean(app)
        self.assertFalse(repo.sale_rows)
        self.assertEqual(repo.case_rows[0]['estado'],'Cotizado')
        self.assertEqual(len(repo.quote_rows),1)


if __name__ == '__main__': unittest.main()
