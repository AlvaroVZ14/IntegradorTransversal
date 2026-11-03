-- Prompt 27. Después de las migraciones existentes, ejecutar completo una vez.
-- No borra casos ni modifica redes de documentos de cotización ya emitidos.
begin;
alter table public.mf_casos add column redes_sociales jsonb not null default '{}';

create function mf_seguridad.normalizar_redes(datos jsonb) returns jsonb
language plpgsql immutable set search_path='' as $$
declare k text;etiqueta text;v text;u text;host text;puerto text;r jsonb:='{}';
begin
 if datos is null or jsonb_typeof(datos)<>'object' or octet_length(datos::text)>6000 or
  exists(select 1 from jsonb_object_keys(datos) x where x not in ('instagram','linkedin','facebook','sitio_web','otra_red')) then
  raise exception 'Revisa las redes sociales de la empresa' using errcode='22023';
 end if;
 foreach k in array array['instagram','linkedin','facebook','sitio_web','otra_red'] loop
  etiqueta=case k when 'instagram' then 'Instagram' when 'linkedin' then 'LinkedIn' when 'facebook' then 'Facebook' when 'sitio_web' then 'Sitio web' else 'Otra red' end;
  if datos ? k and (jsonb_typeof(datos->k) not in ('string','null') or length(datos->>k)>200) then
   raise exception 'Revisa %: máximo 200 caracteres',etiqueta using errcode='22023';end if;
  v=trim(coalesce(datos->>k,''));if v='' then continue;end if;
  if v ~ '[[:cntrl:]<>"]' or position(chr(92) in v)>0 or v ~* '%(00|0a|0d)' or
   v ~* '(javascript|vbscript|data|file|blob|about):' then
   raise exception 'Revisa %: usa un enlace seguro',etiqueta using errcode='22023';end if;
  if k='instagram' and v ~ '^@?[a-zA-Z0-9_.]{1,30}$' then
   u=ltrim(v,'@');
   if u like '.%' or u like '%.' or position('..' in u)>0 then raise exception 'Revisa Instagram: usuario no válido' using errcode='22023';end if;
   v='https://www.instagram.com/'||u||'/';
  elsif k='otra_red' and v !~* '^(https?://|www[.])' and v !~ '^[^[:space:]/]+[.][^[:space:]/]+(/[^[:space:]]*)?$' then
   if v ~ '^[a-zA-Z][a-zA-Z0-9+.-]*://' then raise exception 'Revisa Otra red: usa http o https' using errcode='22023';end if;
  else
   if v ~ '^[a-zA-Z][a-zA-Z0-9+.-]*:' and v !~* '^https?://' then
    raise exception 'Revisa %: usa http o https',etiqueta using errcode='22023';end if;
   if v !~* '^https?://' then v='https://'||v;end if;
   if v !~* '^https?://[a-z0-9]([a-z0-9.-]*[a-z0-9])?(:[0-9]{1,5})?([/?#][^[:space:]]*)?$' then
    raise exception 'Revisa %: escribe un enlace válido',etiqueta using errcode='22023';end if;
   host=(regexp_match(v,'^https?://([^/?#]+)','i'))[1];
   puerto=split_part(host,':',2);host=lower(split_part(host,':',1));
   if position('.' in host)=0 or exists(select 1 from unnest(string_to_array(host,'.')) p
    where p !~ '^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$') or (puerto<>'' and puerto::integer not between 1 and 65535) then
    raise exception 'Revisa %: revisa el dominio del enlace',etiqueta using errcode='22023';end if;
   if k='instagram' then
    u=(regexp_match(v,'^https?://(www[.])?instagram[.]com/([a-zA-Z0-9_.]{1,30})/?([?#][^[:space:]]*)?$','i'))[2];
    if u is null or u like '.%' or u like '%.' or position('..' in u)>0 then
     raise exception 'Revisa Instagram: escribe el enlace de un perfil' using errcode='22023';end if;
    v='https://www.instagram.com/'||u||'/';
   else
    v=regexp_replace(v,'^https?://[^/?#]+',lower((regexp_match(v,'^https?://[^/?#]+','i'))[1]),'i');
   end if;
  end if;
  if length(v)>200 then raise exception 'Revisa %: el enlace completo supera 200 caracteres',etiqueta using errcode='22023';end if;
  r=r||jsonb_build_object(k,v);
 end loop;
 return r;
end $$;
revoke all on function mf_seguridad.normalizar_redes(jsonb) from public,anon,authenticated;

