-- Después de las migraciones 202610210001, 202610220001 y 202610220002.
-- No modifica cotizaciones ni ventas históricas. Aplicar completo.
begin;
create table public.mf_configuracion(
 id text primary key check(id='general'),datos jsonb not null default '{}',version integer not null default 1,
 created_at timestamptz not null default now(),updated_at timestamptz not null default now());
insert into public.mf_configuracion(id) values('general');
create table public.mf_plantillas_programa(
 id uuid primary key default gen_random_uuid(),nombre text not null check(length(nombre) between 2 and 180),
 servicio text not null,tematica text,textos jsonb not null,activa boolean not null default true,
 version integer not null default 1,created_at timestamptz not null default now(),updated_at timestamptz not null default now());
create table public.mf_borradores_cotizacion(
 id uuid primary key references public.mf_casos(id) on delete cascade,datos jsonb not null,
 editado_por uuid not null default auth.uid() references auth.users(id),version integer not null default 1,
 created_at timestamptz not null default now(),updated_at timestamptz not null default now());
create table public.mf_eventos_caso(
 id uuid primary key default gen_random_uuid(),operacion_id uuid not null unique,
 caso_id uuid not null references public.mf_casos(id),cotizacion_id uuid references public.mf_cotizaciones(id),
 tipo text not null,datos jsonb not null default '{}',creado_por uuid not null default auth.uid() references auth.users(id),
 deshecho_en timestamptz,created_at timestamptz not null default now());
create table public.mf_envios_cotizacion(
 id uuid primary key,caso_id uuid not null references public.mf_casos(id),cotizacion_id uuid not null references public.mf_cotizaciones(id),
 canal text not null check(canal in ('correo','WhatsApp')),destinatario text not null,
 estado text not null default 'preparado' check(estado in ('preparado','enviado','incierto','error')),
 creado_por uuid not null default auth.uid() references auth.users(id),created_at timestamptz not null default now(),
 enviado_en timestamptz);
alter table public.mf_tarifas add column tematica text;
alter table public.mf_cotizaciones add column documento jsonb not null default '{}',
 add column version_cotizacion integer not null default 1,add column descuento_motivo text not null default '';
alter table public.mf_casos add column cotizacion_aceptada_id uuid,
 add column motivo_rechazo text not null default '';
alter table public.mf_casos add constraint mf_aceptada_del_caso foreign key(cotizacion_aceptada_id,id)
 references public.mf_cotizaciones(id,caso_id);
alter table public.mf_ventas add column reserva_pct numeric(5,2),add column remuneracion_pct numeric(5,2),
 add column reserva_clp bigint,add column remuneracion_clp bigint,add column documento_numero text not null default '';
alter table public.mf_ventas add constraint mf_reparto_valido check(
 (reserva_pct is null and remuneracion_pct is null and reserva_clp is null and remuneracion_clp is null) or
 (reserva_pct is not null and remuneracion_pct is not null and reserva_clp is not null and remuneracion_clp is not null
 and reserva_pct between 0 and 100 and remuneracion_pct between 0 and 100 and reserva_pct+remuneracion_pct=100
 and reserva_clp>=0 and remuneracion_clp>=0 and reserva_clp+remuneracion_clp=monto_clp));
do $$ declare t text; begin
 foreach t in array array['mf_configuracion','mf_plantillas_programa','mf_borradores_cotizacion','mf_eventos_caso','mf_envios_cotizacion'] loop
  execute format('alter table public.%I enable row level security',t);
  execute format('revoke all on table public.%I from public,anon,authenticated',t);
  execute format('grant select,insert,update,delete on public.%I to authenticated',t);
  execute format('create policy mf_admin on public.%I for all to authenticated using((select public.es_admin())) with check((select public.es_admin()))',t);
  execute format('create policy mf_limite on public.%I as restrictive for all to authenticated using((select public.es_admin())) with check((select public.es_admin()))',t);
 end loop;
end $$;
create trigger mf_config_version before update on public.mf_configuracion for each row execute function public.mf_actualizar_version();
create trigger mf_plantilla_version before update on public.mf_plantillas_programa for each row execute function public.mf_actualizar_version();
create trigger mf_borrador_version before update on public.mf_borradores_cotizacion for each row execute function public.mf_actualizar_version();

create function public.mf_guardar_borrador(p_caso_id uuid,p_version integer,p_datos jsonb)
returns public.mf_borradores_cotizacion language plpgsql security definer set search_path='' as $$
declare b public.mf_borradores_cotizacion;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 if jsonb_typeof(p_datos)<>'object' or octet_length(p_datos::text)>150000 then raise exception 'Borrador no válido'; end if;
 insert into public.mf_borradores_cotizacion(id,datos,editado_por) values(p_caso_id,p_datos,auth.uid())
 on conflict(id) do update set datos=excluded.datos,editado_por=auth.uid()
 where mf_borradores_cotizacion.version=p_version returning * into b;
 if not found then raise exception 'El borrador cambió en otra sesión' using errcode='40001'; end if;
 return b;
end $$;

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
 insert into public.mf_cotizaciones(operacion_id,caso_id,tarifa_id,base_clp,descuento_pct,iva_pct,detalle,condiciones,valida_hasta,snapshot,creado_por,documento,version_cotizacion,descuento_motivo)
 values(p_operacion_id,c.id,nullif(p_datos->>'tarifa_id','')::uuid,(p_datos->>'base_clp')::bigint,
 (p_datos->>'descuento_pct')::numeric,(p_datos->>'iva_pct')::integer,p_datos->>'detalle',coalesce(p_datos->>'condiciones',''),
 (p_datos->>'valida_hasta')::date,to_jsonb(c)||jsonb_build_object('caso_numero',c.numero),auth.uid(),coalesce(p_datos->'documento','{}'),n,coalesce(p_datos->>'descuento_motivo','')) returning * into q;
 update public.mf_casos set estado='Cotizado' where id=c.id;
 return q;
