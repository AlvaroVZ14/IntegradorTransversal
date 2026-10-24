import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../utils/en_vivo.js',import.meta.url),'utf8').replace('export default function','(function')+')';
const window=new EventTarget();
let now=120000,timer,cleared=0;
const node={classList:{toggle(name,value){node.offline=value;}},setAttribute(){},textContent:'',title:''};
const navigator={onLine:true};
class EventData extends Event{constructor(name,{detail}){super(name);this.detail=detail;}}
const run=vm.runInNewContext(source,{window,navigator,CustomEvent:EventData,Date:{now:()=>now},
    setInterval:(fn,ms)=>{assert.equal(ms,1000);timer=fn;return 1;},clearInterval:()=>cleared++});
const parentElement={querySelector:()=>node};
const cleanup=run({data:{vista:'dashboard',fecha:120,conectado:true},parentElement});
assert.match(node.textContent,/En vivo/);
now=132000;timer();assert.match(node.textContent,/hace 12 s/);
navigator.onLine=false;window.dispatchEvent(new Event('offline'));
assert.match(node.textContent,/Sin conexión/);assert.equal(node.offline,true);
navigator.onLine=true;
run({data:{vista:'dashboard',publicar:true,fecha:140,conectado:true},parentElement:{querySelector:()=>({})}});
assert.match(node.textContent,/En vivo/);assert.equal(node.offline,false);
run({data:{vista:'dashboard',publicar:true,fecha:140,conectado:false},parentElement:{querySelector:()=>({})}});
assert.match(node.textContent,/Sin conexión/);
cleanup();assert.equal(cleared,1);
console.log('En vivo navegador: reloj local, offline, recuperación, publicación y limpieza OK.');
