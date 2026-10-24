-- Ejecutar después de 202610220005_mantenimiento.sql. Solo agrega una lectura.
begin;
create or replace function public.mf_lectura_en_vivo(p_vista text) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare resultado jsonb;
begin
 if not coalesce(public.es_admin(),false) then
   raise exception 'Acceso denegado' using errcode='42501';
 end if;
 if p_vista not in ('dashboard','hoy','casos') or p_vista is null then
   raise exception 'Vista inválida' using errcode='22023';
 end if;
 select jsonb_build_object('casos',coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb))
 into resultado from public.mf_casos t;
 if p_vista in ('dashboard','hoy') then
   resultado=resultado || jsonb_build_object('ventas',
     (select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_ventas t));
 end if;
 if p_vista='hoy' then
   resultado=resultado || jsonb_build_object(
     'cotizaciones',(select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_cotizaciones t),
     'eventos',(select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_eventos_caso t),
     'envios',(select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_envios_cotizacion t),
     'configuracion',coalesce((select datos from public.mf_configuracion where id='general'),'{}'::jsonb));
 end if;
 return resultado;
end $$;
revoke all on function public.mf_lectura_en_vivo(text) from public,anon;
grant execute on function public.mf_lectura_en_vivo(text) to authenticated;
notify pgrst,'reload schema';
commit;
