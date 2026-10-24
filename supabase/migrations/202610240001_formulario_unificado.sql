-- Requiere las migraciones hasta 202610230001. También funciona si el SQL
-- público 202610230002 todavía no fue aplicado. Ejecutar completo una vez.
begin;
create table mf_seguridad.formulario_unificado_respaldo(nombre text primary key,definicion text);
revoke all on mf_seguridad.formulario_unificado_respaldo from public,anon,authenticated;
insert into mf_seguridad.formulario_unificado_respaldo
select proname,pg_get_functiondef(oid) from pg_proc where pronamespace='public'::regnamespace
and proname in ('registrar_solicitud','registrar_solicitud_publica','mf_configuracion_publica','mf_nuevo_usuario');

-- Catálogo público acotado. Nunca se publican precios, clientes o programas.
create table public.mf_catalogo_formulario(
 tipo text not null check(tipo in ('servicio','tematica')),nombre text not null,
 orden integer not null,activo boolean not null default true,primary key(tipo,nombre));
alter table public.mf_catalogo_formulario enable row level security;
revoke all on public.mf_catalogo_formulario from public,anon,authenticated;
grant select,insert,update,delete on public.mf_catalogo_formulario to authenticated;
create policy mf_catalogo_admin on public.mf_catalogo_formulario for all to authenticated
 using(public.es_admin()) with check(public.es_admin());
insert into public.mf_catalogo_formulario(tipo,nombre,orden) values
 ('servicio','Coaching individual',1),('servicio','Coaching dúo',2),('servicio','Taller de trabajo en equipo',3),
 ('servicio','Charla de liderazgo',4),('servicio','Otro servicio',5),
 ('tematica','Liderazgo',1),('tematica','Trabajo en equipo',2),('tematica','Comunicación efectiva',3),
 ('tematica','Desarrollo personal',4),('tematica','Gestión emocional',5),('tematica','Otro',6);
create function public.mf_catalogo_solicitudes() returns jsonb language sql stable security definer set search_path='' as $$
 select jsonb_build_object('version',2,
 'servicios',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='servicio' and activo),'[]'),
 'tematicas',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='tematica' and activo),'[]'))
 from public.mf_catalogo_formulario;
$$;
revoke all on function public.mf_catalogo_solicitudes() from public;
grant execute on function public.mf_catalogo_solicitudes() to anon,authenticated;

create or replace function public.mf_configuracion_publica() returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object(
  'sitio_web',case when jsonb_typeof(datos->'sitio_web')='string' then left(datos->>'sitio_web',2048) else '' end,
  'politica_privacidad',case when jsonb_typeof(datos->'politica_privacidad')='string' then left(datos->>'politica_privacidad',2048) else '' end,
  'correo_contacto',case when jsonb_typeof(datos->'correo_contacto')='string' then left(datos->>'correo_contacto',254) else '' end,
  'redes',jsonb_build_object(
   'facebook',case when jsonb_typeof(datos->'redes'->'facebook')='string' then left(datos->'redes'->>'facebook',2048) else '' end,
   'instagram',case when jsonb_typeof(datos->'redes'->'instagram')='string' then left(datos->'redes'->>'instagram',2048) else '' end))
 from public.mf_configuracion where id='general';
$$;
revoke all on function public.mf_configuracion_publica() from public;
grant execute on function public.mf_configuracion_publica() to anon,authenticated;

-- Ningún metadato de registro determina el rol, ni aunque cambie el default.
create or replace function public.mf_nuevo_usuario() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 insert into public.mf_perfiles(id,nombre,email,rol)
 values(new.id,left(coalesce(new.raw_user_meta_data->>'nombre',''),160),coalesce(new.email,''),'cliente');
 return new;
end $$;
revoke all on function public.mf_nuevo_usuario() from public,anon,authenticated;

alter table public.mf_casos
 add column dirigido_a text not null default '' check(length(dirigido_a)<=1000),
 add column referido_por text not null default '' check(length(referido_por)<=160),
 add column tematicas text[] not null default '{}',
 add column datos_incompletos boolean not null default false,
 add column datos_pendientes text[] not null default '{}';
