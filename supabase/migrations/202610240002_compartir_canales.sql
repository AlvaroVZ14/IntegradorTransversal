-- Requiere 202610240001_formulario_unificado.sql. Ejecutar completo una vez.
-- Agrega atribución del enlace. No cambia origen, estados, roles ni políticas.
begin;
create table mf_seguridad.compartir_respaldo(firma text primary key,definicion text not null);
revoke all on mf_seguridad.compartir_respaldo from public,anon,authenticated;
insert into mf_seguridad.compartir_respaldo
select oid::regprocedure::text,pg_get_functiondef(oid) from pg_proc
where (pronamespace='mf_seguridad'::regnamespace and proname in ('validar_solicitud','insertar_solicitud'))
or (pronamespace='public'::regnamespace and proname='mf_catalogo_solicitudes');

alter table public.mf_casos add column canal_captacion text
 constraint mf_canal_captacion_check check(canal_captacion in ('instagram','facebook','whatsapp','sitio_web','qr','directo','otro'));
-- NULL en casos históricos e internos: no se inventa su procedencia.
create function mf_seguridad.normalizar_canal(valor text) returns text
language sql immutable set search_path='' as $$
 select case when valor is null then 'directo'
 when valor in ('instagram','facebook','whatsapp','sitio_web','qr','directo','otro') then valor else 'otro' end;
$$;
revoke all on function mf_seguridad.normalizar_canal(text) from public,anon,authenticated;

create or replace function mf_seguridad.validar_solicitud(datos jsonb,interno boolean) returns void
language plpgsql set search_path='' as $$
declare campo text; permitidos text[]:=array['cliente','contacto','email','telefono','rut','cargo','servicio','tematica','tematicas',
 'participantes','horas','modalidad','lugar','fecha_preferida','detalle','dirigido_a','consentimiento','honeypot','canal_captacion'];
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
 origen,registrado_por,consentimiento,consentimiento_fecha,consentimiento_version)
 values(p_id,usuario,vinculo,case when interno then nullif(trim(d->>'cliente'),'') else coalesce(nullif(trim(d->>'cliente'),''),nombre) end,
 nombre,correo,coalesce(d->>'telefono',''),coalesce(d->>'rut',''),coalesce(d->>'cargo',''),
 nullif(d->>'servicio',''),temas[1],temas,case when interno then null when not (d ? 'canal_captacion') then 'directo'
 else mf_seguridad.normalizar_canal(coalesce(d->>'canal_captacion','')) end,(d->>'participantes')::integer,(d->>'horas')::numeric,nullif(d->>'modalidad',''),
 coalesce(d->>'lugar',''),nullif(d->>'fecha_preferida','')::date,coalesce(d->>'detalle',''),coalesce(d->>'dirigido_a',''),
 case when interno then coalesce(d->>'referido_por','') else '' end,origen,case when interno then 'Administración' else 'Cliente' end,
 consent,case when consent then now() end,case when consent then '2026-10-24' end) returning * into c;
 return c;
end $$;
revoke all on function mf_seguridad.insertar_solicitud(uuid,jsonb,uuid,boolean) from public,anon,authenticated;

-- Registrar_solicitud y registrar_solicitud_publica llaman a los dos helpers
-- anteriores: conservan consentimiento, identidad forzada, límites e idempotencia.
create or replace function public.mf_catalogo_solicitudes() returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object('version',3,
 'servicios',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='servicio' and activo),'[]'),
 'tematicas',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='tematica' and activo),'[]'))
 from public.mf_catalogo_formulario;
$$;
revoke all on function public.mf_catalogo_solicitudes() from public;
grant execute on function public.mf_catalogo_solicitudes() to anon,authenticated;

-- La pantalla privada comprueba el rol también en DB y respeta la RLS existente.
create function public.mf_configuracion_compartir() returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare resultado jsonb;
begin
 if not coalesce(public.es_admin(),false) then raise exception 'Acceso denegado' using errcode='42501';end if;
 select jsonb_build_object('datos',datos,'version',version) into resultado
 from public.mf_configuracion where id='general';
 return resultado;
end $$;
revoke all on function public.mf_configuracion_compartir() from public,anon;
grant execute on function public.mf_configuracion_compartir() to authenticated;

-- Conserva URL, textos y cualquier otra configuración que ya haya sido editada.
update public.mf_configuracion set datos=jsonb_build_object('url_publica','') || datos ||
 jsonb_build_object('compartir',jsonb_build_object(
 'instagram_biografia','✨ Cuéntanos qué necesita tu equipo. Preparamos una propuesta a tu medida. {enlace}',
 'instagram_publicacion','💡 ¿Tu equipo necesita nuevas herramientas para crecer? Cuéntanos qué necesitan y te preparamos una propuesta a su medida. Encuentra el formulario en el enlace de nuestra biografía: {enlace}',
 'facebook','💡 Cada equipo tiene desafíos distintos. Cuéntanos qué necesita el tuyo y preparemos una propuesta a su medida. Completa el formulario aquí: {enlace}',
 'whatsapp','¡Hola! 😊 Si tu equipo necesita una capacitación, cuéntanos qué tienen en mente en este formulario. Te contactaremos para preparar una propuesta a su medida: {enlace}',
 'sitio_web','Cuéntanos qué necesita tu equipo. Completa este formulario y te contactaremos para preparar una propuesta a tu medida: {enlace}') ||
 case when jsonb_typeof(datos->'compartir')='object' then datos->'compartir' else '{}'::jsonb end)
 where id='general';
notify pgrst,'reload schema';
commit;
