import {PGlite} from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import {readFile,readdir} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
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
 for(const n of (await readdir(dir)).filter(n=>n.endsWith('.sql')).sort())await db.exec(await readFile(new URL(n,dir),'utf8'));
 const columnas=JSON.parse(execFileSync('python',['-c','import json;from servicios.hoja_columnas import COLUMNAS;print(json.dumps(COLUMNAS))'],{encoding:'utf8'}));
 for(const [hoja,vista] of [['Casos','v_hoja_casos'],['Cotizaciones','v_hoja_cotizaciones'],['Ventas','v_hoja_ventas']]){
  const columnasSQL=(await db.query("select column_name from information_schema.columns where table_schema='reportes' and table_name=$1 order by ordinal_position",[vista])).rows.map(r=>r.column_name);
  assert.deepEqual(columnasSQL,columnas[hoja]);
 }
 await db.query("insert into auth.users(id,email) values($1,'admin@example.test'),($2,'cliente@example.test')",[admin,cliente]);
 await db.query("update mf_perfiles set rol='admin' where id=$1",[admin]);
 await as(admin);
 const c=(await db.query(`insert into mf_casos(cliente,contacto,email,telefono,rut,servicio,tematica,participantes,horas,modalidad,registrado_por,motivo_rechazo)
 values('Empresa Ficticia','PERSONA_SECRETA','secreto@example.test','+56912345678','12.345.678-5','Coaching individual','Liderazgo',1,2,'Online','NOMBRE_SECRETO','Precio · NOTA_SECRETA') returning *`)).rows[0];
 const q=(await db.query('select * from mf_emitir_cotizacion($1,$2,$3,$4)',[c.id,(await db.query('select version from mf_casos where id=$1',[c.id])).rows[0].version,randomUUID(),{base_clp:100000,descuento_pct:10,descuento_motivo:'Motivo ficticio',iva_pct:0,detalle:'Detalle ficticio',condiciones:'CONDICION_SECRETA',valida_hasta:'2099-01-01',documento:{descuento_motivo:'Motivo ficticio',pago:{numero_cuenta:'BANCO_SECRETO'}}}])).rows[0];
 await db.exec('reset role');
 for(const tabla of ['v_hoja_casos','v_hoja_cotizaciones','v_hoja_ventas','sync_cola','sync_estado','sync_registro']){
  for(const [id,rol] of [['','anon'],[cliente,'authenticated']]){await as(id,rol);await assert.rejects(db.query('select * from reportes.'+tabla));}
 }
 await as(cliente);await assert.rejects(db.query('select mf_estado_hoja()'));
 await as(admin);assert.ok((await db.query('select mf_estado_hoja() r')).rows[0].r);
 await db.exec('reset role;set role mfy_hoja');
 await assert.rejects(db.query('select * from public.mf_casos'));await assert.rejects(db.query('select * from reportes.sync_cola'));
 const rows=(await db.query('select * from reportes.v_hoja_casos')).rows;
 assert.equal(rows.length,1);assert.equal(rows[0].monto_cotizado,90000);assert.equal(rows[0].motivo_rechazo,'Precio');
 const token=randomUUID(),otro=randomUUID();
 let lote=(await db.query('select reportes.tomar($1,false) r',[token])).rows[0].r;
 assert.equal(lote.datos.Cotizaciones.length,1);
 assert.ok(!/912345678|12[.]345|SECRETO|secreto@example|numero_cuenta|"rut"|"contacto"|"telefono"|"documento"/.test(JSON.stringify(lote.datos)));
 assert.equal((await db.query('select reportes.tomar($1,true) r',[otro])).rows[0].r,null);
 assert.equal((await db.query('select reportes.finalizar($1,null,$2) r',[otro,{}])).rows[0].r,false);
 await as(admin);await db.query("update mf_casos set participantes=9 where id=$1",[c.id]);
 await db.exec('reset role;set role mfy_hoja');
 assert.equal((await db.query('select reportes.finalizar($1,null,$2) r',[token,{Casos:1,Cotizaciones:1,Ventas:0}])).rows[0].r,true);
 lote=(await db.query('select reportes.tomar($1,false) r',[otro])).rows[0].r;
 assert.equal(lote.datos.Casos[0].participantes,9); // Escritura posterior al lote no se reconoce antes de enviarse.
 await db.query('select reportes.finalizar($1,$2,$3)',[otro,'JSON_SUPER_SECRETO',{Casos:1}]);
 await as(admin);const estado=(await db.query('select mf_estado_hoja() r')).rows[0].r;
 assert.ok(estado.pendientes>0);assert.ok(!JSON.stringify(estado).includes('JSON_SUPER_SECRETO'));
 await db.exec('reset role');await db.query('update reportes.sync_estado set reintentar_en=null');
 await db.query("update mf_casos set cliente=contacto where id=$1",[c.id]);
 assert.equal((await db.query('select empresa from reportes.v_hoja_casos')).rows[0].empresa,'Cliente particular');
 const venta=(await db.query("insert into mf_ventas(caso_id,cotizacion_id,monto_clp,fecha_venta,estado_pago) values($1,$2,90000,'2026-11-05','Abono recibido') returning id",[c.id,q.id])).rows[0].id;
 assert.equal((await db.query('select monto_pendiente from reportes.v_hoja_ventas')).rows[0].monto_pendiente,90000);
 await db.query("update mf_ventas set estado_pago='Pagado' where id=$1",[venta]);
 assert.equal((await db.query('select monto_pendiente from reportes.v_hoja_ventas')).rows[0].monto_pendiente,0);
 await db.query('update mf_ventas set anulada=true where id=$1',[venta]);
 assert.equal((await db.query('select * from reportes.v_hoja_ventas')).rows.length,0);
 assert.equal((await db.query('select tiene_venta from reportes.v_hoja_casos')).rows[0].tiene_venta,'NO');
 await db.query('delete from mf_ventas where id=$1',[venta]);
 await db.query('delete from mf_cotizaciones where id=$1',[q.id]);
 const ultimo=randomUUID();lote=(await db.query('select reportes.tomar($1,true) r',[ultimo])).rows[0].r;
 assert.equal(lote.datos.Cotizaciones.length,0);
 await db.query('select reportes.finalizar($1,null,$2)',[ultimo,{Casos:1,Cotizaciones:0,Ventas:0}]);
 await db.exec(await readFile(new URL('../supabase/rollback/202611050004_hoja_reportes.sql',import.meta.url),'utf8'));
 assert.equal((await db.query('select count(*)::int n from mf_casos')).rows[0].n,1);
 console.log('Prompt 38 SQL OK: migraciones, vistas sin datos sensibles, permisos, cola, exclusión mutua, reintento, nuevas escrituras, eliminación y reconstrucción.');
}finally{await db.close();}
