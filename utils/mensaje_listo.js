export default function({parentElement,data,setStateValue}) {
  const button=parentElement.querySelector('button');
  button.textContent=data.label;
  const copy=async()=>{
    let ok=false;
    try{await navigator.clipboard.writeText(data.text);ok=true;}catch{
      const area=document.createElement('textarea');area.value=data.text;area.readOnly=true;
      area.setAttribute('aria-label','Texto para copiar');parentElement.appendChild(area);
      area.select();area.setSelectionRange(0,area.value.length);
      try{ok=document.execCommand('copy');}catch{}finally{area.remove();button.focus();}
    }
    if(ok){button.textContent=data.confirmation;button.setAttribute('aria-label',data.confirmation);setStateValue('fallo',false);setStateValue('copiado',data.text);}
    else setStateValue('fallo',true);
  };
  button.addEventListener('click',copy);return()=>button.removeEventListener('click',copy);
}
