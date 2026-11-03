-- Prompt 28. Ejecutar completo tras 202611020004_redes_sociales.sql.
begin;
alter table public.mf_empresas_redes add column telefono text not null default '',
 add column cargo text not null default '',add column version integer not null default 1;
alter table public.mf_empresas_redes drop constraint mf_empresas_redes_empresa_check;
alter table public.mf_empresas_redes add constraint mf_empresa_perfil check(length(empresa)<=180),
 add constraint mf_telefono_perfil check(length(telefono)<=40),add constraint mf_cargo_perfil check(length(cargo)<=160);

-- Inicializa únicamente columnas nuevas; no altera RUT, identidad o documentos.
update public.mf_empresas_redes r set telefono=coalesce(c.telefono,''),cargo=coalesce(c.cargo,'')
from (select distinct on(lower(trim(email)),lower(trim(cliente))) email,cliente,telefono,cargo
 from public.mf_casos where email is not null and cliente is not null order by lower(trim(email)),lower(trim(cliente)),created_at desc,id) c
where r.correo=lower(trim(c.email)) and r.empresa_clave=lower(trim(c.cliente));

create function mf_seguridad.telefono_perfil(v text) returns text
language plpgsql immutable set search_path='' as $$
declare digitos text;
begin
 v=trim(coalesce(v,''));if v='' then return '';end if;
 digitos=regexp_replace(v,'[^0-9]','','g');
 if length(v)>40 or v !~ '^[+]?[0-9[:space:]().-]+$' or length(digitos) not between 8 and 15 then
  raise exception 'Revisa Teléfono: usa entre 8 y 15 dígitos' using errcode='22023';end if;
 if length(digitos)=9 and left(digitos,1)='9' then digitos='56'||digitos;end if;
 if length(digitos)=11 and left(digitos,3)='569' then return '+56 9 '||substring(digitos,4,4)||' '||substring(digitos,8,4);end if;
 return v;
end $$;
revoke all on function mf_seguridad.telefono_perfil(text) from public,anon,authenticated;

create function public.mf_integridad_perfil_empresa() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 new.telefono=mf_seguridad.telefono_perfil(new.telefono);
 new.cargo=trim(new.cargo);new.redes_sociales=mf_seguridad.normalizar_redes(new.redes_sociales);
 if tg_op='UPDATE' then new.version=old.version+1;end if;
 new.updated_at=now();return new;
end $$;
revoke all on function public.mf_integridad_perfil_empresa() from public,anon,authenticated;
create trigger mf_perfil_empresa_integridad before insert or update on public.mf_empresas_redes
 for each row execute function public.mf_integridad_perfil_empresa();

create or replace function public.mf_reutilizar_redes_caso() returns trigger
language plpgsql security definer set search_path='' as $$
declare autorizado boolean;
begin
 if new.email is null or new.cliente is null then return new;end if;
 if tg_op='UPDATE' and (new.email,new.cliente,new.redes_sociales,new.telefono,new.cargo)
  is not distinct from (old.email,old.cliente,old.redes_sociales,old.telefono,old.cargo) then return new;end if;
 autorizado=public.es_admin() or exists(select 1 from auth.users u join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
  where u.id=auth.uid() and u.email_confirmed_at is not null and lower(trim(u.email))=lower(trim(new.email)));
 if autorizado and trim(new.cliente)<>'' and not exists(select 1 from public.mf_empresas_redes
  where correo=lower(trim(new.email)) and empresa_clave=lower(trim(new.cliente))) then
  -- Primera solicitud tras guardar un perfil vacío: reutiliza su mismo registro.
  update public.mf_empresas_redes set empresa=trim(new.cliente),telefono=coalesce(new.telefono,''),
   cargo=coalesce(new.cargo,''),redes_sociales=new.redes_sociales,confirmadas=true
   where correo=lower(trim(new.email)) and empresa_clave='';
  if found then return new;end if;
 end if;
 insert into public.mf_empresas_redes(correo,empresa,redes_sociales,telefono,cargo,confirmadas)
 values(lower(trim(new.email)),trim(new.cliente),new.redes_sociales,coalesce(new.telefono,''),coalesce(new.cargo,''),autorizado)
 on conflict(correo,empresa_clave) do update set redes_sociales=excluded.redes_sociales,telefono=excluded.telefono,
  cargo=excluded.cargo,empresa=excluded.empresa,confirmadas=excluded.confirmadas
 where (not mf_empresas_redes.confirmadas or excluded.confirmadas)
 and (mf_empresas_redes.redes_sociales,mf_empresas_redes.telefono,mf_empresas_redes.cargo,mf_empresas_redes.confirmadas)
 is distinct from (excluded.redes_sociales,excluded.telefono,excluded.cargo,excluded.confirmadas);
 return new;
