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
    create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}');
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
  console.log(`OK: ${checks} comprobaciones SQL de esquema, permisos, aislamiento, cálculos, concurrencia y reintentos.`);
} finally {
  await db.close();
}
