-- Activación opcional de Deshacer para una venta recién registrada.
-- Ejecutar después de 202610210001. No modifica importes ni ventas anteriores.
begin;
alter table public.mf_ventas
  add column if not exists estado_caso_anterior text,
  add column if not exists caso_version_aceptada integer;

create or replace function public.mf_capturar_aceptacion() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  select estado,version+1 into new.estado_caso_anterior,new.caso_version_aceptada
  from public.mf_casos where id=new.caso_id;
  return new;
end $$;
revoke all on function public.mf_capturar_aceptacion() from public,anon,authenticated;
drop trigger if exists mf_aceptacion_anterior on public.mf_ventas;
create trigger mf_aceptacion_anterior before insert on public.mf_ventas
for each row execute function public.mf_capturar_aceptacion();

create or replace function public.mf_deshacer_aceptacion(p_venta_id uuid,p_version integer)
returns public.mf_casos language plpgsql security definer set search_path='' as $$
declare venta public.mf_ventas; caso public.mf_casos; caso_id uuid;
begin
  if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
  select v.caso_id into caso_id from public.mf_ventas v where v.id=p_venta_id;
  if caso_id is null then raise exception 'La venta ya no está disponible'; end if;
  -- Mismo orden de bloqueo que registrar venta: caso y después venta.
  select * into caso from public.mf_casos where id=caso_id for update;
  select * into venta from public.mf_ventas where id=p_venta_id for update;
  if not found then raise exception 'La venta ya no está disponible'; end if;
  if venta.creado_por<>auth.uid() or venta.anulada or venta.version<>1 or
     venta.estado_caso_anterior is null or venta.caso_version_aceptada is null or
     clock_timestamp()>=venta.created_at+interval '10 seconds' or
     caso.estado<>'Vendido' or caso.version<>p_version or caso.version<>venta.caso_version_aceptada then
    raise exception 'El plazo terminó o el caso cambió. No se deshizo la venta';
  end if;
  -- Revierte exclusivamente la aceptación recién creada, de forma atómica.
  -- La anulación ordinaria sigue siendo una acción distinta y confirmada.
  delete from public.mf_ventas where id=venta.id;
  update public.mf_casos set estado=venta.estado_caso_anterior where id=caso.id returning * into caso;
  return caso;
end $$;
revoke all on function public.mf_deshacer_aceptacion(uuid,integer) from public,anon;
grant execute on function public.mf_deshacer_aceptacion(uuid,integer) to authenticated;
notify pgrst,'reload schema';
commit;
