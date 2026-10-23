"""Recuperación de Auth; el rol se vuelve a consultar en Supabase."""
import json
from time import time

DIAS=7
COOKIE='mfy_admin_refresh_v1'


def leer_cookie(value,ahora=None):
    ahora=time() if ahora is None else ahora
    if not value or len(value)>3000:return None
    try:
        dato=json.loads(value)
        token=dato['refresh_token'];vence=dato['expires']
        if not isinstance(token,str) or not 8<=len(token)<=2048:return None
        if isinstance(vence,bool) or not isinstance(vence,(int,float)) or not ahora<vence<=ahora+DIAS*86400+60:return None
        return dict(refresh_token=token,expires=vence)
    except (ValueError,TypeError,KeyError):return None


def perfil_verificado(client):
    response=client.auth.get_user()
    user=response.user if response else None
    if not user:raise PermissionError('Sesión no disponible')
    rows=client.table('mf_perfiles').select('*').eq('id',user.id).execute().data
    if not rows:raise PermissionError('Perfil no disponible')
    return user,rows[0]


def restaurar(value,factory):
    cookie=leer_cookie(value)
    if not cookie:return None
    client=factory()
    response=client.auth.refresh_session(cookie['refresh_token'])
    if not response or not response.session:return None
    user,perfil=perfil_verificado(client)
    if perfil.get('rol')!='admin':
        # Una cookie nunca convierte un cliente en administración.
        return None
    return client,user,perfil,response.session,cookie['expires']
