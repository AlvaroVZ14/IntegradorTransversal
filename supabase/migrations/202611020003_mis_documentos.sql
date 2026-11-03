-- Prompt 21. Ejecutar completo DESPUÉS de 202611020002_documentos_caso.sql.
-- No abre las tablas de gestión: el portal recibe una proyección mínima por RPC.
begin;

alter table public.mf_casos add column correos_documentos text[] not null default '{}';

create function public.mf_normalizar_correos_documentos() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if (tg_op='INSERT' and cardinality(new.correos_documentos)>0) or
    (tg_op='UPDATE' and new.correos_documentos is distinct from old.correos_documentos) then
  if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 end if;
 if cardinality(new.correos_documentos)>20 or exists(select 1 from unnest(new.correos_documentos) e
  where e is null or length(trim(e))>254 or trim(e)!~'^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$') then
  raise exception 'Revisa los correos adicionales (máximo 20)';
 end if;
 new.correos_documentos:=array(select distinct lower(trim(e)) from unnest(new.correos_documentos) e order by 1);
 return new;
end $$;
revoke all on function public.mf_normalizar_correos_documentos() from public,anon,authenticated;
create trigger mf_correos_documentos before insert or update on public.mf_casos
 for each row execute function public.mf_normalizar_correos_documentos();

-- Ni user_metadata, ni el correo de mf_perfiles, ni un ID enviado por el cliente
-- sustituyen el correo ACTUAL confirmado por Auth. No se modifican casos antiguos.
create or replace function public.mf_caso_documentos_propio(p_caso_id uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.mf_casos c
 join auth.users u on u.id=auth.uid() and u.email_confirmed_at is not null
 join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where c.id=p_caso_id and (lower(trim(c.email))=lower(trim(u.email))
 or lower(trim(u.email))=any(c.correos_documentos)));
$$;

-- Evita filtrar nota, subido_por, archivo_path u otros metadatos internos por
-- SELECT directo. Administración conserva su CRUD; cliente usa RPC explícitas.
drop policy mf_documentos_lectura on public.mf_documentos;
create policy mf_documentos_lectura on public.mf_documentos for select to authenticated using(public.es_admin());
create policy mf_documentos_limite on public.mf_documentos as restrictive for all to authenticated
 using(public.es_admin()) with check(public.es_admin());

create function public.mf_mis_documentos(p_desde integer default 0) returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce(jsonb_agg(fila order by fecha desc,id),'[]'::jsonb) from (
  select c.id,c.created_at fecha,jsonb_build_object(
   'id',c.id,'numero',c.numero,'created_at',c.created_at,'cliente',c.cliente,'servicio',c.servicio,
   'documentos',coalesce((select jsonb_agg(jsonb_build_object(
    'id',d.id,'tipo',d.tipo,'nombre',d.nombre,'fecha_subida',d.fecha_subida,'tipo_mime',d.tipo_mime)
    order by d.fecha_subida desc,d.id) from public.mf_documentos d
    where d.caso_id=c.id and d.visible_cliente and d.estado_archivo='disponible'),'[]'::jsonb)) fila
  from public.mf_casos c where public.mf_caso_documentos_propio(c.id)
  order by c.created_at desc,c.id limit 100 offset greatest(0,coalesce(p_desde,0))
 ) casos;
$$;

create function public.mf_documento_cliente(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 -- Descriptor únicamente para el servidor que firma/descarga. Nunca se renderiza.
 select jsonb_build_object('archivo_path',d.archivo_path,'nombre',d.nombre,'tipo_mime',d.tipo_mime)
 from public.mf_documentos d where d.id=p_id and d.visible_cliente and d.estado_archivo='disponible'
 and public.mf_caso_documentos_propio(d.caso_id);
$$;

-- Storage no depende de conceder SELECT de metadatos internos al cliente.
create function public.mf_descarga_documento_permitida(p_path text) returns boolean
language sql stable security definer set search_path='' as $$
 select public.es_admin() or exists(select 1 from public.mf_documentos d where d.archivo_path=p_path
 and d.visible_cliente and d.estado_archivo='disponible' and public.mf_caso_documentos_propio(d.caso_id));
$$;
drop policy mf_docs_leer on storage.objects;
drop policy mf_docs_leer_limite on storage.objects;
create policy mf_docs_leer on storage.objects for select to authenticated using(
 bucket_id='documentos-casos' and public.mf_descarga_documento_permitida(name));
create policy mf_docs_leer_limite on storage.objects as restrictive for select to authenticated using(
 bucket_id<>'documentos-casos' or public.mf_descarga_documento_permitida(name));

create or replace function public.mf_destinatario_documentos(p_caso_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare c public.mf_casos; correo text;
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 select * into c from public.mf_casos where id=p_caso_id;
 if not found then raise exception 'Caso no encontrado'; end if;
 select u.email into correo from auth.users u join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where u.email_confirmed_at is not null and lower(trim(c.email))=lower(trim(u.email)) limit 1;
 return jsonb_build_object('tiene_cuenta',correo is not null,'correo',coalesce(correo,c.email,''));
end $$;

revoke all on function public.mf_mis_documentos(integer),public.mf_documento_cliente(uuid),public.mf_descarga_documento_permitida(text) from public,anon;
grant execute on function public.mf_mis_documentos(integer),public.mf_documento_cliente(uuid),public.mf_descarga_documento_permitida(text) to authenticated;
notify pgrst,'reload schema';
commit;
