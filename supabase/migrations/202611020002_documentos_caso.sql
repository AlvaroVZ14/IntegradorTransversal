-- Prompt 20. Aplicar completo con postgres, después de las migraciones existentes.
-- No cambia permisos de casos, cotizaciones, ventas ni navegación de clientes.
begin;

create table public.mf_documentos (
 id uuid primary key default gen_random_uuid(),
 caso_id uuid not null references public.mf_casos(id),
 tipo text not null check(tipo in ('Lista de asistencia','Informe','Certificado','Material','Cotización','Otro')),
 nombre text not null check(nombre ~ '^[A-Za-z0-9_-]+\.(pdf|docx|xlsx|png|jpg|webp)$'),
 archivo_path text not null unique,
 tamano bigint not null check(tamano between 1 and 10485760),
 tipo_mime text not null check(tipo_mime in ('application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','image/png','image/jpeg','image/webp')),
 visible_cliente boolean not null,
 subido_por uuid not null references auth.users(id),
 fecha_subida timestamptz not null default now(),
 nota text not null default '' check(length(nota)<=2000),
 estado_archivo text not null default 'pendiente' check(estado_archivo in ('pendiente','disponible','eliminando','eliminado')),
 cotizacion_id uuid unique references public.mf_cotizaciones(id),
 aviso_estado text not null default 'no_solicitado' check(aviso_estado in ('no_solicitado','reservado','enviado','fallido','incierto')),
 check(archivo_path ~ ('^'||caso_id::text||'/'||id::text||'\.(pdf|docx|xlsx|png|jpg|webp)$'))
);
create index mf_documentos_caso_fecha on public.mf_documentos(caso_id,fecha_subida desc);
alter table public.mf_documentos enable row level security;
revoke all on public.mf_documentos from public,anon,authenticated;
grant select,insert,update,delete on public.mf_documentos to authenticated;

-- Identidad comprobada en auth.users: nunca en parámetros ni user_metadata.
-- El correo permite recuperar documentos de un caso aún NO vinculado a una cuenta.
create function public.mf_caso_documentos_propio(p_caso_id uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.mf_casos c
 join auth.users u on u.id=auth.uid() and u.email_confirmed_at is not null
 join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where c.id=p_caso_id and (c.cliente_id=u.id or
 (c.cliente_id is null and lower(trim(c.email))=lower(trim(u.email)))));
$$;
revoke all on function public.mf_caso_documentos_propio(uuid) from public,anon;
grant execute on function public.mf_caso_documentos_propio(uuid) to authenticated;
create policy mf_documentos_lectura on public.mf_documentos for select to authenticated
 using(public.es_admin() or (estado_archivo='disponible' and visible_cliente and public.mf_caso_documentos_propio(caso_id)));
create policy mf_documentos_insertar on public.mf_documentos for insert to authenticated with check(public.es_admin());
create policy mf_documentos_editar on public.mf_documentos for update to authenticated using(public.es_admin()) with check(public.es_admin());
create policy mf_documentos_borrar on public.mf_documentos for delete to authenticated using(public.es_admin());

create function public.mf_integridad_documento() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 if tg_op='INSERT' then
  new.subido_por:=auth.uid();new.fecha_subida:=now();new.estado_archivo:='pendiente';
  new.aviso_estado:='no_solicitado';
  new.visible_cliente:=coalesce(new.visible_cliente,new.tipo in ('Lista de asistencia','Informe','Certificado','Material'));
 elsif (new.id,new.caso_id,new.archivo_path,new.cotizacion_id,new.subido_por,new.fecha_subida,new.tamano,new.tipo_mime)
  is distinct from (old.id,old.caso_id,old.archivo_path,old.cotizacion_id,old.subido_por,old.fecha_subida,old.tamano,old.tipo_mime) then
  raise exception 'La identidad del documento no se puede cambiar';
 end if;
 if new.cotizacion_id is not null and (new.tipo<>'Cotización' or not exists(
  select 1 from public.mf_cotizaciones q where q.id=new.cotizacion_id and q.caso_id=new.caso_id)) then
  raise exception 'Cotización ajena al caso';
 end if;
 -- El nombre público también se genera en el servidor: sin nombres de personas.
 new.nombre:='Documento_'||replace(new.id::text,'-','')||'.'||split_part(new.archivo_path,'.',2);
 return new;
end $$;
revoke all on function public.mf_integridad_documento() from public,anon,authenticated;
create trigger mf_documento_integridad before insert or update on public.mf_documentos for each row execute function public.mf_integridad_documento();

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 values('documentos-casos','documentos-casos',false,10485760,array['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','image/png','image/jpeg','image/webp'])
 on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;

-- Cierra el bucket incluso si existen políticas permisivas ajenas para Storage.
create policy mf_docs_anon_limite on storage.objects as restrictive for all to anon
 using(bucket_id<>'documentos-casos') with check(bucket_id<>'documentos-casos');
create policy mf_docs_leer on storage.objects for select to authenticated using(
 bucket_id='documentos-casos' and (public.es_admin() or exists(select 1 from public.mf_documentos d
 where d.archivo_path=name and d.estado_archivo='disponible' and d.visible_cliente and public.mf_caso_documentos_propio(d.caso_id))));
