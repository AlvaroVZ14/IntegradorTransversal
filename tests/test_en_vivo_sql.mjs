// PostgreSQL efímero, únicamente datos ficticios.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const admin='00000000-0000-0000-0000-000000000001',cliente='00000000-0000-0000-0000-000000000002';
const as=async(id,role='authenticated')=>{
 await db.exec('reset role;set role '+role);
 await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);
};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const name of (await readdir(dir)).filter(n=>n.endsWith('.sql')).sort())await db.exec(await readFile(new URL(name,dir),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[admin,cliente]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(admin);
 let datos=(await db.query("select mf_lectura_en_vivo('dashboard') r")).rows[0].r;
 assert.deepEqual(datos,{casos:[],ventas:[]});
 await db.exec(`insert into mf_casos(cliente,contacto,email,servicio,tematica,participantes,horas,modalidad)
 select 'Empresa Ficticia '||g,'Camila Ficticia','cliente@example.test','Coaching individual','Liderazgo',1,2,'Online'
 from generate_series(1,1001) g`);
 datos=(await db.query("select mf_lectura_en_vivo('hoy') r")).rows[0].r;
 assert.equal(datos.casos.length,1001);
 assert.deepEqual(Object.keys(datos).sort(),['casos','configuracion','cotizaciones','envios','eventos','ventas']);
 assert.ok('fecha_realizacion' in datos.casos[0]);
 assert.deepEqual(Object.keys((await db.query("select mf_lectura_en_vivo('casos') r")).rows[0].r),['casos']);
 await assert.rejects(db.query("select mf_lectura_en_vivo('otra')"));
 const definicion=(await db.query("select prosecdef,provolatile from pg_proc where proname='mf_lectura_en_vivo'")).rows[0];
 assert.equal(definicion.prosecdef,false);assert.equal(definicion.provolatile,'s');
 await as(cliente);
 for(const vista of ['casos','dashboard','hoy'])await assert.rejects(db.query('select mf_lectura_en_vivo($1)',[vista]));
 assert.equal((await db.query('select * from mf_casos')).rows.length,0);
 await as('','anon');await assert.rejects(db.query("select mf_lectura_en_vivo('dashboard')"));
 await db.exec('reset role');await db.exec(await readFile(new URL('../supabase/rollback/202610230001_lectura_en_vivo.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,1001);
 console.log('En vivo SQL: snapshot, 1001 filas, vistas, RLS, admin/cliente/anon y rollback OK.');
}finally{await db.close();}
