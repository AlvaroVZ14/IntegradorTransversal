-- Prompt 37. Requiere 202610240002_compartir_canales.sql.
-- No cambia datos, permisos, origen ni el contrato de las RPC existentes.
begin;
alter table public.mf_casos drop constraint if exists mf_canal_captacion_check;
alter table public.mf_casos add constraint mf_canal_captacion_check
 check(canal_captacion in ('instagram','facebook','whatsapp','linkedin','correo','sitio_web','qr','directo','otro'));
create or replace function mf_seguridad.normalizar_canal(valor text) returns text
language sql immutable set search_path='' as $$
 select case valor
 when 'ig' then 'instagram' when 'fb' then 'facebook' when 'wa' then 'whatsapp'
 when 'li' then 'linkedin' when 'mail' then 'correo' when 'web' then 'sitio_web'
 when 'instagram' then valor when 'facebook' then valor when 'whatsapp' then valor
 when 'linkedin' then valor when 'correo' then valor when 'sitio_web' then valor
 when 'qr' then valor when 'directo' then valor when 'otro' then valor
 else 'directo' end;
$$;
revoke all on function mf_seguridad.normalizar_canal(text) from public,anon,authenticated;
commit;