update public.mf_casos set tematicas=array[tematica];
alter table public.mf_casos alter column creado_por drop not null;
-- Se conservan todos los CHECK existentes: un dato presente debe ser válido.
alter table public.mf_casos alter column cliente drop not null,alter column contacto drop not null,
 alter column email drop not null,alter column servicio drop not null,alter column tematica drop not null,
 alter column participantes drop not null,alter column horas drop not null,alter column modalidad drop not null;
alter table public.mf_casos drop constraint if exists mf_solicitud_sin_cuenta_check;
alter table public.mf_casos add constraint mf_solicitud_sin_cuenta_check check(
 creado_por is not null or (cliente_id is null and origen='Formulario web' and registrado_por='Cliente'
 and consentimiento and consentimiento_fecha is not null and not datos_incompletos));
alter table public.mf_casos add constraint mf_caso_completo_check check(
 (datos_incompletos and registrado_por='Administración' and creado_por is not null
  and estado in ('Solicitud','En revisión','Cancelado')) or
 (not datos_incompletos and cliente is not null and contacto is not null and email is not null
  and servicio is not null and tematica is not null and participantes is not null and horas is not null and modalidad is not null));
grant update(dirigido_a,referido_por,tematicas) on public.mf_casos to authenticated;

create function public.mf_integridad_solicitud() returns trigger
language plpgsql security definer set search_path='' as $$
declare datos jsonb;campo text;t text;
begin
 new.cliente=nullif(trim(new.cliente),'');new.contacto=nullif(trim(new.contacto),'');new.email=nullif(trim(new.email),'');
 if tg_op='UPDATE' and new.tematica is distinct from old.tematica and new.tematicas is not distinct from old.tematicas then
  new.tematicas=case when new.tematica is null then '{}'::text[] else array_prepend(new.tematica,array_remove(old.tematicas,new.tematica)) end;
 elsif cardinality(new.tematicas)>0 then new.tematica=new.tematicas[1];
 elsif new.tematica is not null then new.tematicas=array[new.tematica];end if;
 if cardinality(new.tematicas)>6 or cardinality(new.tematicas)<>(select count(distinct x) from unnest(new.tematicas) x) then
  raise exception 'Revisa las temáticas' using errcode='22023';end if;
 foreach t in array new.tematicas loop
  if not exists(select 1 from public.mf_catalogo_formulario where tipo='tematica' and nombre=t) then
   raise exception 'Temática no válida' using errcode='22023';end if;
 end loop;
 new.datos_pendientes='{}';datos=to_jsonb(new);
 foreach campo in array array['cliente','contacto','email','servicio','tematica','modalidad','participantes','horas'] loop
  if datos->campo is null or datos->campo='null'::jsonb then new.datos_pendientes=array_append(new.datos_pendientes,campo);end if;
 end loop;
 new.datos_incompletos=cardinality(new.datos_pendientes)>0;
 if new.datos_incompletos and not public.es_admin() then
  raise exception 'Completa los campos obligatorios' using errcode='22023';end if;
 return new;
end $$;
revoke all on function public.mf_integridad_solicitud() from public,anon,authenticated;
create trigger mf_integridad_formulario before insert or update on public.mf_casos
for each row execute function public.mf_integridad_solicitud();

create table if not exists mf_seguridad.recibos_publicos(
 solicitud_id uuid primary key references public.mf_casos(id),token_hash text not null,
 datos_hash text not null,correo_hash text not null,created_at timestamptz not null default now());
revoke all on mf_seguridad.recibos_publicos from public,anon,authenticated;
alter table mf_seguridad.recibos_publicos enable row level security;
create index if not exists mf_publicos_fecha on mf_seguridad.recibos_publicos(created_at);
create index if not exists mf_publicos_correo_fecha on mf_seguridad.recibos_publicos(correo_hash,created_at);

