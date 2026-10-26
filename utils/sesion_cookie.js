export default function({data,setStateValue}) {
  const name=data.name;
  const legacy=data.legacy||[];
  const secure=location.protocol==='https:';
  const local=['localhost','127.0.0.1','::1'].includes(location.hostname);
  const read=(key=name)=>document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith(key+'='))?.slice(key.length+1)||'';
  const remove=key=>{document.cookie=key+'=; Path=/; Max-Age=0; SameSite=Strict'+(secure?'; Secure':'');};
  const clear=()=>{[name,...legacy].forEach(remove);};
  const exit=e=>{if(e.target instanceof Element && e.target.closest('.st-key-logout,.st-key-recover_login'))clear();};
  document.addEventListener('click',exit);
  if(data.action && data.id){
    let ok=false;
    try{
      if(data.action==='clear'){clear();ok=[name,...legacy].every(key=>!read(key));}
      else if(data.action==='save' && (secure||local)){
        const value=encodeURIComponent(JSON.stringify({refresh_token:data.token,expires:data.expires}));
        const seconds=Math.max(0,Math.min(604800,Math.floor(data.expires-Date.now()/1000)));
        document.cookie=name+'='+value+'; Path=/; Max-Age='+seconds+'; SameSite=Strict'+(secure?'; Secure':'');
        ok=read()===value;
        if(ok)legacy.forEach(remove);
      }
    }catch{}
    if(data.ack!==data.id)setStateValue('ack',{id:data.id,ok});
  }
  return ()=>document.removeEventListener('click',exit);
}
