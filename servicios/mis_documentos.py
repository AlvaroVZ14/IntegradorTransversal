"""Portal cliente: consulta mínima con el JWT personal, sin clave de servidor."""
from urllib.request import urlopen
from servicios.archivos_caso import MAX_BYTES, BUCKET, TIPOS_CLIENTE, validar_archivo
from servicios.repositorio import fila_rpc
from uuid import UUID, uuid4


class MisDocumentos:
    def __init__(self, repo):
        if repo.profile.get('rol') != 'cliente':
            raise PermissionError('Esta sección corresponde a una cuenta de cliente.')
        self.client = repo.client

    def subir(self, caso_id, tipo, nombre, contenido, nota='', documento_id=None):
        """El servidor inspecciona los bytes antes de reservar cupo o subirlos.

        El UUID repetido permite reintentar una respuesta perdida sin duplicar.
        La base vuelve a comprobar correo confirmado, caso, cupos e identidad.
        """
        if tipo not in TIPOS_CLIENTE:
            raise ValueError('Selecciona un tipo de documento válido.')
        if len(nota) > 2000:
            raise ValueError('La nota puede tener hasta 2.000 caracteres.')
        archivo = validar_archivo(nombre, contenido)
        self.client.auth.get_user()
        d = fila_rpc(self.client.rpc('mf_preparar_documento_cliente', {
            'p_id': str(UUID(str(documento_id or uuid4()))), 'p_caso_id': str(UUID(str(caso_id))),
            'p_tipo': tipo, 'p_extension': archivo.extension.lstrip('.'), 'p_tamano': len(contenido),
            'p_mime': archivo.mime, 'p_nota': nota.strip(),
        }).execute().data)
        if d['estado_archivo'] == 'disponible':
            return d
        bucket = self.client.storage.from_(BUCKET)
        carpeta, nombre_opaco = d['archivo_path'].rsplit('/', 1)
        existentes = bucket.list(carpeta, {'search': nombre_opaco})
        if not any(o.get('name') == nombre_opaco for o in existentes):
            bucket.upload(d['archivo_path'], archivo.contenido,
                          {'content-type': archivo.mime, 'cache-control': '0', 'upsert': 'false'})
        return fila_rpc(self.client.rpc('mf_confirmar_documento', {'p_id': d['id']}).execute().data)

    def eliminar(self, documento_id):
        self.client.auth.get_user()
        d = fila_rpc(self.client.rpc('mf_eliminar_documento_cliente', {
            'p_id': documento_id, 'p_finalizar': False}).execute().data)
        self.client.storage.from_(BUCKET).remove([d['archivo_path']])
        self.client.rpc('mf_eliminar_documento_cliente', {'p_id': documento_id, 'p_finalizar': True}).execute()

    def reservar_aviso_socia(self, documento_id):
        datos = self.client.rpc('mf_aviso_documento_cliente', {'p_id': documento_id}).execute().data
        return fila_rpc(datos) if datos else {}

    def resultado_aviso_socia(self, documento_id, estado):
        self.client.rpc('mf_aviso_documento_cliente', {'p_id': documento_id, 'p_resultado': estado}).execute()

    def listar(self):
        filas = []
        while True:
            pagina = self.client.rpc('mf_mis_documentos', {'p_desde': len(filas)}).execute().data or []
            filas.extend(pagina)
            if len(pagina) < 100:
                return filas

    def descargar(self, documento_id):
        """Se ejecuta al pulsar Descargar: permisos actuales, sin caché compartido.

        El enlace firmado dura 600 s y se consume solo en el servidor. Al navegador
        llega el archivo por Streamlit, nunca la ruta de Storage ni el token firmado.
        """
        try:
            self.client.auth.get_user()  # Auth vuelve a verificar/renovar el JWT.
            d = fila_rpc(self.client.rpc('mf_documento_cliente', {'p_id': documento_id}).execute().data)
            if not d:
                raise PermissionError('Documento no disponible para tu cuenta.')
            resultado = self.client.storage.from_(BUCKET).create_signed_url(d['archivo_path'], 600)
            enlace = resultado.get('signedURL') or resultado.get('signedUrl') or resultado.get('signed_url')
            if not enlace or not enlace.startswith('https://'):
                raise ValueError('Descarga no disponible.')
            with urlopen(enlace, timeout=30) as respuesta:
                contenido = respuesta.read(MAX_BYTES + 1)
            if not contenido or len(contenido) > MAX_BYTES:
                raise ValueError('Archivo no disponible.')
            return contenido
        except Exception:
            # No propagar URLs con tokens ni detalles del proveedor al navegador.
            raise RuntimeError('No pudimos descargar el documento. Vuelve a abrir Mis documentos e intenta nuevamente.') from None
