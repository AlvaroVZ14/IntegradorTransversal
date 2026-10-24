-- Después de 202610230001_lectura_en_vivo.sql. Ejecutar completo una vez.
-- No concede SELECT/INSERT de tablas a anon ni cambia los permisos de clientes.
begin;

create function public.mf_configuracion_publica() returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object(
  'sitio_web',case when jsonb_typeof(datos->'sitio_web')='string' then left(datos->>'sitio_web',2048) else '' end,
  'correo_contacto',case when jsonb_typeof(datos->'correo_contacto')='string' then left(datos->>'correo_contacto',254) else '' end,
  'redes',jsonb_build_object(
   'facebook',case when jsonb_typeof(datos->'redes'->'facebook')='string' then left(datos->'redes'->>'facebook',2048) else '' end,
   'instagram',case when jsonb_typeof(datos->'redes'->'instagram')='string' then left(datos->'redes'->>'instagram',2048) else '' end))
 from public.mf_configuracion where id='general';
$$;
revoke all on function public.mf_configuracion_publica() from public;
grant execute on function public.mf_configuracion_publica() to anon,authenticated;

-- Los visitantes no tienen usuario Auth. La autoría NULL solo se admite con
-- origen, consentimiento y tipo de registro explícitos, sin vincular una cuenta.
alter table public.mf_casos alter column creado_por drop not null;
alter table public.mf_casos add constraint mf_solicitud_sin_cuenta_check check(
 creado_por is not null or (cliente_id is null and origen='Formulario web' and
 registrado_por='Cliente' and consentimiento and consentimiento_fecha is not null));

create table mf_seguridad.recibos_publicos(
 solicitud_id uuid primary key references public.mf_casos(id),
 token_hash text not null,datos_hash text not null,correo_hash text not null,
 created_at timestamptz not null default now());
revoke all on mf_seguridad.recibos_publicos from public,anon,authenticated;
alter table mf_seguridad.recibos_publicos enable row level security;
create index mf_publicos_fecha on mf_seguridad.recibos_publicos(created_at);
create index mf_publicos_correo_fecha on mf_seguridad.recibos_publicos(correo_hash,created_at);

create function public.registrar_solicitud_publica(p_solicitud_id uuid,p_token text,p_datos jsonb,p_honeypot text default '')
returns jsonb language plpgsql security definer set search_path='' as $$
declare recibo mf_seguridad.recibos_publicos; caso public.mf_casos; correo text;
 token_h text;datos_h text;correo_h text;campo text;personas numeric;duracion numeric;
begin
 if p_solicitud_id is null or p_token is null or length(p_token) not between 32 and 128
  or p_datos is null or jsonb_typeof(p_datos)<>'object' or octet_length(p_datos::text)>32000
  or coalesce(p_honeypot,'')<>'' then
  raise exception 'No se pudo confirmar el formulario' using errcode='22023';
 end if;
 if p_datos->'consentimiento' is distinct from 'true'::jsonb then
  raise exception 'Debes autorizar el uso de tus datos' using errcode='22023';
 end if;
 if exists(select 1 from jsonb_object_keys(p_datos) k where k not in
  ('cliente','contacto','email','telefono','rut','cargo','servicio','tematica','participantes','horas',
   'modalidad','lugar','fecha_preferida','detalle','consentimiento')) then
  raise exception 'Campos no permitidos' using errcode='22023';
 end if;
 foreach campo in array array['cliente','contacto','email','telefono','rut','cargo','servicio','tematica','modalidad','lugar','detalle'] loop
  if p_datos ? campo and jsonb_typeof(p_datos->campo) is distinct from 'string' then
   raise exception 'Revisa los campos del formulario' using errcode='22023';
  end if;
 end loop;
 if jsonb_typeof(p_datos->'participantes') is distinct from 'number' or jsonb_typeof(p_datos->'horas') is distinct from 'number' then
  raise exception 'Revisa participantes y horas' using errcode='22023';
 end if;
 personas=(p_datos->>'participantes')::numeric;duracion=(p_datos->>'horas')::numeric;
 if personas<>trunc(personas) or personas not between 1 and 10000 or duracion not between .5 and 1000 then
  raise exception 'Revisa participantes y horas' using errcode='22023';
 end if;
 if nullif(p_datos->>'fecha_preferida','')::date < (now() at time zone 'America/Santiago')::date then
  raise exception 'La fecha preferida no puede estar en el pasado' using errcode='22023';
 end if;
 if coalesce(p_datos->>'telefono','')<>'' and
  ((p_datos->>'telefono') !~ '^[+]?[0-9[:space:]().-]+$' or
   length(regexp_replace(p_datos->>'telefono','[^0-9]','','g')) not between 8 and 15) then
  raise exception 'Revisa el teléfono' using errcode='22023';
 end if;
 correo=lower(trim(p_datos->>'email'));
 token_h=encode(sha256(convert_to(p_token,'UTF8')),'hex');
 datos_h=encode(sha256(convert_to(p_datos::text,'UTF8')),'hex');
 correo_h=encode(sha256(convert_to(coalesce(correo,''),'UTF8')),'hex');
 -- Serializa el breve registro para que dos peticiones no salten los límites.
 perform pg_advisory_xact_lock(230002);
 select * into recibo from mf_seguridad.recibos_publicos where solicitud_id=p_solicitud_id;
 if found then
  if recibo.token_hash<>token_h or recibo.datos_hash<>datos_h then
   raise exception 'No se pudo confirmar este reintento' using errcode='22023';
  end if;
  select * into caso from public.mf_casos where id=p_solicitud_id;
 else
  -- Límites modestos para el plan gratuito: no son un CAPTCHA ni evitan todo abuso.
  if (select count(*) from mf_seguridad.recibos_publicos where created_at>now()-interval '1 hour')>=60
   or (select count(*) from mf_seguridad.recibos_publicos where correo_hash=correo_h and created_at>now()-interval '15 minutes')>=3 then
   raise exception 'Espera unos minutos antes de enviar otra solicitud' using errcode='P0001';
  end if;
  insert into public.mf_casos(id,creado_por,cliente_id,cliente,contacto,email,telefono,rut,cargo,
   servicio,tematica,participantes,horas,modalidad,lugar,fecha_preferida,detalle,
   origen,registrado_por,consentimiento,consentimiento_fecha,consentimiento_version)
  values(p_solicitud_id,null,null,coalesce(nullif(trim(p_datos->>'cliente'),''),trim(p_datos->>'contacto')),
   trim(p_datos->>'contacto'),correo,coalesce(p_datos->>'telefono',''),coalesce(p_datos->>'rut',''),coalesce(p_datos->>'cargo',''),
   p_datos->>'servicio',p_datos->>'tematica',personas::integer,duracion,p_datos->>'modalidad',coalesce(p_datos->>'lugar',''),
   nullif(p_datos->>'fecha_preferida','')::date,coalesce(p_datos->>'detalle',''),
   'Formulario web','Cliente',true,now(),'2026-10-23-publico-v1') returning * into caso;
  insert into mf_seguridad.recibos_publicos values(p_solicitud_id,token_h,datos_h,correo_h,now());
 end if;
 return jsonb_build_object('codigo',format('MF-%s-%s',extract(year from caso.created_at at time zone 'America/Santiago'),
  lpad(caso.numero::text,greatest(4,length(caso.numero::text)),'0')));
end $$;
revoke all on function public.registrar_solicitud_publica(uuid,text,jsonb,text) from public;
grant execute on function public.registrar_solicitud_publica(uuid,text,jsonb,text) to anon,authenticated;
notify pgrst,'reload schema';
commit;
