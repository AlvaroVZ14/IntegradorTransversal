// PostgreSQL efímero; nunca conecta Supabase real.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
const db=new PGlite();
const admin=randomUUID(),cliente=randomUUID();
const as=async(id,role='authenticated')=>{await db.exec('reset role;set role '+role);await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
const datos={cliente:'Empresa Ficticia',contacto:'Camila Ficticia',email:'camila@example.test',telefono:'+56 9 1234 5678',
 rut:'12.345.678-5',cargo:'Coordinadora',servicio:'Coaching individual',tematica:'Liderazgo',participantes:12,horas:2,
 modalidad:'Online',lugar:'',fecha_preferida:null,detalle:'Una solicitud ficticia.',consentimiento:true};
const enviar=(id,token,d=datos,honey='')=>db.query('select registrar_solicitud_publica($1,$2,$3::jsonb,$4) r',[id,token,JSON.stringify(d),honey]);
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create role service_role nologin bypassrls;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon,service_role;`);
 const dir=new URL('../supabase/migrations/',import.meta.url);
 for(const name of (await readdir(dir)).filter(n=>n.endsWith('.sql')).sort())await db.exec(await readFile(new URL(name,dir),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cuenta@example.test')",[admin,cliente]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await db.query("update mf_perfiles set nombre='Camila Ficticia' where id=$1",[cliente]);
 await db.exec(`update mf_configuracion set datos=datos||'{"sitio_web":"https://empresa.example.test","redes":{"instagram":"https://social.example.test/perfil"},"correo_contacto":"contacto@example.test","smtp_password":"privado-ficticio"}'::jsonb where id='general'`);
 await as('','anon');
 const config=(await db.query('select mf_configuracion_publica() r')).rows[0].r;
 assert.deepEqual(Object.keys(config).sort(),['correo_contacto','redes','sitio_web']);
 assert.equal(config.redes.facebook,'');assert.equal(config.correo_contacto,'contacto@example.test');
 assert.ok(!JSON.stringify(config).includes('privado-ficticio'));
 const id=randomUUID(),token=randomUUID();
 const codigo=(await enviar(id,token)).rows[0].r.codigo;
 assert.match(codigo,/^MF-\d{4}-\d{4,}$/);
 assert.equal((await enviar(id,token)).rows[0].r.codigo,codigo);
 await assert.rejects(enviar(id,randomUUID()));
 await assert.rejects(enviar(id,token,{...datos,detalle:'Cambio posterior'}));
 for(const mal of [{...datos,consentimiento:false},{...datos,rut:'12.345.678-9'},
  {...datos,email:'incorrecto'},{...datos,participantes:2.5},{...datos,estado:'Vendido'},
  {...datos,creado_por:admin},{...datos,cliente_id:cliente},{...datos,rol:'admin'}]){
  await assert.rejects(enviar(randomUUID(),randomUUID(),mal));
 }
 await assert.rejects(enviar(randomUUID(),randomUUID(),datos,'bot'));
 for(const tabla of ['mf_casos','mf_cotizaciones','mf_tarifas','mf_ventas','mf_configuracion',
  'mf_plantillas_programa','mf_eventos_caso','mf_borradores_cotizacion','mf_envios_cotizacion','mf_mantenimiento','mf_perfiles']){
  try{assert.equal((await db.query('select * from '+tabla)).rows.length,0,tabla);}
  catch(e){if(e.code!=='42501')throw e;}
 }
 await assert.rejects(db.query('select * from mf_seguridad.recibos_publicos'));
 await assert.rejects(db.query(`insert into mf_casos(cliente) values('Intruso')`));
 await enviar(randomUUID(),randomUUID());await enviar(randomUUID(),randomUUID());
 await assert.rejects(enviar(randomUUID(),randomUUID()),/Espera unos minutos/);
 await as(cliente);
 const cuenta=(await db.query('select registrar_solicitud($1,$2::jsonb) r',[randomUUID(),JSON.stringify({...datos,email:'otro@example.test',contacto:'Nombre no autoritativo'})])).rows[0].r;
 assert.ok(cuenta.codigo);
 assert.equal((await db.query('select * from mf_casos')).rows.length,0);
 await as(admin);
 const rows=(await db.query('select * from mf_casos order by numero')).rows;
 assert.equal(rows.length,4);assert.equal(rows[0].creado_por,null);assert.equal(rows[0].cliente_id,null);
 assert.equal(rows[0].registrado_por,'Cliente');assert.equal(rows[0].origen,'Formulario web');assert.equal(rows[0].estado,'Solicitud');
 assert.equal(rows[3].creado_por,cliente);assert.equal(rows[3].email,'cuenta@example.test');
 assert.equal((await db.query("select mf_lectura_en_vivo('hoy') r")).rows[0].r.casos.length,4);
 await db.exec('reset role');
 await db.exec(await readFile(new URL('../supabase/rollback/202610230002_formulario_publico.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,4);
 await as('','anon');await assert.rejects(enviar(randomUUID(),randomUUID()));
 console.log('Público SQL: envío, reintento sin duplicados, validaciones, límites, RLS, cuenta cliente, acceso admin y rollback OK.');
}finally{await db.close();}
