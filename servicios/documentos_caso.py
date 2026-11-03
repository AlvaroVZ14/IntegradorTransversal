"""Persistencia privada con JWT, operaciones recuperables y enlaces de diez minutos."""
from uuid import uuid5,UUID
from servicios.archivos_caso import BUCKET,TIPOS,TIPOS_TODOS,VISIBLES,validar_archivo,identidad_archivo
from servicios.repositorio import fila_rpc


class DocumentosCaso:
    def __init__(self,repo):self.repo=repo;self.client=repo.client

    def listar(self,caso_id=None):
        self.repo.owner_only()
        consulta=self.client.table('mf_documentos').select('*')
        if caso_id:consulta=consulta.eq('caso_id',caso_id)
        filas=[];offset=0
        while True:
            pagina=consulta.order('fecha_subida',desc=True).order('id').range(offset,offset+499).execute().data
            filas.extend(pagina)
            if len(pagina)<500:return filas
            offset+=500

    def buscar(self,documento_id):
        self.repo.owner_only()
        filas=self.client.table('mf_documentos').select('*').eq('id',documento_id).execute().data
        return filas[0] if filas else None

    def subir(self,caso_id,tipo,nombre,contenido,nota='',visible=None,documento_id=None,cotizacion_id=None):
        self.repo.owner_only()
        if tipo not in TIPOS:raise ValueError('Selecciona un tipo de documento válido.')
        if len(nota)>2000:raise ValueError('La nota puede tener hasta 2.000 caracteres.')
        archivo=validar_archivo(nombre,contenido)
        fila=identidad_archivo(caso_id,archivo,documento_id)
        existente=self.buscar(fila['id'])
        if cotizacion_id:
            coincidencias=self.client.table('mf_documentos').select('*').eq('cotizacion_id',cotizacion_id).execute().data
            if coincidencias:existente=coincidencias[0]
        if existente:
            if existente['caso_id']!=fila['caso_id'] or existente['tamano']!=fila['tamano'] or existente['tipo_mime']!=fila['tipo_mime']:raise ValueError('Revisa el documento pendiente antes de reintentarlo.')
            if existente['estado_archivo']=='eliminado':return existente
            if existente['estado_archivo']=='eliminando':raise ValueError('Termina de eliminar este documento antes de volver a subirlo.')
            if existente['estado_archivo']=='disponible':return existente
            fila=existente
        else:
            fila=fila_rpc(self.client.table('mf_documentos').insert({**fila,'tipo':tipo,'nota':nota.strip(),
                'visible_cliente':tipo in VISIBLES if visible is None else bool(visible),
                'subido_por':self.repo.user.id,'cotizacion_id':cotizacion_id}).execute().data)
        bucket=self.client.storage.from_(BUCKET)
        # Un reintento reconoce el objeto existente; nunca se sobrescribe.
        objetos=bucket.list(str(fila['caso_id']),{'search':fila['archivo_path'].split('/')[-1]})
        if not any(o.get('name')==fila['archivo_path'].split('/')[-1] for o in objetos):
            bucket.upload(fila['archivo_path'],archivo.contenido,{'content-type':archivo.mime,'cache-control':'0','upsert':'false'})
        return fila_rpc(self.client.rpc('mf_confirmar_documento',{'p_id':fila['id']}).execute().data)

    def visibilidad(self,documento_id,visible):
        self.repo.owner_only()
        return fila_rpc(self.client.table('mf_documentos').update({'visible_cliente':bool(visible)}).eq('id',documento_id).eq('estado_archivo','disponible').execute().data)

    def cambiar_tipo(self,documento_id,tipo):
        self.repo.owner_only()
        if tipo not in TIPOS_TODOS:raise ValueError('Selecciona un tipo de documento válido.')
        return fila_rpc(self.client.table('mf_documentos').update({'tipo':tipo}).eq('id',documento_id).execute().data)

    def enlace(self,documento_id):
        fila=self.buscar(documento_id)
        if not fila or fila['estado_archivo']!='disponible':raise PermissionError('Documento no disponible para tu cuenta.')
        respuesta=self.client.storage.from_(BUCKET).create_signed_url(fila['archivo_path'],600,{'download':fila['nombre']})
        return respuesta.get('signedURL') or respuesta.get('signedUrl') or respuesta.get('signed_url') or ''

    def eliminar(self,documento_id):
        self.repo.owner_only();fila=self.buscar(documento_id)
        if not fila or fila['estado_archivo']=='eliminado':return
        self.client.rpc('mf_eliminar_documento',{'p_id':documento_id,'p_finalizar':False}).execute()
        self.client.storage.from_(BUCKET).remove([fila['archivo_path']])
        self.client.rpc('mf_eliminar_documento',{'p_id':documento_id,'p_finalizar':True}).execute()

    def destinatario(self,caso_id):
        self.repo.owner_only()
        return fila_rpc(self.client.rpc('mf_destinatario_documentos',{'p_caso_id':caso_id}).execute().data)

    def reservar_aviso(self,documento_id):
        self.repo.owner_only()
        return self.client.rpc('mf_reservar_aviso_documento',{'p_id':documento_id}).execute().data is True

    def resultado_aviso(self,documento_id,estado):
        self.repo.owner_only()
        self.client.rpc('mf_resultado_aviso_documento',{'p_id':documento_id,'p_estado':estado}).execute()

    def sincronizar_cotizacion(self,caso,cotizacion):
        self.repo.owner_only()
        # ID determinista: generar o reabrir la misma versión no duplica el PDF.
        from servicios.documentos_cotizacion import generar_pdf
        identificador=uuid5(UUID(cotizacion['id']),'documento-pdf')
        return self.subir(caso['id'],'Cotización','cotizacion.pdf',generar_pdf(cotizacion),visible=False,
            documento_id=identificador,cotizacion_id=cotizacion['id'])