-- Cola privada: el guardado no depende de SMTP y nunca entrega la clave servidor a la app.
create table public.mf_avisos_solicitud(
 id uuid primary key default gen_random_uuid(),caso_id uuid not null unique references public.mf_casos(id),
 estado text not null default 'pendiente' check(estado in ('pendiente','preparado','enviado','error','incierto')),
 intentos integer not null default 0,proximo_intento timestamptz not null default now(),
 lease uuid,created_at timestamptz not null default now(),updated_at timestamptz not null default now());
alter table public.mf_avisos_solicitud enable row level security;
revoke all on public.mf_avisos_solicitud from public,anon,authenticated;
grant select on public.mf_avisos_solicitud to authenticated;
create policy mf_avisos_admin on public.mf_avisos_solicitud for select to authenticated using(public.es_admin());
create function public.mf_encolar_aviso_solicitud() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if new.registrado_por='Cliente' then insert into public.mf_avisos_solicitud(caso_id) values(new.id) on conflict do nothing;end if;
 return new;
end $$;
revoke all on function public.mf_encolar_aviso_solicitud() from public,anon,authenticated;
create trigger mf_aviso_nueva_solicitud after insert on public.mf_casos
for each row execute function public.mf_encolar_aviso_solicitud();

-- Valida tipos y campos antes de cualquier escritura. No acepta campos ocultos del navegador.
create function mf_seguridad.validar_solicitud(datos jsonb,interno boolean) returns void
language plpgsql set search_path='' as $$
declare campo text; permitidos text[]:=array['cliente','contacto','email','telefono','rut','cargo','servicio','tematica','tematicas',
 'participantes','horas','modalidad','lugar','fecha_preferida','detalle','dirigido_a','consentimiento','honeypot'];
begin
 if datos is null or jsonb_typeof(datos)<>'object' or octet_length(datos::text)>32000 then raise exception 'Formulario no válido' using errcode='22023';end if;
 if interno then permitidos=permitidos||array['cliente_id','origen','referido_por','consentimiento_confirmado'];end if;
 if exists(select 1 from jsonb_object_keys(datos) k where k<>all(permitidos)) then raise exception 'Campos no permitidos' using errcode='22023';end if;
 if coalesce(datos->>'honeypot','')<>'' then raise exception 'Formulario no válido' using errcode='22023';end if;
 if not interno and datos->'consentimiento' is distinct from 'true'::jsonb then raise exception 'Debes autorizar el uso de tus datos' using errcode='22023';end if;
 foreach campo in array array['cliente','contacto','email','telefono','rut','cargo','servicio','tematica','modalidad','lugar','detalle','dirigido_a','origen','referido_por'] loop
  if datos ? campo and jsonb_typeof(datos->campo) not in ('string','null') then raise exception 'Revisa los campos' using errcode='22023';end if;
 end loop;
 foreach campo in array array['participantes','horas'] loop
  if datos ? campo and jsonb_typeof(datos->campo) not in ('number','null') then raise exception 'Revisa los números' using errcode='22023';end if;
 end loop;
 if datos ? 'participantes' and nullif(datos->>'participantes','')::numeric<>trunc(nullif(datos->>'participantes','')::numeric) then
  raise exception 'Participantes debe ser un entero' using errcode='22023';end if;
 if datos ? 'tematicas' and (jsonb_typeof(datos->'tematicas')<>'array' or jsonb_array_length(datos->'tematicas')>6
  or exists(select 1 from jsonb_array_elements(datos->'tematicas') x where jsonb_typeof(x)<>'string')) then raise exception 'Revisa las temáticas' using errcode='22023';end if;
 if nullif(datos->>'fecha_preferida','')::date<(now() at time zone 'America/Santiago')::date then raise exception 'La fecha no puede estar en el pasado' using errcode='22023';end if;
 if coalesce(datos->>'telefono','')<>'' and ((datos->>'telefono') !~ '^[+]?[0-9[:space:]().-]+$'
  or length(regexp_replace(datos->>'telefono','[^0-9]','','g')) not between 8 and 15) then raise exception 'Revisa el teléfono' using errcode='22023';end if;
