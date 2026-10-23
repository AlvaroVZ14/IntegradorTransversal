"""Formato de respaldo compartido por la app y el job, sin claves de servidor."""
import csv
import hashlib
import io
import json
from zipfile import ZipFile, ZIP_DEFLATED

TABLAS = ('mf_perfiles','mf_casos','mf_cotizaciones','mf_ventas','mf_tarifas',
          'mf_plantillas_programa','mf_eventos_caso','mf_configuracion',
          'mf_borradores_cotizacion','mf_envios_cotizacion','mf_mantenimiento')


def zip_csv(snapshot):
    """CSV UTF-8 BOM, JSON anidado, nulos sin ambigüedad en manifiesto aparte.

    Los valores originales se conservan: importar como texto, no abrir con
    ejecución de fórmulas en una planilla. No contiene Auth ni archivos Storage.
    """
    if snapshot.get('format') != 1 or set(snapshot.get('tables', {})) != set(TABLAS):
        raise ValueError('El respaldo está incompleto o su formato no es compatible.')
    manifest = dict(format=1, snapshot_at=snapshot['snapshot_at'], tables={},
        scope='Datos comerciales; no incluye Auth, Storage, esquema SQL ni secretos.',
        encoding='CSV UTF-8 BOM; JSON para objetos; null_cells identifica nulos; filas desde 0.')
    output = io.BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for nombre in TABLAS:
            table = snapshot['tables'][nombre]
            columns = [c['name'] for c in table['columns']]
            if not columns or len(set(columns)) != len(columns):
                raise ValueError('Columnas de respaldo inválidas.')
            text = io.StringIO(newline='')
            writer = csv.writer(text, quoting=csv.QUOTE_ALL)
            writer.writerow(columns)
            nulls = []
            for index, row in enumerate(table['rows']):
                if set(row) != set(columns):
                    raise ValueError('El respaldo contiene una fila incompleta.')
                cells = []
                for col in columns:
                    value = row[col]
                    if value is None:
                        nulls.append([index, col]); cells.append('')
                    elif isinstance(value, (dict, list, bool)):
                        cells.append(json.dumps(value, ensure_ascii=False, separators=(',', ':')))
                    else:
                        cells.append(str(value))
                writer.writerow(cells)
            data = text.getvalue().encode('utf-8-sig')
            archive.writestr(nombre+'.csv', data)
            manifest['tables'][nombre] = dict(columns=table['columns'], rows=len(table['rows']),
                sha256=hashlib.sha256(data).hexdigest(), null_cells=nulls)
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return output.getvalue()
