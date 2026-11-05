-- Restaura la regla anterior. Conserva la restricción ampliada para no perder
-- ni invalidar casos LinkedIn/Correo recibidos después de aplicar Prompt 37.
begin;
create or replace function mf_seguridad.normalizar_canal(valor text) returns text
language sql immutable set search_path='' as $$
 select case when valor is null then 'directo'
 when valor in ('instagram','facebook','whatsapp','sitio_web','qr','directo','otro') then valor else 'otro' end;
$$;
revoke all on function mf_seguridad.normalizar_canal(text) from public,anon,authenticated;
commit;
