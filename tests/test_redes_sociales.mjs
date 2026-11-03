// SQL real en PostgreSQL efímero. Personas/empresas ficticias; no llama Supabase.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {prepararStorage} from './storage_fixture.mjs';
const db=new PGlite(), admin=randomUUID(),a=randomUUID(),b=randomUUID(),pendiente=randomUUID();
const rol=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id||'']);};
const base={cliente:'Empresa Horizonte Ficticia',contacto:'Contacto ficticio',email:'a@example.test',servicio:'Coaching individual',
 tematica:'Liderazgo',tematicas:['Liderazgo'],participantes:8,horas:2,modalidad:'Online',consentimiento:true};
const redes={instagram:'@empresa_norte',linkedin:'linkedin.com/company/empresa-norte',facebook:'facebook.com/empresa-norte',
 sitio_web:'empresa.example.test',otra_red:'TikTok: @empresa_norte'};
const registro=async(datos,id=randomUUID())=>(await db.query('select registrar_solicitud($1,$2) d',[id,datos])).rows[0].d;
const publico=async(datos,id=randomUUID(),token=randomUUID())=>(await db.query("select registrar_solicitud_publica($1,$2,$3,'') d",[id,token,datos])).rows[0].d;
const prefill=async(empresa='')=>(await db.query('select mf_mis_redes_empresa($1) d',[empresa])).rows[0].d;
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 await prepararStorage(db);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const n of (await readdir(dir)).filter(n=>n.endsWith('.sql') && n<'202611020004').sort())await db.exec(await readFile(new URL(n,dir),'utf8'));
 for(const [id,email,confirmado] of [[admin,'admin@example.test',true],[a,'a@example.test',true],[b,'b@example.test',true],[pendiente,'a@example.test',false]])
  await db.query("insert into auth.users(id,email,raw_user_meta_data,email_confirmed_at) values($1,$2,'{\"nombre\":\"Persona Ficticia\"}',case when $3 then now() end)",[id,email,confirmado]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await rol(admin);const antiguo=await registro(base);
 await db.exec('reset role');await db.exec(await readFile(new URL('202611020004_redes_sociales.sql',dir),'utf8'));
 await rol(admin);
 const historico=(await db.query('select * from mf_casos where id=$1',[antiguo.caso.id])).rows[0];
 assert.equal(historico.version,antiguo.caso.version);assert.equal(historico.cliente,antiguo.caso.cliente);assert.deepEqual(historico.redes_sociales,{});
 await rol(null,'anon');
 for(const datos of [{...base,consentimiento:false,redes_sociales:redes},...Object.keys(redes).flatMap(k=>[
  {...base,redes_sociales:{[k]:'javascript:alert(1)'}},{...base,redes_sociales:{[k]:'x'.repeat(201)}},
  {...base,redes_sociales:{[k]:['valor']}}]),{...base,redes_sociales:{rol:'admin'}},
  ...['https://instagram.com.evil.test/empresa','https://evil.test/@empresa','https://instagram.com/p/a'].map(v=>({...base,redes_sociales:{instagram:v}})),
  ...['no es un enlace','https://a..test','https://user:password@example.test','data:text/html,mal','ftp://empresa.test','https://empresa.test/%0a'].map(v=>({...base,redes_sociales:{sitio_web:v}}))])
  await assert.rejects(publico(datos));
 const id=randomUUID(),token=randomUUID();const r=await publico({...base,redes_sociales:redes},id,token);
 assert.deepEqual(Object.keys(r),['codigo']);assert.deepEqual(await publico({...base,redes_sociales:redes},id,token),r);
 await publico({...base,redes_sociales:{...redes,instagram:'empresa_dos'}});
 await publico({...base,email:'sinred@example.test',redes_sociales:{}});
 await assert.rejects(db.query('select * from mf_empresas_redes'));await assert.rejects(db.query('select mf_mis_redes_empresa()'));
 await rol(admin);
 let actuales=(await db.query('select * from mf_empresas_redes')).rows;
 assert.equal(actuales.length,1);assert.equal(actuales[0].redes_sociales.instagram,'https://www.instagram.com/empresa_dos/');assert.equal(actuales[0].confirmadas,false);
 const guardado=(await db.query('select * from mf_casos where id=$1',[id])).rows[0];
 assert.equal(guardado.version,1);assert.equal(guardado.datos_incompletos,false);assert.equal(guardado.redes_sociales.instagram,'https://www.instagram.com/empresa_norte/');
 assert.equal(guardado.consentimiento_version,'2026-11-02-redes');
 const parcial=await registro({cliente:'Empresa por completar',origen:'Llamada',redes_sociales:{instagram:'@parcial'}});
 assert.ok(parcial.caso.datos_incompletos);assert.ok(!parcial.caso.datos_pendientes.includes('redes_sociales'));
 await rol(a);assert.deepEqual(await prefill(),{}); // Un envío anónimo no modifica un perfil verificado.
 await registro({...base,email:'b@example.test',redes_sociales:redes});
 let perfil=await prefill();assert.equal(perfil.redes_sociales.instagram,'https://www.instagram.com/empresa_norte/');
 assert.equal(perfil.redes_sociales.sitio_web,'https://empresa.example.test');
 assert.deepEqual((await db.query('select * from mf_empresas_redes')).rows,[]);
 await rol(b);assert.deepEqual(await prefill(),{});
 await rol(pendiente);assert.deepEqual(await prefill(),{});
 await rol(null,'anon');await publico({...base,redes_sociales:{instagram:'@suplantado'}});
 await rol(a);assert.equal((await prefill()).redes_sociales.instagram,'https://www.instagram.com/empresa_norte/');
 assert.deepEqual((await db.query("update mf_casos set redes_sociales='{}' returning id")).rows,[]);
 await rol(admin);await db.query("update mf_casos set redes_sociales=$1 where id=$2",[{instagram:'@editada',otra_red:'Red local - Empresa'},id]);
 assert.equal((await db.query('select redes_sociales from mf_casos where id=$1',[id])).rows[0].redes_sociales.instagram,'https://www.instagram.com/editada/');
 await assert.rejects(db.query('update mf_casos set redes_sociales=$1 where id=$2',[{sitio_web:'javascript:alert(1)'},id]));
 await rol(a);assert.equal((await prefill()).redes_sociales.instagram,'https://www.instagram.com/editada/');
 await registro({...base,cliente:'Segunda empresa ficticia',redes_sociales:{sitio_web:'segunda.example.test'}});
 assert.deepEqual(await prefill(),{});assert.equal((await prefill('Segunda empresa ficticia')).redes_sociales.sitio_web,'https://segunda.example.test');
 await registro({...base,redes_sociales:{}});assert.deepEqual((await prefill(base.cliente)).redes_sociales,{});
 await db.exec('reset role');assert.equal((await db.query('select count(*)::int n from auth.users')).rows[0].n,4);
 await rol(admin);const snapshot=(await db.query('select mf_exportar_respaldo() d')).rows[0].d;
 assert.ok(snapshot.tables.mf_empresas_redes.rows.length>0);
 await rol(a);await assert.rejects(db.query('select mf_exportar_respaldo()'));
 console.log('Redes SQL OK: normalización, 200 caracteres, esquemas peligrosos, públicas/internas/cliente, opcionales, idempotencia, deduplicación, edición, precarga privada y protección del registro confirmado.');
}finally{await db.close();}
