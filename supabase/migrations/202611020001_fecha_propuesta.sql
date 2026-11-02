-- Fecha editable de la propuesta. Conserva firma, permisos, bloqueo, versiones e idempotencia.
-- No altera tablas, datos existentes ni requiere ajustes generales.
begin;
create or replace function public.mf_emitir_cotizacion(p_caso_id uuid,p_version integer,p_operacion_id uuid,p_datos jsonb)
returns public.mf_cotizaciones language plpgsql security definer set search_path='' as $$
declare c public.mf_casos; q public.mf_cotizaciones; n integer;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select * into c from public.mf_casos where id=p_caso_id for update;
 if not found then raise exception 'Caso no encontrado'; end if;
 select * into q from public.mf_cotizaciones where operacion_id=p_operacion_id;
 if found then
  if q.caso_id<>p_caso_id then raise exception 'Operación no válida'; end if;
  return q;
 end if;
 if c.version<>p_version then raise exception 'El caso cambió. Actualiza antes de emitir.'; end if;
 if c.estado in ('Vendido','En ejecución','Finalizado','Cancelado') or exists(select 1 from public.mf_ventas where caso_id=c.id) then raise exception 'Caso cerrado o vendido'; end if;
 if (p_datos->>'descuento_pct')::numeric>0 and length(trim(coalesce(p_datos->>'descuento_motivo','')))=0 then raise exception 'Indica el motivo del descuento'; end if;
 select coalesce(max(version_cotizacion),0)+1 into n from public.mf_cotizaciones where caso_id=c.id;
 insert into public.mf_cotizaciones(operacion_id,caso_id,tarifa_id,base_clp,descuento_pct,iva_pct,detalle,condiciones,fecha_emision,valida_hasta,snapshot,creado_por,documento,version_cotizacion,descuento_motivo)
 values(p_operacion_id,c.id,nullif(p_datos->>'tarifa_id','')::uuid,(p_datos->>'base_clp')::bigint,
 (p_datos->>'descuento_pct')::numeric,(p_datos->>'iva_pct')::integer,p_datos->>'detalle',coalesce(p_datos->>'condiciones',''),
 coalesce(nullif(p_datos->>'fecha_emision','')::date,(now() at time zone 'America/Santiago')::date),
 (p_datos->>'valida_hasta')::date,to_jsonb(c)||jsonb_build_object('caso_numero',c.numero),auth.uid(),coalesce(p_datos->'documento','{}'),n,coalesce(p_datos->>'descuento_motivo','')) returning * into q;
 update public.mf_casos set estado='Cotizado' where id=c.id;
 return q;
end $$;


-- Entrada versionada: un despliegue anterior no puede ignorar los campos nuevos.
create or replace function public.mf_emitir_propuesta_v2(p_caso_id uuid,p_version integer,p_operacion_id uuid,p_datos jsonb)
returns public.mf_cotizaciones language sql security invoker set search_path='' as $$
 select public.mf_emitir_cotizacion(p_caso_id,p_version,p_operacion_id,p_datos);
$$;
revoke all on function public.mf_emitir_propuesta_v2(uuid,integer,uuid,jsonb) from public,anon;
grant execute on function public.mf_emitir_propuesta_v2(uuid,integer,uuid,jsonb) to authenticated;
commit;
