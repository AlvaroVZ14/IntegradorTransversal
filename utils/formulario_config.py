"""Contrato único de campos. Los catálogos de servicio y temática vienen de Supabase."""
from copy import deepcopy
from dataclasses import dataclass
from mente_futuro.domain import MODALITIES
from servicios.solicitud_rapida import ORIGENES

MODOS=('publico','cliente','interno')
PASOS=('Contacto','Servicio','Detalles y envío')

@dataclass(frozen=True)
class Campo:
    etiqueta:str
    paso:int
    tipo:str='texto'
    ayuda:str=''
    limite:int|None=None
    modos:tuple=MODOS

CAMPOS={
 'cliente':Campo('Empresa o institución',1,ayuda='Si consultas a título personal, puedes usar tu nombre.',limite=180),
 'contacto':Campo('Nombre y apellido',1,limite=160),
 'rut':Campo('RUT (opcional)',1,ayuda='Por ejemplo, 12.345.678-5.',limite=16),
 'cargo':Campo('Cargo (opcional)',1,limite=160),
 'email':Campo('Correo electrónico',1,limite=254),
 'telefono':Campo('Teléfono (opcional)',1,ayuda='Por ejemplo, +56 9 1234 5678.',limite=40),
 'cliente_id':Campo('Vincular a una cuenta de cliente',1,'cuenta',modos=('interno',)),
 'origen':Campo('Origen de la solicitud',1,'origen',modos=('interno',)),
 'referido_por':Campo('Referido por',1,limite=160,modos=('interno',)),
 'servicio':Campo('Tipo de servicio',2,'servicio'),
 'tematicas':Campo('Temáticas',2,'tematicas',ayuda='La primera que elijas será la temática principal.'),
 'modalidad':Campo('Modalidad',2,'modalidad'),
 'participantes':Campo('Participantes',3,'entero'),
 'horas':Campo('Horas estimadas',3,'decimal'),
 'dirigido_a':Campo('Dirigido a (opcional)',3,ayuda='Por ejemplo, líderes de equipo o personas del área de ventas.',limite=1000),
 'lugar':Campo('Lugar o ciudad (opcional)',3,limite=250),
 'fecha_preferida':Campo('Fecha preferida (opcional)',3,'fecha'),
 'detalle':Campo('Comentarios y objetivos (opcional)',3,'parrafo',limite=5000),
 'consentimiento':Campo('Autorizo a Mente y Futuro a utilizar mis datos para gestionar esta solicitud y contactarme.',3,'consentimiento',modos=('publico','cliente')),
 'consentimiento_confirmado':Campo('Confirmé con la persona que sus datos se usarán para esta solicitud',3,'confirmacion',modos=('interno',)),
}
OBLIGATORIOS=('cliente','contacto','email','servicio','tematicas','modalidad','participantes','horas')
BLOQUEADOS={'publico':(), 'cliente':('contacto','email'), 'interno':()}
DIFERENCIAS_INTENCIONALES={
 'cliente_id':'Solo la administración vincula manualmente cuentas.',
 'origen':'El servidor fija Formulario web fuera del modo interno.',
 'referido_por':'Solo administración registra el origen referido.',
 'consentimiento':'Obligatorio para público y cliente; no se restaura del borrador.',
 'consentimiento_confirmado':'La confirmación administrativa es opcional.',
 'identidad':'Nombre y correo se bloquean y se verifican en DB para cliente.',
 'incompletos':'Solo administración puede guardar información pendiente.',
 'navegacion':'Solo administración puede saltar pasos.',
 'acciones':'Guardar, cotizar, registrar otra, búsqueda, sugerencias y duplicados son internos.',
}
OPCIONES={'modalidad':tuple(MODALITIES),'origen':tuple(ORIGENES)}
DEFAULTS=dict(cliente='',contacto='',rut='',cargo='',email='',telefono='',cliente_id=None,
 origen=ORIGENES[0],referido_por='',servicio=None,tematicas=[],tematica=None,modalidad=MODALITIES[2],
 participantes=1,horas=1.0,dirigido_a='',lugar='',fecha_preferida=None,detalle='')
TEXTOS=tuple(k for k,c in CAMPOS.items() if c.tipo in ('texto','parrafo'))

def valores_iniciales():return deepcopy(DEFAULTS)
def campos_modo(modo):
    if modo not in MODOS:raise ValueError('Modo de formulario no válido.')
    return {k:c for k,c in CAMPOS.items() if modo in c.modos}
def campos_paso(modo,paso):return {k:c for k,c in campos_modo(modo).items() if c.paso==paso}
def etiqueta(campo):return CAMPOS[campo].etiqueta
def contrato(modo):return {k:(c.etiqueta,c.paso,c.tipo,c.ayuda) for k,c in campos_modo(modo).items()}
