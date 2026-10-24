-- Desactivar el worker y volver primero al código anterior.
-- No elimina casos, campos nuevos, catálogos ni avisos.
begin;
do $$ declare r record;begin
 if exists(select 1 from public.mf_casos where datos_incompletos) then
  raise exception 'Completa los casos con datos pendientes antes de volver al código anterior';
 end if;
 for r in select * from mf_seguridad.formulario_unificado_respaldo loop execute r.definicion;end loop;
 if not exists(select 1 from mf_seguridad.formulario_unificado_respaldo where nombre='registrar_solicitud_publica') then
  drop function if exists public.registrar_solicitud_publica(uuid,text,jsonb,text);
 end if;
 if not exists(select 1 from mf_seguridad.formulario_unificado_respaldo where nombre='mf_configuracion_publica') then
  drop function if exists public.mf_configuracion_publica();
 end if;
end $$;
drop function if exists public.mf_catalogo_solicitudes();
drop function if exists public.mf_tomar_avisos_solicitud();
drop function if exists public.mf_confirmar_aviso_solicitud(uuid,uuid,text);
notify pgrst,'reload schema';
commit;
