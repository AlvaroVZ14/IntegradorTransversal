"""Enlaces reales guardados en la configuración existente, sin valores inventados."""
import streamlit as st
from utils.permisos import require_admin
from servicios.formulario_publico import url_publica,configuracion_publica
from utils.validaciones import validar_campo

def configuracion_formulario(repo,row):
    require_admin(repo)
    datos=row['datos'];redes=datos.get('redes') or {}
    with st.expander('Formulario: contacto, redes y privacidad'):
        with st.form('config_formulario_'+str(row['version'])):
            sitio=st.text_input('Sitio web',value=datos.get('sitio_web',''),max_chars=2048)
            facebook=st.text_input('Facebook',value=redes.get('facebook',''),max_chars=2048)
            instagram=st.text_input('Instagram',value=redes.get('instagram',''),max_chars=2048)
            privacidad=st.text_input('Enlace de la política de privacidad',value=datos.get('politica_privacidad',''),max_chars=2048)
            correo=st.text_input('Correo público de contacto',value=datos.get('correo_contacto',''),max_chars=254)
            avisos=st.text_input('Correo de la dueña para avisos',value=datos.get('correo_avisos',''),max_chars=254,
                help='Si queda vacío, se utiliza el correo público de contacto. No se publica este campo.')
            guardar=st.form_submit_button('Guardar enlaces y contacto',type='primary')
        if not privacidad:st.info('Completa el enlace real de privacidad para mostrarlo junto al consentimiento del formulario.')
        if guardar:
            urls=[sitio,facebook,instagram,privacidad]
            if any(u.strip() and not url_publica(u) for u in urls):st.error('Revisa los enlaces: utiliza direcciones web válidas.');return
            if any(c.strip() and validar_campo('email',c.strip()) for c in (correo,avisos)):st.error('Revisa los correos de contacto y avisos.');return
            try:
                nuevos=dict(datos,sitio_web=url_publica(sitio),politica_privacidad=url_publica(privacidad),correo_contacto=correo.strip(),correo_avisos=avisos.strip(),
                    redes={**redes,'facebook':url_publica(facebook),'instagram':url_publica(instagram)})
                repo.save_quote_settings(nuevos,row['version']);configuracion_publica.clear()
                st.success('Enlaces y contacto guardados.')
                st.rerun()
            except Exception:st.warning('No pudimos guardar. Conservamos lo escrito; vuelve a intentarlo.')
