"""Documento v2 inspirado en la referencia: PDF A4 y Word editable, sin servicios externos."""
from io import BytesIO
from html import escape
from mente_futuro.presentation import LOGO
from servicios.propuesta_documento import modelo

AZUL='#203864'
CALIDO='#DFA77B'
BORDE='#808080'


def filas_valores(m):
    filas=[['Ítem','Descripción','Valor (CLP)'],['1',m['item'],m['base']]]
    if m['incluye']:filas.append(['2','Valor total incluye: '+m['incluye'],''])
    if m['descuento']:
        filas.append([f"{m['descuento']:g}%",' '.join(x for x in (m['motivo'],m['periodo']) if x),''])
    if not m['exento']:filas.extend([['','Neto',m['neto']],['','IVA 19%',m['iva']]])
    filas.append(['','TOTAL — Exento de IVA' if m['exento'] else 'TOTAL',m['total']])
    return filas


def generar_pdf(q):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak,HRFlowable
    m=modelo(q);salida=BytesIO();ancho,alto=A4;margen=53;util=ancho-2*margen-12
    normal=ParagraphStyle('Cuerpo',fontName='Helvetica',fontSize=9.5,leading=13,spaceAfter=6,alignment=TA_JUSTIFY)
    estilos={
        'body':normal,
        'small':ParagraphStyle('Pequeño',parent=normal,fontSize=8,leading=10),
        'title':ParagraphStyle('Titulo',fontName='Times-Bold',fontSize=14,leading=18,textColor=colors.HexColor(AZUL),alignment=TA_CENTER,spaceAfter=14),
        'heading':ParagraphStyle('Seccion',fontName='Times-Bold',fontSize=12,leading=16,textColor=colors.HexColor(AZUL),spaceBefore=12,spaceAfter=3,keepWithNext=True),
        'sub':ParagraphStyle('Subtitulo',parent=normal,fontName='Helvetica-Bold',spaceBefore=9,spaceAfter=8,keepWithNext=True),
        'bullet':ParagraphStyle('Vineta',parent=normal,leftIndent=12,firstLineIndent=0,bulletIndent=0),
        'right':ParagraphStyle('Monto',parent=normal,alignment=TA_RIGHT),
        'total':ParagraphStyle('Total',parent=normal,fontName='Times-Bold',alignment=TA_RIGHT),
        'white':ParagraphStyle('Cabecera',parent=normal,fontName='Times-Bold',fontSize=9,textColor=colors.white,alignment=0),
    }
    def p(texto,style='body'):return Paragraph(escape(str(texto)).replace('\n','<br/>'),estilos[style])
    def bullet(texto,etiqueta=''):
        txt=(f'<b>{escape(etiqueta.rstrip(":"))}:</b> ' if etiqueta.strip() else '')+escape(str(texto)).replace('\n','<br/>')
        return Paragraph(txt,estilos['bullet'],bulletText='•')
    historia=[Image(str(LOGO),width=77,height=43,kind='proportional',hAlign='LEFT'),Spacer(1,5),
              HRFlowable(width='100%',thickness=.4,color=colors.HexColor('#BFBFBF')),Spacer(1,12),p('COTIZACIÓN DE SERVICIOS','title')]
    for etiqueta,valor in [('Fecha',m['fecha']),('Cliente',m['cliente']),('Servicio',m['servicio'])]:
        historia.append(Paragraph(f'<b>{etiqueta}:</b> '+escape(str(valor)),normal))
    primera=any(k in ('objetivos','metodologia') for k,_,_ in m['secciones']);separado=False
    for clave,numero,titulo in m['secciones']:
        if clave=='detalle' and primera and not separado:historia.append(PageBreak());separado=True
        historia.extend([p(f'{numero}. {titulo}','heading'),HRFlowable(width='100%',thickness=.7,color=colors.HexColor(CALIDO),spaceAfter=9)])
        if clave=='objetivos':
            historia.append(p('Objetivo general','sub'))
            if m['objetivo_general']:historia.append(p(m['objetivo_general']))
            historia.append(p('Objetivos específicos','sub'))
            historia.extend(bullet(x) for x in m['especificos'])
        elif clave=='metodologia':
            if m['introduccion']:historia.append(p(m['introduccion']))
            historia.extend(bullet(x.get('descripcion',''),x.get('etiqueta','')) for x in m['momentos'])
        elif clave=='detalle':
            if m['descripcion']:historia.append(p(m['descripcion']))
            filas=[[p(k,'sub'),p(v)] for k,v in [('Modalidad',m['modalidad']),('Participantes',m['participantes']),('Dirigido a',m['dirigido_a'])]]
            tabla=Table(filas,colWidths=[util*.4,util*.6],hAlign='LEFT',splitInRow=1)
            tabla.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.HexColor(BORDE)),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#F2F2F2')),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));historia.append(tabla)
        elif clave=='valor':
            filas=filas_valores(m)
            celdas=[[p(v,'white' if i==0 else 'right' if j==2 else 'body') for j,v in enumerate(f)] for i,f in enumerate(filas)]
            celdas[-1][0]=p(filas[-1][1],'total');celdas[-1][2]=p(filas[-1][2],'total')
            tabla=Table(celdas,colWidths=[util*.12,util*.58,util*.30],repeatRows=1,hAlign='LEFT',splitInRow=1)
            tabla.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.HexColor(BORDE)),('BACKGROUND',(0,0),(-1,0),colors.HexColor(AZUL)),
                ('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#F2F2F2')),('SPAN',(0,-1),(1,-1)),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            # En la fila final el título ocupa las dos primeras columnas.
            historia.append(tabla)
        else:historia.extend(bullet(x) for x in m['condiciones'])
    def marco(canvas,doc):
        canvas.setStrokeColor(colors.HexColor(BORDE));canvas.setLineWidth(.5);canvas.rect(24,24,ancho-48,alto-48)
        canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(margen,33,m['folio']+f" · Versión {m['version']}")
        canvas.drawRightString(ancho-margen,33,f'Página {doc.page}')
    SimpleDocTemplate(salida,pagesize=A4,leftMargin=margen,rightMargin=margen,topMargin=49,bottomMargin=55,
        title='Cotización '+m['folio'],author='Mente y Futuro').build(historia,onFirstPage=marco,onLaterPages=marco)
    return salida.getvalue()


