// PostgreSQL efímero: no se utiliza Supabase real ni se envían correos.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const db=new PGlite(),admin=randomUUID(),cliente=randomUUID();
const as=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
const entrada=(email='persona@example.test')=>({cliente:'Empresa ficticia',contacto:'Persona ficticia',email,
 servicio:'Coaching individual',tematica:'Liderazgo',tematicas:['Liderazgo'],modalidad:'Online',participantes:8,horas:2,consentimiento:true});
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const n of (await readdir(dir)).filter(n=>n.endsWith('.sql') && n<'202610240002').sort())await db.exec(await readFile(new URL(n,dir),'utf8'));
 for(const [id,email] of [[admin,'admin@example.test'],[cliente,'cliente@example.test']])await db.query('insert into auth.users(id,email,raw_user_meta_data) values($1,$2,$3::jsonb)',[id,email,JSON.stringify({nombre:'Cuenta ficticia',rol:'admin'})]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(admin);
 const historico=randomUUID();await db.query('select registrar_solicitud($1,$2::jsonb)',[historico,JSON.stringify(entrada())]);
 await db.exec(`update mf_configuracion set datos=datos||'{"url_publica":"https://portal.example.test/","compartir":{"whatsapp":"Texto previo {enlace}"}}'::jsonb where id='general'`);
 await db.exec('reset role');
 await db.exec(await readFile(new URL('202610240002_compartir_canales.sql',dir),'utf8'));
 await as(admin);
 let config=(await db.query('select mf_configuracion_compartir() r')).rows[0].r;
 assert.equal(config.datos.url_publica,'https://portal.example.test/');assert.equal(config.datos.compartir.whatsapp,'Texto previo {enlace}');
 assert.equal(Object.keys(config.datos.compartir).length,5);
 assert.equal((await db.query('select canal_captacion from mf_casos where id=$1',[historico])).rows[0].canal_captacion,null);
 await as('','anon');
 await assert.rejects(db.query('select mf_configuracion_compartir()'));
 const canales=['instagram','facebook','whatsapp','sitio_web','qr','directo','hola',null,123,{rol:'admin'},undefined];
 for(const [i,canal] of canales.entries()){
  const id=randomUUID(),token=randomUUID(),data={...entrada(`persona${i}@example.test`),canal_captacion:canal};
  const query=()=>db.query("select registrar_solicitud_publica($1,$2,$3::jsonb,'') r",[id,token,JSON.stringify(data)]);
  const r=(await query()).rows[0].r;assert.deepEqual(Object.keys(r),['codigo']);
  assert.deepEqual((await query()).rows[0].r,r); // Recarga/reintento no duplica.
  await as(admin);
  const row=(await db.query('select * from mf_casos where id=$1',[id])).rows[0];
  assert.equal(row.canal_captacion,canal===undefined?'directo':i<6?canal:'otro');
  assert.equal(row.estado,'Solicitud');assert.equal(row.origen,'Formulario web');assert.equal(row.registrado_por,'Cliente');assert.equal(row.creado_por,null);
  await as('','anon');
 }
 await as(cliente);
 await assert.rejects(db.query('select mf_configuracion_compartir()'));
 await assert.rejects(db.query("select mf_seguridad.normalizar_canal('admin')"));
 const propio=randomUUID();await db.query('select registrar_solicitud($1,$2::jsonb)',[propio,JSON.stringify({...entrada(),canal_captacion:'whatsapp'})]);
 assert.equal((await db.query('select * from mf_casos')).rows.length,0);
 assert.equal((await db.query("update mf_casos set canal_captacion='instagram' where id=$1 returning id",[propio])).rows.length,0);
 await assert.rejects(db.query('select registrar_solicitud($1,$2::jsonb)',[randomUUID(),JSON.stringify({...entrada(),canal_captacion:'instagram',origen:'Correo'})]));
 await as(admin);
 const propioRow=(await db.query('select * from mf_casos where id=$1',[propio])).rows[0];
 assert.equal(propioRow.canal_captacion,'whatsapp');assert.equal(propioRow.cliente_id,cliente);assert.equal(propioRow.email,'cliente@example.test');
 const interno=randomUUID();await db.query('select registrar_solicitud($1,$2::jsonb)',[interno,JSON.stringify({...entrada(),origen:'Referido por colega',referido_por:'Colega ficticio',canal_captacion:'instagram'})]);
 assert.equal((await db.query('select canal_captacion from mf_casos where id=$1',[interno])).rows[0].canal_captacion,null);
 const snapshot=(await db.query("select mf_lectura_en_vivo('dashboard') r")).rows[0].r;
 assert.equal(snapshot.casos.filter(c=>c.canal_captacion).length,canales.length+1);
 const cantidad=(await db.query('select count(*)::int n from mf_casos')).rows[0].n;
 await db.exec('reset role');await db.exec(await readFile(new URL('../supabase/rollback/202610240002_compartir_canales.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,cantidad);
 assert.equal((await db.query("select count(*)::int n from mf_casos where canal_captacion is not null")).rows[0].n,canales.length+1);
 console.log('Compartir SQL: 6 canales + Otro, idempotencia, RLS, rol en DB, origen intacto, lectura en vivo y rollback sin pérdidas OK.');
}finally{await db.close();}
