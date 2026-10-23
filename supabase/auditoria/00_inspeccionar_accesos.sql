-- Solo lectura. Ejecutar en SQL Editor ANTES de la migración nueva.
select c.relname as tabla, c.relrowsecurity as rls, c.relforcerowsecurity as rls_forzado,
       a.attname as columna, pg_catalog.format_type(a.atttypid,a.atttypmod) as tipo
from pg_class c join pg_namespace n on n.oid=c.relnamespace
join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
where n.nspname='public' and c.relkind in ('r','p') order by c.relname,a.attnum;
select * from pg_policies where schemaname='public' order by tablename,policyname;
select * from information_schema.role_table_grants
where table_schema='public' and grantee in ('anon','authenticated','PUBLIC');
select * from information_schema.role_column_grants
where table_schema='public' and grantee in ('anon','authenticated','PUBLIC');
select p.oid::regprocedure as funcion, p.prosecdef as security_definer,
       pg_get_functiondef(p.oid) as definicion
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and (p.proname like 'mf_%' or p.proname in ('es_admin','registrar_solicitud'));
select rol,count(*) as cuentas from public.mf_perfiles group by rol;
select c.relname,c.relkind,pg_get_viewdef(c.oid) as definicion
from pg_class c join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind in ('v','m');
select p.oid::regprocedure as funcion,pg_get_functiondef(p.oid) as definicion
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.prosecdef and p.prokind='f'
  and has_function_privilege('authenticated',p.oid,'EXECUTE');
