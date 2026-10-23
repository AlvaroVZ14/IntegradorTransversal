import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../utils/sesion_cookie.js',import.meta.url),'utf8');
const factory=new Function('document','location','Element',source.replace('export default function','return function'));
let cookie='',last='',listeners=new Map();
const document={get cookie(){return cookie;},set cookie(value){last=value;cookie=value.includes('Max-Age=0')?'':value.split(';')[0];},
 addEventListener:(k,f)=>listeners.set(k,f),removeEventListener:k=>listeners.delete(k)};
class Element{closest(){return true;}}
let ack;
const render=factory(document,{protocol:'https:',hostname:'ficticia.streamlit.app'},Element);
const expires=Date.now()/1000+604800;
let cleanup=render({data:{action:'save',id:'1',token:'REFRESH_FICTICIO',expires},setStateValue:(_,v)=>ack=v});
assert.equal(ack.ok,true);assert.ok(last.includes('Secure'));assert.ok(last.includes('SameSite=Strict'));assert.ok(last.includes('Path=/'));
assert.ok(!last.includes('Domain='));assert.ok(last.includes('Max-Age=604799')||last.includes('Max-Age=604800'));
cleanup();assert.equal(listeners.size,0);
cleanup=render({data:{action:'clear',id:'2'},setStateValue:(_,v)=>ack=v});
assert.equal(cookie,'');assert.equal(ack.ok,true);cleanup();
render({data:{action:'save',id:'3',token:'REFRESH_FICTICIO',expires},setStateValue:(_,v)=>ack=v});
listeners.get('click')({target:new Element()});assert.equal(cookie,'');
const insecure=factory(document,{protocol:'http:',hostname:'ficticia.example.test'},Element);
insecure({data:{action:'save',id:'4',token:'REFRESH_FICTICIO',expires},setStateValue:(_,v)=>ack=v});
assert.equal(ack.ok,false);assert.equal(cookie,'');
console.log('Cookie: Secure, SameSite, siete dias, cierre, limpieza y bloqueo HTTP externo aprobados.');