-- Un registro actual por empresa y correo. El caso conserva su propia copia.
create table public.mf_empresas_redes(
 id uuid primary key default gen_random_uuid(),correo text not null check(correo=lower(trim(correo)) and length(correo)<=254),
 empresa text not null check(length(empresa) between 1 and 180),
 empresa_clave text generated always as(lower(trim(empresa))) stored,
 redes_sociales jsonb not null default '{}',confirmadas boolean not null default false,
 updated_at timestamptz not null default now(),unique(correo,empresa_clave));
alter table public.mf_empresas_redes enable row level security;
revoke all on public.mf_empresas_redes from public,anon,authenticated;
grant select on public.mf_empresas_redes to authenticated;
create policy mf_redes_admin on public.mf_empresas_redes for select to authenticated using(public.es_admin());
create policy mf_redes_limite on public.mf_empresas_redes as restrictive for all to authenticated
 using(public.es_admin()) with check(false);

create function public.mf_validar_redes_caso() returns trigger
language plpgsql security definer set search_path='' as $$
begin new.redes_sociales=mf_seguridad.normalizar_redes(new.redes_sociales);return new;end $$;
revoke all on function public.mf_validar_redes_caso() from public,anon,authenticated;
create trigger mf_redes_validar before insert or update of redes_sociales on public.mf_casos
 for each row execute function public.mf_validar_redes_caso();

create function public.mf_reutilizar_redes_caso() returns trigger
language plpgsql security definer set search_path='' as $$
declare autorizado boolean;
begin
 if new.email is null or new.cliente is null then return new;end if;
 if tg_op='UPDATE' and (new.email,new.cliente,new.redes_sociales) is not distinct from (old.email,old.cliente,old.redes_sociales) then return new;end if;
 autorizado=public.es_admin() or exists(select 1 from auth.users u join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
  where u.id=auth.uid() and u.email_confirmed_at is not null and lower(trim(u.email))=lower(trim(new.email)));
 if new.redes_sociales='{}'::jsonb and (not autorizado or not exists(select 1 from public.mf_empresas_redes
  where correo=lower(trim(new.email)) and empresa_clave=lower(trim(new.cliente)))) then return new;end if;
 insert into public.mf_empresas_redes(correo,empresa,redes_sociales,confirmadas)
 values(lower(trim(new.email)),trim(new.cliente),new.redes_sociales,autorizado)
 on conflict(correo,empresa_clave) do update set redes_sociales=excluded.redes_sociales,
  empresa=excluded.empresa,confirmadas=excluded.confirmadas,updated_at=now()
 where not mf_empresas_redes.confirmadas or excluded.confirmadas;
 return new;
end $$;
revoke all on function public.mf_reutilizar_redes_caso() from public,anon,authenticated;
create trigger mf_redes_reutilizar after insert or update on public.mf_casos
 for each row execute function public.mf_reutilizar_redes_caso();

-- Reutilizable por el futuro perfil del cliente. El correo no viene de un parámetro.
-- Si la cuenta tiene varias empresas, se exige seleccionar/escribir una empresa.
create function public.mf_mis_redes_empresa(p_empresa text default '') returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce((select jsonb_build_object('empresa',r.empresa,'redes_sociales',r.redes_sociales)
 from public.mf_empresas_redes r join auth.users u on u.id=auth.uid() and u.email_confirmed_at is not null
 join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where r.correo=lower(trim(u.email)) and r.confirmadas and
 ((trim(coalesce(p_empresa,''))<>'' and r.empresa_clave=lower(trim(p_empresa))) or
 (trim(coalesce(p_empresa,''))='' and (select count(*) from public.mf_empresas_redes x where x.correo=r.correo and x.confirmadas)=1))
 limit 1),'{}'::jsonb);
$$;
revoke all on function public.mf_mis_redes_empresa(text) from public,anon;
grant execute on function public.mf_mis_redes_empresa(text) to authenticated;

-- Conserva las validaciones, atribución, honeypot, consentimiento e idempotencia.
alter function mf_seguridad.validar_solicitud(jsonb,boolean) rename to validar_solicitud_antes_redes;
create function mf_seguridad.validar_solicitud(datos jsonb,interno boolean) returns void
language plpgsql set search_path='' as $$
begin
 if datos is null or jsonb_typeof(datos)<>'object' or octet_length(datos::text)>32000 then
  raise exception 'Formulario no válido' using errcode='22023';end if;
 perform mf_seguridad.normalizar_redes(coalesce(datos->'redes_sociales','{}'::jsonb));
 perform mf_seguridad.validar_solicitud_antes_redes(datos-'redes_sociales',interno);
