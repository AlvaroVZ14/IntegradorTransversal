-- Prompt 34. Solo amplía una lectura administrativa; no cambia datos ni tablas.
-- Aplicar después de 202610230001_lectura_en_vivo.sql.
begin;
create or replace function public.mf_lectura_en_vivo(p_vista text) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare resultado jsonb; documentos jsonb:='[]'::jsonb;
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
   -- Compatible con una instalación anterior a Documentos o a origen cliente.
   if pg_catalog.to_regclass('public.mf_documentos') is not null then
     execute $consulta$
       select coalesce(jsonb_agg(x.datos order by x.fecha_subida desc,x.id),'[]'::jsonb)
       from (
         select d.id,d.fecha_subida,jsonb_build_object('id',d.id,'caso_id',d.caso_id,
           'tipo',d.tipo,'fecha_subida',d.fecha_subida,'origen','cliente','estado_archivo','disponible') datos
         from public.mf_documentos d
         where to_jsonb(d)->>'origen'='cliente' and d.estado_archivo='disponible'
         order by d.fecha_subida desc,d.id limit 5
       ) x
     $consulta$ into documentos;
   end if;
   resultado=resultado || jsonb_build_object(
     'cotizaciones',(select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_cotizaciones t),
     'eventos',(select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_eventos_caso t),
     'envios',(select coalesce(jsonb_agg(to_jsonb(t) order by t.created_at desc,t.id),'[]'::jsonb) from public.mf_envios_cotizacion t),
     'documentos',documentos,
     'configuracion',coalesce((select datos from public.mf_configuracion where id='general'),'{}'::jsonb));
 end if;
 return resultado;
end $$;
revoke all on function public.mf_lectura_en_vivo(text) from public,anon;
grant execute on function public.mf_lectura_en_vivo(text) to authenticated;
notify pgrst,'reload schema';
commit;
