-- Ejecutar TODO el archivo una vez, con postgres. Requiere la migración inicial.
-- Partes 1-4 son una transacción: un fallo deshace el cambio completo.
begin;

-- PARTE 1: respaldo privado de políticas, permisos y rol anterior.
create schema if not exists mf_seguridad;
revoke all on schema mf_seguridad from public,anon,authenticated;
create table if not exists mf_seguridad.respaldos (
  cambio text primary key, datos jsonb not null, created_at timestamptz default now()
);
revoke all on mf_seguridad.respaldos from public,anon,authenticated;

do $$
declare t record; p record; a record; g record; co record;
  acciones text[] := '{}'; restricciones text[] := '{}'; tablas text[] := '{}';
  roles text; sentencia text; destinatario text;
begin
  if exists(select 1 from mf_seguridad.respaldos where cambio='cliente_solo_solicitud_v1') then
    raise exception 'La migración ya está aplicada; no la ejecutes otra vez.';
  end if;
  if to_regprocedure('public.es_admin()') is not null or
     to_regprocedure('public.registrar_solicitud(uuid,jsonb)') is not null then
    raise exception 'Existe una función con el nombre requerido. Revisa primero 00_inspeccionar_accesos.sql.';
  end if;
  if exists(select 1 from public.mf_perfiles where rol not in ('cliente','duena')) then
    raise exception 'El esquema de roles difiere del versionado. Revisa la auditoría antes de continuar.';
  end if;
  -- Una vista de propietario o una función definer desconocida podría omitir RLS.
  -- No se cambia a ciegas: exige revisión del esquema vivo antes de continuar.
  if exists(select 1 from pg_proc f join pg_namespace n on n.oid=f.pronamespace
    where n.nspname='public' and f.prosecdef and f.prokind='f'
      and has_function_privilege('authenticated',f.oid,'EXECUTE')
      and f.proname not in ('mf_es_duena','mf_emitir_cotizacion','mf_registrar_venta')) then
    raise exception 'Existe una función SECURITY DEFINER adicional accesible por clientes. Revisa la auditoría.';
  end if;
  if exists(select 1 from pg_class v join pg_namespace n on n.oid=v.relnamespace
    where n.nspname='public' and v.relkind in ('v','m') and
      (left(v.relname,3)='mf_' or exists(
        select 1 from pg_rewrite r join pg_depend d on d.classid='pg_rewrite'::regclass and d.objid=r.oid
        join pg_class source_table on source_table.oid=d.refobjid join pg_namespace tn on tn.oid=source_table.relnamespace
        where r.ev_class=v.oid and tn.nspname='public' and source_table.relkind in ('r','p') and
          (left(source_table.relname,3)='mf_' or source_table.relname in ('casos','cotizaciones','tarifas','programas','ventas','historial','configuracion'))
      ))) then
    raise exception 'Existe una vista sobre datos de negocio. Revisa sus permisos antes de migrar.';
  end if;
  -- Incluye tablas mf_* reales y nombres heredados solo si existen.
  for t in select c.oid,c.relname,c.relacl,c.relowner,c.relrowsecurity,c.relforcerowsecurity
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public' and c.relkind in ('r','p') and
      (left(c.relname,3)='mf_' or c.relname in
       ('casos','cotizaciones','tarifas','programas','ventas','historial','configuracion'))
  loop
    tablas := array_append(tablas,t.relname);
    acciones := array_append(acciones,format('revoke all on table public.%I from public,anon,authenticated',t.relname));
    for a in select attname,attacl from pg_attribute where attrelid=t.oid and attnum>0 and not attisdropped loop
      acciones := array_append(acciones,format('revoke all privileges (%I) on public.%I from public,anon,authenticated',a.attname,t.relname));
      for g in select x.*,r.rolname from aclexplode(a.attacl) x left join pg_roles r on r.oid=x.grantee
        where x.grantee=0 or r.rolname in ('anon','authenticated') loop
        destinatario := case when g.grantee=0 then 'PUBLIC' else quote_ident(g.rolname) end;
        acciones := array_append(acciones,format('grant %s (%I) on public.%I to %s%s',g.privilege_type,a.attname,t.relname,destinatario,case when g.is_grantable then ' with grant option' else '' end));
      end loop;
    end loop;
    for g in select x.*,r.rolname from aclexplode(coalesce(t.relacl,acldefault('r',t.relowner))) x
      left join pg_roles r on r.oid=x.grantee where x.grantee=0 or r.rolname in ('anon','authenticated') loop
      destinatario := case when g.grantee=0 then 'PUBLIC' else quote_ident(g.rolname) end;
      acciones := array_append(acciones,format('grant %s on public.%I to %s%s',g.privilege_type,t.relname,destinatario,case when g.is_grantable then ' with grant option' else '' end));
    end loop;
    for p in select * from pg_policy where polrelid=t.oid loop
      select string_agg(case when r=0 then 'PUBLIC' else quote_ident(pg_get_userbyid(r)) end,',')
        into roles from unnest(p.polroles) r;
      sentencia := format('create policy %I on public.%I as %s for %s to %s',p.polname,t.relname,
        case when p.polpermissive then 'permissive' else 'restrictive' end,
        case p.polcmd when 'r' then 'select' when 'a' then 'insert' when 'w' then 'update' when 'd' then 'delete' else 'all' end,roles);
      if p.polqual is not null then sentencia := sentencia||' using ('||pg_get_expr(p.polqual,p.polrelid)||')'; end if;
      if p.polwithcheck is not null then sentencia := sentencia||' with check ('||pg_get_expr(p.polwithcheck,p.polrelid)||')'; end if;
      acciones := array_append(acciones,sentencia);
    end loop;
    acciones := array_append(acciones,format('alter table public.%I %s row level security',t.relname,case when t.relrowsecurity then 'enable' else 'disable' end));
    acciones := array_append(acciones,format('alter table public.%I %sforce row level security',t.relname,case when t.relforcerowsecurity then '' else 'no ' end));
  end loop;
  for co in select conname,pg_get_constraintdef(oid) as def from pg_constraint
    where conrelid='public.mf_perfiles'::regclass and contype='c' and pg_get_constraintdef(oid) like '%rol%' loop
    restricciones := array_append(restricciones,format('alter table public.mf_perfiles add constraint %I %s',co.conname,co.def));
  end loop;
  insert into mf_seguridad.respaldos(cambio,datos) values('cliente_solo_solicitud_v1',jsonb_build_object(
    'tablas',tablas,'restaurar',acciones,'restricciones_rol',restricciones,
    'mf_es_duena',pg_get_functiondef('public.mf_es_duena()'::regprocedure)));
