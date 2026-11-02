"""Datos de transferencia: secretos solo al iniciar un borrador administrativo.

Los generadores utilizan exclusivamente el snapshot, nunca los secretos actuales.
"""
from collections.abc import Mapping

CAMPOS_PAGO={
    'titular':'Titular',
    'rut':'RUT',
    'banco':'Banco',
    'tipo_cuenta':'Tipo de cuenta',
    'numero_cuenta':'N° de cuenta',
    'correo_titular':'Correo del titular',
    'correo_comprobantes':'Correo para comprobantes',
}
LIMITES_PAGO={k:254 if k.startswith('correo_') else 180 for k in CAMPOS_PAGO}


def normalizar_pago(datos):
    datos=datos if isinstance(datos,Mapping) else {}
    salida={}
    for campo in CAMPOS_PAGO:
        valor=datos.get(campo,'')
        texto=' '.join(str(valor).split()) if isinstance(valor,(str,int)) and not isinstance(valor,bool) else ''
        # No truncar silenciosamente una cuenta ni permitir un bloque desmesurado.
        salida[campo]=texto if len(texto)<=LIMITES_PAGO[campo] else ''
    return salida


def leer_pago_secrets():
    import streamlit as st
    try:return normalizar_pago(st.secrets.get('pago',{}))
    except (FileNotFoundError,KeyError,TypeError,st.errors.StreamlitSecretNotFoundError):
        return normalizar_pago({})


def pago_para_documento(documento):
    if not documento.get('incluir_pago',True):return {}
    pago=normalizar_pago(documento.get('pago'))
    return pago if all(pago.values()) else {}


def filas_pago(pago):
    return [(etiqueta,pago[campo]) for campo,etiqueta in CAMPOS_PAGO.items() if campo!='correo_comprobantes']
