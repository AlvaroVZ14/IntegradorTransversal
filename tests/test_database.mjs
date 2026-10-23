// PostgreSQL real en WASM, efímero; nunca conecta con Supabase ni usa sus secretos.
// npm install --prefix tmp/db-test --no-audit --no-fund @electric-sql/pglite
import { PGlite } from '../tmp/db-test/node_modules/@electric-sql/pglite/dist/index.js';
import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';

const db = new PGlite();
let checks = 0;
const owner = '00000000-0000-0000-0000-000000000001';
const alice = '00000000-0000-0000-0000-000000000002';
const bob = '00000000-0000-0000-0000-000000000003';
const caseId = '10000000-0000-0000-0000-000000000001';
const bobCase = '10000000-0000-0000-0000-000000000002';
async function asUser(id) {
  await db.exec('reset role; set role authenticated');
  await db.query("select set_config('request.jwt.claim.sub',$1,false)",[id]);
}
async function denied(sql, params=[]) {
  await assert.rejects(db.query(sql,params)); checks++;
}
function equal(actual, expected) { assert.deepEqual(actual,expected); checks++; }

try {
  await db.exec(`
    create role anon nologin; create role authenticated nologin;
    create schema auth;
    create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}',email_confirmed_at timestamptz default now());
    create function auth.uid() returns uuid language sql stable as
      $$ select nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
    grant usage on schema public,auth to authenticated,anon;
    grant execute on function auth.uid() to authenticated,anon;
  `);
  await db.exec(await readFile(new URL('../supabase/migrations/202610150001_gestion_mente_futuro.sql',import.meta.url),'utf8'));
  equal((await db.query('select count(*)::int n from public.mf_tarifas')).rows[0].n,11);
  await db.query(`insert into auth.users(id,email,raw_user_meta_data) values
    ($1,'owner@example.test','{"nombre":"Dueña"}'),
    ($2,'alice@example.test','{"nombre":"Alice","rol":"duena"}'),
    ($3,'bob@example.test','{"nombre":"Bob"}')`,[owner,alice,bob]);
  equal((await db.query('select rol from mf_perfiles where id=$1',[alice])).rows[0].rol,'cliente');
  await db.query("update mf_perfiles set rol='duena' where id=$1",[owner]);
  const insert = `insert into mf_casos(id,creado_por,cliente_id,cliente,contacto,email,servicio,tematica,participantes,horas,modalidad)
    values($1,$2,$3,'Empresa de prueba','Contacto prueba','contact@example.test','Taller de trabajo en equipo','Trabajo en equipo',56,8,'Presencial') returning *`;
  await asUser(alice);
  await db.query(insert,[caseId,alice,alice]);
  await denied(insert,['10000000-0000-0000-0000-000000000009',alice,bob]);
  await denied(insert,['10000000-0000-0000-0000-000000000009',owner,alice]);
  await denied("update mf_perfiles set rol='duena' where id=$1",[alice]);
  await denied("update mf_casos set created_at=now()-interval '1 year' where id=$1",[caseId]);
  equal((await db.query("update mf_casos set cliente='Manipulado' where id=$1 returning id",[caseId])).rows.length,0);
  await denied('delete from mf_casos where id=$1',[caseId]);
  equal((await db.query('select * from mf_tarifas')).rows.length,0);
  equal((await db.query('select * from mf_ventas')).rows.length,0);
  const quoteData={base_clp:4580000,descuento_pct:15,iva_pct:0,detalle:'Taller de prueba',condiciones:'Solo prueba',valida_hasta:'2099-01-01'};
  const quoteSql='select (public.mf_emitir_cotizacion($1,$2,$3,$4::jsonb)).*';
  const operation='20000000-0000-0000-0000-000000000001';
  await denied(quoteSql,[caseId,1,operation,JSON.stringify(quoteData)]);
  await asUser(bob);
  equal((await db.query('select * from mf_casos')).rows.length,0);
  await db.query(insert,[bobCase,bob,bob]);
  await asUser(owner);
  equal((await db.query('select * from mf_casos')).rows.length,2);
  const quote = (await db.query(quoteSql,[caseId,1,operation,JSON.stringify(quoteData)])).rows[0];
  equal(Number(quote.total_clp),3893000);
  equal((await db.query('select estado,version from mf_casos where id=$1',[caseId])).rows[0],{estado:'Cotizado',version:2});
  await db.query(quoteSql,[caseId,1,operation,JSON.stringify(quoteData)]);
  equal((await db.query('select count(*)::int n from mf_cotizaciones')).rows[0].n,1);
  await denied(quoteSql,[caseId,1,'20000000-0000-0000-0000-000000000002',JSON.stringify(quoteData)]);
  await db.query("update mf_casos set cliente='Nombre actualizado' where id=$1",[caseId]);
  equal((await db.query('select snapshot from mf_cotizaciones where id=$1',[quote.id])).rows[0].snapshot.cliente,'Empresa de prueba');
  equal((await db.query("update mf_casos set cliente='Conflicto' where id=$1 and version=2 returning id",[caseId])).rows.length,0);
  await asUser(alice);
  equal((await db.query('select * from mf_casos')).rows.length,1);
  equal((await db.query('select * from mf_cotizaciones')).rows.length,1);
  await denied('update mf_cotizaciones set base_clp=1 where id=$1',[quote.id]);
  await asUser(bob);
  equal((await db.query('select * from mf_cotizaciones')).rows.length,0);
  await asUser(owner);
  const saleSql="select (mf_registrar_venta($1,$2,(now() at time zone 'America/Santiago')::date,'Pendiente')).*";
  await denied(saleSql,[bobCase,quote.id]);
  const sale=(await db.query(saleSql,[caseId,quote.id])).rows[0];
  equal(Number(sale.monto_clp),3893000);
  await db.query(saleSql,[caseId,quote.id]);
  equal((await db.query('select count(*)::int n from mf_ventas')).rows[0].n,1);
  equal((await db.query('select estado from mf_casos where id=$1',[caseId])).rows[0].estado,'Vendido');
  await denied('update mf_ventas set monto_clp=1 where id=$1',[sale.id]);
  await db.query("update mf_ventas set estado_pago='Pagado' where id=$1",[sale.id]);
  equal((await db.query('select version from mf_ventas where id=$1',[sale.id])).rows[0].version,2);
  await asUser(alice);
  await denied(saleSql,[caseId,quote.id]);
  equal((await db.query("update mf_ventas set estado_pago='Pagado' where id=$1 returning id",[sale.id])).rows.length,0);
  await db.exec('reset role; set role anon;');
  for (const table of ['mf_casos','mf_cotizaciones','mf_tarifas','mf_ventas','mf_perfiles']) {
    await denied(`select * from ${table}`);
  }
  await denied(quoteSql,[caseId,1,operation,JSON.stringify(quoteData)]);
  console.log(`OK: ${checks} comprobaciones del esquema inicial.`);

  // Simula tablas adicionales existentes y una política demasiado permisiva.
  await db.exec('reset role');
  for (const table of ['mf_programas','mf_historial','mf_configuracion','casos']) {
    await db.exec(`create table public.${table}(id integer primary key,detalle text);
      insert into public.${table} values(1,'Dato ficticio');
      grant all on public.${table} to authenticated;
      alter table public.${table} enable row level security;
      create policy acceso_anterior on public.${table} for all to authenticated using(true) with check(true);`);
  }
  const initialPolicies=(await db.query("select tablename,policyname,permissive,roles,cmd,qual,with_check from pg_policies where schemaname='public' order by tablename,policyname")).rows;
  const initialTableGrants=(await db.query("select grantee,table_name,privilege_type from information_schema.role_table_grants where table_schema='public' order by grantee,table_name,privilege_type")).rows;
  const initialColumnGrants=(await db.query("select grantee,table_name,column_name,privilege_type from information_schema.column_privileges where table_schema='public' and table_name='mf_casos' order by grantee,column_name,privilege_type")).rows;
  const migration=await readFile(new URL('../supabase/migrations/202610210001_cliente_solo_solicitud.sql',import.meta.url),'utf8');
  await db.exec('create view resumen_abierto as select * from mf_casos');
  await assert.rejects(db.exec(migration),/vista/); checks++;
  await db.exec('rollback;drop view resumen_abierto');
  await db.exec("create function public.lectura_abierta() returns int language sql security definer as $$select 1$$");
  await assert.rejects(db.exec(migration),/SECURITY DEFINER/); checks++;
  await db.exec('rollback;drop function public.lectura_abierta()');
  await db.exec(migration);
  equal((await db.query('select rol from mf_perfiles where id=$1',[owner])).rows[0].rol,'admin');
  const protectedTables=['mf_casos','mf_cotizaciones','mf_tarifas','mf_ventas','mf_programas','mf_historial','mf_configuracion','casos'];
  const webId='30000000-0000-0000-0000-000000000001';
  const webData={cliente:'Organización ficticia',servicio:'Coaching individual',tematica:'Liderazgo',participantes:1,horas:1,modalidad:'Online',consentimiento:true,
    contacto:'Identidad falsa',email:'otro@example.test',cliente_id:bob,creado_por:owner,estado:'Vendido',origen:'Interno',registrado_por:'Administración'};
  const submitSql='select registrar_solicitud($1,$2::jsonb) as recibo';
  await asUser(alice);
  equal((await db.query('select es_admin() as valor')).rows[0].valor,false);
  equal((await db.query('select id from mf_perfiles')).rows.map(x=>x.id),[alice]);
  for (const table of protectedTables) {
    equal((await db.query(`select * from public.${table}`)).rows.length,0);
    equal((await db.query(`delete from public.${table} returning *`)).rows.length,0);
  }
  await denied(insert,['30000000-0000-0000-0000-000000000009',alice,alice]);
  await denied("update mf_perfiles set rol='admin' where id=$1",[alice]);
  await denied('select * from mf_seguridad.respaldos');
  await denied(quoteSql,[caseId,3,operation,JSON.stringify(quoteData)]);
  await denied(saleSql,[caseId,quote.id]);
  await denied(submitSql,[webId,JSON.stringify({...webData,consentimiento:false})]);
  await denied(submitSql,[webId,JSON.stringify({...webData,consentimiento:'true'})]);
  await denied(submitSql,[webId,JSON.stringify({...webData,participantes:0})]);
  await denied(submitSql,[webId,JSON.stringify({...webData,fecha_preferida:'2000-01-01'})]);
  const receipt=(await db.query(submitSql,[webId,JSON.stringify(webData)])).rows[0].recibo;
  equal(Object.keys(receipt),['codigo']);
  assert.match(receipt.codigo,/^MF-\d{4}-\d{4,}$/); checks++;
  equal((await db.query(submitSql,[webId,JSON.stringify(webData)])).rows[0].recibo,receipt);
  equal((await db.query('select * from mf_casos')).rows.length,0);
  await asUser(bob);
  await denied(submitSql,[webId,JSON.stringify(webData)]);
  await db.exec('reset role');
  const saved=(await db.query('select * from mf_casos where id=$1',[webId])).rows[0];
  equal(saved.cliente_id,alice); equal(saved.creado_por,alice);
  equal(saved.contacto,'Alice'); equal(saved.email,'alice@example.test');
  equal(saved.origen,'Formulario web'); equal(saved.registrado_por,'Cliente');
  equal(saved.consentimiento,true); equal(saved.estado,'Solicitud');
  equal((await db.query('select count(*)::int n from mf_casos where id=$1',[webId])).rows[0].n,1);
  // Una política permisiva accidental no debe vencer el límite restrictivo.
  await db.exec('create policy accidental on mf_casos for select to authenticated using(true)');
  await asUser(alice);
  equal((await db.query('select * from mf_casos')).rows.length,0);
  await db.exec('reset role');
  await db.query("insert into auth.users(id,email,raw_user_meta_data) values('00000000-0000-0000-0000-000000000004','new@example.test','{\"nombre\":\"Cliente nuevo\",\"rol\":\"admin\"}')");
  equal((await db.query("select rol from mf_perfiles where email='new@example.test'")).rows[0].rol,'cliente');
  await asUser(owner);
  equal((await db.query('select es_admin() as valor')).rows[0].valor,true);
  for (const table of protectedTables) assert.ok((await db.query(`select * from public.${table}`)).rows.length>0);
  checks+=protectedTables.length;
  await db.query("update mf_casos set detalle='Revisión de Administración' where id=$1",[webId]);
  const extra=(await db.query(insert,['30000000-0000-0000-0000-000000000008',owner,bob])).rows[0];
  const adminQuote=(await db.query(quoteSql,[extra.id,1,'40000000-0000-0000-0000-000000000001',JSON.stringify(quoteData)])).rows[0];
  equal(Number(adminQuote.total_clp),3893000);
  await db.query(saleSql,[extra.id,adminQuote.id]);
  await db.exec('reset role;set role anon');
  await denied(submitSql,[webId,JSON.stringify(webData)]);
  for (const table of [...protectedTables,'mf_perfiles']) await denied(`select * from public.${table}`);
  // Reversión exacta de políticas y privilegios, con conservación de solicitudes.
  await db.exec('reset role');
  await db.exec(await readFile(new URL('../supabase/rollback/202610210001_cliente_solo_solicitud.sql',import.meta.url),'utf8'));
  equal((await db.query('select rol from mf_perfiles where id=$1',[owner])).rows[0].rol,'duena');
  equal((await db.query("select tablename,policyname,permissive,roles,cmd,qual,with_check from pg_policies where schemaname='public' order by tablename,policyname")).rows,initialPolicies);
  equal((await db.query("select grantee,table_name,privilege_type from information_schema.role_table_grants where table_schema='public' order by grantee,table_name,privilege_type")).rows,initialTableGrants);
  const restoredColumns=(await db.query("select grantee,table_name,column_name,privilege_type from information_schema.column_privileges where table_schema='public' and table_name='mf_casos' and column_name not in ('origen','registrado_por','consentimiento','consentimiento_fecha','consentimiento_version') order by grantee,column_name,privilege_type")).rows;
  equal(restoredColumns,initialColumnGrants);
  equal((await db.query('select consentimiento from mf_casos where id=$1',[webId])).rows[0].consentimiento,true);
  await asUser(alice);
  assert.ok((await db.query('select * from mf_casos')).rows.length>0); checks++;
  await db.exec('reset role');
  await db.exec(await readFile(new URL('../supabase/migrations/202610210001_cliente_solo_solicitud.sql',import.meta.url),'utf8'));
  await asUser(alice);
  equal((await db.query('select * from mf_casos')).rows.length,0);
  console.log(`OK: ${checks} comprobaciones totales, incluidas migración, RLS, RPC, identidad, consentimiento, administración, rollback y reaplicación.`);
} finally {
  await db.close();
}
