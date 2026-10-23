"""Períodos y comparaciones del tablero, sin dependencias de Streamlit."""
from datetime import date, timedelta

import pandas as pd

from mente_futuro.domain import dashboard_data
from utils.estados import etiqueta_estado

AGRUPACIONES = ("Semanal", "Mensual", "Trimestral", "Semestral", "Anual")
RANGOS = ("Últimas 8 semanas", "Últimos 6 meses", "Este año", "Año anterior", "Personalizado")
MINIMOS = {"Semanal": 4, "Mensual": 2, "Trimestral": 2, "Semestral": 2, "Anual": 2}
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
MESES_POR_PERIODO = {"Mensual": 1, "Trimestral": 3, "Semestral": 6, "Anual": 12}


def inicio_periodo(fecha, agrupacion):
    if agrupacion not in AGRUPACIONES:
        raise ValueError("Selecciona una agrupación válida.")
    fecha = pd.Timestamp(fecha).date()
    if agrupacion == "Semanal":
        return fecha - timedelta(days=fecha.weekday())
    meses = MESES_POR_PERIODO[agrupacion]
    return date(fecha.year, ((fecha.month - 1) // meses) * meses + 1, 1)


def mover_periodo(fecha, cantidad, agrupacion):
    offset = pd.DateOffset(weeks=cantidad) if agrupacion == "Semanal" else pd.DateOffset(months=cantidad * MESES_POR_PERIODO[agrupacion])
    return (pd.Timestamp(fecha) + offset).date()


def periodos_del_rango(desde, hasta, agrupacion):
    if desde > hasta:
        raise ValueError("La fecha inicial debe ser anterior a la final.")
    periodos = []
    actual, ultimo = inicio_periodo(desde, agrupacion), inicio_periodo(hasta, agrupacion)
    while actual <= ultimo:
        periodos.append(actual)
        actual = mover_periodo(actual, 1, agrupacion)
    return periodos


def etiqueta_periodo(inicio, agrupacion):
    fin = mover_periodo(inicio, 1, agrupacion) - timedelta(days=1)
    if agrupacion == "Semanal":
        if inicio.month == fin.month:
            tramo = f"{inicio.day}–{fin.day} {MESES[fin.month-1]}"
        else:
            tramo = f"{inicio.day} {MESES[inicio.month-1]}–{fin.day} {MESES[fin.month-1]}"
        return f"Sem {inicio.isocalendar().week:02d} · {tramo}"
    if agrupacion == "Mensual":
        return f"{MESES[inicio.month-1]} {inicio.year}"
    if agrupacion == "Trimestral":
        return f"T{(inicio.month-1)//3+1} · {inicio.year}"
    if agrupacion == "Semestral":
        return f"S{(inicio.month-1)//6+1} · {inicio.year}"
    return str(inicio.year)


def rango_rapido(nombre, hoy):
    if nombre == "Últimas 8 semanas":
        return inicio_periodo(hoy, "Semanal") - timedelta(weeks=7), hoy
    if nombre == "Últimos 6 meses":
        return mover_periodo(hoy.replace(day=1), -5, "Mensual"), hoy
    if nombre == "Este año":
        return date(hoy.year, 1, 1), hoy
    if nombre == "Año anterior":
        return date(hoy.year-1, 1, 1), date(hoy.year-1, 12, 31)
    raise ValueError("El rango personalizado requiere fechas propias.")


def ajustar_rango(desde, hasta, agrupacion):
    """Asegura suficientes barras visibles, sin mover el extremo final al futuro."""
    mensajes = []
    if desde > hasta:
        desde, hasta = hasta, desde
        mensajes.append("Ordenamos las fechas para que el inicio sea anterior al término.")
    minimo = MINIMOS[agrupacion]
    if len(periodos_del_rango(desde, hasta, agrupacion)) < minimo:
        desde = mover_periodo(inicio_periodo(hasta, agrupacion), -(minimo-1), agrupacion)
        mensajes.append(f"Ampliamos el rango para mostrar al menos {minimo} períodos en la vista {agrupacion.lower()}.")
    return desde, hasta, " ".join(mensajes)


def rango_anterior(desde, hasta, agrupacion):
    periodos = periodos_del_rango(desde, hasta, agrupacion)
    primero = periodos[0]
    return mover_periodo(primero, -len(periodos), agrupacion), primero - timedelta(days=1)


def agrupar_por_periodo(df, agrupacion, desde=None, hasta=None):
    """Devuelve inicio, fin, periodo, total y cantidad, incluidos los ceros.

    Se pueden pasar los límites o fijarlos en df.attrs['desde'/'hasta'] para
    llamar con solo (df, agrupacion). Para un df vacío los límites son necesarios.
    Ventas: fecha_venta DATE, monto_clp y anulada. Solicitudes: created_at UTC.
    """
    frame = df.copy()
    columna = "fecha_venta" if "fecha_venta" in frame else "created_at" if "created_at" in frame else "fecha"
    if columna not in frame:
        if not frame.empty:
            raise ValueError("Falta una columna de fecha para agrupar.")
        frame[columna] = pd.Series(dtype="datetime64[ns]")
    if columna == "created_at":
        fechas = pd.to_datetime(frame[columna], utc=True, format="mixed").dt.tz_convert("America/Santiago").dt.date
    else:
        fechas = pd.to_datetime(frame[columna], format="mixed").dt.date
    desde = desde or df.attrs.get("desde")
    hasta = hasta or df.attrs.get("hasta")
    if desde is None or hasta is None:
        if frame.empty or fechas.dropna().empty:
            raise ValueError("Indica Desde y Hasta para incluir períodos sin movimientos.")
        desde, hasta = fechas.min(), fechas.max()
    desde, hasta = pd.Timestamp(desde).date(), pd.Timestamp(hasta).date()
    if "anulada" in frame:
        frame = frame[frame["anulada"].eq(False)].copy()
        fechas = fechas.loc[frame.index]
    frame = frame.loc[(fechas >= desde) & (fechas <= hasta)].copy()
    frame["_inicio"] = fechas.loc[frame.index].map(lambda d: inicio_periodo(d, agrupacion))
    frame["_valor"] = pd.to_numeric(frame["monto_clp"]) if "monto_clp" in frame else 0
    sumas = frame.groupby("_inicio").agg(total=("_valor", "sum"), cantidad=("_valor", "size"))
    periodos = periodos_del_rango(desde, hasta, agrupacion)
    resultado = sumas.reindex(periodos, fill_value=0).rename_axis("inicio").reset_index()
    resultado["fin"] = [mover_periodo(p, 1, agrupacion) - timedelta(days=1) for p in periodos]
    resultado["periodo"] = [etiqueta_periodo(p, agrupacion) for p in periodos]
    resultado["cantidad"] = resultado["cantidad"].astype(int)
    return resultado[["inicio", "fin", "periodo", "total", "cantidad"]]


def _calcular(casos, ventas, desde, hasta, agrupacion, servicio, tematica):
    filtrados = casos if tematica == "Todas" else [c for c in casos if c.get("tematica") == tematica]
    data = dashboard_data(filtrados, ventas, desde, hasta, servicio)
    data["average"] = data["average"] if data["sales_count"] else None
    data["conversion"] = data["conversion"] if data["requests_count"] else None
    estados = data["states"].copy()
    estados["estado"] = estados["estado"].map(etiqueta_estado)
    data["states"] = estados.groupby("estado", as_index=False)["Casos"].sum()
    serie = agrupar_por_periodo(data["sales"], agrupacion, desde, hasta)
    solicitudes = agrupar_por_periodo(data["requests"], agrupacion, desde, hasta)
    serie["solicitudes"] = solicitudes["cantidad"].to_numpy()
    data["series"] = serie
    return data


def datos_dashboard(casos, ventas, desde, hasta, agrupacion="Mensual", servicio="Todos", tematica="Todas"):
    actual = _calcular(casos, ventas, desde, hasta, agrupacion, servicio, tematica)
    previo_desde, previo_hasta = rango_anterior(desde, hasta, agrupacion)
    actual["previous"] = _calcular(casos, ventas, previo_desde, previo_hasta, agrupacion, servicio, tematica)
    actual["previous_range"] = (previo_desde, previo_hasta)
    actual["variations"] = {k: variacion(actual[k], actual["previous"][k]) for k in
        ("total", "sales_count", "requests_count", "average", "conversion", "pending_payment")}
    return actual


def variacion(actual, anterior):
    if actual is None or anterior is None or anterior == 0:
        return 0.0 if actual == anterior == 0 else None
    return (actual-anterior) / abs(anterior) * 100
