import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../utils/celebracion.js',import.meta.url),'utf8').replace('export default function','(function')+')';
let reduced=false,removed=0,added=0,callback,delay;
const overlays=[];
const document={createElement:tag=>({tag,children:[],setAttribute(){},appendChild(n){this.children.push(n);},remove(){removed++;}}),
  body:{appendChild(n){added++;overlays.push(n);}}};
const run=vm.runInNewContext(source,{window:{},document,matchMedia:()=>({matches:reduced}),
  setTimeout:(fn,ms)=>{callback=fn;delay=ms;return 1;},clearTimeout(){}});
const cleanup=run({data:{id:'venta-ficticia'}});
assert.equal(added,1);assert.equal(overlays[0].children.length,18);assert.equal(delay,2000);
run({data:{id:'venta-ficticia'}});assert.equal(added,1);
callback();assert.equal(removed,1);cleanup();
reduced=true;run({data:{id:'otra-venta-ficticia'}});assert.equal(added,1);
console.log('Celebración: 2 segundos, una vez por confirmación y movimiento reducido OK.');
