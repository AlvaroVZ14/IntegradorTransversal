-- Ejecutar completo DESPUÉS de 202610210001_cliente_solo_solicitud.sql.
-- Añade datos opcionales; conserva roles, políticas, consentimiento e idempotencia.
begin;
create or replace function public.mf_rut_valido(valor text) returns boolean
language plpgsql immutable set search_path='' as $$
declare limpio text; cuerpo text; dv text; suma integer:=0; factor integer:=2; resto integer; i integer;
begin
  if valor is null or trim(valor)='' then return true; end if;
  limpio:=upper(regexp_replace(valor,'[.[:space:]-]','','g'));
  if limpio !~ '^[0-9]{1,8}[0-9K]$' then return false; end if;
  cuerpo:=left(limpio,length(limpio)-1); dv:=right(limpio,1);
  for i in reverse length(cuerpo)..1 loop
    suma:=suma+substring(cuerpo,i,1)::integer*factor;
    factor:=case when factor=7 then 2 else factor+1 end;
  end loop;
  resto:=11-suma%11;
  return dv=case when resto=11 then '0' when resto=10 then 'K' else resto::text end;
end $$;
revoke all on function public.mf_rut_valido(text) from public,anon;
grant execute on function public.mf_rut_valido(text) to authenticated;
alter table public.mf_casos
  add column if not exists rut text not null default '',
  add column if not exists cargo text not null default '';
alter table public.mf_casos drop constraint if exists mf_casos_rut_check;
alter table public.mf_casos add constraint mf_casos_rut_check check(length(rut)<=16 and public.mf_rut_valido(rut));
alter table public.mf_casos drop constraint if exists mf_casos_cargo_check;
alter table public.mf_casos add constraint mf_casos_cargo_check check(length(cargo)<=160);

create or replace function public.registrar_solicitud(p_solicitud_id uuid,p_datos jsonb) returns jsonb
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
  insert into public.mf_casos(id,creado_por,cliente_id,cliente,contacto,email,telefono,
    servicio,tematica,participantes,horas,modalidad,lugar,fecha_preferida,detalle,rut,cargo,
    origen,registrado_por,consentimiento,consentimiento_fecha,consentimiento_version)
  values(p_solicitud_id,perfil.id,perfil.id,coalesce(nullif(trim(p_datos->>'cliente'),''),perfil.nombre),perfil.nombre,correo,
    coalesce(p_datos->>'telefono',''),p_datos->>'servicio',p_datos->>'tematica',
    (p_datos->>'participantes')::integer,(p_datos->>'horas')::numeric,p_datos->>'modalidad',
    coalesce(p_datos->>'lugar',''),nullif(p_datos->>'fecha_preferida','')::date,coalesce(p_datos->>'detalle',''),
    coalesce(p_datos->>'rut',''),coalesce(p_datos->>'cargo',''),
    'Formulario web','Cliente',true,now(),'2026-10-21') on conflict(id) do nothing;
  select * into caso from public.mf_casos where id=p_solicitud_id and creado_por=perfil.id
    and cliente_id=perfil.id and origen='Formulario web' and consentimiento;
  if not found then raise exception 'No se pudo registrar la solicitud' using errcode='42501'; end if;
  return jsonb_build_object('codigo',format('MF-%s-%s',extract(year from caso.created_at at time zone 'America/Santiago'),
    lpad(caso.numero::text,greatest(4,length(caso.numero::text)),'0')));
end $$;
revoke all on function public.registrar_solicitud(uuid,jsonb) from public,anon;
grant execute on function public.registrar_solicitud(uuid,jsonb) to authenticated;
notify pgrst,'reload schema';
commit;
