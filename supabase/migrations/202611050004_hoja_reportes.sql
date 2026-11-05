-- Esquema PRIVADO: NO añadir reportes a los esquemas expuestos de la API.
-- No contiene contraseñas. El rol nace sin poder iniciar sesión.
begin;
create schema reportes;
revoke all on schema reportes from public,anon,authenticated,service_role;
do $$begin
 if not exists(select 1 from pg_roles where rolname='mfy_hoja') then create role mfy_hoja nologin noinherit; end if;
end$$;
alter role mfy_hoja set statement_timeout='30s';
alter default privileges in schema reportes revoke all on tables from public,anon,authenticated;
alter default privileges in schema reportes revoke execute on functions from public,anon,authenticated;

create function reportes.texto(t text) returns text language sql immutable set search_path='' as $$
 select trim(regexp_replace(coalesce(t,''),'[[:space:]]+',' ','g'));
$$;
create function reportes.codigo(n bigint,f timestamptz) returns text language sql immutable set search_path='' as $$
 select 'MF-'||extract(year from f at time zone 'America/Santiago')::text||'-'||lpad(n::text,greatest(4,length(n::text)),'0');
$$;
create function reportes.empresa(c text,p text) returns text language sql immutable set search_path='' as $$
 select case when lower(reportes.texto(c))=lower(reportes.texto(p)) or reportes.texto(c)='' then 'Cliente particular' else reportes.texto(c) end;
$$;
create table reportes.caso_estado(caso_id uuid primary key references public.mf_casos(id) on delete cascade,fecha timestamptz not null);
insert into reportes.caso_estado select id,updated_at from public.mf_casos;
alter table reportes.caso_estado enable row level security;

create view reportes.v_hoja_casos as
select reportes.codigo(c.numero,c.created_at) codigo,
 (c.created_at at time zone 'America/Santiago')::date fecha_solicitud,
 extract(year from c.created_at at time zone 'America/Santiago')::int "año",
 to_char(c.created_at at time zone 'America/Santiago','YYYY-MM') mes,
 to_char(c.created_at at time zone 'America/Santiago','YYYY')||'-T'||extract(quarter from c.created_at at time zone 'America/Santiago')::int trimestre,
 to_char(c.created_at at time zone 'America/Santiago','YYYY')||'-S'||case when extract(month from c.created_at at time zone 'America/Santiago')<=6 then '1' else '2' end semestre,
 reportes.empresa(c.cliente,c.contacto) empresa,reportes.texto(c.servicio) tipo_servicio,
 reportes.texto(c.tematica) tematica,reportes.texto(c.modalidad) modalidad,c.participantes,c.horas,
 reportes.texto(c.origen) origen_pedido,
 case c.canal_captacion when 'instagram' then 'Instagram' when 'facebook' then 'Facebook' when 'whatsapp' then 'WhatsApp' when 'linkedin' then 'LinkedIn' when 'correo' then 'Correo' when 'qr' then 'Código QR' when 'sitio_web' then 'Sitio web' when 'directo' then 'Directo' when 'otro' then 'Otro' else 'Sin canal registrado' end canal_captacion,
 case when c.registrado_por='Cliente' then 'Cliente' else 'Administración' end registrado_por,
 case c.estado when 'Cotizado' then 'Cotizada' when 'Vendido' then 'Aceptada' when 'En ejecución' then 'En seguimiento' when 'Finalizado' then 'Cerrada' when 'Cancelado' then 'Rechazada' else 'Solicitud' end estado,
 (coalesce(e.fecha,c.updated_at) at time zone 'America/Santiago')::date fecha_ultimo_cambio,
 greatest(0,(now() at time zone 'America/Santiago')::date-(coalesce(e.fecha,c.updated_at) at time zone 'America/Santiago')::date) dias_en_estado,
 case when split_part(c.motivo_rechazo,' · ',1) in ('Precio','Fecha','Eligió otra empresa','Eligió a otro proveedor','Sin presupuesto','Otro') then split_part(c.motivo_rechazo,' · ',1) else '' end motivo_rechazo,
 case when c.datos_incompletos then 'SI' else 'NO' end faltan_datos,
 coalesce(q.total_clp,0) monto_cotizado,case when v.id is null then 'NO' else 'SI' end tiene_venta,
 coalesce(v.monto_clp,0) monto_vendido,
 case v.estado_pago when 'Abono recibido' then 'Anticipo pagado' else coalesce(v.estado_pago,'Sin venta') end estado_pago,
 case when v.estado_pago<>'Pagado' then v.monto_clp else 0 end monto_pendiente
