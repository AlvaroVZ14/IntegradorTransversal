"""Identidad visual y documentos imprimibles."""
import base64
from html import escape
from pathlib import Path
from .domain import code, money

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo-mente-y-futuro.jpeg"
FAVICON = ROOT / "assets" / "favicon-mente-y-futuro.svg"

from utils.estilos import ESTILOS_BASE as CSS


def quote_html(quote):
    snapshot = quote["snapshot"]
    e = lambda value: escape(str(value if value is not None else "Por definir"))
    logo = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    details = "".join(f"<tr><th>{label}</th><td>{e(snapshot.get(key))}</td></tr>" for label,key in [
        ("Cliente / organización","cliente"),("Contacto","contacto"),("Correo","email"),
        ("Servicio","servicio"),("Temática","tematica"),("Participantes","participantes"),
        ("Horas totales","horas"),("Modalidad","modalidad"),("Lugar","lugar"),("Fecha preferida","fecha_preferida"),
    ])
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cotización {e(code(quote,'COT'))} · Mente y Futuro</title><style>
body{{font:15px Arial,sans-serif;color:#23324d;background:#f4f7fc;margin:0;padding:35px}}
main{{max-width:800px;margin:auto;background:white;padding:42px;border-top:6px solid #ffcf00}}
img{{width:230px}}h1{{color:#527fe5}}h2{{font-size:18px;color:#8760c9;margin-top:26px}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #e5eaf3}}
th{{width:34%;color:#66758f;font-weight:normal}}.total{{font-size:25px;color:#527fe5;font-weight:bold}}
.text{{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.6}}.muted{{color:#78849a;font-size:13px}}
@media print{{body{{background:white;padding:0}}main{{padding:15px;border:0}}tr{{break-inside:avoid}}}}
</style></head><body><main><img src="data:image/jpeg;base64,{logo}" alt="Mente y Futuro">
<h1>Cotización de servicios</h1><p><b>{e(code(quote,'COT'))}</b></p>
<p class="muted">Emisión: {e(quote['fecha_emision'])} · Válida hasta: {e(quote['valida_hasta'])}</p>
<h2>Datos de la propuesta</h2><table>{details}</table>
<h2>Detalle del servicio</h2><div class="text">{e(quote['detalle'])}</div>
<h2>Inversión</h2><table><tr><th>Valor base</th><td>{money(quote['base_clp'])}</td></tr>
<tr><th>Descuento</th><td>{e(quote['descuento_pct'])}%</td></tr>
<tr><th>Impuesto</th><td>{'Exento de IVA' if quote['iva_pct']==0 else 'IVA 19%'}</td></tr>
<tr><th>Total (CLP)</th><td class="total">{money(quote['total_clp'])}</td></tr></table>
<h2>Condiciones comerciales</h2><div class="text">{e(quote['condiciones'])}</div>
<p class="muted">Mente y Futuro · Creando canales para el aprendizaje</p></main></body></html>"""
