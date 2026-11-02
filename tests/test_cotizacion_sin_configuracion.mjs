// Base local aislada: no consulta ni modifica Supabase publicado.
import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const db=new PGlite();
const admin='00000000-0000-0000-0000-000000000001';
const caso='10000000-0000-0000-0000-000000000001';
try {
 await db.exec(`create role anon nologin;create role authenticated nologin;create schema auth;
 create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
 create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
 grant usage on schema public,auth to authenticated,anon;grant execute on function auth.uid() to authenticated,anon;`);
 for(const name of ['202610150001_gestion_mente_futuro.sql','202610210001_cliente_solo_solicitud.sql','202610220001_deshacer_aceptacion.sql','202610220002_solicitud_rapida.sql','202610220003_cotizador_asistido.sql'])
  await db.exec(await readFile(new URL('../supabase/migrations/'+name,import.meta.url),'utf8'));
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test')",[admin]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await db.exec('set role authenticated');
 await db.query("select set_config('request.jwt.claim.sub',$1,false)",[admin]);
 await db.exec('delete from mf_configuracion');
 await db.query("insert into mf_casos(id,cliente,contacto,email,servicio,tematica,participantes,horas,modalidad) values($1,'Empresa ficticia','Contacto ficticio','contacto@example.test','Coaching individual','Liderazgo',10,2,'Online')",[caso]);
 const datos={base_clp:250000,iva_pct:0,descuento_pct:0,detalle:'Taller · Online, dos horas',condiciones:'',valida_hasta:'2099-01-01',documento:{emisor:{},textos:{},detalle_modalidad:'Online, dos horas'}};
 const q=(await db.query('select * from mf_emitir_cotizacion($1,1,$2,$3)',[caso,'20000000-0000-0000-0000-000000000001',datos])).rows[0];
 assert.equal(Number(q.total_clp),250000);
 assert.equal(q.condiciones,'');assert.deepEqual(q.documento.emisor,{});
 assert.equal((await db.query('select * from mf_configuracion')).rows.length,0);
 const fecha=(await db.query("select to_char(now() at time zone 'America/Santiago','YYYY-MM-DD') fecha")).rows[0].fecha;
 const r=(await db.query('select mf_decidir_cotizacion($1,$2,2,$3,$4) r',[caso,q.id,'20000000-0000-0000-0000-000000000002',{accion:'vender',monto_clp:250000,fecha,reserva_pct:30,remuneracion_pct:70,estado_pago:'Pendiente'}])).rows[0].r;
 assert.equal(Number(r.venta.reserva_clp),75000);assert.equal(Number(r.venta.remuneracion_clp),175000);
 await db.query('select mf_deshacer_decision($1)',[r.evento.id]);
 assert.equal((await db.query('select * from mf_ventas')).rows.length,0);
 console.log('SQL sin configuración: emisión opcional, total, reparto editable y deshacer aprobados.');
} finally {await db.close();}

