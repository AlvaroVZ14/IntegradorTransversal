// PostgreSQL efímero; jamás escribe en Supabase real.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {prepararStorage} from './storage_fixture.mjs';
const db=new PGlite();
const admin='00000000-0000-0000-0000-000000000001',cliente='00000000-0000-0000-0000-000000000002';
const uid=n=>'20000000-0000-0000-0000-'+String(n).padStart(12,'0');
const as=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 await prepararStorage(db);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const nombre of (await readdir(dir)).filter(n=>n.endsWith('.sql')).sort())await db.exec(await readFile(new URL(nombre,dir),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[admin,cliente]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(admin);
 let ultimo,version,operacion;
 for(const [i,motivo] of ['Precio','Fecha','Eligió a otro proveedor','Sin presupuesto','Otro','Eligió otra empresa'].entries()){
  const c=(await db.query(`insert into mf_casos(cliente,contacto,email,servicio,tematica,participantes,horas,modalidad)
   values('Empresa ficticia','Contacto ficticio','cliente@example.test','Coaching individual','Liderazgo',1,2,'Online') returning *`)).rows[0];
  const q=(await db.query('select * from mf_emitir_cotizacion($1,$2,$3,$4)',[c.id,c.version,uid(i*2+1),{
    base_clp:100000,descuento_pct:0,iva_pct:0,detalle:'Servicio ficticio',condiciones:'',valida_hasta:'2099-01-01',documento:{}}])).rows[0];
  version=(await db.query('select version from mf_casos where id=$1',[c.id])).rows[0].version;
  operacion=uid(i*2+2);
  const decidir=()=>db.query('select mf_decidir_cotizacion($1,$2,$3,$4,$5) r',[c.id,q.id,version,operacion,{accion:'rechazar',motivo,nota:'Nota ficticia'}]);
  await as(cliente);await assert.rejects(decidir());await as('','anon');await assert.rejects(decidir());await as(admin);
  ultimo=(await decidir()).rows[0].r;
  assert.equal(ultimo.caso.estado,'Cancelado');assert.equal(ultimo.caso.motivo_rechazo,motivo+' · Nota ficticia');
  assert.equal(ultimo.evento.datos.motivo,motivo);
  assert.equal((await decidir()).rows[0].r.evento.id,ultimo.evento.id); // Reintento idempotente.
 }
 await db.exec('reset role');
 const previo=(await db.query('select count(*)::int n from mf_casos')).rows[0].n;
 await db.exec(await readFile(new URL('../supabase/rollback/202611050002_cotizaciones_fluidas.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,previo);
 assert.equal((await db.query("select count(*)::int n from mf_casos where motivo_rechazo like 'Sin presupuesto%'")).rows[0].n,1);
 console.log('Prompt 35 SQL: todos los motivos, nota, permisos admin/cliente/anon, reintento y rollback sin borrar datos OK.');
}finally{await db.close();}
