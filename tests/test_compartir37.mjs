// PostgreSQL efímero: canales recibidos por la RPC pública, sin datos reales.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {prepararStorage} from './storage_fixture.mjs';
const db=new PGlite(),admin=randomUUID(),cliente=randomUUID();
const as=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 await prepararStorage(db);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const n of (await readdir(dir)).filter(n=>n.endsWith('.sql')&&n<'202611050003').sort())await db.exec(await readFile(new URL(n,dir),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[admin,cliente]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(admin);
 const historico=(await db.query(`insert into mf_casos(cliente,contacto,email,servicio,tematica,participantes,horas,modalidad,canal_captacion)
 values('Empresa ficticia','Contacto ficticio','persona@example.test','Coaching individual','Liderazgo',1,2,'Online','otro') returning *`)).rows[0];
 await db.exec('reset role');await db.exec(await readFile(new URL('202611050003_compartir_compacto.sql',dir),'utf8'));
 for(const [codigo,esperado] of [['ig','instagram'],['fb','facebook'],['wa','whatsapp'],['li','linkedin'],['mail','correo'],['qr','qr'],['web','sitio_web'],['hola','directo'],[null,'directo'],[undefined,'directo']]){
  await as('','anon');const id=randomUUID();
  const datos={cliente:'Empresa ficticia',contacto:'Contacto ficticio',email:'persona'+id.slice(0,8)+'@example.test',servicio:'Coaching individual',tematicas:['Liderazgo'],modalidad:'Online',participantes:8,horas:2,consentimiento:true,canal_captacion:codigo};
  const token=randomUUID();const enviar=()=>db.query("select registrar_solicitud_publica($1,$2,$3,'') r",[id,token,datos]);
  const respuesta=(await enviar()).rows[0].r;assert.ok(respuesta.codigo);
  assert.deepEqual((await enviar()).rows[0].r,respuesta);
  await as(admin);const row=(await db.query('select * from mf_casos where id=$1',[id])).rows[0];
  assert.equal(row.canal_captacion,esperado);assert.equal(row.origen,'Formulario web');assert.equal(row.registrado_por,'Cliente');assert.equal(row.cliente_id,null);
 }
 await as(cliente);await assert.rejects(db.query('select mf_configuracion_compartir()'));
 await as('','anon');await assert.rejects(db.query('select * from mf_casos'));
 await assert.rejects(db.query("select mf_seguridad.normalizar_canal('admin')"));
 await db.exec('reset role');
 const despues=(await db.query('select * from mf_casos where id=$1',[historico.id])).rows[0];
 assert.deepEqual(despues,historico);
 await db.exec(await readFile(new URL('../supabase/rollback/202611050003_compartir_compacto.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,11);
 assert.equal((await db.query("select count(*)::int n from mf_casos where canal_captacion in ('linkedin','correo')")).rows[0].n,2);
 console.log('Prompt 37 SQL OK: códigos, inválido/sin canal, origen, idempotencia, permisos, históricos intactos y rollback sin pérdida.');
}finally{await db.close();}
