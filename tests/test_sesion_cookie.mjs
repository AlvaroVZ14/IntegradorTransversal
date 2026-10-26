import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../utils/sesion_cookie.js',import.meta.url),'utf8');
const factory=new Function('document','location','Element',source.replace('export default function','return function'));
const cookies=new Map(),writes=[];let listeners=new Map();
const document={get cookie(){return [...cookies].map(([k,v])=>k+'='+v).join('; ');},set cookie(value){writes.push(value);const [key,...parts]=value.split(';')[0].split('=');if(value.includes('Max-Age=0'))cookies.delete(key);else cookies.set(key,parts.join('='));},
 addEventListener:(k,f)=>listeners.set(k,f),removeEventListener:k=>listeners.delete(k)};
class Element{closest(){return true;}}
let ack;
const render=factory(document,{protocol:'https:',hostname:'ficticia.streamlit.app'},Element);
const expires=Date.now()/1000+604800;
const base={name:'mfy_session_refresh_v2',legacy:['mfy_admin_refresh_v1']};
cookies.set('mfy_admin_refresh_v1','LEGACY_FICTICIO');
let cleanup=render({data:{...base,action:'save',id:'1',token:'REFRESH_FICTICIO',expires},setStateValue:(_,v)=>ack=v});
const last=writes.find(v=>v.startsWith(base.name+'=')&&!v.includes('Max-Age=0'));
assert.equal(ack.ok,true);assert.ok(last.includes('Secure'));assert.ok(last.includes('SameSite=Strict'));assert.ok(last.includes('Path=/'));
assert.equal(cookies.has('mfy_admin_refresh_v1'),false);
assert.ok(!last.includes('Domain='));assert.ok(last.includes('Max-Age=604799')||last.includes('Max-Age=604800'));
cleanup();assert.equal(listeners.size,0);
cookies.set('mfy_admin_refresh_v1','LEGACY_FICTICIO');
cleanup=render({data:{...base,action:'clear',id:'2'},setStateValue:(_,v)=>ack=v});
assert.equal(cookies.size,0);assert.equal(ack.ok,true);cleanup();
render({data:{...base,action:'save',id:'3',token:'REFRESH_FICTICIO',expires},setStateValue:(_,v)=>ack=v});
listeners.get('click')({target:new Element()});assert.equal(cookies.size,0);
const insecure=factory(document,{protocol:'http:',hostname:'ficticia.example.test'},Element);
insecure({data:{...base,action:'save',id:'4',token:'REFRESH_FICTICIO',expires},setStateValue:(_,v)=>ack=v});
assert.equal(ack.ok,false);assert.equal(cookies.size,0);
console.log('Cookie: Secure, SameSite, siete dias, migración, cierre, limpieza y bloqueo HTTP externo aprobados.');