end $$;
revoke all on function mf_seguridad.validar_solicitud(jsonb,boolean) from public,anon,authenticated;

create function mf_seguridad.insertar_solicitud(p_id uuid,d jsonb,usuario uuid,interno boolean) returns public.mf_casos
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
 servicio,tematica,tematicas,participantes,horas,modalidad,lugar,fecha_preferida,detalle,dirigido_a,referido_por,
 origen,registrado_por,consentimiento,consentimiento_fecha,consentimiento_version)
 values(p_id,usuario,vinculo,case when interno then nullif(trim(d->>'cliente'),'') else coalesce(nullif(trim(d->>'cliente'),''),nombre) end,
 nombre,correo,coalesce(d->>'telefono',''),coalesce(d->>'rut',''),coalesce(d->>'cargo',''),
 nullif(d->>'servicio',''),temas[1],temas,(d->>'participantes')::integer,(d->>'horas')::numeric,nullif(d->>'modalidad',''),
 coalesce(d->>'lugar',''),nullif(d->>'fecha_preferida','')::date,coalesce(d->>'detalle',''),coalesce(d->>'dirigido_a',''),
 case when interno then coalesce(d->>'referido_por','') else '' end,origen,case when interno then 'Administración' else 'Cliente' end,
 consent,case when consent then now() end,case when consent then '2026-10-24' end) returning * into c;
 return c;
end $$;
revoke all on function mf_seguridad.insertar_solicitud(uuid,jsonb,uuid,boolean) from public,anon,authenticated;

