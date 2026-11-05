"""Ficha administrativa básica del caso; independiente de la cotización."""
from html import escape
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from mente_futuro.domain import code
from mente_futuro.presentation import LOGO
from servicios.redes_sociales import REDES, redes_del_caso
from ui.estados import color_estado


def generar_ficha_pdf(caso):
    salida=BytesIO()
    azul=colors.HexColor('#0B2545');acento=colors.HexColor('#3D6FE0')
    normal=ParagraphStyle('FichaTexto',fontName='Helvetica',fontSize=10,leading=15,textColor=azul,splitLongWords=1,spaceAfter=5)
    titulo=ParagraphStyle('FichaTitulo',parent=normal,fontName='Helvetica-Bold',fontSize=20,leading=25,spaceAfter=10)
    seccion=ParagraphStyle('FichaSeccion',parent=normal,fontName='Helvetica-Bold',fontSize=13,leading=18,spaceBefore=14,keepWithNext=True)
    def p(valor):return Paragraph(escape(str(valor or 'No informado')).replace('\n','<br/>'),normal)
    def tabla(filas):
        t=Table([[p(k),v if isinstance(v,Paragraph) else p(v)] for k,v in filas],colWidths=[130,355],hAlign='LEFT',splitByRow=1,splitInRow=1)
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#E4E9F2')),
                              ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#F6F8FC')),('LEFTPADDING',(0,0),(-1,-1),9),
                              ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        return t
    fecha=datetime.fromisoformat(caso['created_at'].replace('Z','+00:00'))
    if fecha.tzinfo:fecha=fecha.astimezone(ZoneInfo('America/Santiago'))
    estado=color_estado(caso.get('estado'))
    estilo_estado=ParagraphStyle('FichaEstado',parent=normal,textColor=colors.HexColor(estado['texto']))
    banda=Table([[Paragraph(escape(estado['etiqueta'])+'<br/>'+escape(estado['ayuda']),estilo_estado)]],colWidths=[485])
    banda.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(estado['fondo'])),
        ('LINEBEFORE',(0,0),(0,-1),5,colors.HexColor(estado['solido'])),
        ('BOX',(0,0),(-1,-1),.5,colors.HexColor(estado['borde'])),
        ('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    historia=[Image(str(LOGO),width=170,height=94,kind='proportional',hAlign='LEFT'),Spacer(1,12),
              Paragraph('Ficha del caso '+code(caso),titulo),p('Registrado el '+fecha.strftime('%d/%m/%Y')),
              banda,Spacer(1,8),
              HRFlowable(width='100%',thickness=2,color=acento),Paragraph('Empresa y contacto',seccion),
              tabla([(k,caso.get(v)) for k,v in [('Empresa','cliente'),('Contacto','contacto'),('RUT','rut'),
                    ('Cargo','cargo'),('Correo','email'),('Teléfono','telefono')]]),Paragraph('Servicio solicitado',seccion),
              tabla([(k,caso.get(v)) for k,v in [('Servicio','servicio'),('Temática','tematica'),('Modalidad','modalidad'),
                    ('Participantes','participantes'),('Horas','horas'),('Lugar','lugar'),('Dirigido a','dirigido_a')]]),
              Paragraph('Detalle de la solicitud',seccion),p(caso.get('detalle')),Paragraph('Redes sociales',seccion)]
    redes=redes_del_caso(caso)
    filas=[]
    for campo,valor in redes.items():
        texto=(f'<link href="{escape(valor,quote=True)}" color="#3D6FE0">{escape(valor)}</link>'
               if valor.startswith(('http://','https://')) else escape(valor))
        filas.append((REDES[campo][0],Paragraph(texto,normal)))
    historia.append(tabla(filas) if filas else p('Sin redes registradas'))
    def pie(canvas,documento):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(azul)
        canvas.drawString(55,28,'Mente y Futuro - Ficha del caso');canvas.drawRightString(A4[0]-55,28,str(documento.page));canvas.restoreState()
    SimpleDocTemplate(salida,pagesize=A4,leftMargin=55,rightMargin=55,topMargin=35,bottomMargin=48,
                      title='Ficha '+code(caso),author='Mente y Futuro').build(historia,onFirstPage=pie,onLaterPages=pie)
    return salida.getvalue()
