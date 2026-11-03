"""Perfil acotado con el JWT personal; sin acceso directo a tablas de gestión."""
from servicios.repositorio import fila_rpc
from servicios.redes_sociales import REDES,normalizar_redes
from servicios.solicitud_rapida import normalizar_telefono
from utils.validaciones import validar_campo

EDITABLES=('telefono','cargo',*REDES)


def validar_perfil(datos):
    if not isinstance(datos,dict) or set(datos)-set(EDITABLES):
        return {'perfil':'Solo puedes editar teléfono, cargo y redes sociales.'}
    errores={}
    for campo in EDITABLES:
        valor=datos.get(campo,'')
        if not isinstance(valor,str):errores[campo]='Escribe un texto válido.'
        elif error:=validar_campo(campo,valor):errores[campo]=error
    return errores


class PerfilCliente:
    def __init__(self,repo):
        if repo.profile.get('rol')!='cliente' or not getattr(repo.user,'email_confirmed_at',None):
            raise PermissionError('Confirma el correo de tu cuenta para acceder a Mi perfil.')
        self.repo=repo

    def leer(self):
        perfil=fila_rpc(self.repo.client.rpc('mf_mi_perfil',{}).execute().data)
        if not all(k in perfil for k in ('id','version','empresa','nombre','correo','telefono','cargo','redes_sociales')):
            raise ValueError('No pudimos leer tu perfil. Intenta nuevamente.')
        return perfil

    def guardar(self,perfil,datos):
        errores=validar_perfil(datos)
        if errores:raise ValueError(next(iter(errores.values())))
        redes=normalizar_redes(datos)
        payload={'telefono':normalizar_telefono(datos.get('telefono','').strip()),'cargo':datos.get('cargo','').strip(),
                 **{k:redes.get(k,'') for k in REDES}}
        actualizado=fila_rpc(self.repo.client.rpc('mf_guardar_mi_perfil',{
            'p_id':perfil.get('id'),'p_version':perfil['version'],'p_datos':payload}).execute().data)
        from servicios.dashboard_cache import invalidar_dashboard
        invalidar_dashboard()
        return actualizado


def actualizar_borrador_perfil(estado,usuario,perfil):
    """Actualiza precarga pendiente, conservando campos editados por la persona."""
    borrador=estado.get('formularios',{}).get('cliente:'+str(usuario))
    if not borrador:return {}
    if borrador['values'].get('cliente') not in ('',perfil['empresa']):return {}
    datos={'telefono':perfil['telefono'],'cargo':perfil['cargo'],**{k:perfil['redes_sociales'].get(k,'') for k in REDES}}
    cambios={k:v for k,v in datos.items() if k not in borrador['tocados']}
    for k,v in cambios.items():
        borrador['values'][k]=v
        estado.pop('request_'+k,None)
    borrador['ack']=dict(borrador['values'])
    return cambios