create or replace function public.registrar_solicitud(p_solicitud_id uuid,p_datos jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare c public.mf_casos;administracion boolean;codigo text;
begin
 if auth.uid() is null then raise exception 'Inicia sesión' using errcode='42501';end if;
 administracion=public.es_admin();
 if not administracion and not exists(select 1 from public.mf_perfiles where id=auth.uid() and rol='cliente') then raise exception 'Acceso denegado' using errcode='42501';end if;
 perform mf_seguridad.validar_solicitud(p_datos,administracion);
 perform pg_advisory_xact_lock(hashtextextended(p_solicitud_id::text,0));
 select * into c from public.mf_casos where id=p_solicitud_id;
 if found then
  if c.creado_por is distinct from auth.uid() or (not administracion and c.cliente_id is distinct from auth.uid()) then raise exception 'Acceso denegado' using errcode='42501';end if;
 else
  if not administracion and (select count(*) from public.mf_casos where creado_por=auth.uid() and created_at>now()-interval '15 minutes')>=3 then raise exception 'Espera unos minutos antes de enviar otra solicitud' using errcode='P0001';end if;
  c=mf_seguridad.insertar_solicitud(p_solicitud_id,p_datos,auth.uid(),administracion);
 end if;
 codigo=format('MF-%s-%s',extract(year from c.created_at at time zone 'America/Santiago'),lpad(c.numero::text,greatest(4,length(c.numero::text)),'0'));
 return case when administracion then jsonb_build_object('codigo',codigo,'caso',to_jsonb(c)) else jsonb_build_object('codigo',codigo) end;
end $$;
revoke all on function public.registrar_solicitud(uuid,jsonb) from public,anon;
grant execute on function public.registrar_solicitud(uuid,jsonb) to authenticated;

create or replace function public.registrar_solicitud_publica(p_solicitud_id uuid,p_token text,p_datos jsonb,p_honeypot text default '')
returns jsonb language plpgsql security definer set search_path='' as $$
declare r mf_seguridad.recibos_publicos;c public.mf_casos;th text;dh text;eh text;
begin
 if p_solicitud_id is null or p_token is null or length(p_token) not between 32 and 128 or coalesce(p_honeypot,'')<>'' then raise exception 'Formulario no válido' using errcode='22023';end if;
 perform mf_seguridad.validar_solicitud(p_datos,false);
 th=encode(sha256(convert_to(p_token,'UTF8')),'hex');dh=encode(sha256(convert_to(p_datos::text,'UTF8')),'hex');
 eh=encode(sha256(convert_to(lower(trim(coalesce(p_datos->>'email',''))),'UTF8')),'hex');
 perform pg_advisory_xact_lock(230002);
 select * into r from mf_seguridad.recibos_publicos where solicitud_id=p_solicitud_id;
 if found then
  if r.token_hash<>th or r.datos_hash<>dh then raise exception 'No se pudo confirmar este reintento' using errcode='22023';end if;
  select * into c from public.mf_casos where id=p_solicitud_id;
 else
  if (select count(*) from mf_seguridad.recibos_publicos where created_at>now()-interval '1 hour')>=60 or
   (select count(*) from mf_seguridad.recibos_publicos where correo_hash=eh and created_at>now()-interval '15 minutes')>=3 then raise exception 'Espera unos minutos antes de enviar otra solicitud' using errcode='P0001';end if;
  c=mf_seguridad.insertar_solicitud(p_solicitud_id,p_datos,null,false);
  insert into mf_seguridad.recibos_publicos values(p_solicitud_id,th,dh,eh,now());
 end if;
 return jsonb_build_object('codigo',format('MF-%s-%s',extract(year from c.created_at at time zone 'America/Santiago'),lpad(c.numero::text,greatest(4,length(c.numero::text)),'0')));
end $$;
revoke all on function public.registrar_solicitud_publica(uuid,text,jsonb,text) from public;
grant execute on function public.registrar_solicitud_publica(uuid,text,jsonb,text) to anon,authenticated;

-- Solo el worker de servidor puede reservar y confirmar avisos.
create function public.mf_tomar_avisos_solicitud() returns jsonb
language plpgsql security definer set search_path='' as $$
declare r public.mf_avisos_solicitud;datos jsonb;resultado jsonb:='[]';token uuid;
begin
 update public.mf_avisos_solicitud set estado='incierto',updated_at=now()
 where estado='preparado' and updated_at<now()-interval '15 minutes';
 for r in select * from public.mf_avisos_solicitud where estado in ('pendiente','error')
  and intentos<5 and proximo_intento<=now() order by created_at for update skip locked limit 10 loop
  token=gen_random_uuid();
  update public.mf_avisos_solicitud set estado='preparado',intentos=intentos+1,lease=token,updated_at=now() where id=r.id;
  select jsonb_build_object('id',r.id,'lease',token,
   'destinatario',coalesce(nullif(cfg.datos->>'correo_avisos',''),cfg.datos->>'correo_contacto',''),
   'codigo',format('MF-%s-%s',extract(year from c.created_at at time zone 'America/Santiago'),lpad(c.numero::text,greatest(4,length(c.numero::text)),'0')),
   'contacto',c.contacto,'email',c.email,'telefono',c.telefono,'cliente',c.cliente,'servicio',c.servicio,
   'tematicas',c.tematicas,'fecha_preferida',c.fecha_preferida)
  into datos from public.mf_casos c left join public.mf_configuracion cfg on cfg.id='general' where c.id=r.caso_id;
  resultado=resultado||jsonb_build_array(datos);
 end loop;
 return resultado;
end $$;
create function public.mf_confirmar_aviso_solicitud(p_id uuid,p_lease uuid,p_estado text) returns boolean
language plpgsql security definer set search_path='' as $$
begin
 if p_estado not in ('enviado','error','incierto') or p_estado is null then raise exception 'Estado no válido';end if;
 update public.mf_avisos_solicitud set estado=p_estado,updated_at=now(),
  proximo_intento=now()+interval '5 minutes'*power(2,least(intentos,5))
 where id=p_id and lease=p_lease and estado='preparado';
 return found;
end $$;
revoke all on function public.mf_tomar_avisos_solicitud() from public,anon,authenticated;
revoke all on function public.mf_confirmar_aviso_solicitud(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.mf_tomar_avisos_solicitud() to service_role;
grant execute on function public.mf_confirmar_aviso_solicitud(uuid,uuid,text) to service_role;
notify pgrst,'reload schema';
commit;
