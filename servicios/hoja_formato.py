"""Preparación repetible del libro. No lee secretos ni modifica Resumen existente."""
from servicios.hoja_columnas import COLUMNAS,CLAVES,FECHAS,MONEDAS,leyenda
from ui.estados import CATALOGO

MARCA='MFY_HOJA_38_V1'

def letra(numero):
    texto=''
    while numero:
        numero,resto=divmod(numero-1,26);texto=chr(65+resto)+texto
    return texto

def rgb(hexadecimal):
    return {k:int(hexadecimal[1+i*2:3+i*2],16)/255 for i,k in enumerate(('red','green','blue'))}

def formulas_resumen():
    def consulta(hoja,grupo,monto=None,etiqueta='Período'):
        cols=COLUMNAS[hoja];g=letra(cols.index(grupo)+1)
        agregado='sum('+letra(cols.index(monto)+1)+')' if monto else 'count(A)'
        texto=f"select {g}, {agregado} where A is not null group by {g} label {g} '{etiqueta}', {agregado} '"+('Total vendido' if monto else 'Solicitudes')+"'"
        # Fórmulas inglesas con separador regional de Chile. Solo expresiones
        # propias; ningún texto de cliente se evalúa como fórmula.
        return '=IF(COUNTA('+hoja+'!A2:A)=0;"Sin datos";QUERY('+hoja+'!A1:'+letra(len(cols))+';"'+texto+'";1))'
    return {'A1':consulta('Ventas','mes','monto_vendido','Mes'),
            'D1':consulta('Ventas','trimestre','monto_vendido','Trimestre'),
            'G1':consulta('Ventas','tematica','monto_vendido','Temática'),
            'J1':consulta('Casos','mes',None,'Mes de solicitudes')}

def preparar(libro,correo_servicio):
    metadata=libro.fetch_sheet_metadata()
    existentes={s['properties']['title']:s for s in metadata.get('sheets',[])}
    faltantes=[h for h in COLUMNAS if h not in existentes]
    if faltantes:
        libro.batch_update({'requests':[{'addSheet':{'properties':{'title':h,'gridProperties':{'rowCount':5000 if h in CLAVES else 1000,'columnCount':max(12,len(COLUMNAS[h]))}}}} for h in faltantes]})
        metadata=libro.fetch_sheet_metadata();existentes={s['properties']['title']:s for s in metadata['sheets']}
    solicitudes=[];encabezados=[]
    for hoja,columnas in COLUMNAS.items():
        sheet=existentes[hoja];sid=sheet['properties']['sheetId']
        if any(m.get('metadataKey')==MARCA for m in sheet.get('developerMetadata',[])):continue
        rango={'sheetId':sid,'startRowIndex':0,'endRowIndex':1,'startColumnIndex':0,'endColumnIndex':len(columnas)}
        solicitudes += [
            {'updateSheetProperties':{'properties':{'sheetId':sid,'gridProperties':{'frozenRowCount':1},'tabColorStyle':{'rgbColor':rgb('#9966FF')}},'fields':'gridProperties.frozenRowCount,tabColorStyle'}},
            {'repeatCell':{'range':rango,'cell':{'userEnteredFormat':{'backgroundColor':rgb('#CCCCFF'),'textFormat':{'bold':True,'foregroundColor':rgb('#0B2545')}}},'fields':'userEnteredFormat'}},
            {'updateDimensionProperties':{'range':{'sheetId':sid,'dimension':'COLUMNS','startIndex':0,'endIndex':len(columnas)},'properties':{'pixelSize':155},'fields':'pixelSize'}},
            {'addProtectedRange':{'protectedRange':{'range':rango,'description':MARCA,'warningOnly':False,'editors':{'users':[correo_servicio]}}}},
            {'createDeveloperMetadata':{'developerMetadata':{'metadataKey':MARCA,'metadataValue':'1','location':{'sheetId':sid},'visibility':'DOCUMENT'}}},
        ]
        if hoja in CLAVES:
            solicitudes.append({'setBasicFilter':{'filter':{'range':{'sheetId':sid,'startRowIndex':0,'startColumnIndex':0,'endColumnIndex':len(columnas)}}}})
        for i,columna in enumerate(columnas):
            formato={'type':'DATE','pattern':'dd/mm/yyyy'} if columna in FECHAS else {'type':'NUMBER','pattern':'"$" #,##0'} if columna in MONEDAS else None
            if formato:solicitudes.append({'repeatCell':{'range':{'sheetId':sid,'startRowIndex':1,'startColumnIndex':i,'endColumnIndex':i+1},'cell':{'userEnteredFormat':{'numberFormat':formato}},'fields':'userEnteredFormat.numberFormat'}})
        tipo='caso' if hoja=='Casos' else 'cotizacion' if hoja=='Cotizaciones' else 'pago' if hoja=='Ventas' else None
        campo='estado' if hoja=='Casos' else 'estado_cotizacion' if hoja=='Cotizaciones' else 'estado_pago'
        if tipo:
            ix=columnas.index(campo)
            for e in CATALOGO[tipo].values():
                solicitudes.append({'addConditionalFormatRule':{'index':0,'rule':{'ranges':[{'sheetId':sid,'startRowIndex':1,'startColumnIndex':ix,'endColumnIndex':ix+1}],
                    'booleanRule':{'condition':{'type':'TEXT_EQ','values':[{'userEnteredValue':e['etiqueta']}]},'format':{'backgroundColor':rgb(e['fondo']),'textFormat':{'foregroundColor':rgb(e['texto'])}}}}}})
        if hoja!='Resumen':encabezados.append({'range':"'"+hoja+"'!A1",'values':[list(columnas)]})
    if solicitudes:
        solicitudes.insert(0,{'updateSpreadsheetProperties':{'properties':{'locale':'es_CL','timeZone':'America/Santiago'},'fields':'locale,timeZone'}})
        libro.batch_update({'requests':solicitudes})
    if encabezados:libro.values_batch_update({'valueInputOption':'RAW','data':encabezados})
    # Recupera también una preparación interrumpida después de marcar formatos.
    libro.values_update("'Leyenda'!A1",params={'valueInputOption':'RAW'},body={'values':[list(COLUMNAS['Leyenda'])]+leyenda()})
    libro.values_update("'Registro'!A1",params={'valueInputOption':'RAW'},body={'values':[list(COLUMNAS['Registro'])]})
    # Solo se inicializa vacío. Ni la preparación repetida ni las sincronizaciones
    # tocan fórmulas o personalizaciones ya presentes en Resumen.
    contenido=libro.values_get("'Resumen'!A1:K5").get('values',[])
    if not any(any(c!='' for c in f) for f in contenido):
        libro.values_batch_update({'valueInputOption':'USER_ENTERED','data':[{'range':"'Resumen'!"+celda,'values':[[formula]]} for celda,formula in formulas_resumen().items()]})
    return {h:s['properties'] for h,s in existentes.items() if h in COLUMNAS}
