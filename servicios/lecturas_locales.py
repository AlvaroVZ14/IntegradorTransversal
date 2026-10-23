"""Respaldo de lectura por sesión para seguir editando durante un fallo temporal."""
from copy import deepcopy
from time import time
import streamlit as st


def leer_con_respaldo(repo,clave,consulta):
    repo.owner_only()
    almacen=st.session_state.setdefault("lecturas_edicion",{})
    llave=f"{repo.user.id}:{clave}"
    anterior=almacen.get(llave)
    if anterior and time()<anterior.get("reintento",0):
        return deepcopy(anterior["datos"]),True
    try:
        datos=consulta()
        almacen[llave]={"datos":deepcopy(datos),"reintento":0}
        return datos,False
    except Exception:
        if anterior is None:raise
        anterior["reintento"]=time()+15
        return deepcopy(anterior["datos"]),True
