"""Genera una vista HTML interactiva con datos ficticios, sin iniciar sesión."""
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from datos_dashboard_ficticios import datos_ficticios
from servicios.dashboard import datos_dashboard
from utils.componentes import html_encabezado
from utils.estilos import ESTILOS_BASE, AZUL
from utils.graficos_dashboard import (barras_horizontales,distribucion,embudo_estados,modalidades,origenes,
                                     reparto,solicitudes_vs_ventas,tematicas_dona,ventas_por_periodo)

casos,ventas=datos_ficticios()
data=datos_dashboard(casos,ventas,date(2026,5,1),date(2026,10,21))
tipos=distribucion(casos,'servicio')
figuras=[('Ventas por período',ventas_por_periodo(data['series'])),
         ('Solicitudes vs ventas',solicitudes_vs_ventas(data['series'])),
         ('Temáticas más solicitadas',tematicas_dona(data['topics'])),
         ('Embudo por estado del caso',embudo_estados(data['states'])),
         ('Origen de las solicitudes',origenes(casos)),('Modalidad',modalidades(casos)),
         ('Reserva vs remuneración · solo ejemplo ficticio',reparto(ventas)),
         ('Tipo de servicio',barras_horizontales(list(tipos),list(tipos.values()),AZUL))]
cards=[]
for i,(titulo,fig) in enumerate(figuras):
    cards.append(f'<article class="st-key-mfy_chart_preview"><h3>{titulo}</h3>'+fig.to_html(full_html=False,
        include_plotlyjs=True if i==0 else False,config={'displayModeBar':False,'responsive':True})+'</article>')
html='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+ESTILOS_BASE
html+='<body class="stApp"><main class="mfy-preview-shell">'+html_encabezado('Mensual',date(2026,5,1),date(2026,10,21))
html+='<p>VISTA DE PRUEBA · Datos completamente ficticios. El reparto ilustrado no es una regla del negocio.</p>'
html+='<div class="mfy-preview-grid">'+''.join(cards)+'</div></main></body></html>'
target=Path('output/dashboard-vista-ficticia.html');target.parent.mkdir(exist_ok=True)
target.write_text(html,encoding='utf-8')
print(target)
