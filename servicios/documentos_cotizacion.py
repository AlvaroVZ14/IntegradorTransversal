"""Word con docxtpl y PDF nativo, ambos desde el snapshot de la versión emitida."""
from io import BytesIO
from datetime import date
from html import escape

from mente_futuro.domain import code, money,quote_total
from mente_futuro.presentation import LOGO
from servicios.cotizacion_asistida import SECCIONES, EMISOR


def contenido(cotizacion):
    d=cotizacion.get('documento') or {}
    s={**cotizacion['snapshot'],**{k:d[k] for k in ('modalidad','participantes','horas') if k in d}}
    emisor=d.get('emisor',{})
    contacto=[('Cliente',s.get('cliente','')),('Contacto',s.get('contacto','')),('Correo',s.get('email','')),
        ('Teléfono',s.get('telefono','')),('Servicio',s.get('servicio','')),('Temática',s.get('tematica','')),
        ('Modalidad',s.get('modalidad','')),('Participantes',s.get('participantes','')),('Horas',f"{float(s.get('horas',0)):g}".replace('.',',')),
        ('Lugar',s.get('lugar',''))]
    bloques=[('Detalle del servicio',cotizacion['detalle'])]
    for k,label in SECCIONES.items():
        if d.get('mostrar',{}).get(k,True) and d.get('textos',{}).get(k):bloques.append((label,d['textos'][k]))
    descuento=f"{float(cotizacion['descuento_pct']):g}".replace('.',',')+'%'
    motivo=cotizacion.get('descuento_motivo') or d.get('descuento_motivo')
    if motivo:descuento+=' · '+motivo
    base=int(cotizacion['base_clp']); porcentaje=float(cotizacion['descuento_pct'])
    neto=quote_total(base,cotizacion['descuento_pct'],0)
    importes=[('Valor base',money(base)),('Descuento',descuento),('Neto después de descuento',money(neto)),
        ('Impuesto','Exento de IVA' if cotizacion['iva_pct']==0 else 'IVA 19%'),('Total CLP',money(cotizacion['total_clp']))]
    return dict(codigo=code(cotizacion,'COT'),version=str(cotizacion.get('version_cotizacion',1)),
        emision=date.fromisoformat(cotizacion['fecha_emision']).strftime('%d/%m/%Y'),
        vigencia=date.fromisoformat(cotizacion['valida_hasta']).strftime('%d/%m/%Y'),
        emisor=[(label,str(emisor.get(k,''))) for k,label in EMISOR.items() if emisor.get(k)],
        contacto=[(k,str(v or 'Por definir')) for k,v in contacto],bloques=bloques,importes=importes,
        condiciones=cotizacion.get('condiciones',''))


