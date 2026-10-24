"""Copiar un mensaje no lo envía ni lo registra como contacto realizado."""
import streamlit as st
from streamlit.components.v2 import component
from utils.estilos import CSS_COPIAR


def copiar_mensaje(texto,key,*,etiqueta='Copiar',confirmacion='Mensaje copiado.'):
    puente=component('mfy_copiar_hoy',html='<button type="button">Copiar</button>',css=CSS_COPIAR,js="""
    export default function({parentElement,data,setStateValue}) {
      const button=parentElement.querySelector('button');
      button.textContent=data.label;
      const copy=async()=>{try{await navigator.clipboard.writeText(data.text);button.textContent=data.confirmation;button.setAttribute('aria-label',data.confirmation);setStateValue('copiado',data.text);}catch{setStateValue('fallo',true);}};
      button.addEventListener('click',copy);return()=>button.removeEventListener('click',copy);
    }
    """)
    estado=puente(data={'text':texto,'confirmation':confirmacion,'label':etiqueta},default={'copiado':False,'fallo':False},on_copiado_change=lambda:None,on_fallo_change=lambda:None,key=key,height=50)
    if estado.copiado==texto:st.caption(confirmacion)
    if estado.fallo:st.caption('Puedes seleccionar y copiar el texto del cuadro anterior.')
