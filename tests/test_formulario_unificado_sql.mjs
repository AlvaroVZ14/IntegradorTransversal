// Todo se ejecuta en PostgreSQL efímero con personas y empresas ficticias.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
async function comprobar(anterior){
 const db=new PGlite();const admin=randomUUID(),cliente=randomUUID(),intruso=randomUUID();
 const as=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
 const datos={cliente:'Empresa Ficticia',contacto:'Contacto del navegador',email:'escrito@example.test',telefono:'+56 9 1234 5678',rut:'12.345.678-5',cargo:'Coordinadora',
  servicio:'Coaching individual',tematica:'Liderazgo',tematicas:['Liderazgo','Trabajo en equipo'],modalidad:'Online',participantes:12,horas:2,
  dirigido_a:'Líderes de equipo',lugar:'Antofagasta',fecha_preferida:null,detalle:'Objetivo ficticio',consentimiento:true};
 const guardar=d=>db.query('select registrar_solicitud($1,$2::jsonb) r',[randomUUID(),JSON.stringify(d)]);
 try{
  await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
  create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
  create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
  grant usage on schema public,auth to authenticated,anon,service_role;`);
  const dir=new URL('../supabase/migrations/',import.meta.url);
  for(const name of (await readdir(dir)).filter(n=>n.endsWith('.sql')).sort()){
   if(!anterior && name.startsWith('202610230002'))continue;
   await db.exec(await readFile(new URL(name,dir),'utf8'));
  }
  for(const [id,email,nombre,rol] of [[admin,'admin@example.test','Camila Ficticia','admin'],[cliente,'cliente@example.test','Valentina Ficticia','cliente'],[intruso,'intruso@example.test','Intento Ficticio','admin']]){
   await db.query('insert into auth.users(id,email,raw_user_meta_data) values($1,$2,$3::jsonb)',[id,email,JSON.stringify({nombre,rol,role:'admin',is_admin:true})]);
  }
  assert.equal((await db.query('select rol from mf_perfiles where id=$1',[intruso])).rows[0].rol,'cliente');
  await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
  await as('','anon');
  const cat=(await db.query('select mf_catalogo_solicitudes() r')).rows[0].r;
  assert.equal(cat.servicios.length,5);assert.equal(cat.tematicas.length,6);
  for(const tabla of ['mf_casos','mf_perfiles','mf_cotizaciones','mf_ventas','mf_tarifas','mf_configuracion']){
   await assert.rejects(db.query('select * from '+tabla+' limit 1'));
  }
  await assert.rejects(db.query('select registrar_solicitud($1,$2::jsonb)',[randomUUID(),JSON.stringify(datos)]));
  await assert.rejects(db.query('insert into mf_casos(id) values($1)',[randomUUID()]));
  await assert.rejects(db.query('select mf_tomar_avisos_solicitud()'));
  await assert.rejects(db.query('select mf_seguridad.insertar_solicitud($1,$2::jsonb,$3,true)',[randomUUID(),JSON.stringify(datos),admin]));
  const publicoId=randomUUID(),token=randomUUID();
  const publica=(await db.query("select registrar_solicitud_publica($1,$2,$3::jsonb,'') r",[publicoId,token,JSON.stringify(datos)])).rows[0].r;
  assert.deepEqual(Object.keys(publica),['codigo']);
  await db.exec('reset role');
  assert.equal((await db.query('select count(*)::int n from auth.users')).rows[0].n,3);
  await as(cliente);
  const c=(await guardar({...datos,contacto:'Nombre manipulado',email:'otro@example.test',honeypot:''})).rows[0].r;
  assert.deepEqual(Object.keys(c),['codigo']);
  for(const extra of [{origen:'Correo'},{referido_por:'Colega'},{consentimiento_confirmado:true},{cliente_id:admin},{registrado_por:'Administración'},{datos_incompletos:true},{rol:'admin'}]){
   await assert.rejects(guardar({...datos,...extra}));
  }
  await assert.rejects(guardar({...datos,honeypot:'robot'}));
  await assert.rejects(guardar({...datos,consentimiento:false}));
  await assert.rejects(guardar({...datos,horas:null}));
  await assert.rejects(db.query('select mf_tomar_avisos_solicitud()'));
  const tablas=(await db.query("select tablename from pg_tables where schemaname='public' and tablename like 'mf_%'")).rows;
  for(const {tablename} of tablas){
   try{
    const rows=(await db.query('select * from '+tablename)).rows;
    if(tablename==='mf_perfiles'){assert.equal(rows.length,1);assert.equal(rows[0].id,cliente);}
    else assert.equal(rows.length,0,tablename);
   }catch(e){if(e.code!=='42501')throw e;}
  }
  await assert.rejects(db.query("update mf_perfiles set rol='admin' where id=$1",[cliente]));
  await as(admin);
  let casos=(await db.query('select * from mf_casos order by numero')).rows;
  assert.equal(casos.length,2);assert.equal(casos[0].creado_por,null);
  assert.equal(casos[1].contacto,'Valentina Ficticia');assert.equal(casos[1].email,'cliente@example.test');assert.equal(casos[1].cliente_id,cliente);
  assert.equal(casos[1].dirigido_a,'Líderes de equipo');assert.deepEqual(casos[1].tematicas,['Liderazgo','Trabajo en equipo']);
  const parcial=(await guardar({cliente:'Empresa por completar',origen:'Referido por colega',referido_por:'Colega Ficticia',consentimiento_confirmado:false})).rows[0].r.caso;
  assert.equal(parcial.datos_incompletos,true);assert.equal(parcial.email,null);assert.equal(parcial.consentimiento,false);assert.equal(parcial.referido_por,'Colega Ficticia');
  assert.ok(parcial.datos_pendientes.includes('email'));
  await assert.rejects(db.query("update mf_casos set estado='Cotizado' where id=$1",[parcial.id]));
  await db.query("update mf_casos set contacto='Camila Ficticia',email='completo@example.test',servicio='Coaching individual',tematica='Liderazgo',modalidad='Online',participantes=10,horas=2 where id=$1",[parcial.id]);
  assert.equal((await db.query('select datos_incompletos from mf_casos where id=$1',[parcial.id])).rows[0].datos_incompletos,false);
  await assert.rejects(guardar({cliente:'Empresa',email:'incorrecto',origen:'Correo'}));
  const avisos=(await db.query('select * from mf_avisos_solicitud')).rows;
  assert.equal(avisos.length,2); // El registro interno no envía avisos a sí mismo.
  await as('','service_role');
  const reservados=(await db.query('select mf_tomar_avisos_solicitud() r')).rows[0].r;
  assert.equal(reservados.length,2);
  assert.deepEqual((await db.query('select mf_tomar_avisos_solicitud() r')).rows[0].r,[]);
  assert.equal((await db.query("select mf_confirmar_aviso_solicitud($1,$2,'enviado') r",[reservados[0].id,randomUUID()])).rows[0].r,false);
  assert.equal((await db.query("select mf_confirmar_aviso_solicitud($1,$2,'enviado') r",[reservados[0].id,reservados[0].lease])).rows[0].r,true);
  await as(admin);assert.equal((await db.query("select count(*)::int n from mf_avisos_solicitud where estado='enviado'")).rows[0].n,1);
  await db.exec('reset role');
  await db.exec(await readFile(new URL('../supabase/rollback/202610240001_formulario_unificado.sql',import.meta.url),'utf8'));
  assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,3);
  assert.equal((await db.query('select count(*)::int n from mf_avisos_solicitud')).rows[0].n,2);
  console.log('Formulario SQL ('+(anterior?'con':'sin')+' migración pública anterior): roles, RLS, campos internos, múltiples temas, incompletos y avisos OK.');
 }finally{await db.close();}
}
await comprobar(true);await comprobar(false);
