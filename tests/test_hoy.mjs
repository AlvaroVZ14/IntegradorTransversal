// Ensayos locales PostgreSQL. No escribe en Supabase vivo.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const admin='00000000-0000-0000-0000-000000000001',client='00000000-0000-0000-0000-000000000002';
const cid='10000000-0000-0000-0000-000000000001';
const op=n=>`20000000-0000-0000-0000-${String(n).padStart(12,'0')}`;
const as=async id=>{await db.exec('reset role;set role authenticated');await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);};
try{
 await db.exec(`create role anon nologin;create role authenticated nologin;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon;grant execute on function auth.uid() to authenticated,anon;`);
 for(const name of ['202610150001_gestion_mente_futuro.sql','202610210001_cliente_solo_solicitud.sql','202610220001_deshacer_aceptacion.sql','202610220002_solicitud_rapida.sql','202610220003_cotizador_asistido.sql','202610220004_hoy.sql'])
  await db.exec(await readFile(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[admin,client]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);await as(admin);
 await db.query("insert into mf_casos(id,cliente,contacto,email,servicio,tematica,participantes,horas,modalidad,fecha_preferida) values($1,'Fundación Horizonte','Daniela Soto','cliente@example.test','Coaching individual','Liderazgo',12,2,'Online',current_date-2)",[cid]);
 const datos={base_clp:100000,descuento_pct:0,iva_pct:0,detalle:'Capacitación ficticia',condiciones:'Prueba',valida_hasta:'2099-01-01'};
 const q=(await db.query('select * from mf_emitir_cotizacion($1,1,$2,$3)',[cid,op(1),datos])).rows[0];
 const venta=(await db.query("select * from mf_registrar_venta($1,$2,(now() at time zone 'America/Santiago')::date,'Pagado')",[cid,q.id])).rows[0];
 const actual=async()=>(await db.query('select * from mf_casos where id=$1',[cid])).rows[0];
 const cerrar=async(n,v,sv=1)=>(await db.query('select mf_cerrar_caso_hoy($1,$2,$3,$4) r',[cid,v,sv,op(n)])).rows[0].r;
 await assert.rejects(cerrar(2,(await actual()).version)); // Fecha preferida pasada NO prueba realización.
 await assert.rejects(db.query('update mf_casos set fecha_realizacion=current_date+1 where id=$1',[cid]));
 await db.query("update mf_casos set fecha_realizacion=(now() at time zone 'America/Santiago')::date where id=$1",[cid]);
 let c=await actual();
 await as(client);await assert.rejects(cerrar(2,c.version));
 await assert.rejects(db.query('select mf_registrar_contacto_hoy($1,$2,$3,$4,$5)',[cid,q.id,op(10),'seguimiento',{}]));
 assert.equal((await db.query('select * from mf_eventos_caso')).rows.length,0);
 await as(admin);
 await assert.rejects(cerrar(2,c.version,null));
 let r=await cerrar(2,c.version);assert.equal(r.caso.estado,'Finalizado');
 assert.equal((await cerrar(2,c.version)).evento.id,r.evento.id);
 await db.query('select mf_deshacer_cierre_hoy($1)',[r.evento.id]);
 assert.equal((await actual()).estado,'Vendido');
 assert.equal((await db.query('select count(*)::int n from mf_ventas')).rows[0].n,1);
 c=await actual();r=await cerrar(3,c.version);
 await db.query("update mf_eventos_caso set created_at=now()-interval '11 seconds' where id=$1",[r.evento.id]);
 await assert.rejects(db.query('select mf_deshacer_cierre_hoy($1)',[r.evento.id]));
 await db.query('update mf_eventos_caso set created_at=now() where id=$1',[r.evento.id]);
 await db.query('select mf_deshacer_cierre_hoy($1)',[r.evento.id]);
 c=await actual();r=await cerrar(4,c.version);
 await db.query("update mf_casos set contacto='Camila Rojas' where id=$1",[cid]);
 await assert.rejects(db.query('select mf_deshacer_cierre_hoy($1)',[r.evento.id]));
 const version=(await actual()).version;
 const registrar=async()=>(await db.query('select * from mf_registrar_contacto_hoy($1,$2,$3,$4,$5)',[cid,q.id,op(10),'seguimiento',{}])).rows[0];
 let evento=await registrar();assert.equal((await registrar()).id,evento.id);
 assert.equal((await actual()).version,version); // Registrar contacto no cambia estado ni versión de caso.
 assert.equal(evento.datos.tipo_mensaje,'seguimiento');
 await db.query("update mf_ventas set estado_pago='Pendiente' where id=$1",[venta.id]);
 await db.query("update mf_casos set estado='En ejecución' where id=$1",[cid]);
 await assert.rejects(cerrar(6,(await actual()).version,2));
 console.log('Hoy SQL: permisos, fecha efectiva, cierre pagado, idempotencia, deshacer, plazo y concurrencia aprobados.');
}finally{await db.close();}
