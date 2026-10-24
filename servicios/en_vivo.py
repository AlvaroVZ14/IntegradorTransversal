"""Snapshots por sesión: una RPC por ciclo, con última lectura válida en memoria."""
from copy import deepcopy
from time import time
from uuid import uuid4
from contextlib import nullcontext
import streamlit as st

INTERVALOS = {'dashboard': 60, 'hoy': 30, 'casos': 60}


@st.cache_data(ttl=60, show_spinner=False, max_entries=128)
def _consultar(ambito, vista, revision, ciclo, _repo):
    return _repo.live_snapshot(vista), time()


def estado(vista):
    return st.session_state.get('en_vivo', {}).get(vista, {})


def carga_inicial(vista, mensaje):
    from utils.componentes import cargando_datos
    return nullcontext() if estado(vista).get('intentado') else cargando_datos(mensaje)


def _compatibilidad(repo, vista):
    """Solo primera carga sin migración. Nunca repetir estas lecturas en el timer."""
    datos = {'casos': repo.cases()}
    if vista in ('dashboard', 'hoy'):
        datos['ventas'] = repo.sales()
    if vista == 'hoy':
        datos.update(cotizaciones=repo.all_quotes(), eventos=repo.today_events(),
                     envios=repo.email_attempts(), configuracion=repo.quote_settings()['datos'])
    return datos


def cargar(repo, vista):
    repo.owner_only()
    intervalo = INTERVALOS[vista]
    ambito = st.session_state.setdefault('en_vivo_scope', str(uuid4()))
    estados = st.session_state.setdefault('en_vivo', {})
    anterior = estados.get(vista, {})
    revision = st.session_state.get('dashboard_revision', 0)
    ciclo = int(time() // intervalo)
    # Los fallos tampoco provocan varias llamadas al mover filtros en el mismo ciclo.
    if anterior.get('intento') == (revision, ciclo):
        return deepcopy(anterior)
    nuevo = dict(anterior, intentado=True, intento=(revision, ciclo))
    try:
        datos, fecha = _consultar(ambito, vista, revision, ciclo, repo)
        tablas = ['casos'] + (['ventas'] if vista != 'casos' else [])
        if vista == 'hoy':tablas += ['cotizaciones', 'eventos', 'envios']
        if (not isinstance(datos, dict) or any(not isinstance(datos.get(t), list) for t in tablas)
                or (vista == 'hoy' and not isinstance(datos.get('configuracion'), dict))):
            raise ValueError('Snapshot incompleto')
        nuevo.update(datos=datos, fecha=fecha, conectado=True, falta_sql=False)
    except PermissionError:
        raise
    except Exception as error:
        if getattr(error, 'code', '') in ('42501', 'PGRST301', 'PGRST302', 'PGRST303'):
            raise
        falta_sql = getattr(error, 'code', '') == 'PGRST202'
        if falta_sql and not anterior.get('compatibilidad_intentada'):
            nuevo['compatibilidad_intentada'] = True
            try:
                nuevo.update(datos=_compatibilidad(repo, vista), fecha=time())
            except Exception:
                pass
        nuevo.update(conectado=False, falta_sql=falta_sql)
    estados[vista] = nuevo
    return deepcopy(nuevo)
