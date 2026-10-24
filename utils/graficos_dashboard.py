"""Gráficos de presentación: no consulta datos ni modifica los indicadores."""
from html import escape

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from mente_futuro.domain import money
from utils.estilos import AMARILLO, AZUL, AZUL_CLARO, LAVANDA, MORADO, PALETA
from utils.estilos import ESTADOS_COLORES
from utils.plotly_tema import aplicar_tema, eje_conteo


def ventas_por_periodo(serie, reduced_motion=False):
    if serie.empty or not serie["cantidad"].sum():
        return None
    x = list(range(len(serie)))
    labels = serie.periodo.astype(str).tolist()
    valores = serie.total.astype(float).tolist()
    fig = go.Figure(go.Scatter(x=x,y=valores,name="Ventas",mode="lines+markers",
        line=dict(color=AZUL,width=3,shape="spline",smoothing=.65),marker=dict(size=7,color=AZUL,line=dict(color="white",width=2)),
        fill="tozeroy",fillgradient=dict(type="vertical",colorscale=[[0,"rgba(61,111,224,0)"],[1,"rgba(61,111,224,.25)"]]),
        customdata=[[escape(label),money(value)] for label,value in zip(labels,valores)],
        hovertemplate="%{customdata[0]}<br>Ventas: %{customdata[1]}<extra></extra>"))
    promedio = sum(valores)/len(valores)
    mejor = max(range(len(valores)),key=valores.__getitem__)
    fig.add_trace(go.Scatter(x=x,y=[promedio]*len(x),name="Promedio por período",mode="lines",
        line=dict(color=AMARILLO,width=2,dash="dot"),
        hovertemplate=f"Promedio por período: {money(promedio)}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[mejor],y=[valores[mejor]],name="Mejor período",mode="markers",
        marker=dict(color=AMARILLO,size=16,symbol='star',line=dict(color="#8A6A00",width=1)),
        hovertemplate=f"Mejor período: {escape(labels[mejor])}<br>{money(valores[mejor])}<extra></extra>"))
    fig.add_annotation(x=mejor,y=valores[mejor],text=f"Mejor: {money(valores[mejor])}",showarrow=True,arrowhead=0,
                       ax=0,ay=-30,bgcolor="#FFF6CC",borderpad=5,font=dict(color="#705800",size=11))
    fig.update_xaxes(tickmode="array",tickvals=x,ticktext=labels,nticks=6)
    fig.update_yaxes(tickprefix="$",tickformat=",.0f",rangemode="tozero",range=[0,max(valores)*1.3 or 1])
    return aplicar_tema(fig,reduced_motion)


def solicitudes_vs_ventas(serie, reduced_motion=False):
    if serie.empty or not (serie.solicitudes.sum() or serie.cantidad.sum()):
        return None
    fig = make_subplots(specs=[[{"secondary_y":True}]])
    x = list(range(len(serie)))
    fig.add_trace(go.Bar(x=x,y=serie.solicitudes.tolist(),name="Solicitudes",marker_color=MORADO,
                        text=serie.solicitudes.tolist(),textposition="outside",customdata=serie.periodo.tolist(),
                        hovertemplate="%{customdata}<br>Solicitudes: %{y:d}<extra></extra>"),secondary_y=False)
    fig.add_trace(go.Scatter(x=x,y=serie.cantidad.tolist(),name="Ventas cerradas",mode="lines+markers",line=dict(color=AZUL,width=3),
                            customdata=serie.periodo.tolist(),hovertemplate="%{customdata}<br>Ventas cerradas: %{y:d}<extra></extra>"),secondary_y=True)
    fig.update_xaxes(tickmode="array",tickvals=x,ticktext=serie.periodo.tolist())
    fig.update_yaxes(title_text="Solicitudes",tickformat=",d",dtick=1,rangemode="tozero",secondary_y=False)
    fig.update_yaxes(title_text="Ventas cerradas",tickformat=",d",dtick=1,rangemode="tozero",showgrid=False,secondary_y=True)
    return aplicar_tema(fig,reduced_motion)


def dona(labels, values, centro, *, colores=None, moneda=False, reduced_motion=False):
    if not values or sum(values)<=0:
        return None
    labels = [escape(str(x)) for x in labels]
    valores = list(values)
    hover = "%{label}<br>" + ("%{customdata}" if moneda else "%{value:d} solicitudes") + " · %{percent:.1%}<extra></extra>"
    fig = go.Figure(go.Pie(labels=labels,values=valores,hole=.7,sort=False,
        marker=dict(colors=colores or PALETA,line=dict(color="white",width=3)),
        textinfo="percent",textposition="inside",textfont=dict(size=12,color='#0B2545'),pull=.015,
        customdata=[money(v) if moneda else str(v) for v in valores],hovertemplate=hover))
    total = money(sum(valores)) if moneda else f"{sum(valores):,.0f}".replace(",", ".")
    fig.add_annotation(text=f"<b>{total}</b>",x=.5,y=.55,showarrow=False,font=dict(size=22))
    fig.add_annotation(text=escape(centro),x=.5,y=.43,showarrow=False,font=dict(size=11))
    fig.update_layout(margin=dict(l=8,r=8,t=15,b=55))
    return aplicar_tema(fig,reduced_motion)


