"""Diagnóstico privado: no es un endpoint público para el monitor HTTP."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import streamlit as st
from servicios.respaldos import zip_csv
from utils.componentes import encabezado_pagina
from utils.permisos import require_admin
from mente_futuro.domain import code


def fecha_chile(value):
    if not value:return 'Sin registro'
    return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(ZoneInfo('America/Santiago')).strftime('%d/%m/%Y %H:%M')


def datos_respaldo(repo):
    require_admin(repo)
    # Callable diferido: solo genera al descargar. Revalida Auth y rol en el
    # servidor; no retiene ZIP ni datos de otro usuario en st.cache_data.
    try:
        user=repo.client.auth.get_user().user
        profiles=repo.client.table('mf_perfiles').select('rol').eq('id',user.id).execute().data
        if user.id!=repo.user.id or not profiles or profiles[0]['rol']!='admin':
            raise PermissionError()
        return zip_csv(repo.backup_snapshot())
    except Exception:
        raise RuntimeError('No pudimos preparar el respaldo. Revisa /estado y vuelve a intentar; no se descargó una copia parcial.') from None


def tarjeta_respaldo(repo):
    require_admin(repo)
    with st.container(key='mfy_form_respaldo'):
        st.subheader('Respaldo de tu información')
        try:
            ultimo=repo.maintenance_latest('respaldo',True)
            intento=repo.maintenance_latest('respaldo')
        except Exception:
            st.info('Respaldo pendiente de activar: aplica 202610220005_mantenimiento.sql y configura GitHub Actions.')
            return
        st.caption('Último respaldo automático confirmado: '+fecha_chile((ultimo or {}).get('created_at')))
        if intento and intento['estado']=='error':st.warning('El último intento automático falló. Revisa la issue de mantenimiento en GitHub.')
        if ultimo and (datetime.now(timezone.utc)-datetime.fromisoformat(ultimo['created_at'].replace('Z','+00:00'))).total_seconds()>9*86400:
            st.warning('El respaldo automático tiene más de 9 días. Revisa los workflows de GitHub.')
        st.download_button('Descargar respaldo completo (ZIP de CSV)',data=lambda:datos_respaldo(repo),
            file_name='mente-y-futuro-'+datetime.now(ZoneInfo('America/Santiago')).strftime('%Y%m%d-%H%M')+'.zip',
            mime='application/zip',on_click='ignore',width='stretch',icon=':material/download:')
        st.caption('Incluye todos los datos comerciales. No incluye cuentas Auth ni archivos Storage. El ZIP manual no está cifrado: guárdalo en un lugar privado.')
        st.page_link('paginas/estado.py',label='Ver estado del sistema',icon=':material/monitor_heart:')


def page(repo):
    require_admin(repo)
    encabezado_pagina('Estado del sistema','Comprobaciones privadas de mantenimiento.','ADMINISTRACIÓN','◉')
    st.button('Comprobar de nuevo',icon=':material/refresh:')
    try:
        repo.connection_check()
        st.success('Conexión a Supabase disponible con tu sesión.')
    except Exception:
        st.error('No pudimos conectar con Supabase. Revisa si el proyecto está pausado o hay una incidencia.');return
    tarjeta_respaldo(repo)
    try:
        ultimo=repo.latest_case()
        if ultimo:st.info(f"Último caso recibido: {code(ultimo)} · {fecha_chile(ultimo['created_at'])}")
        else:st.info('Aún no hay solicitudes registradas.')
    except Exception:st.warning('No pudimos comprobar el último caso recibido.')
    try:
        intentos=[e for e in repo.email_attempts() if e.get('canal')=='correo']
        if not intentos:st.info('Sin registros de correos de aviso o cotizaciones. Esto no confirma que SMTP esté configurado.')
        else:
            totales={s:sum(e.get('estado')==s for e in intentos) for s in ['enviado','preparado','incierto','error']}
            st.write('Correos registrados: '+ ' · '.join(f'{s}: {n}' for s,n in totales.items()))
            st.caption('Enviado indica aceptación por SMTP, no entrega al destinatario. Los avisos que no se registran en esta tabla no se pueden verificar aquí.')
        monitor=repo.maintenance_latest('monitor')
        if monitor:st.caption('Última revisión automática: '+fecha_chile(monitor['created_at'])+' · '+monitor['estado'])
        else:st.caption('Monitoreo automático: sin ejecución registrada.')
    except Exception:st.warning('No pudimos leer los registros de correos o mantenimiento.')


if __name__=='__main__':page(st.session_state._repo_actual)
