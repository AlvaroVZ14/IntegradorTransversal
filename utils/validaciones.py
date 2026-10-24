"""Validaciones por campo; un error no impide guardar otros datos del caso."""
from datetime import date
import math
import re

from mente_futuro.domain import SERVICES, TOPICS, MODALITIES, STATES


def rut_valido(valor):
    rut = re.sub(r"[.\s-]", "", str(valor)).upper()
    if not re.fullmatch(r"\d{1,8}[0-9K]", rut):
        return False
    cuerpo, digito = rut[:-1], rut[-1]
    suma = sum(int(n) * (2+i%6) for i,n in enumerate(reversed(cuerpo)))
    resto = 11-suma%11
    return digito == ("0" if resto==11 else "K" if resto==10 else str(resto))


def validar_campo(campo, valor):
    if campo=='tematicas':
        if not isinstance(valor,list) or not 1<=len(valor)<=6 or len(set(valor))!=len(valor) or any(v not in TOPICS for v in valor):return 'Selecciona entre 1 y 6 temáticas válidas.'
        return None
    if campo in ("cliente", "contacto") and len(str(valor or "").strip())<2:
        return "Escribe al menos 2 caracteres."
    limites = {"cliente":180,"contacto":160,"email":254,"telefono":40,"lugar":250,"detalle":5000,"cargo":160,"rut":16,"dirigido_a":1000,"referido_por":160}
    if campo in limites and len(str(valor or ""))>limites[campo]:
        return f"Usa como máximo {limites[campo]} caracteres."
    if campo=="email" and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",str(valor or "")):
        return "Revisa el correo: por ejemplo, nombre@correo.cl."
    if campo=="telefono" and valor:
        if not re.fullmatch(r"\+?[\d\s().-]+",str(valor)) or not 8<=len(re.sub(r"\D","",str(valor)))<=15:
            return "Revisa el teléfono: usa entre 8 y 15 dígitos, por ejemplo +56 9 1234 5678."
    if campo=="rut" and valor and not rut_valido(valor):
        return "Revisa el RUT y su dígito verificador."
    if campo=='origen':
        from servicios.solicitud_rapida import ORIGENES
        if valor not in ORIGENES:return 'Selecciona un origen válido.'
    opciones={"servicio":SERVICES,"tematica":TOPICS,"modalidad":MODALITIES,"estado":STATES}
    if campo in opciones and valor not in opciones[campo]:
        return "Selecciona una opción válida."
    if campo in ("participantes","horas"):
        try:
            numero=float(valor)
            valido=math.isfinite(numero) and ((1<=numero<=10000 and numero.is_integer()) if campo=="participantes" else .5<=numero<=1000)
        except (TypeError,ValueError):
            valido=False
        if not valido:
            return "Usa un entero entre 1 y 10.000." if campo=="participantes" else "Usa un número entre 0,5 y 1.000."
    if campo in ("fecha_preferida","fecha_realizacion") and valor:
        try:
            fecha=date.fromisoformat(str(valor))
            if campo=='fecha_realizacion':
                from mente_futuro.domain import today
                if fecha>today():return 'La jornada realizada no puede estar en el futuro.'
        except ValueError:
            return "Selecciona una fecha válida."
    return None
