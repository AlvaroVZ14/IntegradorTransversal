"""Validación en memoria y nombres opacos. Nunca se conservan nombres originales."""
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from uuid import UUID,uuid4
from zipfile import ZipFile
from xml.etree import ElementTree
import warnings

MAX_BYTES=10*1024*1024
BUCKET='documentos-casos'
TIPOS=('Lista de asistencia','Informe','Certificado','Material','Cotización','Otro')
VISIBLES=('Lista de asistencia','Informe','Certificado','Material')
MIMES={'.pdf':'application/pdf','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
       '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
       '.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}


@dataclass(frozen=True)
class ArchivoValidado:
    contenido:bytes
    extension:str
    mime:str


def validar_archivo(nombre,contenido):
    extension=PurePosixPath(str(nombre).replace('\\','/')).suffix.lower()
    if extension not in MIMES:raise ValueError('Usa PDF, Word (.docx), Excel (.xlsx), PNG, JPG o WebP.')
    if not isinstance(contenido,bytes) or not contenido:raise ValueError('El archivo está vacío o no se pudo leer.')
    if len(contenido)>MAX_BYTES:raise ValueError('Cada archivo puede pesar hasta 10 MB.')
    try:
        if extension=='.pdf':
            from pypdf import PdfReader
            if not contenido.startswith(b'%PDF-'):raise ValueError()
            lector=PdfReader(BytesIO(contenido),strict=False)
            if not lector.is_encrypted and not len(lector.pages):raise ValueError()
        elif extension in ('.docx','.xlsx'):
            with ZipFile(BytesIO(contenido)) as z:
                partes=z.infolist();nombres={p.filename for p in partes}
                if len(partes)>2000 or sum(p.file_size for p in partes)>100*1024*1024 or any(p.flag_bits&1 for p in partes):raise ValueError()
                principal='word/document.xml' if extension=='.docx' else 'xl/workbook.xml'
                tipo=b'wordprocessingml.document.main+xml' if extension=='.docx' else b'spreadsheetml.sheet.main+xml'
                if '[Content_Types].xml' not in nombres or principal not in nombres or z.getinfo('[Content_Types].xml').file_size>1024*1024:raise ValueError()
                tipos=z.read('[Content_Types].xml')
                if tipo not in tipos or any(p.filename.lower().endswith('vbaproject.bin') for p in partes) or z.getinfo(principal).file_size>20*1024*1024:raise ValueError()
                documento=z.read(principal)
                if b'<!DOCTYPE' in tipos.upper() or b'<!DOCTYPE' in documento.upper():raise ValueError()
                raiz_tipos=ElementTree.fromstring(tipos);raiz=ElementTree.fromstring(documento)
                if raiz_tipos.tag!='{http://schemas.openxmlformats.org/package/2006/content-types}Types':raise ValueError()
                if not any(e.get('PartName')=='/'+principal and (e.get('ContentType') or '').encode()==b'application/vnd.openxmlformats-officedocument.'+tipo for e in raiz_tipos):raise ValueError()
                nombre_raiz='document' if extension=='.docx' else 'workbook'
                espacios=('http://schemas.openxmlformats.org/wordprocessingml/2006/main','http://purl.oclc.org/ooxml/wordprocessingml/main') if extension=='.docx' else ('http://schemas.openxmlformats.org/spreadsheetml/2006/main','http://purl.oclc.org/ooxml/spreadsheetml/main')
                if raiz.tag not in ('{'+espacio+'}'+nombre_raiz for espacio in espacios):raise ValueError()
                if z.testzip() is not None:raise ValueError()
        else:
            from PIL import Image
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(BytesIO(contenido)) as imagen:
                    if imagen.format!={'.png':'PNG','.jpg':'JPEG','.jpeg':'JPEG','.webp':'WEBP'}[extension] or imagen.width*imagen.height>20_000_000:raise ValueError()
                    imagen.verify()
    except Exception:
        raise ValueError('El contenido no corresponde al formato elegido, está dañado o supera los límites de lectura segura.') from None
    return ArchivoValidado(contenido,'.jpg' if extension=='.jpeg' else extension,MIMES[extension])


def identidad_archivo(caso_id,archivo,documento_id=None):
    caso=str(UUID(str(caso_id)));doc=str(UUID(str(documento_id or uuid4())))
    return dict(id=doc,caso_id=caso,nombre=f'Documento_{doc.replace("-","")}{archivo.extension}',
        archivo_path=f'{caso}/{doc}{archivo.extension}',tamano=len(archivo.contenido),tipo_mime=archivo.mime)
