"""Identidad visual y documentos imprimibles."""
import base64
from html import escape
from pathlib import Path
from .domain import code, money

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo-mente-y-futuro.jpeg"

CSS = """
<style>
h1,h2,h3 {letter-spacing:-.035em;}
h1 {font-size:2.35rem!important; font-weight:800!important; color:#23324d;}
h2 {font-size:1.5rem!important;} h3 {font-size:1.12rem!important;}
.block-container {max-width:1440px; padding-top:2.3rem; padding-bottom:3rem;}
[data-testid="stSidebar"] {background:white; border-right:1px solid #e7ecf7;}
[data-testid="stSidebar"] [data-testid="stImage"] {background:white; padding:8px 0 22px;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:.5rem;}
[data-testid="stSidebar"] [role="radiogroup"] label {border-radius:10px; padding:12px 10px; width:100%;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#edf3ff; color:#3565cb; font-weight:700;}
[data-testid="stMetric"] {background:white; padding:21px 23px; border:1px solid #e6ebf6; border-radius:16px; box-shadow:0 3px 12px #23324d03;}
[data-testid="stMetricLabel"] {color:#69758c; font-size:.8rem;}
[data-testid="stMetricValue"] {font-size:1.8rem; font-weight:800; color:#284573;}
[data-testid="stForm"] {background:white; border-radius:18px; border-color:#e5ebf6; padding:26px;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:16px;}
.stButton button,.stDownloadButton button,.stFormSubmitButton button {border-radius:10px; font-weight:600; min-height:42px;}
.eyebrow {color:#6384c5; font-size:.72rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; margin-bottom:10px;}
.intro {color:#6e7a90; font-size:.98rem; line-height:1.6; margin-top:-6px; margin-bottom:25px;}
.banner {background:linear-gradient(110deg,#e7f0ff 0%,#eff0ff 75%,#f7f0ff 100%); border:1px solid #dce5fb; border-radius:18px; padding:24px 28px; margin:5px 0 22px; position:relative; overflow:hidden;}
.banner:after {content:'';position:absolute;right:-25px;top:-58px;width:180px;height:180px;border:22px solid #ffffff5c;border-radius:50%;pointer-events:none;}
.banner b {font-size:1.1rem; color:#324d84;}.banner p {margin:6px 0 0;color:#647598;font-size:.9rem;}
.pill {display:inline-block;padding:6px 12px;border-radius:7px;background:#f0ebff;color:#7450b7;font-size:.74rem;font-weight:700;}
.note {padding:18px 20px;border-radius:12px;background:#fff9df;border-left:3px solid #ffd328;color:#78672c;font-size:.88rem;line-height:1.55;}
.step {font-weight:700;color:#5179c7;font-size:.8rem;letter-spacing:.06em;margin-bottom:8px;}
.login-intro {padding:32px 16px 20px 0;}.login-intro h1{font-size:3rem!important;line-height:1.13;max-width:560px;}
.login-intro p{color:#76839a;font-size:1.05rem;max-width:510px;line-height:1.8;}
.login-features {display:flex;flex-direction:column;gap:17px;margin-top:30px;color:#465b7c;}
.login-features span {background:#fff; border:1px solid #e1e8f7; border-radius:12px; padding:16px 20px;max-width:490px;}
.login-features b {color:#8b68d4;margin-right:15px;}
.footer {color:#8e99ae;font-size:.75rem; margin-top:25px;}
@media(max-width:800px){.block-container{padding:1.2rem;}h1{font-size:1.9rem!important;}.login-intro h1{font-size:2.2rem!important;}[data-testid="stForm"]{padding:16px;}}
</style>
"""


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
