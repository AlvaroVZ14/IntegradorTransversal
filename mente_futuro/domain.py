"""Reglas de negocio independientes de la interfaz y de Supabase."""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from zoneinfo import ZoneInfo

import pandas as pd

SERVICES = ["Coaching individual", "Coaching dúo", "Taller de trabajo en equipo", "Charla de liderazgo", "Otro servicio"]
TOPICS = ["Liderazgo", "Trabajo en equipo", "Comunicación efectiva", "Desarrollo personal", "Gestión emocional", "Otro"]
STATES = ["Solicitud", "En revisión", "Cotizado", "Vendido", "En ejecución", "Finalizado", "Cancelado"]
MODALITIES = ["Presencial", "Online", "Por definir"]
PAYMENTS = ["Pendiente", "Abono recibido", "Pagado"]


def today():
    return datetime.now(ZoneInfo("America/Santiago")).date()


def money(value):
    return "$" + f"{Decimal(str(value or 0)):,.0f}".replace(",", ".")


def code(row, prefix="MF"):
    year = str(row.get("created_at", today().isoformat()))[:4]
    return f"{prefix}-{year}-{int(row['numero']):04d}"


def quote_total(base, discount=0, tax=0):
    base, discount, tax = map(lambda x: Decimal(str(x)), (base, discount, tax))
    if not all(v.is_finite() for v in (base, discount, tax)):
        raise ValueError("Los montos deben ser números finitos.")
    if base < 0 or not 0 <= discount <= 100 or tax not in (0, 19):
        raise ValueError("Revisa el monto, descuento e impuesto.")
    # PostgreSQL almacena descuento_pct como numeric(5,2).
    discount = discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    net = base * (1 - discount / 100)
    return int((net * (1 + tax / 100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def validate_request(data):
    errors = []
    for field, label in [("cliente", "nombre o empresa"), ("contacto", "nombre de contacto")]:
        if len(data.get(field, "").strip()) < 2:
            errors.append(f"Ingresa un {label} de al menos 2 caracteres.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data.get("email", "")):
        errors.append("Ingresa un correo electrónico válido.")
    if data.get("servicio") not in SERVICES or data.get("tematica") not in TOPICS:
        errors.append("Selecciona un servicio y una temática válidos.")
    if not 1 <= data.get("participantes", 0) <= 10000:
        errors.append("Los participantes deben estar entre 1 y 10.000.")
    if not 0.5 <= data.get("horas", 0) <= 1000:
        errors.append("La duración debe estar entre 0,5 y 1.000 horas.")
    if data.get("modalidad") not in MODALITIES:
        errors.append("Selecciona una modalidad válida.")
    preferred = data.get("fecha_preferida")
    if preferred and date.fromisoformat(str(preferred)) < today():
        errors.append("La fecha preferida no puede estar en el pasado.")
    return errors


def dashboard_data(cases, sales, start, end, service="Todos"):
    """Ventas por fecha de cierre; demanda por fecha de solicitud, en hora de Chile."""
    case_columns = ["id", "created_at", "servicio", "tematica", "estado", "participantes", "horas", "cliente", "numero"]
    sale_columns = ["caso_id", "fecha_venta", "monto_clp", "anulada", "estado_pago"]
    all_cases = pd.DataFrame(cases).reindex(columns=case_columns)
    all_sales = pd.DataFrame(sales).reindex(columns=sale_columns)
    if service != "Todos":
        all_cases = all_cases[all_cases.servicio == service]
    created = pd.to_datetime(all_cases.created_at, utc=True).dt.tz_convert("America/Santiago").dt.date
    requests = all_cases[(created >= start) & (created <= end)].copy()
    dates = pd.to_datetime(all_sales.fecha_venta).dt.date
    sold = all_sales[(dates >= start) & (dates <= end) & all_sales.anulada.eq(False)].copy()
    sold = sold[sold.caso_id.isin(all_cases.id)]
    sold["monto_clp"] = pd.to_numeric(sold.monto_clp)
    months = pd.period_range(start, end, freq="M").astype(str)
    sold["Mes"] = pd.to_datetime(sold.fecha_venta).dt.to_period("M").astype(str)
    monthly = sold.groupby("Mes").monto_clp.sum().reindex(months, fill_value=0).rename_axis("Mes").reset_index()
    topics = requests.groupby("tematica").size().reset_index(name="Solicitudes").sort_values("Solicitudes", ascending=False)
    states = requests.groupby("estado").size().reset_index(name="Casos")
    # Conversión de la cohorte: solicitudes del período vendidas hasta su fecha de cierre.
    converted = all_sales[all_sales.anulada.eq(False) & (dates <= end)].caso_id
    count = len(requests)
    return {
        "total": int(sold.monto_clp.sum()), "sales_count": len(sold), "requests_count": count,
        "average": int(sold.monto_clp.mean()) if len(sold) else 0,
        "conversion": 100 * requests.id.isin(converted).sum() / count if count else 0,
        "pending_payment": int(sold[sold.estado_pago != "Pagado"].monto_clp.sum()),
        "monthly": monthly, "topics": topics, "states": states, "requests": requests,
        "sales": sold,
    }


def csv_bytes(frame):
    """Neutraliza fórmulas cuando un texto de cliente se abre en Excel."""
    frame = frame.copy()
    for col in frame.columns:
        frame[col] = frame[col].map(
            lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
        )
    return frame.to_csv(index=False, sep=";").encode("utf-8-sig")