def generar_word(q):
    from docx import Document
    from docx.shared import Pt,Mm,RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    m=modelo(q);doc=Document();s=doc.sections[0]
    s.page_width=Mm(210);s.page_height=Mm(297);s.top_margin=Mm(17);s.bottom_margin=Mm(20);s.left_margin=s.right_margin=Mm(18.7)
    normal=doc.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(9.5)
    normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.1
    for name,size in [('Title',14),('Heading 1',12)]:
        st=doc.styles[name];st.font.name='Times New Roman';st.font.size=Pt(size);st.font.bold=True;st.font.color.rgb=RGBColor.from_string(AZUL[1:]);st.paragraph_format.keep_with_next=True
    bordes=OxmlElement('w:pgBorders');bordes.set(qn('w:offsetFrom'),'page')
    for lado in ('top','left','bottom','right'):
        e=OxmlElement('w:'+lado)
        for k,v in {'val':'single','sz':'4','space':'24','color':'808080'}.items():e.set(qn('w:'+k),v)
        bordes.append(e)
    s._sectPr.append(bordes)
    def linea(parrafo,color):
        b=OxmlElement('w:pBdr');e=OxmlElement('w:bottom')
        for k,v in {'val':'single','sz':'4','color':color,'space':'4'}.items():e.set(qn('w:'+k),v)
        b.append(e);parrafo._p.get_or_add_pPr().append(b)
    pic=doc.add_paragraph();pic.add_run().add_picture(str(LOGO),width=Mm(27));linea(pic,'BFBFBF')
    titulo=doc.add_paragraph('COTIZACIÓN DE SERVICIOS','Title');titulo.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for etiqueta,valor in [('Fecha',m['fecha']),('Cliente',m['cliente']),('Servicio',m['servicio'])]:
        p=doc.add_paragraph();p.add_run(etiqueta+': ').bold=True;p.add_run(str(valor))
    def parrafo(texto,bold=False,bullet=False,etiqueta=''):
        p=doc.add_paragraph(style='List Bullet' if bullet else None)
        p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        if etiqueta:p.add_run(etiqueta.rstrip(':')+': ').bold=True
        p.add_run(texto).bold=bold
        return p
    def tabla(filas,anchos,cabecera=False):
        t=doc.add_table(rows=0,cols=len(anchos));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
        for col,w in zip(t.columns,anchos):col.width=Mm(w)
        for i,fila in enumerate(filas):
            row=t.add_row()
            for j,valor in enumerate(fila):
                c=row.cells[j];c.width=Mm(anchos[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;c.text=str(valor)
                tcPr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
                for lado in ('top','left','bottom','right'):
                    e=OxmlElement('w:'+lado)
                    for k,v in {'val':'single','sz':'4','color':'808080'}.items():e.set(qn('w:'+k),v)
                    b.append(e)
                tcPr.append(b)
                if i==0 and cabecera or j==0 and not cabecera or i==len(filas)-1 and cabecera:
                    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),AZUL[1:] if i==0 and cabecera else 'F2F2F2');tcPr.append(sh)
                for p in c.paragraphs:
                    p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(4)
                    if j==len(fila)-1 and cabecera:p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
                    for run in p.runs:
                        if i==0 and cabecera:run.font.bold=True;run.font.color.rgb=RGBColor(255,255,255)
            if i==0 and cabecera:
                repeat=OxmlElement('w:tblHeader');row._tr.get_or_add_trPr().append(repeat)
        if cabecera:
            t.rows[-1].cells[0].merge(t.rows[-1].cells[1]).text=filas[-1][1]
        doc.add_paragraph().paragraph_format.space_after=Pt(0)
    primera=any(k in ('objetivos','metodologia') for k,_,_ in m['secciones'])
    for clave,n,titulo in m['secciones']:
        if clave=='detalle' and primera:doc.add_page_break()
        h=doc.add_paragraph(f'{n}. {titulo}','Heading 1');linea(h,CALIDO[1:])
        if clave=='objetivos':
            parrafo('Objetivo general',True);parrafo(m['objetivo_general'])
            parrafo('Objetivos específicos',True)
            for x in m['especificos']:parrafo(x,bullet=True)
        elif clave=='metodologia':
            parrafo(m['introduccion'])
            for x in m['momentos']:parrafo(x.get('descripcion',''),bullet=True,etiqueta=x.get('etiqueta',''))
        elif clave=='detalle':
            if m['descripcion']:parrafo(m['descripcion'])
            tabla([['Modalidad',m['modalidad']],['Participantes',m['participantes']],['Dirigido a',m['dirigido_a']]],[69,103])
        elif clave=='valor':tabla(filas_valores(m),[20,100,52],True)
        else:
            for x in m['condiciones']:parrafo(x,bullet=True)
    footer=s.footer.paragraphs[0];footer.add_run(m['folio']+f" · Versión {m['version']} · Página ").font.size=Pt(8)
    campo=OxmlElement('w:fldSimple');campo.set(qn('w:instr'),'PAGE');footer._p.append(campo)
    doc.core_properties.title='Cotización '+m['folio'];doc.core_properties.author='Mente y Futuro'
    salida=BytesIO();doc.save(salida);return salida.getvalue()
