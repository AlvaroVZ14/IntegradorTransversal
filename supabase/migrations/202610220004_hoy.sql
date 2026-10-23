-- Aplicar completo DESPUÉS de 202610220003_cotizador_asistido.sql. No cambia estados existentes.
begin;
alter table public.mf_casos add column fecha_realizacion date;
alter table public.mf_casos add constraint mf_fecha_realizacion_check
 check(fecha_realizacion is null or fecha_realizacion<=(now() at time zone 'America/Santiago')::date);

create function public.mf_registrar_contacto_hoy(p_caso_id uuid,p_cotizacion_id uuid,p_operacion_id uuid,p_tipo text,p_datos jsonb)
returns public.mf_eventos_caso language plpgsql security definer set search_path='' as $$
declare e public.mf_eventos_caso; envio public.mf_envios_cotizacion;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 if p_tipo not in ('seguimiento','pago','agradecimiento','correo_revisado') then raise exception 'Tipo no válido'; end if;
 if not exists(select 1 from public.mf_casos where id=p_caso_id) then raise exception 'Caso no encontrado'; end if;
 if p_cotizacion_id is not null and not exists(select 1 from public.mf_cotizaciones where id=p_cotizacion_id and caso_id=p_caso_id) then raise exception 'Cotización ajena'; end if;
 if p_tipo='correo_revisado' then
  select * into envio from public.mf_envios_cotizacion where id=(p_datos->>'envio_id')::uuid and caso_id=p_caso_id;
  if not found or envio.estado is distinct from p_datos->>'estado' then raise exception 'El envío cambió'; end if;
 end if;
 insert into public.mf_eventos_caso(operacion_id,caso_id,cotizacion_id,tipo,datos)
 values(p_operacion_id,p_caso_id,p_cotizacion_id,case when p_tipo='correo_revisado' then 'correo_revisado' else 'seguimiento' end,
 jsonb_build_object('tipo_mensaje',p_tipo,'envio_id',p_datos->>'envio_id','estado',p_datos->>'estado'))
 on conflict(operacion_id) do nothing returning * into e;
 if not found then
  select * into e from public.mf_eventos_caso where operacion_id=p_operacion_id;
  if e.caso_id<>p_caso_id or e.creado_por<>auth.uid() then raise exception 'Operación ajena'; end if;
 end if;
 return e;
end $$;

create function public.mf_cerrar_caso_hoy(p_caso_id uuid,p_version integer,p_venta_version integer,p_operacion_id uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare c public.mf_casos; v public.mf_ventas; e public.mf_eventos_caso; anterior text;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select * into c from public.mf_casos where id=p_caso_id for update;
 if not found then raise exception 'Caso no encontrado'; end if;
 select * into e from public.mf_eventos_caso where operacion_id=p_operacion_id;
 if found then
  if e.caso_id<>c.id or e.tipo<>'cierre' or e.creado_por<>auth.uid() or e.deshecho_en is not null then raise exception 'Operación ajena o deshecha'; end if;
  return jsonb_build_object('caso',to_jsonb(c),'evento',to_jsonb(e));
 end if;
 select * into v from public.mf_ventas where caso_id=c.id for update;
 if not found or p_venta_version is null or v.anulada or v.estado_pago<>'Pagado' or v.version<>p_venta_version then raise exception 'Revisa el pago de la venta'; end if;
 if p_version is null or c.version<>p_version or c.estado not in ('Vendido','En ejecución') or c.fecha_realizacion is null or
 c.fecha_realizacion>(now() at time zone 'America/Santiago')::date then raise exception 'Confirma la jornada y el estado actual'; end if;
 anterior:=c.estado;
 update public.mf_casos set estado='Finalizado' where id=c.id returning * into c;
 insert into public.mf_eventos_caso(operacion_id,caso_id,cotizacion_id,tipo,datos)
 values(p_operacion_id,c.id,v.cotizacion_id,'cierre',jsonb_build_object('estado_anterior',anterior,'version_despues',c.version,
 'venta_id',v.id,'venta_version',v.version)) returning * into e;
 return jsonb_build_object('caso',to_jsonb(c),'evento',to_jsonb(e));
end $$;

create function public.mf_deshacer_cierre_hoy(p_evento_id uuid) returns public.mf_casos
language plpgsql security definer set search_path='' as $$
declare e public.mf_eventos_caso; c public.mf_casos; v public.mf_ventas; cid uuid;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select caso_id into cid from public.mf_eventos_caso where id=p_evento_id;
 select * into c from public.mf_casos where id=cid for update;
 select * into e from public.mf_eventos_caso where id=p_evento_id for update;
 if not found or e.tipo<>'cierre' or e.creado_por<>auth.uid() or e.deshecho_en is not null or
 clock_timestamp()>=e.created_at+interval '10 seconds' or c.estado<>'Finalizado' or c.version<>(e.datos->>'version_despues')::integer then raise exception 'Terminó el plazo o el caso cambió'; end if;
 select * into v from public.mf_ventas where id=(e.datos->>'venta_id')::uuid for update;
 if not found or v.version<>(e.datos->>'venta_version')::integer then raise exception 'La venta cambió'; end if;
 update public.mf_casos set estado=e.datos->>'estado_anterior' where id=c.id returning * into c;
 update public.mf_eventos_caso set deshecho_en=clock_timestamp() where id=e.id;
 return c;
end $$;
revoke all on function public.mf_registrar_contacto_hoy(uuid,uuid,uuid,text,jsonb),
 public.mf_cerrar_caso_hoy(uuid,integer,integer,uuid),public.mf_deshacer_cierre_hoy(uuid) from public,anon;
grant execute on function public.mf_registrar_contacto_hoy(uuid,uuid,uuid,text,jsonb),
 public.mf_cerrar_caso_hoy(uuid,integer,integer,uuid),public.mf_deshacer_cierre_hoy(uuid) to authenticated;
notify pgrst,'reload schema';
commit;
