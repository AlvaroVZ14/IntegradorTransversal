begin;
drop function if exists public.mf_deshacer_aceptacion(uuid,integer);
drop trigger if exists mf_aceptacion_anterior on public.mf_ventas;
drop function if exists public.mf_capturar_aceptacion();
alter table public.mf_ventas drop column if exists estado_caso_anterior,drop column if exists caso_version_aceptada;
notify pgrst,'reload schema';
commit;