end $$;

-- PARTE 2: una fuente de roles. Conserva IDs y migra todas las dueñas existentes.
do $$ declare c record; begin
  for c in select conname from pg_constraint where conrelid='public.mf_perfiles'::regclass
    and contype='c' and pg_get_constraintdef(oid) like '%rol%' loop
    execute format('alter table public.mf_perfiles drop constraint %I',c.conname);
  end loop;
end $$;
update public.mf_perfiles set rol='admin' where rol='duena';
alter table public.mf_perfiles add constraint mf_perfiles_rol_v2_check check(rol in ('admin','cliente'));
alter table public.mf_perfiles alter column rol set default 'cliente';

create function public.es_admin() returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.mf_perfiles where id=(select auth.uid()) and rol='admin');
$$;
revoke all on function public.es_admin() from public,anon;
grant execute on function public.es_admin() to authenticated;
-- Alias de compatibilidad: las funciones de ventas/cotizaciones existentes lo usan.
create or replace function public.mf_es_duena() returns boolean
language sql stable security definer set search_path='' as $$ select public.es_admin(); $$;

alter table public.mf_casos
  add column if not exists origen text not null default 'No informado',
  add column if not exists registrado_por text not null default 'No informado',
  add column if not exists consentimiento boolean not null default false,
  add column if not exists consentimiento_fecha timestamptz,
  add column if not exists consentimiento_version text;

