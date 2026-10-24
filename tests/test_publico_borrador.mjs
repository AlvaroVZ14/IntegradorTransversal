import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const source=await readFile(new URL('../utils/publico_borrador.js',import.meta.url),'utf8');
const run=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
const memory=new Map(),listeners={},styles={};
globalThis.window={sessionStorage:{getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)},
 innerHeight:800,visualViewport:{height:500,offsetTop:0,addEventListener(){},removeEventListener(){}},addEventListener(){},removeEventListener(){}};
globalThis.document={body:{},querySelector:()=>null,documentElement:{style:{setProperty:(k,v)=>styles[k]=v}},
 addEventListener:(k,f)=>listeners[k]=f,removeEventListener(){}};
globalThis.MutationObserver=class{observe(){}disconnect(){}};
globalThis.Element=class{};
const base={id:'ficticio',token:'secreto-aleatorio-ficticio',step:1,values:{contacto:'',email:'',participantes:12},texts:['contacto','email'],ack:{},discard:[]};
let recovered;
const execute=data=>run({data,setStateValue:(k,v)=>recovered=v});
let cleanup=execute(base);
assert.equal(styles['--mfy-keyboard-bottom'],'300px');
const input=new Element();input.closest=s=>s==='.st-key-publico_contacto';input.value='Camila Ficticia';listeners.input({target:input});
cleanup();
execute({...base,id:'otra-sesion'});
assert.equal(recovered.values.contacto,'Camila Ficticia');assert.equal(recovered.token,base.token);
assert.ok(!('consentimiento' in recovered.values));assert.ok(!('password' in recovered.values));
recovered=null;execute({...base,values:{...base.values,contacto:'Camila Ficticia'},ack:{contacto:'Camila Ficticia'},step:2});
assert.equal(JSON.parse(memory.get('mfy-public-draft-v1')).step,2);
execute({...base,discard:[base.id]});assert.equal(memory.size,0);
execute(base);memory.set('mfy-public-draft-v1',JSON.stringify({...base,saved:Date.now()-86400001}));
recovered=null;execute({...base,id:'nueva'});assert.equal(recovered,null);
Object.defineProperty(window,'sessionStorage',{get(){throw Error('almacenamiento no disponible');}});
assert.doesNotThrow(()=>execute(base));
console.log('Borrador público JS: captura antes de blur, recarga, pasos, caducidad, limpieza y teclado OK.');
