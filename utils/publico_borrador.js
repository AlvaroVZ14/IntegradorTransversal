export default function({data,setStateValue}) {
  const key='mfy-public-draft-v1';
  let storage;try{storage=window.sessionStorage;}catch{}
  const load=()=>{try{return JSON.parse(storage?.getItem(key)||'null');}catch{return null;}};
  const write=d=>{try{storage?.setItem(key,JSON.stringify({...d,saved:Date.now()}));}catch{}};
  let draft=load();
  if(draft && (data.discard.includes(draft.id) || !draft.saved || Date.now()-draft.saved>86400000)){
    try{storage?.removeItem(key);}catch{}draft=null;
  }
  const unsent={};
  if(draft?.id===data.id)for(const field of data.texts){
    const value=draft.values?.[field];
    if(typeof value==='string' && value!==data.ack?.[field] && value!==data.values[field])unsent[field]=value;
  }
  if(draft && draft.id!==data.id){setStateValue('recovered',draft);}
  else if(Object.keys(unsent).length){setStateValue('recovered',{...data,values:{...data.values,...unsent}});}
  else if(!data.discard.includes(data.id))write({id:data.id,token:data.token,step:data.step,values:{...data.values}});

  // Solo atributos de los campos públicos: React conserva valores y callbacks.
  const decorate=()=>{
    const step=document.querySelector('.mfy-progress-'+data.step);
    if(step && window.__mfyPublicStep!==data.step){
      if(window.__mfyPublicStep!==undefined)step.scrollIntoView({block:'start',behavior:'instant'});
      window.__mfyPublicStep=data.step;
    }
    if(data.focus && window.__mfyPublicFocus!==data.focus.id){
      const target=document.querySelector('.st-key-publico_'+data.focus.field+' input');
      if(target){target.focus({preventScroll:true});target.scrollIntoView({block:'center',behavior:'instant'});window.__mfyPublicFocus=data.focus.id;}
    }
    for(const [field,type,mode,complete] of [
      ['email','email','email','email'],['telefono','tel','tel','tel'],
      ['contacto','text','text','name'],['cliente','text','text','organization'],
      ['rut','text','text','off'],['participantes',null,'numeric','off'],['horas',null,'decimal','off']]){
      const input=document.querySelector('.st-key-publico_'+field+' input');
      // st.number_input formatea decimales localizados: cambiar su type borraría
      // valores con coma. inputMode pide el teclado sin modificar ese formato.
      if(input){if(type)input.type=type;input.inputMode=mode;input.autocomplete=complete;}
    }
    const honey=document.querySelector('.st-key-publico_sitio_confirmacion input');
    if(honey){honey.tabIndex=-1;honey.autocomplete='off';honey.setAttribute('aria-hidden','true');}
  };
  const viewport=()=>{
    const v=window.visualViewport;
    const bottom=v?Math.max(0,window.innerHeight-v.height-v.offsetTop):0;
    document.documentElement.style.setProperty('--mfy-keyboard-bottom',bottom+'px');
  };
  const capture=event=>{
    if(!(event.target instanceof Element))return;
    for(const field of data.texts){
      if(!event.target.closest('.st-key-publico_'+field))continue;
      if(typeof event.target.value!=='string')return;
      const local=load();
      const next=local?.id===data.id?local:{id:data.id,token:data.token,step:data.step,values:{...data.values}};
      next.values[field]=event.target.value;write(next);return;
    }
  };
  const observer=new MutationObserver(decorate);
  observer.observe(document.body,{childList:true,subtree:true});
  decorate();viewport();
  document.addEventListener('input',capture);document.addEventListener('change',capture);
  window.visualViewport?.addEventListener('resize',viewport);
  window.visualViewport?.addEventListener('scroll',viewport);
  window.addEventListener('resize',viewport);
  return ()=>{
    observer.disconnect();document.removeEventListener('input',capture);document.removeEventListener('change',capture);
    window.visualViewport?.removeEventListener('resize',viewport);window.visualViewport?.removeEventListener('scroll',viewport);
    window.removeEventListener('resize',viewport);
  };
}