def tematicas_dona(topics, reduced_motion=False):
    ordered=topics.sort_values("Solicitudes",ascending=False)
    top=ordered.head(5)
    labels,values=top.tematica.tolist(),top.Solicitudes.astype(int).tolist()
    if len(ordered)>5:
        labels.append("Otras"); values.append(int(ordered.iloc[5:].Solicitudes.sum()))
    return dona(labels,values,"solicitudes",colores=[MORADO,"#B794FF",AZUL,AZUL_CLARO,AMARILLO,LAVANDA],reduced_motion=reduced_motion)


def embudo_estados(states, reduced_motion=False):
    etapas=["Solicitud","Cotizada","Aceptada","En seguimiento","Cerrada"]
    conteos=states.set_index("estado")["Casos"].to_dict() if not states.empty else {}
    valores=[int(conteos.get(e,0)) for e in etapas]
    if not sum(valores):
        return None
    total=sum(valores)
    porcentajes=[f"{v/total:.0%}" for v in valores]
    fig=go.Figure(go.Funnel(y=etapas,x=valores,text=porcentajes,textinfo="value+text",textposition="inside",
        marker=dict(color=[ESTADOS_COLORES[e][0] for e in etapas]),connector=dict(line=dict(color="#E4E9F2")),
        hovertemplate="%{y}<br>%{x:d} casos · %{text} del embudo actual<extra></extra>"))
    return aplicar_tema(fig,reduced_motion)


def barras_horizontales(labels,values,color=MORADO,reduced_motion=False):
    if not values or not sum(values):
        return None
    ordered=sorted(zip(labels,values),key=lambda row:row[1],reverse=True)
    labels,values=zip(*ordered)
    total=sum(values)
    fig=go.Figure(go.Bar(y=[escape(str(x)) for x in labels],x=values,orientation="h",marker_color=color,
        text=[f"{v} · {v/total:.0%}" for v in values],textposition="outside",cliponaxis=False,
        hovertemplate="%{y}<br>%{x:d} solicitudes<extra></extra>"))
    fig.update_yaxes(autorange="reversed",showgrid=False)
    fig.update_xaxes(range=[0,max(values)*1.35],showgrid=True)
    return aplicar_tema(eje_conteo(fig),reduced_motion)


def distribucion(casos,campo):
    counts={}
    for caso in casos:
        label=str(caso.get(campo) or "No informado").strip() or "No informado"
        counts[label]=counts.get(label,0)+1
    return counts


def origenes(casos,reduced_motion=False):
    counts=distribucion(casos,"origen")
    counts.setdefault("Referido por colega",0)
    return barras_horizontales(list(counts),list(counts.values()),reduced_motion=reduced_motion)


def modalidades(casos,reduced_motion=False):
    counts=distribucion(casos,"modalidad")
    for label in ["Presencial","Online","Híbrida"]:
        counts.setdefault(label,0)
    return dona(list(counts),list(counts.values()),"solicitudes",reduced_motion=reduced_motion)


def reparto(ventas,reduced_motion=False):
    # Sin columnas reales no se presupone un reparto comercial.
    if not ventas or not all("reserva_clp" in v and "remuneracion_clp" in v for v in ventas):
        return None
    frame=pd.DataFrame(ventas)[["reserva_clp","remuneracion_clp"]].apply(pd.to_numeric,errors="coerce")
    if frame.isna().any().any() or (frame<0).any().any():
        return None
    return dona(["Reserva","Remuneración"],frame.sum().tolist(),"reparto registrado",colores=[AMARILLO,AZUL],moneda=True,reduced_motion=reduced_motion)


def frase_destacada(data,agrupacion):
    serie=data["series"]
    if data["sales_count"]:
        best=serie.loc[serie.total.idxmax()]
        unidad={"Semanal":"semana","Mensual":"mes","Trimestral":"trimestre","Semestral":"semestre","Anual":"año"}[agrupacion]
        return f"Tu mejor {unidad} fue {best['periodo']} con {money(best['total'])}."
    if not data["topics"].empty:
        best=data["topics"].iloc[0]
        porcentaje=best["Solicitudes"]/data["requests_count"]*100
        return f"Tu temática más pedida es {best['tematica']} ({porcentaje:.0f}% de las solicitudes)."
    return "Cada nueva solicitud será una oportunidad para conocer mejor tu negocio."