from public.mf_casos c left join reportes.caso_estado e on e.caso_id=c.id
left join lateral(select total_clp from public.mf_cotizaciones where caso_id=c.id order by version_cotizacion desc,numero desc limit 1) q on true
left join public.mf_ventas v on v.caso_id=c.id and not v.anulada;

create view reportes.v_hoja_cotizaciones as
select q.numero,q.version_cotizacion version,reportes.codigo(c.numero,c.created_at) codigo_caso,q.fecha_emision,
 extract(year from q.fecha_emision)::int "año",to_char(q.fecha_emision,'YYYY-MM') mes,
 to_char(q.fecha_emision,'YYYY')||'-T'||extract(quarter from q.fecha_emision)::int trimestre,
 to_char(q.fecha_emision,'YYYY')||'-S'||case when extract(month from q.fecha_emision)<=6 then '1' else '2' end semestre,
 reportes.empresa(c.cliente,c.contacto) empresa,reportes.texto(c.servicio) servicio,reportes.texto(c.tematica) tematica,
 q.base_clp monto_bruto,q.descuento_pct,q.total_clp monto_total,case when q.iva_pct=0 then 'SI' else 'NO' end exento_iva,
 (env.fecha at time zone 'America/Santiago')::date fecha_envio,
 case when decision.tipo is not null or c.cotizacion_aceptada_id=q.id then 0 else greatest(0,(now() at time zone 'America/Santiago')::date-q.fecha_emision) end dias_sin_respuesta,
 case when decision.tipo='rechazar' then 'Rechazada'
 when decision.tipo in ('aceptar','vender') or c.cotizacion_aceptada_id=q.id then 'Aceptada'
 when q.valida_hasta<(now() at time zone 'America/Santiago')::date or (now() at time zone 'America/Santiago')::date-q.fecha_emision>30 then 'Vencida'
 when (now() at time zone 'America/Santiago')::date-q.fecha_emision>5 then 'Sin respuesta'
 when env.fecha is not null then 'Enviada' else 'Generada' end estado_cotizacion
from public.mf_cotizaciones q join public.mf_casos c on c.id=q.caso_id
left join lateral(select min(created_at) fecha from public.mf_eventos_caso where cotizacion_id=q.id and tipo='envio' and deshecho_en is null) env on true
left join lateral(select tipo from public.mf_eventos_caso where cotizacion_id=q.id and tipo in ('aceptar','vender','rechazar') and deshecho_en is null order by created_at desc,id desc limit 1) decision on true;

create view reportes.v_hoja_ventas as
select v.id::text id_venta,reportes.codigo(c.numero,c.created_at) codigo_caso,v.fecha_venta,
 extract(year from v.fecha_venta)::int "año",to_char(v.fecha_venta,'YYYY-MM') mes,
 to_char(v.fecha_venta,'YYYY')||'-T'||extract(quarter from v.fecha_venta)::int trimestre,
 to_char(v.fecha_venta,'YYYY')||'-S'||case when extract(month from v.fecha_venta)<=6 then '1' else '2' end semestre,
 reportes.empresa(c.cliente,c.contacto) empresa,reportes.texto(c.servicio) tipo_servicio,reportes.texto(c.tematica) tematica,
 reportes.texto(c.modalidad) modalidad,c.participantes,v.monto_clp monto_vendido,v.reserva_pct pct_reserva,v.reserva_clp monto_reserva,
 v.remuneracion_pct pct_remuneracion,v.remuneracion_clp monto_remuneracion,
 case v.estado_pago when 'Abono recibido' then 'Anticipo pagado' else v.estado_pago end estado_pago,
 case when v.estado_pago<>'Pagado' then v.monto_clp else 0 end monto_pendiente
from public.mf_ventas v join public.mf_casos c on c.id=v.caso_id where not v.anulada;

create table reportes.sync_cola(
 id bigint generated always as identity primary key,tabla text not null,registro_id uuid not null,operacion text not null,
 creado_en timestamptz not null default now(),intentos integer not null default 0,ultimo_error text,procesado_en timestamptz,
 codigo_caso text not null);
