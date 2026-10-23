-- Solo lectura. Ejecutar como postgres si existe un historial creado fuera
-- de las migraciones del proyecto. No altera tablas, permisos ni datos.
select table_name,column_name,data_type,is_nullable
from information_schema.columns
where table_schema='public' and table_name in ('mf_casos','mf_historial','historial')
order by table_name,ordinal_position;

select event_object_table,trigger_name,action_timing,event_manipulation,action_statement
from information_schema.triggers
where trigger_schema='public' and event_object_table in ('mf_casos','mf_historial','historial')
order by event_object_table,trigger_name;

select schemaname,tablename,policyname,roles,cmd,qual,with_check
from pg_policies where schemaname='public' and tablename in ('mf_historial','historial');
