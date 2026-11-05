"""Control nocturno. No imprime datos ni excepciones que contengan secretos."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from servicios.hoja_sync import ejecutar_cli

if __name__=='__main__':
    try:
        ejecutado=ejecutar_cli()
        print('Copia de datos actualizada.' if ejecutado else 'Otro procesador ya está actualizando la hoja.')
    except Exception:
        print('No pudimos actualizar la hoja. La cola se conserva para reintentar.')
        raise SystemExit(1) from None