end $$;
revoke all on function mf_seguridad.validar_solicitud(jsonb,boolean) from public,anon,authenticated;

-- La definición completa del helper de inserción se incluye a continuación.

create or replace function mf_seguridad.insertar_solicitud(p_id uuid,d jsonb,usuario uuid,interno boolean) returns public.mf_casos
language plpgsql set search_path='' as $$
declare c public.mf_casos; nombre text;correo text;vinculo uuid;consent boolean;origen text;temas text[];
begin
 if p_id is null then raise exception 'Solicitud no válida' using errcode='22023';end if;
 if interno then
  nombre=nullif(trim(d->>'contacto'),'');correo=nullif(lower(trim(d->>'email')),'');vinculo=nullif(d->>'cliente_id','')::uuid;
  if vinculo is not null and not exists(select 1 from public.mf_perfiles where id=vinculo and rol='cliente') then raise exception 'Cuenta de cliente no válida' using errcode='22023';end if;
  origen=coalesce(d->>'origen','No informado');
  if origen not in ('Llamada','Correo','Reunión','Programa propio','Referido por colega','Formulario web','Otro','No informado') then raise exception 'Origen no válido' using errcode='22023';end if;
  if d ? 'consentimiento_confirmado' and jsonb_typeof(d->'consentimiento_confirmado')<>'boolean' then raise exception 'Confirmación no válida' using errcode='22023';end if;
  consent=coalesce((d->>'consentimiento_confirmado')::boolean,false);
 else
  origen='Formulario web';consent=true;
  if usuario is not null then
   select p.nombre,u.email into nombre,correo from public.mf_perfiles p join auth.users u on u.id=p.id
   where p.id=usuario and p.rol='cliente' and u.email_confirmed_at is not null;
   if not found or length(trim(nombre))<2 then raise exception 'Confirma tu cuenta antes de enviar' using errcode='42501';end if;
   vinculo=usuario;
  else nombre=trim(d->>'contacto');correo=lower(trim(d->>'email'));end if;
 end if;
 temas=case when d ? 'tematicas' then array(select jsonb_array_elements_text(d->'tematicas'))
  when nullif(d->>'tematica','') is not null then array[d->>'tematica'] else '{}'::text[] end;
 insert into public.mf_casos(id,creado_por,cliente_id,cliente,contacto,email,telefono,rut,cargo,
 servicio,tematica,tematicas,canal_captacion,participantes,horas,modalidad,lugar,fecha_preferida,detalle,dirigido_a,referido_por,
 origen,registrado_por,consentimiento,consentimiento_fecha,consentimiento_version,redes_sociales)
 values(p_id,usuario,vinculo,case when interno then nullif(trim(d->>'cliente'),'') else coalesce(nullif(trim(d->>'cliente'),''),nombre) end,
 nombre,correo,coalesce(d->>'telefono',''),coalesce(d->>'rut',''),coalesce(d->>'cargo',''),
 nullif(d->>'servicio',''),temas[1],temas,case when interno then null when not (d ? 'canal_captacion') then 'directo'
 else mf_seguridad.normalizar_canal(coalesce(d->>'canal_captacion','')) end,(d->>'participantes')::integer,(d->>'horas')::numeric,nullif(d->>'modalidad',''),
 coalesce(d->>'lugar',''),nullif(d->>'fecha_preferida','')::date,coalesce(d->>'detalle',''),coalesce(d->>'dirigido_a',''),
 case when interno then coalesce(d->>'referido_por','') else '' end,origen,case when interno then 'Administración' else 'Cliente' end,
 consent,case when consent then now() end,case when consent then '2026-11-02-redes' end,mf_seguridad.normalizar_redes(coalesce(d->'redes_sociales','{}'::jsonb))) returning * into c;
 return c;
end $$;
revoke all on function mf_seguridad.insertar_solicitud(uuid,jsonb,uuid,boolean) from public,anon,authenticated;


create or replace function public.mf_catalogo_solicitudes() returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object('version',4,
 'servicios',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='servicio' and activo),'[]'),
 'tematicas',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='tematica' and activo),'[]'))
 from public.mf_catalogo_formulario;
$$;
notify pgrst,'reload schema';

-- El registro reutilizable también forma parte del respaldo privado.
create or replace function public.mf_exportar_respaldo() returns jsonb
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
   'mf_envios_cotizacion','mf_mantenimiento','mf_empresas_redes'] loop
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
commit;