create policy mf_docs_leer_limite on storage.objects as restrictive for select to authenticated using(
 bucket_id<>'documentos-casos' or public.es_admin() or exists(select 1 from public.mf_documentos d
 where d.archivo_path=name and d.estado_archivo='disponible' and d.visible_cliente and public.mf_caso_documentos_propio(d.caso_id)));
create policy mf_docs_insertar on storage.objects for insert to authenticated with check(
 bucket_id='documentos-casos' and public.es_admin() and exists(select 1 from public.mf_documentos d where d.archivo_path=name and d.estado_archivo='pendiente'));
create policy mf_docs_insertar_limite on storage.objects as restrictive for insert to authenticated with check(
 bucket_id<>'documentos-casos' or (public.es_admin() and exists(select 1 from public.mf_documentos d where d.archivo_path=name and d.estado_archivo='pendiente')));
create policy mf_docs_editar on storage.objects for update to authenticated using(bucket_id='documentos-casos' and public.es_admin()) with check(bucket_id='documentos-casos' and public.es_admin());
create policy mf_docs_editar_limite on storage.objects as restrictive for update to authenticated using(bucket_id<>'documentos-casos' or public.es_admin()) with check(bucket_id<>'documentos-casos' or public.es_admin());
create policy mf_docs_borrar on storage.objects for delete to authenticated using(bucket_id='documentos-casos' and public.es_admin());
create policy mf_docs_borrar_limite on storage.objects as restrictive for delete to authenticated using(bucket_id<>'documentos-casos' or public.es_admin());

create function public.mf_confirmar_documento(p_id uuid) returns public.mf_documentos
language plpgsql security definer set search_path='' as $$
declare d public.mf_documentos;
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 select * into d from public.mf_documentos where id=p_id for update;
 if not found or d.estado_archivo not in ('pendiente','disponible') then raise exception 'Documento no disponible'; end if;
 if not exists(select 1 from storage.objects o where o.bucket_id='documentos-casos' and o.name=d.archivo_path
  and (o.metadata->>'size')::bigint=d.tamano and o.metadata->>'mimetype'=d.tipo_mime) then
  raise exception 'No se confirmó el archivo completo';
 end if;
 update public.mf_documentos set estado_archivo='disponible' where id=p_id returning * into d;
 return d;
end $$;

create function public.mf_eliminar_documento(p_id uuid,p_finalizar boolean default false) returns boolean
language plpgsql security definer set search_path='' as $$
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 perform 1 from public.mf_documentos where id=p_id for update;
 if not found then return true; end if;
 if p_finalizar then
  if exists(select 1 from public.mf_documentos d join storage.objects o on o.bucket_id='documentos-casos' and o.name=d.archivo_path where d.id=p_id) then
   raise exception 'El archivo todavía no se ha eliminado';
  end if;
  -- Tumba sin archivo: evita regenerar automáticamente una cotización eliminada.
  update public.mf_documentos set estado_archivo='eliminado',visible_cliente=false,nota='' where id=p_id;
 else
  update public.mf_documentos set estado_archivo='eliminando',visible_cliente=false where id=p_id and estado_archivo<>'eliminado';
 end if;
 return true;
end $$;

-- Estado y destinatario de aviso: solo administración puede consultar correos ajenos.
create function public.mf_destinatario_documentos(p_caso_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare c public.mf_casos; correo text;
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 select * into c from public.mf_casos where id=p_caso_id;
 if not found then raise exception 'Caso no encontrado'; end if;
 select u.email into correo from auth.users u join public.mf_perfiles p on p.id=u.id and p.rol='cliente'
 where u.email_confirmed_at is not null and
 (c.cliente_id=u.id or (c.cliente_id is null and lower(trim(c.email))=lower(trim(u.email)))) limit 1;
 return jsonb_build_object('tiene_cuenta',correo is not null,'correo',coalesce(correo,c.email,''));
end $$;

create function public.mf_reservar_aviso_documento(p_id uuid) returns boolean
language plpgsql security definer set search_path='' as $$
declare reservado uuid;
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 update public.mf_documentos set aviso_estado='reservado' where id=p_id and visible_cliente and estado_archivo='disponible' and aviso_estado='no_solicitado' returning id into reservado;
 return reservado is not null;
end $$;

create function public.mf_resultado_aviso_documento(p_id uuid,p_estado text) returns void
language plpgsql security definer set search_path='' as $$
begin
 if not public.es_admin() then raise exception 'Solo Administración' using errcode='42501'; end if;
 if p_estado not in ('enviado','fallido','incierto') then raise exception 'Resultado no válido'; end if;
 update public.mf_documentos set aviso_estado=p_estado where id=p_id and aviso_estado='reservado';
end $$;

revoke all on function public.mf_confirmar_documento(uuid),public.mf_eliminar_documento(uuid,boolean),public.mf_destinatario_documentos(uuid),public.mf_reservar_aviso_documento(uuid),public.mf_resultado_aviso_documento(uuid,text) from public,anon;
grant execute on function public.mf_confirmar_documento(uuid),public.mf_eliminar_documento(uuid,boolean),public.mf_destinatario_documentos(uuid),public.mf_reservar_aviso_documento(uuid),public.mf_resultado_aviso_documento(uuid,text) to authenticated;
commit;
