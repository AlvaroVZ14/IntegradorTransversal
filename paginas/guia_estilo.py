"""Guía visual oculta. No consulta ni modifica datos de negocio."""
import pandas as pd
import streamlit as st
from ui import tema
from utils.permisos import require_admin,proteger_pagina


def guia_estilo(repo):
    require_admin(repo)
    tema.encabezado_pagina('Nuestra guía visual','Colores y componentes para revisar el portal.','GUÍA DE ESTILO','',mostrar_metricas=False)
    st.caption('Ejemplos ficticios. Los botones de esta guía no cambian datos.')
    st.subheader('Colores y tipografía')
    tema.chips_activos(['Celeste #6699FF','Morado #9966FF','Amarillo #FFCC00','Texto #0B2545'])
    st.write('Títulos claros, texto de 16 px y ayudas breves. Se usan fuentes del sistema, sin descargas externas.')
    with tema.tarjeta('Una tarjeta',key='guia_tarjeta'):
        tema.boton_principal('Guardar ejemplo',key='guia_guardar')
        tema.boton_secundario('Descargar ejemplo',key='guia_descargar')
        tema.boton_peligro('Eliminar ejemplo',key='guia_eliminar')
    tema.tarjeta_lista('Una solicitud de ejemplo','Recibida hoy, lista para revisar.',key='guia_lista')
    tema.tarjeta_accion('Por revisar',3,key='guia_accion',icono=':material/folder_open:',ayuda='Ejemplo de acción.',on_click=lambda:None)
    st.markdown(tema.avatar('Camila Ficticia'),unsafe_allow_html=True)
    for tipo in ('exito','info','atencion','error'):tema.aviso('Un mensaje breve de ejemplo.',tipo)
    tema.leyenda_estados()
    tema.estado_vacio('Aquí aparecerán tus documentos. Puedes comenzar con una nueva solicitud.')
    tema.tabla(pd.DataFrame([{'Caso':'MF-2026-0001','Cliente':'Empresa ficticia','Estado':'Solicitud'}]),'Tabla de ejemplo')
    tema.linea_de_tiempo([{'fecha':'05/11/2026','titulo':'Solicitud recibida','detalle':'Ejemplo de seguimiento.'}])
    tema.esqueleto_carga()


if __name__=='__main__':
    guia_estilo(proteger_pagina('Guía de estilo',admin=True))
