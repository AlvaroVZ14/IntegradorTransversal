export default function({data,setStateValue}) {
  const name='mfy_admin_refresh_v1';
  const secure=location.protocol==='https:';
  const local=['localhost','127.0.0.1','::1'].includes(location.hostname);
  const read=()=>document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith(name+'='))?.slice(name.length+1)||'';
  const clear=()=>{document.cookie=name+'=; Path=/; Max-Age=0; SameSite=Strict'+(secure?'; Secure':'');};
  const exit=e=>{if(e.target instanceof Element && e.target.closest('.st-key-logout,.st-key-recover_login'))clear();};
  document.addEventListener('click',exit);
  if(data.action && data.id){
    let ok=false;
    try{
      if(data.action==='clear'){clear();ok=!read();}
      else if(data.action==='save' && (secure||local)){
        const value=encodeURIComponent(JSON.stringify({refresh_token:data.token,expires:data.expires}));
        const seconds=Math.max(0,Math.min(604800,Math.floor(data.expires-Date.now()/1000)));
        document.cookie=name+'='+value+'; Path=/; Max-Age='+seconds+'; SameSite=Strict'+(secure?'; Secure':'');
        ok=read()===value;
      }
    }catch{}
    if(data.ack!==data.id)setStateValue('ack',{id:data.id,ok});
  }
  return ()=>document.removeEventListener('click',exit);
}