create index sync_pendientes on reportes.sync_cola(id) where procesado_en is null;
create table reportes.sync_estado(
 id boolean primary key default true check(id),integrada boolean not null default false,
 ultimo_exito timestamptz,ultimo_error timestamptz,mensaje text not null default '',cantidad_pendiente bigint not null default 0,
 lease_token uuid,lease_hasta timestamptz,lease_ids bigint[],reintentar_en timestamptz);
insert into reportes.sync_estado(id) values(true);
create table reportes.sync_registro(id bigint generated always as identity primary key,fecha timestamptz not null default now(),hoja text not null,filas integer not null,resultado text not null,error text not null default '');
alter table reportes.sync_cola enable row level security;
alter table reportes.sync_estado enable row level security;
alter table reportes.sync_registro enable row level security;

create function reportes.encolar() returns trigger language plpgsql security definer set search_path='' as $$
declare r jsonb;cid uuid;codigo text;tabla text;
begin
 r=case when TG_OP='DELETE' then to_jsonb(old) else to_jsonb(new) end;
 cid=case when TG_TABLE_NAME='mf_casos' then (r->>'id')::uuid else (r->>'caso_id')::uuid end;
 if TG_TABLE_NAME='mf_casos' then
  codigo=reportes.codigo((r->>'numero')::bigint,(r->>'created_at')::timestamptz);
  if TG_OP<>'DELETE' then
   if TG_OP='INSERT' or old.estado is distinct from new.estado then
    insert into reportes.caso_estado(caso_id,fecha) values(cid,now()) on conflict(caso_id) do update set fecha=excluded.fecha;
   end if;
  end if;
 else select reportes.codigo(numero,created_at) into codigo from public.mf_casos where id=cid; end if;
 tabla=case when TG_TABLE_NAME in ('mf_casos','mf_cotizaciones','mf_ventas') then TG_TABLE_NAME else 'mf_casos' end;
 if codigo is not null then
  insert into reportes.sync_cola(tabla,registro_id,operacion,codigo_caso) values(tabla,(r->>'id')::uuid,TG_OP,codigo);
  update reportes.sync_estado set cantidad_pendiente=cantidad_pendiente+1 where id;
 end if;
 if TG_TABLE_NAME='mf_casos' and TG_OP='UPDATE' then
  if old.numero is distinct from new.numero or old.created_at is distinct from new.created_at then
   insert into reportes.sync_cola(tabla,registro_id,operacion,codigo_caso) values(tabla,old.id,'DELETE',reportes.codigo(old.numero,old.created_at));
   update reportes.sync_estado set cantidad_pendiente=cantidad_pendiente+1 where id;
  end if;
 end if;
 return null;
end$$;
create trigger mf_hoja_casos after insert or update or delete on public.mf_casos for each row execute function reportes.encolar();
create trigger mf_hoja_cotizaciones after insert or update or delete on public.mf_cotizaciones for each row execute function reportes.encolar();
create trigger mf_hoja_ventas after insert or update or delete on public.mf_ventas for each row execute function reportes.encolar();
create trigger mf_hoja_eventos after insert or update or delete on public.mf_eventos_caso for each row execute function reportes.encolar();
insert into reportes.sync_cola(tabla,registro_id,operacion,codigo_caso)
 select 'mf_casos',id,'INICIAL',reportes.codigo(numero,created_at) from public.mf_casos;
update reportes.sync_estado set cantidad_pendiente=(select count(*) from reportes.sync_cola);

create function reportes.tomar(p_token uuid,p_completo boolean default false) returns jsonb
language plpgsql security definer set search_path='' as $$
declare e reportes.sync_estado;ids bigint[];codigos text[];
begin
 select * into e from reportes.sync_estado where id for update;
 if e.lease_hasta>clock_timestamp() or (not p_completo and e.reintentar_en>now()) then return null; end if;
 select array_agg(id),array_agg(distinct codigo_caso) into ids,codigos from
  (select id,codigo_caso from reportes.sync_cola where procesado_en is null order by id limit case when p_completo then 100000 else 500 end) t;
 if not p_completo and ids is null then return null; end if;
 update reportes.sync_estado set integrada=true,lease_token=p_token,lease_hasta=clock_timestamp()+interval '15 minutes',lease_ids=coalesce(ids,'{}') where id;
 update reportes.sync_cola set intentos=intentos+1 where id=any(ids);
 return jsonb_build_object('completo',p_completo,'codigos',coalesce(to_jsonb(codigos),'[]'::jsonb),'datos',jsonb_build_object(
  'Casos',(select coalesce(jsonb_agg(to_jsonb(v) order by codigo),'[]'::jsonb) from reportes.v_hoja_casos v where p_completo or codigo=any(codigos)),
  'Cotizaciones',(select coalesce(jsonb_agg(to_jsonb(v) order by numero,version),'[]'::jsonb) from reportes.v_hoja_cotizaciones v where p_completo or codigo_caso=any(codigos)),
  'Ventas',(select coalesce(jsonb_agg(to_jsonb(v) order by id_venta),'[]'::jsonb) from reportes.v_hoja_ventas v where p_completo or codigo_caso=any(codigos))));
