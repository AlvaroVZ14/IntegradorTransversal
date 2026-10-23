export default function({data,setStateValue}) {
  let storage;
  try {storage=window.sessionStorage;} catch {return;}
  const key='mfy-solicitud:'+data.user;
  const load=()=>{try{return JSON.parse(storage.getItem(key)||'null');}catch{return null;}};
  const write=draft=>{try{storage.setItem(key,JSON.stringify(draft));}catch{}};
  let draft=load();
  if(draft && data.discard.includes(draft.id)){try{storage.removeItem(key);}catch{} draft=null;}
  if(!draft || typeof draft!=='object' || !draft.values || Array.isArray(draft.values))draft=null;
  // Recupera antes de sobrescribir con los valores iniciales de una nueva sesión.
  const unsent={};
  if(draft?.id===data.id)for(const field of data.texts){
    const local=draft.values[field];
    if(typeof local==='string' && local!==data.ackValues?.[field] && local!==data.values[field])unsent[field]=local;
  }
  if(draft && draft.id!==data.id && data.ack!==draft.id){
    setStateValue('recovered',draft);
  }else if(Object.keys(unsent).length){
    // No pierde un selector que acaba de llegar al servidor al recuperar texto.
    setStateValue('recovered',{id:data.id,values:{...data.values,...unsent}});
  }else{
    const local=draft?.values||{};
    draft={id:data.id,values:{...data.values}};
    // Los textos capturados antes de perder conexión siguen siendo la autoridad
    // hasta que Python los reconoce. Los controles restantes se respaldan al salir.
    for(const field of data.texts)if(local[field]!==undefined && local[field]!==data.ackValues?.[field])draft.values[field]=local[field];
    write(draft);
  }
  const report=()=>{const pending=load();if(pending)setStateValue('recovered',pending);};
  const capture=event=>{
    if(!(event.target instanceof Element))return;
    for(const field of data.texts){
      if(!event.target.closest('.st-key-request_'+field))continue;
      let value=event.target.value;
      if(typeof value!=='string')return;
      if(field==='rut'){
        const raw=value.replace(/[.\s-]/g,'').toUpperCase();
        if(/^\d{1,8}[\dK]$/.test(raw)){
          value=raw.slice(0,-1).replace(/\B(?=(\d{3})+(?!\d))/g,'.')+'-'+raw.slice(-1);
          // El setter nativo mantiene sincronizado el input controlado de React.
          const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set;
          if(setter && event.target.value!==value){
            const before=event.target.value.slice(0,event.target.selectionStart??event.target.value.length).replace(/[.\s-]/g,'').length;
            setter.call(event.target,value);
            let cursor=0,count=0;
            while(cursor<value.length && count<before){if(/[\dK]/.test(value[cursor]))count++;cursor++;}
            event.target.setSelectionRange?.(cursor,cursor);
            event.target.dispatchEvent(new Event('input',{bubbles:true}));
          }
        }
      }
      const saved=load();
      const next=saved?.id===data.id?saved:{id:data.id,values:{...data.values}};
      next.values[field]=value;write(next);return;
    }
  };
  const logout=event=>{if(event.target instanceof Element && event.target.closest('.st-key-logout'))try{storage.removeItem(key);}catch{}};
  document.addEventListener('input',capture);document.addEventListener('change',capture);document.addEventListener('click',logout);
  window.addEventListener('online',report);
  return ()=>{document.removeEventListener('input',capture);document.removeEventListener('change',capture);document.removeEventListener('click',logout);window.removeEventListener('online',report);};
}
