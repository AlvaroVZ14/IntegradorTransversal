"""Cola de borradores con reintento, validación y control optimista de concurrencia."""
from copy import deepcopy
from datetime import datetime
from time import time
from zoneinfo import ZoneInfo

from utils.validaciones import validar_campo

CAMPOS = ("cliente","contacto","email","telefono","servicio","tematica","estado",
          "participantes","horas","modalidad","lugar","fecha_preferida","detalle","cliente_id","rut","cargo","origen","fecha_realizacion","dirigido_a","referido_por","tematicas")


def preparar(almacen, caso):
    borrador = almacen.setdefault(caso["id"], {"ultimo":deepcopy(caso),"pendientes":{},"errores":{},
        "conflictos":{},"guardado":None,"reintento":0,"intentos":0,"deshacer":None})
    # Actualiza la base sin tocar cambios sin confirmar.
    for campo in CAMPOS:
        if campo not in borrador["pendientes"]:
            borrador["ultimo"][campo]=caso.get(campo)
    borrador["ultimo"]["version"]=caso["version"]
    return borrador


def editar(borrador, campo, valor):
    if campo not in CAMPOS:
        raise ValueError("Campo no editable.")
    if isinstance(valor, str):
        valor=valor.strip()
    if campo in ("fecha_preferida","fecha_realizacion") and valor:
        valor=valor.isoformat() if hasattr(valor,"isoformat") else str(valor)
    base=borrador["pendientes"].get(campo,{}).get("base",borrador["ultimo"].get(campo))
    borrador["pendientes"][campo]={"valor":valor,"base":base}
    error=validar_campo(campo,valor)
    if error:
        borrador["errores"][campo]=error
    else:
        borrador["errores"].pop(campo,None)
    borrador["conflictos"].pop(campo,None)
    borrador["reintento"]=0


def guardar(repo, borrador, *, ahora=None, campos=None, confirmar_anulacion=False):
    repo.owner_only()
    ahora=time() if ahora is None else ahora
    if campos is None and ahora<borrador["reintento"]:
        return False
    cambio=False
    for campo in list(borrador["pendientes"]):
        if campos is not None and campo not in campos:
            continue
        if campo in borrador["errores"] or campo in borrador["conflictos"]:
            continue
        pendiente=borrador["pendientes"][campo]
        if campo=="estado" and pendiente["valor"]=="Cancelado" and not confirmar_anulacion:
            continue
        try:
            actual=repo.get_case(borrador["ultimo"]["id"])
            if actual.get(campo)==pendiente["valor"]:
                actualizado=actual  # Reintento tras perder la respuesta: no duplica la escritura.
            elif actual.get(campo)!=pendiente["base"]:
                borrador["fallo"]=False
                borrador["conflictos"][campo]="Este dato cambió en otra sesión. Conservamos lo que escribiste para que lo revises."
                continue
            else:
                actualizado=repo.update_case(actual,{campo:pendiente["valor"]})
            if campo=="estado" and pendiente["base"]!=pendiente["valor"] and pendiente["valor"]!="Cancelado":
                borrador["deshacer"]={"antes":pendiente["base"],"despues":pendiente["valor"],
                    "version":actualizado["version"],"vence":ahora+10}
            borrador["ultimo"]=deepcopy(actualizado)
            borrador["pendientes"].pop(campo,None)
            borrador["guardado"]=datetime.now(ZoneInfo("America/Santiago")).strftime("%H:%M")
            borrador["fallo"]=False
            borrador["intentos"]=0
            borrador["reintento"]=0
            cambio=True
        except Exception:
            borrador["fallo"]=True
            borrador["intentos"]+=1
            borrador["reintento"]=ahora+min(2**borrador["intentos"],30)
            # La cola y los valores originales permanecen en memoria.
            break
    return cambio


def deshacer(repo, borrador, *, ahora=None):
    repo.owner_only()
    ahora=time() if ahora is None else ahora
    accion=borrador.get("deshacer")
    if not accion or ahora>=accion["vence"]:
        borrador["deshacer"]=None
        raise ValueError("El plazo para deshacer terminó.")
    actual=repo.get_case(borrador["ultimo"]["id"])
    if actual["version"]!=accion["version"] or actual["estado"]!=accion["despues"]:
        borrador["deshacer"]=None
        raise ValueError("El caso cambió después. Conservamos los cambios más recientes.")
    borrador["ultimo"]=repo.update_case(actual,{"estado":accion["antes"]})
    borrador["deshacer"]=None
    borrador["guardado"]=datetime.now(ZoneInfo("America/Santiago")).strftime("%H:%M")
    return borrador["ultimo"]
