// Simula el puente de borrador. No reemplaza una revisión visual del navegador.
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../utils/solicitud_borrador.js',import.meta.url),'utf8');
const create=new Function('window','document','Element','HTMLInputElement','Event',source.replace('export default function(','return function('));
const storage={};
Object.defineProperties(storage,{getItem:{value:k=>storage[k]??null},setItem:{value:(k,v)=>storage[k]=v},removeItem:{value:k=>delete storage[k]}});
const doc={},win={},reports=[];
const document={addEventListener:(k,v)=>doc[k]=v,removeEventListener:k=>delete doc[k]};
const window={sessionStorage:storage,addEventListener:(k,v)=>win[k]=v,removeEventListener:k=>delete win[k]};
class Element{
 constructor(field,value){this.field=field;this.value=value;this.selectionStart=value.length;}
 closest(selector){return selector.endsWith(this.field)?this:null;}
 dispatchEvent(){doc.input({target:this});}
 setSelectionRange(a){this.selectionStart=a;}
}
class Input{}
Object.defineProperty(Input.prototype,'value',{set(v){this.value=v;}});
const data={user:'cliente-ficticio',id:'borrador-1',values:{cliente:'',email:'cuenta@example.test',rut:'',participantes:12},
 texts:['cliente','email','rut'],discard:[],ackValues:{cliente:'',email:'cuenta@example.test',rut:''}};
const mount=()=>create(window,document,Element,Input,Event)({data,setStateValue:(k,v)=>reports.push(structuredClone(v))});
let cleanup=mount();
doc.input({target:new Element('cliente','Fundación Horizonte')});
assert.equal(JSON.parse(storage['mfy-solicitud:cliente-ficticio']).values.cliente,'Fundación Horizonte');
assert.equal(reports.length,0);
const rut=new Element('rut','123456785');doc.input({target:rut});
assert.equal(rut.value,'12.345.678-5');
assert.equal(JSON.parse(storage['mfy-solicitud:cliente-ficticio']).values.rut,'12.345.678-5');
cleanup();data.id='borrador-2';cleanup=mount();
assert.equal(reports.length,1);assert.equal(reports[0].id,'borrador-1');
assert.equal(reports[0].values.participantes,12);
cleanup();data.id=reports[0].id;data.values=reports[0].values;data.ackValues={...data.values};cleanup=mount();
assert.equal(reports.length,1); // Sin bucle de recuperación.
// El servidor normaliza o precarga sin que una copia local antigua lo deshaga.
cleanup();data.values={...data.values,cliente:'Fundación Horizonte Norte'};cleanup=mount();
assert.equal(JSON.parse(storage['mfy-solicitud:cliente-ficticio']).values.cliente,'Fundación Horizonte Norte');
win.online();assert.equal(reports.length,2);
doc.input({target:new Element('cliente','Texto sin salir del campo')});
cleanup();data.values={...data.values,participantes:20};cleanup=mount();
assert.equal(reports.at(-1).values.cliente,'Texto sin salir del campo');
assert.equal(reports.at(-1).values.participantes,20);
cleanup();data.discard=[data.id];data.id='nuevo';data.values={cliente:'',rut:''};cleanup=mount();
assert.equal(JSON.parse(storage['mfy-solicitud:cliente-ficticio']).id,'nuevo');
doc.click({target:new Element('logout','')});assert.equal(storage['mfy-solicitud:cliente-ficticio'],undefined);
cleanup();assert.equal(Object.keys(doc).length,0);
console.log('Borrador de solicitud: captura, recarga, valores, reconocimiento, limpieza y reconexión aprobados.');
