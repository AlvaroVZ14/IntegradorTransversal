// PostgreSQL efímero, cuentas y empresas ficticias; no conecta a Supabase.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const admin='00000000-0000-0000-0000-000000000001',client='00000000-0000-0000-0000-000000000002';
const as=async id=>{await db.exec('reset role;set role authenticated');await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon;grant execute on function auth.uid() to authenticated,anon;`);
 for(const name of ['202610150001_gestion_mente_futuro.sql','202610210001_cliente_solo_solicitud.sql','202610220001_deshacer_aceptacion.sql','202610220002_solicitud_rapida.sql'])
  await db.exec(await readFile(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
 await db.query(`insert into auth.users(id,email,raw_user_meta_data) values($1,'admin@example.test','{"nombre":"Camila Rojas"}'),($2,'cliente@example.test','{"nombre":"Daniela Soto"}')`,[admin,client]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(client);
 const datos={cliente:'Fundación Horizonte',contacto:'Identidad falsa',email:'falso@example.test',cliente_id:admin,
   rut:'12.345.678-5',cargo:'Coordinadora',telefono:'+56 9 1234 5678',servicio:'Coaching individual',tematica:'Liderazgo',
   participantes:10,horas:2,modalidad:'Online',origen:'Programa propio',registrado_por:'Administración',consentimiento:true};
 const id='10000000-0000-0000-0000-000000000001';
 const enviar=async (uuid,d)=>db.query('select registrar_solicitud($1,$2) recibo',[uuid,d]);
 const recibo=await enviar(id,datos);
 assert.deepEqual(await enviar(id,datos),recibo);
 await assert.rejects(enviar('10000000-0000-0000-0000-000000000002',{...datos,rut:'12.345.678-9'}));
 await assert.rejects(enviar('10000000-0000-0000-0000-000000000003',{...datos,consentimiento:false}));
 for(const tabla of ['mf_casos','mf_cotizaciones','mf_ventas','mf_tarifas'])assert.equal((await db.query(`select * from ${tabla}`)).rows.length,0);
 await assert.rejects(db.query("update mf_perfiles set rol='admin' where id=$1",[client]));
 await as(admin);
 const row=(await db.query('select * from mf_casos where id=$1',[id])).rows[0];
 assert.equal(row.rut,datos.rut);assert.equal(row.cargo,datos.cargo);
 assert.equal(row.contacto,'Daniela Soto');assert.equal(row.email,'cliente@example.test');
 assert.equal(row.cliente_id,client);assert.equal(row.origen,'Formulario web');assert.equal(row.registrado_por,'Cliente');
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,1);
 await db.query("update mf_casos set cargo='Encargada de personas',rut='' where id=$1",[id]);
 await assert.rejects(db.query("update mf_casos set rut='12.345.678-9' where id=$1",[id]));
 assert.equal((await db.query("select mf_rut_valido('123456785') valido")).rows[0].valido,true);
 console.log('Solicitud rápida SQL: campos, RUT, idempotencia, identidad y RLS aprobados.');
}finally{await db.close();}
