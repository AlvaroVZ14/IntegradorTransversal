// PostgreSQL efímero. Storage se modela con sus tablas: no es una prueba HTTP real.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const uuid=(grupo,n)=>`${grupo}0000000-0000-0000-0000-${String(n).padStart(12,'0')}`;
const admin=uuid(0,1),a=uuid(0,2),b=uuid(0,3),futuro=uuid(0,4),sinConfirmar=uuid(0,5);
const c1=uuid(1,1),c2=uuid(1,2),c3=uuid(1,3),c4=uuid(1,4);
const d1=uuid(2,1),d2=uuid(2,2),d3=uuid(2,3),d4=uuid(2,4);
const rol=async(id,role='authenticated')=>{
 await db.exec('reset role;set role '+role);
 await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id||'']);
};
const denegado=async(q,args=[])=>assert.rejects(db.query(q,args));
const meta=async(id,caso,tipo='Lista de asistencia',visible=null,cotizacion=null)=>{
 const r=(await db.query(`insert into mf_documentos(id,caso_id,tipo,nombre,archivo_path,tamano,tipo_mime,visible_cliente,subido_por,cotizacion_id)
 values($1,$2,$3,'Nombre_Personal.pdf',$4,123,'application/pdf',$5,$6,$7) returning *`,[id,caso,tipo,`${caso}/${id}.pdf`,visible,a,cotizacion])).rows[0];
 assert.equal(r.subido_por,admin);assert.ok(!r.nombre.includes('Personal'));return r;
};
const objeto=async(id,caso,size=123)=>db.query("insert into storage.objects(bucket_id,name,metadata) values('documentos-casos',$1,$2)",[`${caso}/${id}.pdf`,{size,mimetype:'application/pdf'}]);
const confirmar=async(id)=>(await db.query('select * from mf_confirmar_documento($1)',[id])).rows[0];
const documentos=async()=>(await db.query('select id from mf_documentos order by id')).rows.map(x=>x.id);
const objetos=async()=>(await db.query("select name from storage.objects where bucket_id='documentos-casos' order by name")).rows.map(x=>x.name);
try {
 await db.exec(`create role anon nologin;create role authenticated nologin;create schema auth;create schema storage;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 create table storage.buckets(id text primary key,name text,public boolean default false,file_size_limit bigint,allowed_mime_types text[]);
 create table storage.objects(id uuid default gen_random_uuid(),bucket_id text references storage.buckets(id),name text,metadata jsonb,unique(bucket_id,name));
 alter table storage.objects enable row level security;
 grant usage on schema public,auth,storage to authenticated,anon;
 grant execute on function auth.uid() to authenticated,anon;
 grant select,insert,update,delete on storage.objects to authenticated,anon;
 grant select on storage.buckets to authenticated,anon;
 create policy ajena_permisiva on storage.objects for all to authenticated,anon using(true) with check(true);`);
 for(const n of ['202610150001_gestion_mente_futuro.sql','202610210001_cliente_solo_solicitud.sql','202610220003_cotizador_asistido.sql','202611020002_documentos_caso.sql'])
  await db.exec(await readFile(new URL('../supabase/migrations/'+n,import.meta.url),'utf8'));
 await db.query("insert into auth.users(id,email,email_confirmed_at) values($1,'admin@example.test',now()),($2,'a@example.test',now()),($3,'b@example.test',now()),($4,'futuro@example.test',null),($5,'a@example.test',null)",[admin,a,b,futuro,sinConfirmar]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await db.exec("insert into storage.buckets(id,name,public) values('otro','otro',true);insert into storage.objects(bucket_id,name) values('otro','publico.pdf')");
 await rol(admin);
 for(const [id,cliente,email] of [[c1,a,'a@example.test'],[c2,b,'a@example.test'],[c3,null,'a@example.test'],[c4,null,'futuro@example.test']])
  await db.query("insert into mf_casos(id,cliente_id,cliente,contacto,email,servicio,tematica,participantes,horas,modalidad) values($1,$2,'Empresa ficticia','Contacto ficticio',$3,'Coaching individual','Liderazgo',5,2,'Online')",[id,cliente,email]);
 assert.equal((await meta(d1,c1)).visible_cliente,true);
 await denegado('select * from mf_confirmar_documento($1)',[d1]);
 await objeto(d1,c1);
 await rol(a);assert.deepEqual(await documentos(),[]);assert.deepEqual(await objetos(),[]);
 await rol(admin);assert.equal((await confirmar(d1)).estado_archivo,'disponible');
 await meta(d2,c2);await objeto(d2,c2);await confirmar(d2);
 await meta(d3,c3);await objeto(d3,c3);await confirmar(d3);
 await meta(d4,c4);await objeto(d4,c4);await confirmar(d4);
 await rol(a);assert.deepEqual(await documentos(),[d1,d3]);assert.equal((await objetos()).length,2);
 await rol(b);assert.deepEqual(await documentos(),[d2]);assert.equal((await objetos()).length,1);
 await rol(sinConfirmar);assert.deepEqual(await documentos(),[]);assert.deepEqual(await objetos(),[]);
 await rol(futuro);assert.deepEqual(await documentos(),[]);
 await db.exec('reset role');await db.query('update auth.users set email_confirmed_at=now() where id=$1',[futuro]);
 await rol(futuro);assert.deepEqual(await documentos(),[d4]);
 await rol(a);
 assert.deepEqual((await db.query('select * from mf_casos')).rows,[]); // No se abrió la tabla del caso.
 assert.equal((await db.query("update mf_documentos set visible_cliente=false where id=$1 returning id",[d1])).rows.length,0);
 await denegado("insert into storage.objects(bucket_id,name) values('documentos-casos','ataque.pdf')");
 assert.equal((await db.query("update storage.objects set name='cambiado.pdf' where name=$1 returning id",[`${c1}/${d1}.pdf`])).rows.length,0);
 assert.equal((await db.query('delete from mf_documentos where id=$1 returning id',[d1])).rows.length,0);
 assert.equal((await db.query('delete from storage.objects where name=$1 returning id',[`${c1}/${d1}.pdf`])).rows.length,0);
 for(const sql of ['select * from mf_confirmar_documento($1)','select mf_eliminar_documento($1)','select mf_destinatario_documentos($1)','select mf_reservar_aviso_documento($1)'])await denegado(sql,[d1]);
 await rol(null,'anon');await denegado('select * from mf_documentos');assert.deepEqual(await objetos(),[]);
 assert.equal((await db.query("select * from storage.objects where bucket_id='otro'")).rows.length,1);
 await denegado("insert into storage.objects(bucket_id,name) values('documentos-casos','anon.pdf')");
 assert.equal((await db.query("select public from storage.buckets where id='documentos-casos'")).rows[0].public,false);
 await rol(admin);
 const destino=(await db.query('select mf_destinatario_documentos($1) d',[c1])).rows[0].d;
 assert.equal(destino.tiene_cuenta,true);assert.equal(destino.correo,'a@example.test');
 await db.query('update mf_documentos set visible_cliente=false where id=$1',[d1]);
 await rol(a);assert.deepEqual(await documentos(),[d3]);assert.equal((await objetos()).length,1);
 await rol(admin);await db.query('update mf_documentos set visible_cliente=true where id=$1',[d1]);
 assert.equal((await db.query('select mf_reservar_aviso_documento($1) b',[d1])).rows[0].b,true);
 assert.equal((await db.query('select mf_reservar_aviso_documento($1) b',[d1])).rows[0].b,false);
 await db.query("select mf_resultado_aviso_documento($1,'enviado')",[d1]);
 await denegado("update mf_documentos set archivo_path='otra/ruta.pdf' where id=$1",[d1]);
 const q=(await db.query('select * from mf_emitir_cotizacion($1,1,$2,$3)',[c1,uuid(3,1),{base_clp:100000,descuento_pct:0,iva_pct:0,detalle:'Servicio ficticio',condiciones:'',valida_hasta:'2099-01-01',documento:{}}])).rows[0];
 assert.equal((await meta(uuid(2,5),c1,'Cotización',null,q.id)).visible_cliente,false);
 await denegado(`insert into mf_documentos(id,caso_id,tipo,nombre,archivo_path,tamano,tipo_mime,visible_cliente,subido_por,cotizacion_id)
 values($1,$2,'Cotización','doc.pdf',$3,123,'application/pdf',false,$4,$5)`,[uuid(2,6),c2,`${c2}/${uuid(2,6)}.pdf`,admin,q.id]);
 await db.query('select mf_eliminar_documento($1,false)',[d1]);
 await rol(a);assert.deepEqual(await documentos(),[d3]);
 await rol(admin);await denegado('select mf_eliminar_documento($1,true)',[d1]);
 await db.query('delete from storage.objects where name=$1',[`${c1}/${d1}.pdf`]);
 await db.query('select mf_eliminar_documento($1,true)',[d1]);
 assert.equal((await db.query('select estado_archivo from mf_documentos where id=$1',[d1])).rows[0].estado_archivo,'eliminado');
 for(const [i,tipo] of ['Lista de asistencia','Informe','Certificado','Material','Cotización','Otro'].entries())
  assert.equal((await meta(uuid(2,20+i),c1,tipo)).visible_cliente,i<4);
 console.log('Documentos SQL: privado, RLS admin/propio/ajeno/anónimo, correo verificado, permisos de Storage, visibilidad, aviso único, cotización privada y eliminación aprobados.');
} finally {await db.close();}
