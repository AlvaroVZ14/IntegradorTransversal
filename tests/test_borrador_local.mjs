// Simula el componente de respaldo: no abre navegador ni utiliza datos reales.
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../utils/borrador_local.py',import.meta.url),'utf8');
const js=source.match(/js="""([\s\S]*?)"""/)[1];
const create=new Function('window','document','Element',js.replace('export default function(','return function('));
const storage={};
Object.defineProperties(storage,{
 getItem:{value:key=>storage[key]??null},
 setItem:{value:(key,value)=>storage[key]=value},
 removeItem:{value:key=>delete storage[key]},
});
const docEvents={},windowEvents={},reports=[];
const document={addEventListener:(k,v)=>docEvents[k]=v,removeEventListener:k=>delete docEvents[k]};
const window={sessionStorage:storage,addEventListener:(k,v)=>windowEvents[k]=v,removeEventListener:k=>delete windowEvents[k]};
class Element{
 constructor(field,value){this.field=field;this.value=value;}
 closest(selector){return selector.endsWith(this.field)?this:null;}
}
const data={user:'admin-ficticio',id:'caso-ficticio',fields:['contacto'],saved:{contacto:'Camila Rojas'},ack:{}};
const mount=()=>create(window,document,Element)({data,setStateValue:(key,value)=>reports.push(JSON.parse(JSON.stringify(value)))});
let cleanup=mount();
docEvents.input({target:new Element('contacto','Daniela Soto')});
assert.equal(reports.length,0); // Escribir no exige WebSocket ni reenvía cada tecla.
assert.equal(JSON.parse(storage['mfy-borrador:admin-ficticio:caso-ficticio']).contacto.value,'Daniela Soto');
cleanup();cleanup=mount(); // Un refresco recupera el texto de esta pestaña.
assert.equal(reports.length,1);
assert.equal(reports[0].contacto.base,'Camila Rojas');
data.ack=reports[0];cleanup();cleanup=mount();
assert.equal(reports.length,1); // Sin bucle de rerun por la misma recuperación.
data.saved.contacto='Daniela Soto';cleanup();cleanup=mount();
assert.equal(storage['mfy-borrador:admin-ficticio:caso-ficticio'],undefined); // Confirmado en Supabase.
docEvents.input({target:new Element('contacto','Francisca Ríos')});
storage['mfy-borrador:otra-cuenta:otro-caso']='{}';
docEvents.click({target:new Element('logout','')});
assert.equal(storage['mfy-borrador:admin-ficticio:caso-ficticio'],undefined);
assert.equal(storage['mfy-borrador:otra-cuenta:otro-caso'],'{}');
cleanup();assert.equal(Object.keys(docEvents).length,0);
const globalJs=[...source.matchAll(/js="""([\s\S]*?)"""/g)][1][1];
const globalMount=new Function('window','document','Element',globalJs.replace('export default function(','return function('));
storage['mfy-borrador:admin-ficticio:caso-ficticio']='{}';
const globalCleanup=globalMount(window,document,Element)({data});
docEvents.click({target:new Element('logout','')});
assert.equal(storage['mfy-borrador:admin-ficticio:caso-ficticio'],undefined);
globalCleanup();
console.log('Respaldo local: escritura offline, recuperación, reconocimiento y cierre de sesión aprobados.');
