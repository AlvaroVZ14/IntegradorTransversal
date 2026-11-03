"""Agregaciones y comparaciones del tablero; calendario en servicios/periodos.py."""
import pandas as pd

from mente_futuro.domain import dashboard_data
from utils.estados import etiqueta_estado

# Se reexportan estos nombres para conservar los consumidores de reportes.
from servicios.periodos import (AGRUPACIONES, inicio_periodo, fin_periodo, mover_periodo,
    periodos_del_rango, etiqueta_periodo, periodo_anterior, agrupacion_evolucion)


def rango_anterior(desde, hasta, agrupacion=None):
    return periodo_anterior(desde, hasta)


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
    resultado["fin"] = [fin_periodo(p, agrupacion) for p in periodos]
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
    detalle = agrupacion_evolucion(desde, hasta, agrupacion)
    actual["evolution_grouping"] = detalle
    evolucion = agrupar_por_periodo(actual["sales"], detalle, desde, hasta)
    solicitudes = agrupar_por_periodo(actual["requests"], detalle, desde, hasta)
    evolucion["solicitudes"] = solicitudes["cantidad"].to_numpy()
    actual["evolution"] = evolucion
    actual["previous"] = _calcular(casos, ventas, previo_desde, previo_hasta, agrupacion, servicio, tematica)
    actual["previous_range"] = (previo_desde, previo_hasta)
    actual["variations"] = {k: variacion(actual[k], actual["previous"][k]) for k in
        ("total", "sales_count", "requests_count", "average", "conversion", "pending_payment")}
    return actual


def variacion(actual, anterior):
    if actual is None or anterior is None or anterior == 0:
        return None
    return (actual-anterior) / abs(anterior) * 100


def ventas_por_dimension(casos, ventas, dimension):
    """Atribuye cada venta una sola vez a su caso, conservando el total vendido.

    Recibe ventas ya filtradas por fecha. La temática es la principal del caso;
    repartir por todas sus temáticas duplicaría montos. Incluye casos antiguos
    con venta en el rango y conserva ventas sin referencia bajo Sin información.
    """
    if dimension not in ('tematica', 'servicio'):
        raise ValueError('Selecciona temática o tipo de servicio.')
    indice = {c['id']: c for c in casos}
    totales = {}
    for venta in ventas:
        if venta.get('anulada'):
            continue
        etiqueta = indice.get(venta['caso_id'], {}).get(dimension) or 'Sin información'
        totales[etiqueta] = totales.get(etiqueta, 0) + float(venta['monto_clp'])
    return dict(sorted(totales.items(), key=lambda item: (-item[1], item[0])))