end $$;

-- Conserva la validación de casos incompletos. Solo admite la sincronización
-- exacta de campos opcionales desde el registro propio ya confirmado.
create or replace function public.mf_integridad_solicitud() returns trigger
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
 if new.datos_incompletos and not public.es_admin() and not (
  tg_op='UPDATE' and (to_jsonb(new)-array['redes_sociales','telefono','cargo','updated_at','version'])
  is not distinct from (to_jsonb(old)-array['redes_sociales','telefono','cargo','updated_at','version'])
  and exists(select 1 from auth.users u join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
   join public.mf_empresas_redes r on r.correo=lower(trim(u.email)) and r.empresa_clave=lower(trim(new.cliente)) and r.confirmadas
   where u.id=auth.uid() and u.email_confirmed_at is not null and lower(trim(new.email))=r.correo
   and (new.redes_sociales,coalesce(new.telefono,''),coalesce(new.cargo,''))=(r.redes_sociales,r.telefono,r.cargo))
 ) then
  raise exception 'Completa los campos obligatorios' using errcode='22023';end if;
 return new;
end $$;

-- Una sola fuente de contacto actual. Solo estos tres datos se sincronizan.
-- El WHERE evita reescribir casos idénticos y corta la recursión de triggers.
create function public.mf_perfil_empresa_a_casos() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if not new.confirmadas or new.empresa_clave='' then return new;end if;
 update public.mf_casos c set redes_sociales=new.redes_sociales,telefono=new.telefono,cargo=new.cargo
 where lower(trim(c.email))=new.correo and lower(trim(c.cliente))=new.empresa_clave
 and (c.redes_sociales,coalesce(c.telefono,''),coalesce(c.cargo,'')) is distinct from (new.redes_sociales,new.telefono,new.cargo);
 return new;
end $$;
revoke all on function public.mf_perfil_empresa_a_casos() from public,anon,authenticated;
create trigger mf_perfil_empresa_sincronizar after insert or update on public.mf_empresas_redes
 for each row execute function public.mf_perfil_empresa_a_casos();

create function public.mf_mi_perfil() returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare cuenta_correo text;cuenta_nombre text;empresa_actual text;r public.mf_empresas_redes;c public.mf_casos;
begin
 select lower(trim(u.email)),p.nombre into cuenta_correo,cuenta_nombre from auth.users u join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where u.id=auth.uid() and u.email_confirmed_at is not null;
 if not found then raise exception 'Confirma el correo de tu cuenta para acceder a Mi perfil' using errcode='42501';end if;
 select * into c from public.mf_casos where lower(trim(email))=cuenta_correo order by created_at desc,id limit 1;
 if found then
  empresa_actual=coalesce(c.cliente,'');
  select * into r from public.mf_empresas_redes x where x.correo=cuenta_correo and x.empresa_clave=lower(trim(empresa_actual));
  if not found then
   select * into c from public.mf_casos where lower(trim(email))=cuenta_correo and lower(trim(cliente))=lower(trim(empresa_actual))
    order by datos_incompletos,created_at desc,id limit 1;
  end if;
 else
  select * into r from public.mf_empresas_redes x where x.correo=cuenta_correo order by x.confirmadas desc,x.updated_at desc,x.id limit 1;
  empresa_actual=coalesce(r.empresa,'');
 end if;
 return jsonb_build_object('id',r.id,'version',coalesce(r.version,0),'empresa',empresa_actual,'nombre',cuenta_nombre,'correo',cuenta_correo,
  'telefono',coalesce(r.telefono,c.telefono,''),'cargo',coalesce(r.cargo,c.cargo,''),
  'redes_sociales',coalesce(r.redes_sociales,c.redes_sociales,'{}'::jsonb));
end $$;

