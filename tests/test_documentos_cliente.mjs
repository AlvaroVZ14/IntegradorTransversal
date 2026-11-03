// PostgreSQL efímero con RLS real. Storage se modela; no es una prueba HTTP.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {prepararStorage} from './storage_fixture.mjs';
const db=new PGlite(),admin=randomUUID(),a=randomUUID(),b=randomUUID(),sinConfirmar=randomUUID();
const rol=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id||'']);};
const reservar=async(caso,id=randomUUID(),tipo='Requerimientos',ext='pdf',tamano=123,mime='application/pdf')=>
 (await db.query('select mf_preparar_documento_cliente($1,$2,$3,$4,$5,$6,$7) d',[id,caso,tipo,ext,tamano,mime,'Nota ficticia'])).rows[0].d;
const confirmar=async(id)=>(await db.query('select * from mf_confirmar_documento($1)',[id])).rows[0];
const objeto=async(d)=>db.query("insert into storage.objects(bucket_id,name,metadata) values('documentos-casos',$1,$2)",[d.archivo_path,{size:123,mimetype:'application/pdf'}]);
const listar=async()=>(await db.query('select mf_mis_documentos() d')).rows[0].d;
try {
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 await prepararStorage(db);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const n of (await readdir(dir)).filter(n=>n.endsWith('.sql') && n<='202611030002_documentos_cliente.sql').sort())
  await db.exec(await readFile(new URL(n,dir),'utf8'));
 await db.exec('create policy ajena_permisiva on storage.objects for all to authenticated,anon using(true) with check(true)');
 for(const [id,email,confirmado] of [[admin,'admin@example.test',true],[a,'a@example.test',true],[b,'b@example.test',true],[sinConfirmar,'a@example.test',false]])
  await db.query('insert into auth.users(id,email,email_confirmed_at) values($1,$2,case when $3 then now() end)',[id,email,confirmado]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await rol(admin);
 const crear=async(email)=>(await db.query('select registrar_solicitud($1,$2) d',[randomUUID(),{
  cliente:'Empresa ficticia',contacto:'Contacto ficticio',email,servicio:'Coaching individual',tematicas:['Liderazgo'],
  modalidad:'Online',participantes:5,horas:2,telefono:'912345678'}])).rows[0].d.caso.id;
 const ca=await crear('a@example.test'),cb=await crear('b@example.test'),cb2=await crear('b@example.test');
 const privado=randomUUID(),publico=randomUUID();
 for(const [id,visible] of [[privado,false],[publico,true]]){
  await db.query(`insert into mf_documentos(id,caso_id,tipo,nombre,archivo_path,tamano,tipo_mime,visible_cliente,subido_por)
   values($1,$2,'Material','Documento.pdf',$3,123,'application/pdf',$4,$5)`,[id,ca,`${ca}/${id}.pdf`,visible,admin]);
  await objeto({archivo_path:`${ca}/${id}.pdf`});await confirmar(id);
 }
 await rol(a);
 await assert.rejects(reservar(cb));
 for(const args of [[ca,randomUUID(),'Informe'],[ca,randomUUID(),'Otro','exe'],[ca,randomUUID(),'Otro','pdf',10485761],
 [ca,randomUUID(),'Otro','pdf',123,'image/png'],[ca,randomUUID(),'Otro','pdf',0]])await assert.rejects(reservar(...args));
 const d=await reservar(ca);
 assert.equal(d.archivo_path,`${ca}/cliente/${d.id}.pdf`);assert.ok(!d.nombre.includes('Contacto'));
 assert.deepEqual((await db.query('select * from mf_documentos')).rows,[]);
 await assert.rejects(db.query(`insert into mf_documentos(caso_id,tipo,nombre,archivo_path,tamano,tipo_mime,visible_cliente,subido_por,origen)
  values($1,'Otro','Documento.pdf','ruta.pdf',123,'application/pdf',true,$2,'cliente')`,[ca,admin]));
 await assert.rejects(confirmar(d.id));await objeto(d);const confirmado=await confirmar(d.id);
 assert.equal(confirmado.origen,'cliente');assert.equal(confirmado.subido_por,a);assert.equal(confirmado.visible_cliente,false);
 assert.equal((await reservar(ca,d.id)).estado_archivo,'disponible');
 let casos=await listar();assert.equal(casos.length,1);assert.equal(casos[0].puede_enviar,true);
 assert.deepEqual(casos[0].documentos.map(x=>x.id).sort(),[publico,d.id].sort());
 assert.ok(casos[0].documentos.find(x=>x.id===d.id).es_mio);
 assert.ok(!JSON.stringify(casos).includes('archivo_path'));assert.ok(!JSON.stringify(casos).includes('Nota ficticia'));
 assert.equal((await db.query('select mf_documento_cliente($1) d',[privado])).rows[0].d,null);
 assert.ok((await db.query('select mf_documento_cliente($1) d',[d.id])).rows[0].d);
 await assert.rejects(db.query('select mf_destinatario_documentos($1)',[ca]));
 await rol(admin);await db.query("update mf_configuracion set datos=datos||$1::jsonb where id='general'",[{correo_contacto:'socia@example.test'}]);
 await rol(a);
 assert.equal((await db.query('select mf_aviso_documento_cliente($1) d',[d.id])).rows[0].d.correo,'socia@example.test');
 assert.deepEqual((await db.query('select mf_aviso_documento_cliente($1) d',[d.id])).rows[0].d,{});
 await db.query("select mf_aviso_documento_cliente($1,'enviado')",[d.id]);
 assert.equal((await db.query('delete from storage.objects where name=$1 returning name',[d.archivo_path])).rows.length,0);
 assert.equal((await db.query("update storage.objects set name='ataque' where name=$1 returning name",[d.archivo_path])).rows.length,0);
 await assert.rejects(db.query("insert into storage.objects(bucket_id,name) values('documentos-casos','ataque.pdf')"));
 await rol(b);
 await assert.rejects(db.query('select mf_aviso_documento_cliente($1)',[d.id]));
 assert.equal((await db.query('select mf_documento_cliente($1) d',[d.id])).rows[0].d,null);
 await assert.rejects(db.query('select mf_eliminar_documento_cliente($1)',[d.id]));
 await assert.rejects(confirmar(d.id));await assert.rejects(objeto({...d,archivo_path:`${ca}/cliente/${randomUUID()}.pdf`}));
 assert.ok(!(await listar()).some(x=>x.id===ca));
 for(let i=0;i<20;i++)await reservar(i<10?cb:cb2);
 await assert.rejects(reservar(cb2),/20 archivos en una hora/);
 await rol(sinConfirmar);assert.deepEqual(await listar(),[]);await assert.rejects(reservar(ca));
 await rol(null,'anon');await assert.rejects(reservar(ca));await assert.rejects(db.query('select mf_mis_documentos()'));
 assert.deepEqual((await db.query("select name from storage.objects where bucket_id='documentos-casos'")).rows,[]);
 await rol(admin);
 let filas=(await db.query('select * from mf_documentos where caso_id=$1',[ca])).rows;assert.equal(filas.length,3);
 await db.query("update mf_documentos set tipo='Nómina de participantes' where id=$1",[d.id]);
 await db.query("update mf_casos set estado='Finalizado' where id=$1",[ca]);
 await rol(a);assert.equal((await listar())[0].puede_enviar,false);
 await assert.rejects(reservar(ca));await assert.rejects(db.query('select mf_eliminar_documento_cliente($1)',[d.id]));
 assert.ok((await db.query('select mf_documento_cliente($1) d',[d.id])).rows[0].d); // descargar sigue permitido.
 await rol(admin);await db.query("update mf_casos set estado='En ejecución' where id=$1",[ca]);
 // El límite por caso incluye archivos de ambos orígenes, no solo el lote del cliente.
 for(let i=3;i<20;i++){
  const id=randomUUID();await db.query(`insert into mf_documentos(id,caso_id,tipo,nombre,archivo_path,tamano,tipo_mime,visible_cliente,subido_por)
   values($1,$2,'Otro','Documento.pdf',$3,123,'application/pdf',false,$4)`,[id,ca,`${ca}/${id}.pdf`,admin]);
 }
 await rol(a);await assert.rejects(reservar(ca),/máximo de 20 archivos/);
 await db.query('select mf_eliminar_documento_cliente($1,false)',[d.id]);
 await assert.rejects(db.query('select mf_eliminar_documento_cliente($1,true)',[d.id]));
 assert.equal((await db.query('delete from storage.objects where name=$1 returning name',[d.archivo_path])).rows.length,1);
 await db.query('select mf_eliminar_documento_cliente($1,true)',[d.id]);
 assert.ok(!(await listar())[0].documentos.some(x=>x.id===d.id));
 await reservar(ca); // el cupo se libera solo después de borrar el objeto.
 console.log('Documentos cliente SQL OK: origen, A/B, confirmación, anon, Cerrada, cuotas 20/caso y 20/hora, reintentos, Storage privado, borrado recuperable y administración.');
} finally {await db.close();}