end$$;
create function reportes.renovar(p_token uuid) returns boolean language plpgsql security definer set search_path='' as $$
begin
 update reportes.sync_estado set lease_hasta=clock_timestamp()+interval '15 minutes' where id and lease_token=p_token and lease_hasta>clock_timestamp();
 return found;
end$$;
create function reportes.finalizar(p_token uuid,p_error text,p_filas jsonb) returns boolean
language plpgsql security definer set search_path='' as $$
declare e reportes.sync_estado;k text;n integer;v_mensaje text;
begin
 select * into e from reportes.sync_estado where id for update;
 if e.lease_token is distinct from p_token or e.lease_hasta<=clock_timestamp() then return false; end if;
 v_mensaje=case when p_error is null then '' else 'No pudimos actualizar la hoja. Tus datos están a salvo; lo reintentamos solos.' end;
 if p_error is null then
  update reportes.sync_cola set procesado_en=now(),ultimo_error=null where id=any(e.lease_ids);
 else update reportes.sync_cola set ultimo_error=v_mensaje where id=any(e.lease_ids); end if;
 update reportes.sync_estado set ultimo_exito=case when p_error is null then now() else ultimo_exito end,
  ultimo_error=case when p_error is not null then now() else ultimo_error end,mensaje=v_mensaje,
  cantidad_pendiente=(select count(*) from reportes.sync_cola where procesado_en is null),
  lease_token=null,lease_hasta=null,lease_ids=null,reintentar_en=case when p_error is null then null else now()+interval '60 seconds' end where id;
 for k in select jsonb_object_keys(p_filas) loop
  if k not in ('Casos','Cotizaciones','Ventas') then continue; end if;
  n=greatest(0,least(coalesce((p_filas->>k)::integer,0),10000000));
  insert into reportes.sync_registro(hoja,filas,resultado,error) values(k,n,case when p_error is null then 'Correcto' else 'Error' end,v_mensaje);
 end loop;
 delete from reportes.sync_registro where id not in (select id from reportes.sync_registro order by id desc limit 500);
 delete from reportes.sync_cola where procesado_en<now()-interval '7 days';
 return true;
end$$;

-- Única RPC pública: solo estado administrativo, nunca filas ni credenciales.
create function public.mf_estado_hoja() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare salida jsonb;
begin
 if not coalesce(public.es_admin(),false) then raise exception 'Acceso denegado' using errcode='42501'; end if;
 select jsonb_build_object('integrada',integrada,'ultimo_exito',ultimo_exito,'ultimo_error',ultimo_error,'mensaje',mensaje,
  'pendientes',(select count(*) from reportes.sync_cola where procesado_en is null),'actualizando',lease_hasta>clock_timestamp(),
  'registro',(select coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) from (select fecha,hoja,filas,resultado,error from reportes.sync_registro order by id desc limit 50) t)) into salida from reportes.sync_estado where id;
 return salida;
end$$;
revoke all on all tables in schema reportes from public,anon,authenticated,service_role,mfy_hoja;
revoke all on all functions in schema reportes from public,anon,authenticated,service_role,mfy_hoja;
grant usage on schema reportes to mfy_hoja;
grant select on reportes.v_hoja_casos,reportes.v_hoja_cotizaciones,reportes.v_hoja_ventas to mfy_hoja;
grant execute on function reportes.texto(text),reportes.codigo(bigint,timestamptz),reportes.empresa(text,text),reportes.tomar(uuid,boolean),reportes.renovar(uuid),reportes.finalizar(uuid,text,jsonb) to mfy_hoja;
revoke all on function public.mf_estado_hoja() from public,anon;
grant execute on function public.mf_estado_hoja() to authenticated;
notify pgrst,'reload schema';
commit;
