import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const fuente=await readFile(new URL('../utils/mensaje_listo.js',import.meta.url),'utf8');
const iniciar=(await import('data:text/javascript,'+encodeURIComponent(fuente))).default;
for(const modo of ['normal','respaldo','bloqueado']){
  let click;const estado={};let copiado='';let area;
  const button={textContent:'',setAttribute(){},focus(){},addEventListener(_,f){click=f;},removeEventListener(){}};
  const parentElement={querySelector(){return button;},appendChild(a){area=a;}};
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{clipboard:{async writeText(t){if(modo!=='normal')throw Error('Bloqueado');copiado=t;}}}});
  globalThis.document={createElement(){return {setAttribute(){},select(){},setSelectionRange(){},remove(){}};},execCommand(){if(modo==='respaldo'){copiado=area.value;return true;}return false;}};
  const limpiar=iniciar({parentElement,data:{text:'https://portal.example.test/?vista=solicitud',label:'Copiar enlace',confirmation:'Enlace copiado'},setStateValue(k,v){estado[k]=v;}});
  await click();
  if(modo==='bloqueado'){assert.equal(estado.fallo,true);assert.equal(estado.copiado,undefined);}
  else{assert.equal(estado.copiado,copiado);assert.equal(button.textContent,'Enlace copiado');assert.equal(estado.fallo,false);}
  limpiar();
}
console.log('OK: copiar normal, respaldo y bloqueo sin confirmaciones falsas.');