end $$;

create function public.mf_decidir_cotizacion(p_caso_id uuid,p_cotizacion_id uuid,p_version integer,p_operacion_id uuid,p_datos jsonb)
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
  if coalesce(p_datos->>'motivo','') not in ('','Precio','Fecha','Eligió otra empresa','Otro') then raise exception 'Motivo no válido'; end if;
  update public.mf_casos set estado='Cancelado',motivo_rechazo=concat_ws(' · ',nullif(p_datos->>'motivo',''),nullif(left(p_datos->>'nota',500),'')) where id=c.id returning * into c;
 else raise exception 'Acción no válida'; end if;
 insert into public.mf_eventos_caso(operacion_id,caso_id,cotizacion_id,tipo,datos)
 values(p_operacion_id,c.id,q.id,accion,jsonb_build_object('estado_anterior',anterior.estado,'aceptada_anterior',anterior.cotizacion_aceptada_id,
 'rechazo_anterior',anterior.motivo_rechazo,'version_despues',c.version,'venta_id',v.id,'motivo',p_datos->>'motivo')) returning * into e;
 return jsonb_build_object('caso',to_jsonb(c),'venta',to_jsonb(v),'evento',to_jsonb(e));
end $$;

create function public.mf_deshacer_decision(p_evento_id uuid) returns public.mf_casos
language plpgsql security definer set search_path='' as $$
declare e public.mf_eventos_caso; c public.mf_casos; v public.mf_ventas; cid uuid;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select caso_id into cid from public.mf_eventos_caso where id=p_evento_id;
 select * into c from public.mf_casos where id=cid for update;
 select * into e from public.mf_eventos_caso where id=p_evento_id for update;
 if not found or e.creado_por<>auth.uid() or e.tipo not in ('aceptar','vender') or e.deshecho_en is not null or
 clock_timestamp()>=e.created_at+interval '10 seconds' or c.version<>(e.datos->>'version_despues')::integer then raise exception 'Terminó el plazo o el caso cambió'; end if;
 if nullif(e.datos->>'venta_id','') is not null then
  select * into v from public.mf_ventas where id=(e.datos->>'venta_id')::uuid for update;
  if not found or v.version<>1 or v.creado_por<>auth.uid() or v.anulada then raise exception 'La venta cambió'; end if;
  delete from public.mf_ventas where id=v.id;
 elsif exists(select 1 from public.mf_ventas where caso_id=c.id) then raise exception 'Ya se registró una venta'; end if;
 update public.mf_casos set estado=e.datos->>'estado_anterior',cotizacion_aceptada_id=nullif(e.datos->>'aceptada_anterior','')::uuid,
 motivo_rechazo=coalesce(e.datos->>'rechazo_anterior','') where id=c.id returning * into c;
 update public.mf_eventos_caso set deshecho_en=clock_timestamp() where id=e.id;
 return c;
end $$;

create function public.mf_preparar_envio(p_id uuid,p_cotizacion_id uuid,p_canal text,p_destinatario text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare q public.mf_cotizaciones; e public.mf_envios_cotizacion;
begin
 if not public.es_admin() then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select * into q from public.mf_cotizaciones where id=p_cotizacion_id;
 if not found then raise exception 'Cotización no encontrada'; end if;
 insert into public.mf_envios_cotizacion(id,caso_id,cotizacion_id,canal,destinatario) values(p_id,q.caso_id,q.id,p_canal,p_destinatario)
 on conflict(id) do nothing returning * into e;
 if found then return jsonb_build_object('nuevo',true,'envio',to_jsonb(e)); end if;
 select * into e from public.mf_envios_cotizacion where id=p_id;
 if e.creado_por<>auth.uid() or e.cotizacion_id<>q.id then raise exception 'Operación ajena'; end if;
 return jsonb_build_object('nuevo',false,'envio',to_jsonb(e));
end $$;
create function public.mf_confirmar_envio(p_id uuid,p_estado text) returns public.mf_envios_cotizacion
language plpgsql security definer set search_path='' as $$
declare e public.mf_envios_cotizacion;
begin
 if not public.es_admin() or p_estado not in ('enviado','incierto','error') then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select * into e from public.mf_envios_cotizacion where id=p_id and creado_por=auth.uid() for update;
 if not found then raise exception 'Envío ajeno'; end if;
 if e.estado='enviado' then return e; end if;
 update public.mf_envios_cotizacion set estado=p_estado,enviado_en=case when p_estado='enviado' then now() else null end where id=p_id returning * into e;
 if p_estado='enviado' then
  insert into public.mf_eventos_caso(operacion_id,caso_id,cotizacion_id,tipo,datos)
  values(e.id,e.caso_id,e.cotizacion_id,'envio',jsonb_build_object('canal',e.canal,'destinatario',e.destinatario)) on conflict(operacion_id) do nothing;
 end if;
 return e;
end $$;
revoke all on function public.mf_guardar_borrador(uuid,integer,jsonb),public.mf_decidir_cotizacion(uuid,uuid,integer,uuid,jsonb),
 public.mf_deshacer_decision(uuid),public.mf_preparar_envio(uuid,uuid,text,text),public.mf_confirmar_envio(uuid,text) from public,anon;
grant execute on function public.mf_guardar_borrador(uuid,integer,jsonb),public.mf_decidir_cotizacion(uuid,uuid,integer,uuid,jsonb),
 public.mf_deshacer_decision(uuid),public.mf_preparar_envio(uuid,uuid,text,text),public.mf_confirmar_envio(uuid,text) to authenticated;
notify pgrst,'reload schema';
commit;
