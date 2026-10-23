-- Solo elimina metadatos de mantenimiento. No borra casos ni respaldos de GitHub.
begin;
drop function if exists public.mf_exportar_respaldo();
drop table if exists public.mf_mantenimiento;
commit;
