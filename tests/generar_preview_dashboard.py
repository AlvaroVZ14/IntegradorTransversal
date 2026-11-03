"""Genera una vista HTML interactiva con datos ficticios, sin iniciar sesión."""
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from servicios.dashboard_demo import datos_demo
from servicios.dashboard import datos_dashboard,ventas_por_dimension
from mente_futuro.domain import money
from utils.componentes import html_encabezado
from utils.estilos import ESTILOS_BASE
from utils.graficos_dashboard import barras_ventas,embudo_estados,origenes,ventas_por_periodo

desde,hasta=date(2026,11,1),date(2026,11,30)
casos,ventas=datos_demo(desde,hasta)
data=datos_dashboard(casos,ventas,desde,hasta)
ventas_actuales=data['sales'].to_dict('records')
ids=set(data['requests'].id)
figuras=[('Ventas por período',ventas_por_periodo(data['evolution'],True)),
         ('Ventas por temática',barras_ventas(ventas_por_dimension(casos,ventas_actuales,'tematica'),True)),
         ('Ventas por tipo de servicio',barras_ventas(ventas_por_dimension(casos,ventas_actuales,'servicio'),True)),
         ('Embudo de casos por estado',embudo_estados(data['states'],True)),
         ('Origen de las solicitudes',origenes([c for c in casos if c['id'] in ids],True))]
cards=[]
for i,(titulo,fig) in enumerate(figuras):
    fig.update_layout(height=320)
    cards.append(f'<article class="st-key-mfy_chart_preview"><h3>{titulo}</h3>'+fig.to_html(full_html=False,
        include_plotlyjs=True if i==0 else False,config={'displayModeBar':False,'responsive':True})+'</article>')
html='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+ESTILOS_BASE
html+='<body class="stApp"><main class="mfy-preview-shell st-key-mfy_dashboard">'+html_encabezado('Mes: noviembre 2026',desde,hasta)
html+='<p>VISTA DE PRUEBA · Datos completamente ficticios; no se guardan en Supabase.</p>'
valores=[('Total vendido',money(data['total'])),('Venta promedio',money(data['average'])),
         ('Conversión',f"{data['conversion']:.1f}%".replace('.',',')),('Pago pendiente',money(data['pending_payment']))]
html+='<div class="mfy-preview-kpis">'+''.join(f'<article class="st-key-mfy_kpi_preview"><p>{titulo}</p><h2>{valor}</h2></article>' for titulo,valor in valores)+'</div>'
html+='<div class="mfy-preview-grid">'+''.join(cards)+'</div></main></body></html>'
target=Path('output/dashboard-vista-ficticia.html');target.parent.mkdir(exist_ok=True)
target.write_text(html,encoding='utf-8')
print(target)
