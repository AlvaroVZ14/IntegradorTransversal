export default function({data,setStateValue}) {
  let storage;try{storage=window.sessionStorage;}catch{return;}
  const name='mfy-cotizacion:'+data.user+':'+data.id;
  let pending={};try{pending=JSON.parse(storage.getItem(name)||'{}');}catch{}
  if(!pending || typeof pending!=='object' || Array.isArray(pending))pending={};
  let resets={};try{resets=JSON.parse(storage.getItem(name+':reset')||'{}');}catch{}
  for(const field of data.fields)if(data.reset?.[field] && data.reset[field]!==resets[field]){delete pending[field];resets[field]=data.reset[field];}
  try{storage.setItem(name+':reset',JSON.stringify(resets));}catch{}
  for(const field of Object.keys(pending))if(!data.fields.includes(field) || typeof pending[field]!=='string' || pending[field]===data.saved[field])delete pending[field];
  const write=()=>{try{if(Object.keys(pending).length)storage.setItem(name,JSON.stringify(pending));else storage.removeItem(name);}catch{}};
  const report=()=>{if(Object.keys(pending).length && JSON.stringify(pending)!==JSON.stringify(data.ack||{}))setStateValue('patch',{...pending});};
  write();report();let timer;
  const capture=event=>{
    if(!(event.target instanceof Element))return;
    for(const field of data.fields)if(event.target.closest('.st-key-cotedit_'+data.id+'_'+field)){
      if(typeof event.target.value!=='string')return;
      pending[field]=event.target.value;write();clearTimeout(timer);timer=setTimeout(report,700);return;
    }
  };
  const logout=event=>{if(event.target instanceof Element && event.target.closest('.st-key-logout'))try{storage.removeItem(name);storage.removeItem(name+':reset');}catch{}};
  document.addEventListener('input',capture);document.addEventListener('click',logout);window.addEventListener('online',report);
  return ()=>{clearTimeout(timer);document.removeEventListener('input',capture);document.removeEventListener('click',logout);window.removeEventListener('online',report);};
}
