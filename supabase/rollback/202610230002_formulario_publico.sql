-- Revertir el código antes de ejecutar. Conserva TODOS los casos y recibos.
begin;
drop function if exists public.registrar_solicitud_publica(uuid,text,jsonb,text);
drop function if exists public.mf_configuracion_publica();
-- La autoría NULL se conserva si ya hubo solicitudes anónimas. No se inventa
-- una cuenta propietaria ni se eliminan solicitudes para restaurar NOT NULL.
do $$ begin
 if not exists(select 1 from public.mf_casos where creado_por is null) then
  alter table public.mf_casos alter column creado_por set not null;
 end if;
end $$;
notify pgrst,'reload schema';
commit;
