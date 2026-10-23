"""Copiar un mensaje no lo envía ni lo registra como contacto realizado."""
import streamlit as st
from streamlit.components.v2 import component
from utils.estilos import CSS_COPIAR


def copiar_mensaje(texto,key):
    puente=component('mfy_copiar_hoy',html='<button type="button">Copiar</button>',css=CSS_COPIAR,js="""
    export default function({parentElement,data,setStateValue}) {
      const button=parentElement.querySelector('button');
      const copy=async()=>{try{await navigator.clipboard.writeText(data.text);setStateValue('copiado',true);}catch{setStateValue('fallo',true);}};
      button.addEventListener('click',copy);return()=>button.removeEventListener('click',copy);
    }
    """)
    estado=puente(data={'text':texto},default={'copiado':False,'fallo':False},on_copiado_change=lambda:None,on_fallo_change=lambda:None,key=key,height=50)
    if estado.copiado:st.caption('Mensaje copiado.')
    if estado.fallo:st.caption('Puedes seleccionar y copiar el texto del cuadro anterior.')
