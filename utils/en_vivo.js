export default function({data,parentElement}) {
  const event='mfy-live-'+data.vista;
  const store=window.__mfyLive ||= {};
  const node=parentElement.querySelector('.live');
  if(data.publicar){
    store[data.vista]=data;
    window.dispatchEvent(new CustomEvent(event,{detail:data}));
    node.hidden=true;
    return;
  }
  let state=store[data.vista]||data;
  const paint=()=>{
    const online=navigator.onLine!==false && state.conectado;
    node.classList.toggle('offline',!online);
    const age=Math.max(0,Math.floor(Date.now()/1000-(state.fecha||Date.now()/1000)));
    const label=state.falta_sql?'Actualización pendiente':!online?'Sin conexión · reintentando…':
      state.pausado?'Edición · actualización pausada':
      !state.fecha?'Preparando datos…':`En vivo · actualizado hace ${age<60?age+' s':Math.floor(age/60)+' min'}`;
    node.textContent=label;
    // Solo los cambios de conexión se anuncian; el reloj no se lee cada segundo.
    node.setAttribute('aria-live','off');
    node.title=state.falta_sql?'Falta activar la lectura automática en Supabase.':state.pausado?
      'El refresco se reanuda al cerrar la edición. El autoguardado sigue disponible.':
      'La información se actualiza automáticamente. Tus filtros y formularios se conservan.';
  };
  const receive=e=>{state=e.detail;paint();};
  window.addEventListener(event,receive);
  window.addEventListener('offline',paint);
  window.addEventListener('online',paint);
  paint();
  const timer=setInterval(paint,1000);
  return ()=>{
    clearInterval(timer);
    window.removeEventListener(event,receive);
    window.removeEventListener('offline',paint);
    window.removeEventListener('online',paint);
  };
}