create function public.mf_guardar_mi_perfil(p_datos jsonb,p_id uuid default null,p_version integer default 0) returns jsonb
language plpgsql security definer set search_path='' as $$
declare identidad jsonb;r public.mf_empresas_redes;redes jsonb;v_telefono text;v_cargo text;
begin
 identidad=public.mf_mi_perfil(); -- Cuenta confirmada y rol cliente, en el servidor.
 if p_datos is null or jsonb_typeof(p_datos)<>'object' or octet_length(p_datos::text)>8000 or exists(
  select 1 from jsonb_object_keys(p_datos) k where k not in ('telefono','cargo','instagram','linkedin','facebook','sitio_web','otra_red')) then
  raise exception 'Solo puedes editar teléfono, cargo y redes sociales' using errcode='22023';end if;
 if exists(select 1 from jsonb_each(p_datos) x where jsonb_typeof(x.value)<>'string') then
  raise exception 'Revisa los campos de tu perfil' using errcode='22023';end if;
 v_telefono=mf_seguridad.telefono_perfil(p_datos->>'telefono');v_cargo=trim(coalesce(p_datos->>'cargo',''));
 if length(v_cargo)>160 then raise exception 'Revisa Cargo: máximo 160 caracteres' using errcode='22023';end if;
 redes=mf_seguridad.normalizar_redes(p_datos-array['telefono','cargo']);
 perform pg_advisory_xact_lock(hashtextextended(identidad->>'correo',28));
 if p_id is not null then
  select * into r from public.mf_empresas_redes where id=p_id and correo=identidad->>'correo' for update;
  if not found then raise exception 'No puedes modificar un perfil ajeno' using errcode='42501';end if;
  if r.version is distinct from p_version then raise exception 'Tu perfil cambió en otra sesión. Vuelve a abrir Mi perfil antes de guardar' using errcode='40001';end if;
  update public.mf_empresas_redes set telefono=v_telefono,cargo=v_cargo,redes_sociales=redes,confirmadas=true
   where id=r.id and (telefono,cargo,redes_sociales,confirmadas) is distinct from(v_telefono,v_cargo,redes,true) returning * into r;
  if not found then select * into r from public.mf_empresas_redes where id=p_id;end if;
 else
  if p_version is distinct from 0 or exists(select 1 from public.mf_empresas_redes where correo=identidad->>'correo' and empresa_clave=lower(trim(identidad->>'empresa'))) then
   raise exception 'Tu perfil cambió en otra sesión. Vuelve a abrir Mi perfil antes de guardar' using errcode='40001';end if;
  insert into public.mf_empresas_redes(correo,empresa,telefono,cargo,redes_sociales,confirmadas)
  values(identidad->>'correo',identidad->>'empresa',v_telefono,v_cargo,redes,true) returning * into r;
 end if;
 return jsonb_build_object('id',r.id,'version',r.version,'empresa',r.empresa,'nombre',identidad->>'nombre','correo',r.correo,
  'telefono',r.telefono,'cargo',r.cargo,'redes_sociales',r.redes_sociales);
end $$;

revoke all on function public.mf_mi_perfil(),public.mf_guardar_mi_perfil(jsonb,uuid,integer) from public,anon;
grant execute on function public.mf_mi_perfil(),public.mf_guardar_mi_perfil(jsonb,uuid,integer) to authenticated;

-- El lector del prompt 27 conserva su contrato y agrega teléfono/cargo.
create or replace function public.mf_mis_redes_empresa(p_empresa text default '') returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce((select jsonb_build_object('empresa',r.empresa,'telefono',r.telefono,'cargo',r.cargo,'redes_sociales',r.redes_sociales)
 from public.mf_empresas_redes r join auth.users u on u.id=auth.uid() and u.email_confirmed_at is not null
 join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where r.correo=lower(trim(u.email)) and r.confirmadas and
 ((trim(coalesce(p_empresa,''))<>'' and r.empresa_clave=lower(trim(p_empresa))) or
 (trim(coalesce(p_empresa,''))='' and (select count(*) from public.mf_empresas_redes x where x.correo=r.correo and x.confirmadas)=1))
 limit 1),'{}'::jsonb);
$$;
create or replace function public.mf_catalogo_solicitudes() returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object('version',5,
 'servicios',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='servicio' and activo),'[]'),
 'tematicas',coalesce(jsonb_agg(nombre order by orden,nombre) filter(where tipo='tematica' and activo),'[]'))
 from public.mf_catalogo_formulario;
$$;
notify pgrst,'reload schema';
commit;
