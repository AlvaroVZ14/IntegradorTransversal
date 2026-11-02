"""Captura de texto con pausa breve; recuperación administrativa por usuario/caso."""
from pathlib import Path
import streamlit as st
from streamlit.components.v2 import component
from servicios.cotizacion_asistida import SECCIONES

TEXTOS=['cliente','servicio','detalle_modalidad','jornadas_duracion','item_descripcion','descuento_periodo','nombre_archivo','detalle','condiciones','descuento_motivo',*SECCIONES]


def rutas_texto(datos):
    rutas={f:('textos',f) if f in SECCIONES else (f,) for f in TEXTOS}
    for nombre,campos in [('objetivos_especificos',('texto',)),('momentos',('etiqueta','descripcion'))]:
        for i,item in enumerate(datos.get(nombre,[])):
            for campo in campos:rutas[f'{nombre}_{item["id"]}_{campo}']=(nombre,i,campo)
    return rutas


def valores_texto(datos):
    valores={}
    for campo,ruta in rutas_texto(datos).items():
        valor=datos
        for k in ruta:valor=valor.get(k,'') if isinstance(valor,dict) else valor[k]
        valores[campo]=valor
    return valores


def capturar(repo,caso_id,draft):
    repo.owner_only()
    puente=component('mfy_cotizacion_texto',html="<span aria-hidden='true'></span>",js=Path(__file__).with_suffix('.js').read_text(encoding='utf-8'))
    saved=valores_texto(draft['datos']);rutas=rutas_texto(draft['datos'])
    resultado=puente(data=dict(user=repo.user.id,id=caso_id,fields=list(rutas),saved=saved if not draft['pendiente'] else draft.get('confirmado',{}),ack=draft.get('ack',{}),reset=draft.get('reset_local',{})),
        default={'patch':{}},on_patch_change=lambda:None,key='cottext_'+caso_id,height=0)
    patch=resultado.patch
    if not isinstance(patch,dict) or patch==draft.get('ack'):return
    draft['ack']=dict(patch)
    for campo,valor in patch.items():
        if campo not in rutas or not isinstance(valor,str) or len(valor)>5000:continue
        ruta=rutas[campo];destino=draft['datos']
        for k in ruta[:-1]:destino=destino[k]
        destino[ruta[-1]]=valor;draft['pendiente']=True
        st.session_state[f'cotedit_{caso_id}_{campo}']=valor
