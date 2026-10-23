// Prueba transaccional en PostgreSQL efímero; nunca usa Supabase real.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const owner='00000000-0000-0000-0000-000000000001',client='00000000-0000-0000-0000-000000000002';
const caseId='10000000-0000-0000-0000-000000000001';
const as=async id=>{await db.exec('reset role;set role authenticated');await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon;grant execute on function auth.uid() to authenticated,anon;`);
 for(const name of ['202610150001_gestion_mente_futuro.sql','202610210001_cliente_solo_solicitud.sql','202610220001_deshacer_aceptacion.sql'])
  await db.exec(await readFile(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[owner,client]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[owner]);
 await as(owner);
 await db.query(`insert into mf_casos(id,cliente,contacto,email,servicio,tematica,participantes,horas,modalidad)
 values($1,'Fundación Horizonte','Camila Rojas','camila@example.test','Coaching individual','Liderazgo',1,1,'Online')`,[caseId]);
 const data={base_clp:420000,descuento_pct:0,iva_pct:0,detalle:'Sesión ficticia',condiciones:'Prueba',valida_hasta:'2099-01-01'};
 const quote=(await db.query('select * from mf_emitir_cotizacion($1,1,$2,$3)',[caseId,'20000000-0000-0000-0000-000000000001',data])).rows[0];
 const sell=async()=> (await db.query("select * from mf_registrar_venta($1,$2,current_date,'Pendiente')",[caseId,quote.id])).rows[0];
 const undo=async sale=>db.query('select * from mf_deshacer_aceptacion($1,$2)',[sale.id,sale.caso_version_aceptada]);
 let sale=await sell();
 assert.equal(sale.estado_caso_anterior,'Cotizado');
 await as(client);await assert.rejects(undo(sale));
 await as(owner);await undo(sale);
 assert.equal((await db.query('select estado from mf_casos where id=$1',[caseId])).rows[0].estado,'Cotizado');
 assert.equal((await db.query('select count(*)::int n from mf_ventas')).rows[0].n,0);
 assert.equal((await db.query('select count(*)::int n from mf_cotizaciones')).rows[0].n,1);
 sale=await sell();
 await db.exec('reset role');
 await db.exec('alter table mf_ventas disable trigger mf_version_venta');
 await db.query("update mf_ventas set created_at=now()-interval '11 seconds' where id=$1",[sale.id]);
 await db.exec('alter table mf_ventas enable trigger mf_version_venta');
 await as(owner);await assert.rejects(undo(sale));
 await db.exec('reset role');
 await db.exec('alter table mf_ventas disable trigger mf_version_venta');
 await db.query("update mf_ventas set created_at=now() where id=$1",[sale.id]);
 await db.exec('alter table mf_ventas enable trigger mf_version_venta');
 await as(owner);await db.query("update mf_casos set contacto='Daniela Soto' where id=$1",[caseId]);
 await assert.rejects(undo(sale));
 assert.equal((await db.query('select count(*)::int n from mf_ventas')).rows[0].n,1);
 await db.exec('reset role');
 await db.exec(await readFile(new URL('../supabase/rollback/202610220001_deshacer_aceptacion.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_ventas')).rows[0].n,1);
 console.log('Deshacer aceptación: atomicidad, permisos, plazo, concurrencia y reversión aprobados.');
}finally{await db.close();}
