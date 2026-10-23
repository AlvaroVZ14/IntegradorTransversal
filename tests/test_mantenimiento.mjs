// PostgreSQL efímero: no modifica el proyecto real.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const admin='00000000-0000-0000-0000-000000000001',cliente='00000000-0000-0000-0000-000000000002';
const as=async(id,role='authenticated')=>{
 await db.exec('reset role;set role '+role);
 await db.query("select set_config('request.jwt.claim.sub',$1,false),set_config('request.jwt.claim.role',$2,false)",[id,role]);
};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 for(const name of ['202610150001_gestion_mente_futuro.sql','202610210001_cliente_solo_solicitud.sql','202610220001_deshacer_aceptacion.sql','202610220002_solicitud_rapida.sql','202610220003_cotizador_asistido.sql','202610220004_hoy.sql','202610220005_mantenimiento.sql'])
  await db.exec(await readFile(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[admin,cliente]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(admin);
 let s=(await db.query('select mf_exportar_respaldo() r')).rows[0].r;
 assert.equal(Object.keys(s.tables).length,11);assert.equal(s.tables.mf_perfiles.rows.length,2);
 assert.ok(s.tables.mf_cotizaciones.columns.find(c=>c.name==='total_clp').generated);
 assert.equal(s.tables.mf_casos.rows.length,0);
 await db.exec(`insert into mf_casos(cliente,contacto,email,servicio,tematica,participantes,horas,modalidad)
 select 'Empresa Ficticia '||g,'Camila Ficticia','cliente@example.test','Coaching individual','Liderazgo',1,2,'Online'
 from generate_series(1,1001) g`);
 s=(await db.query('select mf_exportar_respaldo() r')).rows[0].r;
 assert.equal(s.tables.mf_casos.rows.length,1001); // Sin truncamiento REST a 1000.
 await assert.rejects(db.query("insert into mf_mantenimiento(tipo,estado,run_url) values('respaldo','ok','https://github.com/ficticio/mantenimiento/actions/runs/1')"));
 await as(cliente);assert.equal((await db.query('select * from mf_mantenimiento')).rows.length,0);
 await assert.rejects(db.query('select mf_exportar_respaldo()'));
 // NULL en los claims NO puede saltarse la autorización del SECURITY DEFINER.
 await db.query("select set_config('request.jwt.claim.role','',false)");
 await assert.rejects(db.query('select mf_exportar_respaldo()'));
 await as('', 'anon');await assert.rejects(db.query('select mf_exportar_respaldo()'));
 await as('', 'service_role');
 s=(await db.query('select mf_exportar_respaldo() r')).rows[0].r;assert.equal(s.tables.mf_perfiles.rows.length,2);
 await assert.rejects(db.query("insert into mf_mantenimiento(tipo,estado,run_url) values('respaldo','ok','https://github.com/ficticio/mantenimiento/actions/runs/1')"));
 await db.query("insert into mf_mantenimiento(tipo,estado,run_url,artefacto_id,sha256) values('respaldo','ok','https://github.com/ficticio/mantenimiento/actions/runs/1','123',$1)",['a'.repeat(64)]);
 await as(admin);assert.equal((await db.query('select * from mf_mantenimiento')).rows.length,1);
 await as(cliente);assert.equal((await db.query('select * from mf_mantenimiento')).rows.length,0);
 await db.exec('reset role');await db.exec(await readFile(new URL('../supabase/rollback/202610220005_mantenimiento.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_perfiles')).rows[0].n,2);
 console.log('Mantenimiento SQL: snapshot, tablas reales, columnas generadas, RLS, admin, cliente, anon, servidor y rollback aprobados.');
}finally{await db.close();}
