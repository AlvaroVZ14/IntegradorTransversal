import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {prepararStorage} from './storage_fixture.mjs';
const db=new PGlite(),admin=randomUUID(),a=randomUUID(),b=randomUUID(),sinConfirmar=randomUUID();
const rol=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id||'']);};
const leer=async()=>(await db.query('select mf_mi_perfil() d')).rows[0].d;
const guardar=async(perfil,datos)=>(await db.query('select mf_guardar_mi_perfil($1,$2,$3) d',[datos,perfil.id,perfil.version])).rows[0].d;
const datos={telefono:'9 1234 5678',cargo:'Coordinadora',instagram:'@empresa_ficticia',linkedin:'linkedin.com/company/ficticia',facebook:'',sitio_web:'empresa.example.test',otra_red:'TikTok: @ficticia'};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 await prepararStorage(db);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const n of (await readdir(dir)).filter(n=>n.endsWith('.sql') && n<'202611030001').sort())await db.exec(await readFile(new URL(n,dir),'utf8'));
 for(const [id,email,nombre,confirmado] of [[admin,'admin@example.test','Administradora ficticia',true],[a,'a@example.test','Persona A',true],[b,'b@example.test','Persona B',true],[sinConfirmar,'a@example.test','Sin confirmar',false]])
  await db.query('insert into auth.users(id,email,raw_user_meta_data,email_confirmed_at) values($1,$2,$3,case when $4 then now() end)',[id,email,{nombre},confirmado]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await rol(admin);
 const base={cliente:'Empresa A ficticia',contacto:'Persona A',email:'a@example.test',servicio:'Coaching individual',tematicas:['Liderazgo'],modalidad:'Online',participantes:5,horas:2,telefono:'912345678',cargo:'Contacto',rut:'12.345.678-5'};
 const caso=(await db.query('select registrar_solicitud($1,$2) d',[randomUUID(),base])).rows[0].d.caso;
 const cotizacion=(await db.query('select * from mf_emitir_cotizacion($1,$2,$3,$4)',[caso.id,caso.version,randomUUID(),
  {base_clp:100000,descuento_pct:0,iva_pct:0,detalle:'Programa ficticio',condiciones:'',valida_hasta:'2099-01-01',documento:{}}])).rows[0];
 const incompleto=(await db.query('select registrar_solicitud($1,$2) d',[randomUUID(),{cliente:base.cliente,email:base.email,origen:'Llamada'}])).rows[0].d.caso;
 await db.exec('reset role');await db.exec(await readFile(new URL('202611030001_mi_perfil_cliente.sql',dir),'utf8'));
 await rol(a);let perfil=await leer();assert.equal(perfil.empresa,base.cliente);assert.equal(perfil.correo,'a@example.test');
 assert.ok(!('rut' in perfil));assert.equal(perfil.nombre,'Persona A');
 for(const extra of [{rut:'1-9'},{estado:'Cerrada'},{correo:'b@example.test'},{empresa:'Otra'},{nombre:'Otra persona'},{rol:'admin'},{id:b}])
  await assert.rejects(guardar(perfil,{...datos,...extra}));
 for(const malo of [{...datos,telefono:'mal'},{...datos,cargo:'x'.repeat(161)},{...datos,instagram:'javascript:alert(1)'},{...datos,telefono:123}])await assert.rejects(guardar(perfil,malo));
 const anterior=perfil;perfil=await guardar(perfil,datos);
 assert.equal(perfil.telefono,'+56 9 1234 5678');assert.equal(perfil.redes_sociales.instagram,'https://www.instagram.com/empresa_ficticia/');
 await assert.rejects(guardar(anterior,datos));assert.deepEqual(await leer(),perfil);
 assert.deepEqual((await db.query('select * from mf_casos')).rows,[]);assert.deepEqual((await db.query('select * from mf_empresas_redes')).rows,[]);
 await assert.rejects(db.query("update mf_empresas_redes set cargo='Ataque' returning id"));
 await rol(b);let nuevo=await leer();assert.equal(nuevo.id,null);assert.equal(nuevo.empresa,'');assert.equal(nuevo.telefono,'');
 await assert.rejects(guardar(perfil,datos));
 nuevo=await guardar(nuevo,{...datos,telefono:'987654321',instagram:'@empresa_b'});
 assert.equal(nuevo.correo,'b@example.test');assert.equal(nuevo.empresa,'');assert.equal((await leer()).redes_sociales.instagram,'https://www.instagram.com/empresa_b/');
 await rol(a);assert.equal((await leer()).redes_sociales.instagram,'https://www.instagram.com/empresa_ficticia/');
 await rol(sinConfirmar);await assert.rejects(leer());await assert.rejects(guardar(nuevo,datos));
 await rol(null,'anon');await assert.rejects(leer());await assert.rejects(guardar(nuevo,datos));
 await rol(admin);await assert.rejects(leer());
 let filas=(await db.query('select * from mf_casos order by numero')).rows;
 assert.equal(filas.length,2);assert.equal(filas[0].rut,base.rut);assert.equal(filas[0].estado,'Cotizado');
 assert.deepEqual((await db.query('select snapshot from mf_cotizaciones where id=$1',[cotizacion.id])).rows[0].snapshot,cotizacion.snapshot);
 for(const c of filas){assert.equal(c.telefono,perfil.telefono);assert.equal(c.cargo,perfil.cargo);assert.deepEqual(c.redes_sociales,perfil.redes_sociales);}
 assert.equal(filas[1].datos_incompletos,true);assert.equal(filas[1].estado,incompleto.estado);
 await db.query("update mf_casos set telefono='+56 9 1111 2222',cargo='Encargada',redes_sociales=$1 where id=$2",[{instagram:'@cambio_admin'},caso.id]);
 await rol(a);perfil=await leer();assert.equal(perfil.telefono,'+56 9 1111 2222');assert.equal(perfil.redes_sociales.instagram,'https://www.instagram.com/cambio_admin/');
 await db.query('select registrar_solicitud($1,$2)',[randomUUID(),{...base,telefono:'933344455',cargo:'Desde solicitud',redes_sociales:{instagram:'@desde_formulario'},consentimiento:true}]);
 perfil=await leer();assert.equal(perfil.cargo,'Desde solicitud');assert.equal(perfil.redes_sociales.instagram,'https://www.instagram.com/desde_formulario/');
 await rol(b);assert.equal((await leer()).redes_sociales.instagram,'https://www.instagram.com/empresa_b/');
 const idVacio=nuevo.id;
 await db.query('select registrar_solicitud($1,$2)',[randomUUID(),{...base,cliente:'Empresa B ficticia',email:'b@example.test',telefono:'987654321',cargo:'Desde B',consentimiento:true,redes_sociales:{instagram:'@empresa_b'}}]);
 nuevo=await leer();assert.equal(nuevo.id,idVacio);assert.equal(nuevo.empresa,'Empresa B ficticia');
 console.log('Mi perfil SQL OK: A/B aislados, sin confirmar, sin registro, whitelist, concurrencia, sincronización de casos completos/incompletos, edición administrativa y formulario.');
}finally{await db.close();}
