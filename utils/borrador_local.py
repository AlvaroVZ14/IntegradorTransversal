"""Respaldo de texto en la pestaña; nunca almacena tokens ni contraseñas."""
import json
import streamlit as st
from streamlit.components.v2 import component
from servicios.autoguardado import editar

TEXTOS=("cliente","contacto","email","telefono","lugar","detalle")


def recuperar_borrador(repo,caso_id,borrador):
    repo.owner_only()
    puente=component("mfy_borrador_local",html="<span aria-hidden='true'></span>",js="""
    export default function({data,setStateValue}) {
      let storage;
      try {storage=window.sessionStorage;}catch{return;}
      const name='mfy-borrador:'+data.user+':'+data.id;
      let draft={};
      try {draft=JSON.parse(storage.getItem(name)||'{}');}catch{draft={};}
      if(!draft || typeof draft!=='object' || Array.isArray(draft))draft={};
      for(const field of Object.keys(draft))if(!data.fields.includes(field) || typeof draft[field]?.value!=='string')delete draft[field];
      const write=()=>{try{if(Object.keys(draft).length)storage.setItem(name,JSON.stringify(draft));else storage.removeItem(name);}catch{}};
      for(const field of data.fields)if(draft[field] && draft[field].value.trim()===data.saved[field])delete draft[field];
      write();
      const report=()=>{
        const ack=data.ack||{};
        if(Object.keys(draft).length && (Object.keys(draft).length!==Object.keys(ack).length || Object.keys(draft).some(f=>draft[f].value!==ack[f]?.value || draft[f].base!==ack[f]?.base)))setStateValue('recovered',draft);
      };
      report();
      const capture=event=>{
        if(!(event.target instanceof Element))return;
        for(const field of data.fields)if(event.target.closest('.st-key-mfy_edit_'+data.id+'_'+field)){
          const value=event.target.value;
          if(typeof value!=='string')return;
          if(value.trim()===data.saved[field])delete draft[field];
          else draft[field]={value,base:draft[field]?.base ?? data.saved[field]};
          write();return;
        }
      };
      const logout=event=>{
        if(event.target instanceof Element && event.target.closest('.st-key-logout'))try{
          for(const key of Object.keys(storage))if(key.startsWith('mfy-borrador:'+data.user+':') || key.startsWith('mfy-cotizacion:'+data.user+':') || key==='mfy-solicitud:'+data.user)storage.removeItem(key);
        }catch{}
      };
      document.addEventListener('input',capture);document.addEventListener('change',capture);document.addEventListener('click',logout);
      window.addEventListener('online',report);
      return ()=>{document.removeEventListener('input',capture);document.removeEventListener('change',capture);document.removeEventListener('click',logout);window.removeEventListener('online',report);};
    }
    """)
    resultado=puente(data={"user":repo.user.id,"id":caso_id,"fields":list(TEXTOS),
        "saved":{f:str(borrador["ultimo"].get(f) or "") for f in TEXTOS},"ack":borrador.get("recuperacion_ack",{})},
        default={"recovered":{}},on_recovered_change=lambda:None,key=f"draft_local_{caso_id}",height=0)
    recuperado=resultado.recovered or {}
    if not isinstance(recuperado,dict) or recuperado==borrador.get("recuperacion_ack"):return
    borrador["recuperacion_ack"]=json.loads(json.dumps(recuperado))
    for campo,entrada in recuperado.items():
        if campo not in TEXTOS or campo in borrador["pendientes"] or not isinstance(entrada,dict):continue
        valor=entrada.get("value")
        if not isinstance(valor,str) or len(valor)>10000:continue
        editar(borrador,campo,valor)
        borrador["pendientes"][campo]["base"]=entrada.get("base")
        st.session_state[f"mfy_edit_{caso_id}_{campo}"]=valor


def limpiar_borrador_al_salir(usuario_id):
    """Se monta en el marco común, incluso si se sale desde el Dashboard."""
    puente=component("mfy_limpiar_borrador",html="<span aria-hidden='true'></span>",js="""
    export default function({data}) {
      const clear=event=>{
        if(!(event.target instanceof Element) || !event.target.closest('.st-key-logout'))return;
        try{const storage=window.sessionStorage;
          for(const key of Object.keys(storage))if(key.startsWith('mfy-borrador:'+data.user+':') || key.startsWith('mfy-cotizacion:'+data.user+':') || key==='mfy-solicitud:'+data.user)storage.removeItem(key);
        }catch{}
      };
      document.addEventListener('click',clear);
      return ()=>document.removeEventListener('click',clear);
    }
    """)
    puente(data={"user":usuario_id},key="mfy_limpiar_borrador",height=0)