def generar_word(cotizacion):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docxtpl import DocxTemplate
    datos=contenido(cotizacion)
    doc=Document()
    sec=doc.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=sec.bottom_margin=Inches(.65)
    sec.left_margin=sec.right_margin=Inches(.8)
    normal=doc.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(11)
    normal.paragraph_format.space_after=Pt(7)
    for n in (1,2):
        estilo=doc.styles['Heading '+str(n)];estilo.font.name='Arial'
        estilo.font.color.rgb=RGBColor.from_string('3D6FE0');estilo.font.size=Pt(14 if n==1 else 12)
        estilo.paragraph_format.keep_with_next=True
    doc.styles['Title'].font.color.rgb=RGBColor(0,0,0);doc.styles['Title'].font.size=Pt(24)
    # La plantilla base de python-docx trae una regla bajo Title; se elimina.
    for borde in doc.styles['Title'].element.xpath('.//w:pBdr'):borde.getparent().remove(borde)
    doc.add_picture(str(LOGO),width=Inches(1.65))
    doc.add_paragraph('Cotización de servicios',style='Title')
    doc.add_paragraph('{{ codigo }} · Versión {{ version }}')
    doc.add_paragraph('Emisión {{ emision }} · Vigente hasta {{ vigencia }}')
    if datos['emisor']:
        doc.add_heading('Emisor',level=1)
        doc.add_paragraph('{{ emisor_texto }}')
    doc.add_heading('Datos de la propuesta',level=1)
    tabla=doc.add_table(rows=0,cols=2);tabla.style='Light Shading Accent 1'
    contexto={k:datos[k] for k in ('codigo','version','emision','vigencia')}
    contexto['emisor_texto']='\n'.join(f'{k}: {v}' for k,v in datos['emisor'])
    for i,(label,valor) in enumerate(datos['contacto']):
        celdas=tabla.add_row().cells;celdas[0].text=label;celdas[1].text='{{ contacto_'+str(i)+' }}';contexto['contacto_'+str(i)]=valor
    for i,(label,valor) in enumerate(datos['bloques']):
        doc.add_heading(label,level=1);doc.add_paragraph('{{ bloque_'+str(i)+' }}');contexto['bloque_'+str(i)]=valor
    doc.add_heading('Inversión',level=1)
    tabla=doc.add_table(rows=0,cols=2);tabla.style='Light Shading Accent 1'
    for i,(label,valor) in enumerate(datos['importes']):
        celdas=tabla.add_row().cells;celdas[0].text=label;celdas[1].text='{{ importe_'+str(i)+' }}';contexto['importe_'+str(i)]=valor
    doc.add_heading('Condiciones comerciales',level=1)
    doc.add_paragraph('{{ condiciones }}');contexto['condiciones']=datos['condiciones']
    doc.core_properties.title='Cotización de servicios '+datos['codigo'];doc.core_properties.author='Mente y Futuro'
    plantilla=BytesIO();doc.save(plantilla);plantilla.seek(0)
    tpl=DocxTemplate(plantilla);tpl.render(contexto,autoescape=True)
    salida=BytesIO();tpl.save(salida)
    return salida.getvalue()


def generar_pdf(cotizacion):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
    datos=contenido(cotizacion);salida=BytesIO()
    estilos=getSampleStyleSheet()
    estilos['Title'].alignment=0
    estilos.add(ParagraphStyle(name='Mfy',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=8,textColor=colors.HexColor('#0B2545')))
    estilos.add(ParagraphStyle(name='MfyHeading',parent=estilos['Mfy'],fontName='Helvetica-Bold',fontSize=13,spaceBefore=14,keepWithNext=True,textColor=colors.HexColor('#3D6FE0')))
    p=lambda texto:Paragraph(escape(str(texto)).replace('\n','<br/>'),estilos['Mfy'])
    historia=[Image(str(LOGO),width=120,height=66.5,hAlign='LEFT'),Spacer(1,10),Paragraph('Cotización de servicios',estilos['Title']),
        p(f"{datos['codigo']} · Versión {datos['version']}"),p(f"Emisión {datos['emision']} · Vigente hasta {datos['vigencia']}")]
    if datos['emisor']:
        historia.extend([Paragraph('Emisor',estilos['MfyHeading']),p('\n'.join(f'{k}: {v}' for k,v in datos['emisor']))])
    def tabla(filas):
        t=Table([[p(k),p(v)] for k,v in filas],colWidths=[155,342],hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#F6F8FC'),colors.white]),
            ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        return t
    historia.extend([Paragraph('Datos de la propuesta',estilos['MfyHeading']),tabla(datos['contacto'])])
    for label,valor in datos['bloques']:historia.extend([Paragraph(label,estilos['MfyHeading']),p(valor)])
    historia.extend([Paragraph('Inversión',estilos['MfyHeading']),tabla(datos['importes']),
        Paragraph('Condiciones comerciales',estilos['MfyHeading']),p(datos['condiciones'])])
    def pie(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#5B6B82'))
        canvas.drawString(57,28,'Mente y Futuro · '+datos['codigo']);canvas.drawRightString(555,28,str(doc.page))
    SimpleDocTemplate(salida,pagesize=letter,leftMargin=57,rightMargin=57,topMargin=40,bottomMargin=46,
        title='Cotización '+datos['codigo'],author='Mente y Futuro').build(historia,onFirstPage=pie,onLaterPages=pie)
    return salida.getvalue()
