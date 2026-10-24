export default function({data}) {
  if(!data.id || matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const seen=window.__mfyCelebraciones ||= new Set();
  if(seen.has(data.id))return;
  seen.add(data.id);
  const overlay=document.createElement('div');
  overlay.className='mfy-celebration';overlay.setAttribute('aria-hidden','true');
  for(let i=0;i<18;i++){
    const piece=document.createElement('i');piece.className='mfy-confetti-piece';overlay.appendChild(piece);
  }
  document.body.appendChild(overlay);
  const timer=setTimeout(()=>overlay.remove(),2000);
  return ()=>{clearTimeout(timer);overlay.remove();};
}
