"""Edición de redes dentro del autoguardado existente del caso."""
import streamlit as st
from servicios.redes_sociales import REDES, normalizar_red, redes_del_caso
from servicios.autoguardado import editar, guardar
from utils.permisos import require_admin


def _cambiar(repo, borrador, campo, llave):
    valor = st.session_state[llave]
    try:
        valor = normalizar_red(campo, valor)
        st.session_state[llave] = valor
    except ValueError:
        pass  # Conserva el texto inválido y permite corregirlo.
    pendiente = borrador['pendientes'].get('redes_sociales', {}).get('valor')
    actuales = dict(pendiente if pendiente is not None else borrador['ultimo'].get('redes_sociales') or {})
    if valor: actuales[campo] = valor
    else: actuales.pop(campo, None)
    editar(borrador, 'redes_sociales', actuales)
    guardar(repo, borrador, campos=['redes_sociales'])


def redes_caso(repo, caso, borrador):
    require_admin(repo)
    st.subheader('Redes sociales')
    guardadas = redes_del_caso(borrador['ultimo'])
    if not guardadas:
        st.caption('Sin redes registradas')
    for campo, valor in guardadas.items():
        nombre, icono = REDES[campo]
        if valor.startswith(('http://', 'https://')):
            st.link_button(nombre, valor, icon=icono, width='stretch')
        else:
            st.text(nombre + ': ' + valor)
    with st.expander('Editar redes sociales'):
        pendientes = borrador['pendientes'].get('redes_sociales', {}).get('valor')
        valores = pendientes if pendientes is not None else borrador['ultimo'].get('redes_sociales') or {}
        with st.container(key='mfy_redes_caso'):
            for fila in (list(REDES)[:2], list(REDES)[2:4], list(REDES)[4:]):
                columnas = st.columns(2)
                for columna, campo in zip(columnas, fila):
                    llave = f"red_caso_{caso['id']}_{campo}"
                    if llave not in st.session_state or pendientes is None:
                        st.session_state[llave] = valores.get(campo, '')
                    with columna:
                        st.text_input(REDES[campo][0]+' (opcional)', key=llave, max_chars=200, icon=REDES[campo][1],
                                      on_change=_cambiar, args=(repo,borrador,campo,llave))
                        try: normalizar_red(campo, valores.get(campo,''))
                        except ValueError as error: st.error(str(error))
            if borrador['conflictos'].get('redes_sociales'):
                st.warning(borrador['conflictos']['redes_sociales'])
                if st.button('Guardar mis redes',key='conflicto_redes_'+caso['id']):
                    try:
                        actual=repo.get_case(caso['id'])
                        borrador['pendientes']['redes_sociales']['base']=actual.get('redes_sociales')
                        borrador['conflictos'].pop('redes_sociales',None)
                        guardar(repo,borrador,campos=['redes_sociales']);st.rerun()
                    except Exception:
                        st.warning('No pudimos conectar. Conservamos tus cambios para reintentarlo.')
    from servicios.ficha_caso import generar_ficha_pdf
    from mente_futuro.domain import code
    st.download_button('Descargar ficha del caso', data=lambda: generar_ficha_pdf(repo.get_case(caso['id'])),
                       file_name=f'Ficha_{code(caso)}.pdf', mime='application/pdf',
                       key='ficha_caso_'+caso['id'], on_click='ignore', width='stretch')
