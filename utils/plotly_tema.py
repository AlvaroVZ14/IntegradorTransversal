"""Plantilla común: importes chilenos, conteos enteros y marca Mente y Futuro."""
import plotly.graph_objects as go
import plotly.io as pio

from utils.estilos import AZUL, MORADO, PALETA, SECUNDARIO, TEXTO

TEMA = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color=TEXTO), colorway=PALETA,
    separators=",.", hoverlabel=dict(bgcolor="white", font=dict(family="Inter", color=TEXTO), bordercolor="#E4E9F2"),
    margin=dict(l=12,r=22,t=24,b=40),
    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color=SECUNDARIO), automargin=True),
    yaxis=dict(gridcolor="rgba(91,107,130,.08)", zeroline=False, tickfont=dict(color=SECUNDARIO), automargin=True),
    legend=dict(orientation="h", y=-.18, x=0, font=dict(size=11)),
    transition=dict(duration=0),
    barcornerradius=7,
))
pio.templates["mente_futuro"] = TEMA


def aplicar_tema(fig, reduced_motion=False):
    fig.update_layout(template="mente_futuro", height=320,
                      paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      transition=dict(duration=0))
    return fig


def eje_conteo(fig, eje="x"):
    getattr(fig, f"update_{eje}axes")(tickformat=",d", dtick=1, rangemode="tozero")
    return fig
