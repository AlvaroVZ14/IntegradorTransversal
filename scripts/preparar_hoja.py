"""Preparación y primera copia; repetible, sin sobrescribir Resumen existente."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from servicios.hoja_sync import ejecutar_cli

if __name__=='__main__':
    try:
        ejecutar_cli(preparar=True)
        print('Hoja preparada y copia de datos actualizada.')
    except Exception:
        print('No pudimos preparar la hoja. Revisa los secretos y permisos; los datos originales siguen a salvo.')
        raise SystemExit(1) from None