-- PARTE 3: único punto de entrada del cliente, sin acceso a las tablas.
create function public.registrar_solicitud(p_solicitud_id uuid,p_datos jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare perfil public.mf_perfiles; correo text; confirmado timestamptz; caso public.mf_casos;
begin
  if auth.uid() is null then raise exception 'Inicia sesión para enviar la solicitud' using errcode='42501'; end if;
  select * into perfil from public.mf_perfiles where id=auth.uid() and rol='cliente';
  if not found then raise exception 'Acceso denegado' using errcode='42501'; end if;
  select email,email_confirmed_at into correo,confirmado from auth.users where id=auth.uid();
  if confirmado is null then raise exception 'Confirma tu correo antes de enviar la solicitud' using errcode='42501'; end if;
  if p_solicitud_id is null or jsonb_typeof(p_datos) <> 'object' or p_datos is null then
    raise exception 'La solicitud no es válida' using errcode='22023';
  end if;
  if p_datos->'consentimiento' is distinct from 'true'::jsonb then
    raise exception 'Debes autorizar el uso de tus datos' using errcode='22023';
  end if;
  if length(trim(perfil.nombre)) < 2 then raise exception 'Tu perfil necesita un nombre de contacto válido' using errcode='22023'; end if;
  if nullif(p_datos->>'fecha_preferida','')::date < (now() at time zone 'America/Santiago')::date then
    raise exception 'La fecha preferida no puede estar en el pasado' using errcode='22023';
  end if;
  -- Omite campos internos aunque el usuario los envíe: identidad, origen y autor son del servidor.
  insert into public.mf_casos(id,creado_por,cliente_id,cliente,contacto,email,telefono,
    servicio,tematica,participantes,horas,modalidad,lugar,fecha_preferida,detalle,
    origen,registrado_por,consentimiento,consentimiento_fecha,consentimiento_version)
  values(p_solicitud_id,perfil.id,perfil.id,coalesce(nullif(trim(p_datos->>'cliente'),''),perfil.nombre),perfil.nombre,correo,
    coalesce(p_datos->>'telefono',''),p_datos->>'servicio',p_datos->>'tematica',
    (p_datos->>'participantes')::integer,(p_datos->>'horas')::numeric,p_datos->>'modalidad',
    coalesce(p_datos->>'lugar',''),nullif(p_datos->>'fecha_preferida','')::date,coalesce(p_datos->>'detalle',''),
    'Formulario web','Cliente',true,now(),'2026-10-21') on conflict(id) do nothing;
  -- Un UUID ajeno nunca devuelve datos; un reintento propio devuelve solo el comprobante.
  select * into caso from public.mf_casos where id=p_solicitud_id and creado_por=perfil.id
    and cliente_id=perfil.id and origen='Formulario web' and consentimiento;
  if not found then raise exception 'No se pudo registrar la solicitud' using errcode='42501'; end if;
  return jsonb_build_object('codigo',format('MF-%s-%s',extract(year from caso.created_at at time zone 'America/Santiago'),
    lpad(caso.numero::text,greatest(4,length(caso.numero::text)),'0')));
end;
$$;
revoke all on function public.registrar_solicitud(uuid,jsonb) from public,anon;
grant execute on function public.registrar_solicitud(uuid,jsonb) to authenticated;

-- PARTE 4: elimina políticas permisivas anteriores, incluso las no versionadas.
-- La política RESTRICTIVE impide que una política permisiva accidental reabra las tablas.
do $$ declare tabla text; p record; a record; begin
  for tabla in select jsonb_array_elements_text(datos->'tablas') from mf_seguridad.respaldos
    where cambio='cliente_solo_solicitud_v1' loop
    for p in select policyname from pg_policies where schemaname='public' and tablename=tabla loop
      execute format('drop policy %I on public.%I',p.policyname,tabla);
    end loop;
    execute format('alter table public.%I enable row level security',tabla);
    execute format('revoke all on table public.%I from public,anon,authenticated',tabla);
    for a in select attname from pg_attribute where attrelid=format('public.%I',tabla)::regclass and attnum>0 and not attisdropped loop
      execute format('revoke all privileges (%I) on public.%I from public,anon,authenticated',a.attname,tabla);
    end loop;
    if tabla='mf_perfiles' then
      execute 'grant select on public.mf_perfiles to authenticated';
      execute 'create policy mf_v2_perfil on public.mf_perfiles for select to authenticated using(id=(select auth.uid()) or (select public.es_admin()))';
      execute 'create policy mf_v2_perfil_limite on public.mf_perfiles as restrictive for select to authenticated using(id=(select auth.uid()) or (select public.es_admin()))';
      -- Sin INSERT/UPDATE/DELETE de perfiles para la API. Rol solo por administración SQL.
    else
      execute format('grant select,insert,update,delete on public.%I to authenticated',tabla);
      execute format('create policy mf_v2_admin on public.%I for all to authenticated using((select public.es_admin())) with check((select public.es_admin()))',tabla);
      execute format('create policy mf_v2_limite on public.%I as restrictive for all to authenticated using((select public.es_admin())) with check((select public.es_admin()))',tabla);
    end if;
  end loop;
end $$;

notify pgrst,'reload schema';
commit;
