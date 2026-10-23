"""Comprobación manual con JWT real de una cuenta ficticia. No imprime tokens.

Ejecutar desde la raíz: python tests/probar_sesion_cliente.py
La contraseña se solicita de forma oculta. Solo hace consultas de lectura.
"""
from getpass import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from servicios.repositorio import public_client


def main():
    client = public_client()
    email = input("Correo de la cuenta ficticia cliente: ").strip()
    client.auth.sign_in_with_password({"email":email,"password":getpass("Contraseña: ")})
    try:
        user = client.auth.get_user().user
        profiles = client.table("mf_perfiles").select("id,rol").execute().data
        assert len(profiles)==1 and profiles[0]=={"id":user.id,"rol":"cliente"}, "Usa una cuenta de cliente y revisa los permisos de perfiles."
        for table in ["mf_casos","mf_cotizaciones","mf_tarifas","mf_ventas","mf_programas","mf_historial","mf_configuracion","casos","cotizaciones","tarifas","programas","ventas","historial","configuracion"]:
            try:
                rows = client.table(table).select("*").limit(1).execute().data
            except Exception as error:
                if getattr(error,"code",None) in ("42501","PGRST301"):
                    print(f"OK: {table}: acceso denegado")
                elif getattr(error,"code",None)=="PGRST205":
                    print(f"NO APLICA: {table}: no existe en este proyecto")
                else:
                    raise
            else:
                assert rows==[], f"FALLO: {table} permite leer información"
                print(f"OK: {table}: 0 filas")
        print("OK: el JWT del cliente solo puede consultar su perfil.")
    finally:
        client.auth.sign_out({"scope":"local"})


if __name__=="__main__":
    main()
