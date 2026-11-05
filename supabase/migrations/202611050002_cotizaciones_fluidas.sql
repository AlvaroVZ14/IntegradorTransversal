-- Prompt 35: conserva permisos, datos e idempotencia; nuevos motivos de rechazo.
begin;
create or replace function public.mf_decidir_cotizacion(p_caso_id uuid,p_cotizacion_id uuid,p_version integer,p_operacion_id uuid,p_datos jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare c public.mf_casos; anterior public.mf_casos; q public.mf_cotizaciones; v public.mf_ventas;
 e public.mf_eventos_caso; accion text; monto bigint; reserva numeric; remuneracion numeric; fecha date;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select * into c from public.mf_casos where id=p_caso_id for update;
 if not found then raise exception 'Caso no encontrado'; end if;
 select * into e from public.mf_eventos_caso where operacion_id=p_operacion_id;
 if found then
  if e.caso_id<>c.id or e.deshecho_en is not null then raise exception 'Operación ya deshecha o ajena'; end if;
  return jsonb_build_object('caso',to_jsonb(c),'evento',to_jsonb(e));
 end if;
 if c.version<>p_version then raise exception 'El caso cambió'; end if;
 select * into q from public.mf_cotizaciones where id=p_cotizacion_id and caso_id=c.id;
 if not found then raise exception 'Cotización ajena'; end if;
 if c.estado in ('Finalizado','Cancelado') or exists(select 1 from public.mf_ventas where caso_id=c.id) then raise exception 'Caso cerrado o con venta'; end if;
 anterior:=c; accion:=p_datos->>'accion';
 if accion='vender' then
  monto:=(p_datos->>'monto_clp')::bigint; reserva:=(p_datos->>'reserva_pct')::numeric; remuneracion:=(p_datos->>'remuneracion_pct')::numeric;
  fecha:=(p_datos->>'fecha')::date;
  if monto is null or reserva is null or remuneracion is null or fecha is null or
   reserva+remuneracion<>100 or reserva not between 0 and 100 or remuneracion not between 0 and 100 then raise exception 'Revisa monto y reparto'; end if;
  if fecha> (now() at time zone 'America/Santiago')::date or fecha<q.fecha_emision or fecha>q.valida_hasta then raise exception 'Fecha fuera de vigencia'; end if;
  insert into public.mf_ventas(caso_id,cotizacion_id,monto_clp,fecha_venta,estado_pago,creado_por,reserva_pct,remuneracion_pct,reserva_clp,remuneracion_clp,documento_numero)
  values(c.id,q.id,monto,fecha,p_datos->>'estado_pago',auth.uid(),reserva,remuneracion,round(monto*reserva/100),monto-round(monto*reserva/100),left(coalesce(p_datos->>'documento_numero',''),100)) returning * into v;
  update public.mf_casos set estado='En ejecución',cotizacion_aceptada_id=q.id,motivo_rechazo='' where id=c.id returning * into c;
 elsif accion='aceptar' then
  if q.valida_hasta<(now() at time zone 'America/Santiago')::date then raise exception 'Cotización vencida'; end if;
  update public.mf_casos set estado='Vendido',cotizacion_aceptada_id=q.id,motivo_rechazo='' where id=c.id returning * into c;
 elsif accion='rechazar' then
  if coalesce(p_datos->>'motivo','') not in ('','Precio','Fecha','Sin presupuesto','Eligió a otro proveedor','Eligió otra empresa','Otro') then raise exception 'Motivo no válido'; end if;
  update public.mf_casos set estado='Cancelado',motivo_rechazo=concat_ws(' · ',nullif(p_datos->>'motivo',''),nullif(left(p_datos->>'nota',500),'')) where id=c.id returning * into c;
 else raise exception 'Acción no válida'; end if;
 insert into public.mf_eventos_caso(operacion_id,caso_id,cotizacion_id,tipo,datos)
 values(p_operacion_id,c.id,q.id,accion,jsonb_build_object('estado_anterior',anterior.estado,'aceptada_anterior',anterior.cotizacion_aceptada_id,
 'rechazo_anterior',anterior.motivo_rechazo,'version_despues',c.version,'venta_id',v.id,'motivo',p_datos->>'motivo')) returning * into e;
 return jsonb_build_object('caso',to_jsonb(c),'venta',to_jsonb(v),'evento',to_jsonb(e));
end $$;

commit;
