"""Portal cliente: consulta mínima con el JWT personal, sin clave de servidor."""
from urllib.request import urlopen
from servicios.archivos_caso import MAX_BYTES, BUCKET
from servicios.repositorio import fila_rpc


class MisDocumentos:
    def __init__(self, repo):
        if repo.profile.get('rol') != 'cliente':
            raise PermissionError('Esta sección corresponde a una cuenta de cliente.')
        self.client = repo.client

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
