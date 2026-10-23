-- Reversión: ejecutar como postgres y luego restaurar la versión anterior del código.
-- Conserva los casos nuevos y sus metadatos de consentimiento.
begin;
do $$ declare respaldo jsonb; tabla text; p record; sentencia text; begin
  select datos into respaldo from mf_seguridad.respaldos where cambio='cliente_solo_solicitud_v1';
  if respaldo is null then raise exception 'No hay respaldo para esta migración'; end if;
  for tabla in select jsonb_array_elements_text(respaldo->'tablas') loop
    for p in select policyname from pg_policies where schemaname='public' and tablename=tabla loop
      execute format('drop policy %I on public.%I',p.policyname,tabla);
    end loop;
  end loop;
  alter table public.mf_perfiles drop constraint mf_perfiles_rol_v2_check;
  update public.mf_perfiles set rol='duena' where rol='admin';
  for sentencia in select jsonb_array_elements_text(respaldo->'restricciones_rol') loop execute sentencia; end loop;
  execute respaldo->>'mf_es_duena';
  for sentencia in select jsonb_array_elements_text(respaldo->'restaurar') loop execute sentencia; end loop;
end $$;
drop function public.registrar_solicitud(uuid,jsonb);
drop function public.es_admin();
-- Las columnas se conservan para mantener la trazabilidad de envíos ya recibidos.
delete from mf_seguridad.respaldos where cambio='cliente_solo_solicitud_v1';
notify pgrst,'reload schema';
commit;
