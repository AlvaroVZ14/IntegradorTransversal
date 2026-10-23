-- Después de 202610220004_hoy.sql. No cambia permisos ni datos comerciales.
begin;
create table public.mf_mantenimiento (
 id uuid primary key default gen_random_uuid(),
 tipo text not null check(tipo in ('monitor','respaldo')),
 estado text not null check(estado in ('ok','error')),
 created_at timestamptz not null default now(),
 run_url text not null check(run_url ~ '^https://github[.]com/[^/]+/[^/]+/actions/runs/[0-9]+$'),
 artefacto_id text,
 sha256 text,
 constraint mf_respaldo_comprobado check(tipo<>'respaldo' or estado<>'ok' or
   (artefacto_id is not null and sha256 is not null and artefacto_id ~ '^[0-9]+$' and sha256 ~ '^[a-f0-9]{64}$'))
);
alter table public.mf_mantenimiento enable row level security;
grant select on public.mf_mantenimiento to authenticated;
revoke all on public.mf_mantenimiento from anon;
grant select,insert on public.mf_mantenimiento to service_role;
create policy mantenimiento_admin on public.mf_mantenimiento for select to authenticated using(public.es_admin());
create policy mantenimiento_limite on public.mf_mantenimiento as restrictive for all to authenticated
 using(public.es_admin()) with check(false);

-- Una lectura STABLE usa el mismo snapshot en toda la llamada; no se pagina
-- mediante REST (que produciría snapshots distintos y podría omitir filas).
create function public.mf_exportar_respaldo() returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare nombre text; filas jsonb; columnas jsonb; tablas jsonb:='{}';
begin
 if not coalesce((public.es_admin() or current_user='service_role' or
   coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb->>'role'='service_role' or
   current_setting('request.jwt.claim.role',true)='service_role'),false) then
   raise exception 'Acceso denegado' using errcode='42501';
 end if;
 foreach nombre in array array['mf_perfiles','mf_casos','mf_cotizaciones','mf_ventas','mf_tarifas',
   'mf_plantillas_programa','mf_eventos_caso','mf_configuracion','mf_borradores_cotizacion',
   'mf_envios_cotizacion','mf_mantenimiento'] loop
   execute format('select coalesce(jsonb_agg(to_jsonb(t)),''[]''::jsonb) from
     (select * from public.%I order by id limit 100001) t',nombre) into filas;
   if jsonb_array_length(filas)>100000 then
     raise exception 'Respaldo excede 100000 filas por tabla; usar pg_dump. No se exportaron datos parciales.';
   end if;
   select jsonb_agg(jsonb_build_object('name',a.attname,'type',pg_catalog.format_type(a.atttypid,a.atttypmod),
     'generated',a.attgenerated<>'','identity',a.attidentity<>'') order by a.attnum) into columnas
     from pg_catalog.pg_attribute a where a.attrelid=('public.'||nombre)::regclass
       and a.attnum>0 and not a.attisdropped;
   tablas:=tablas||jsonb_build_object(nombre,jsonb_build_object('columns',columnas,'rows',filas));
   if octet_length(tablas::text)>52428800 then
     raise exception 'Respaldo excede 50 MiB; usar pg_dump. No se exportaron datos parciales.';
   end if;
 end loop;
 return jsonb_build_object('format',1,'snapshot_at',statement_timestamp(),'tables',tablas);
end $$;
revoke all on function public.mf_exportar_respaldo() from public,anon;
grant execute on function public.mf_exportar_respaldo() to authenticated,service_role;
commit;
