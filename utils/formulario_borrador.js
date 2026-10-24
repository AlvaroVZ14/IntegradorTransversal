export default function({data,setStateValue}) {
  const key=data.storageKey;
  const legacy=()=>{try{return JSON.parse(storage?.getItem(data.legacyKey)||'null');}catch{return null;}};
  let storage;try{storage=window.sessionStorage;}catch{}
  const load=()=>{try{return JSON.parse(storage?.getItem(key)||'null');}catch{return null;}};
  const write=d=>{try{storage?.setItem(key,JSON.stringify({...d,saved:Date.now()}));}catch{}};
  let draft=load()||legacy();
  if(!draft || typeof draft!=='object' || Array.isArray(draft) || !draft.values || typeof draft.values!=='object' || Array.isArray(draft.values))draft=null;
  if(draft && !draft.token)draft.token=data.token;
  if(draft && !draft.saved)draft.saved=Date.now();
  if(draft && (data.discard.includes(draft.id) || !draft.saved || Date.now()-draft.saved>86400000)){
    try{storage?.removeItem(key);storage?.removeItem(data.legacyKey);}catch{}draft=null;
  }
  const unsent={};
  if(draft?.id===data.id)for(const field of data.texts){
    const value=draft.values?.[field];
    if(typeof value==='string' && value!==data.ack?.[field] && value!==data.values[field])unsent[field]=value;
  }
  if(draft && draft.id!==data.id){setStateValue('recovered',draft);}
  else if(Object.keys(unsent).length){setStateValue('recovered',{...data,values:{...data.values,...unsent}});}
  else if(!data.discard.includes(data.id))write({id:data.id,token:data.token,step:data.step,values:{...data.values},canal_captacion:data.canal_captacion,canal_explicito:data.canal_explicito});

  // Solo atributos de los campos públicos: React conserva valores y callbacks.
  const decorate=()=>{
    const step=document.querySelector('.mfy-progress-'+data.step);
    if(step && window.__mfyFormStep!==data.step){
      if(window.__mfyFormStep!==undefined)step.scrollIntoView({block:'start',behavior:'instant'});
      window.__mfyFormStep=data.step;
    }
    if(data.focus && window.__mfyFormFocus!==data.focus.id){
      const target=document.querySelector('.st-key-'+data.prefix+data.focus.field+' input');
      if(target){target.focus({preventScroll:true});target.scrollIntoView({block:'center',behavior:'instant'});window.__mfyFormFocus=data.focus.id;}
    }
    for(const [field,type,mode,complete] of [
      ['email','email','email','email'],['telefono','tel','tel','tel'],
      ['contacto','text','text','name'],['cliente','text','text','organization'],
      ['rut','text','text','off'],['participantes',null,'numeric','off'],['horas',null,'decimal','off']]){
      const input=document.querySelector('.st-key-'+data.prefix+field+' input');
      // st.number_input formatea decimales localizados: cambiar su type borraría
      // valores con coma. inputMode pide el teclado sin modificar ese formato.
      if(input){if(type)input.type=type;input.inputMode=mode;input.autocomplete=complete;}
    }
    const honey=document.querySelector('.st-key-'+data.prefix+'sitio_confirmacion input');
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
      if(!event.target.closest('.st-key-'+data.prefix+field))continue;
      if(typeof event.target.value!=='string')return;
      const local=load();
      const next=local?.id===data.id?local:{id:data.id,token:data.token,step:data.step,values:{...data.values},canal_captacion:data.canal_captacion,canal_explicito:data.canal_explicito};
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
  const logout=e=>{if(e.target instanceof Element && e.target.closest('.st-key-logout')){try{storage?.removeItem(key);storage?.removeItem(data.legacyKey);}catch{}}};
  document.addEventListener('click',logout);
  return ()=>{
    observer.disconnect();document.removeEventListener('click',logout);document.removeEventListener('input',capture);document.removeEventListener('change',capture);
    window.visualViewport?.removeEventListener('resize',viewport);window.visualViewport?.removeEventListener('scroll',viewport);
    window.removeEventListener('resize',viewport);
  };
}
