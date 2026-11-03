-- Prompt 29. Después de Documentos (20), Mis documentos (21) y Mi perfil (28).
-- No elimina archivos ni abre SELECT de las tablas internas al cliente.
begin;
alter table public.mf_documentos add column origen text not null default 'socia'
 check(origen in ('socia','cliente'));
alter table public.mf_documentos drop constraint mf_documentos_tipo_check;
alter table public.mf_documentos add constraint mf_documentos_tipo_check check(tipo in
 ('Lista de asistencia','Informe','Certificado','Material','Cotización','Otro',
 'Antecedentes de la empresa','Nómina de participantes','Requerimientos'));
-- Localiza la restricción de ruta sin depender del nombre automático de PostgreSQL.
do $$ declare n text; begin
 for n in select conname from pg_constraint where conrelid='public.mf_documentos'::regclass
 and contype='c' and pg_get_constraintdef(oid) like '%archivo_path%' loop
 execute format('alter table public.mf_documentos drop constraint %I',n);
 end loop;
end $$;
alter table public.mf_documentos add constraint mf_documentos_ruta_origen check(
 archivo_path ~ ('^'||caso_id::text||case when origen='cliente' then '/cliente/' else '/' end||id::text||'\.(pdf|docx|xlsx|png|jpg|webp)$'));
create index mf_documentos_cuenta_fecha on public.mf_documentos(subido_por,fecha_subida desc) where origen='cliente';

create function public.mf_documento_cliente_propio(p_id uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.mf_documentos d where d.id=p_id and d.origen='cliente'
 and d.subido_por=auth.uid() and public.mf_caso_documentos_propio(d.caso_id));
$$;
create function public.mf_caso_admite_documentos(p_id uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select public.mf_caso_documentos_propio(p_id) and exists(select 1 from public.mf_casos
 where id=p_id and estado<>'Finalizado'); -- Nombre almacenado de «Cerrada».
$$;

create or replace function public.mf_integridad_documento() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if tg_op='INSERT' then
  -- Serializa el cupo del caso; pendiente/eliminando también ocupan espacio.
  perform 1 from public.mf_casos where id=new.caso_id for update;
  if not public.es_admin() then
   if new.origen<>'cliente' or not public.mf_caso_admite_documentos(new.caso_id)
    or new.tipo not in ('Antecedentes de la empresa','Nómina de participantes','Requerimientos','Otro')
    or new.cotizacion_id is not null then
    raise exception 'No puedes enviar documentos a este caso' using errcode='42501';
   end if;
   perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text,29));
   if (select count(*) from public.mf_documentos where subido_por=auth.uid() and origen='cliente'
    and fecha_subida>now()-interval '1 hour')>=20 then
    raise exception 'Alcanzaste 20 archivos en una hora. Intenta más tarde' using errcode='P0001';
   end if;
   new.visible_cliente:=false;
  elsif new.origen<>'socia' then
   raise exception 'El origen se asigna según la cuenta que sube el documento';
  end if;
  if (select count(*) from public.mf_documentos where caso_id=new.caso_id and estado_archivo<>'eliminado')>=20 then
   raise exception 'Este caso alcanzó el máximo de 20 archivos. Solicita ayuda a Administración' using errcode='P0001';
  end if;
  new.subido_por:=auth.uid();new.fecha_subida:=now();new.estado_archivo:='pendiente';new.aviso_estado:='no_solicitado';
  new.visible_cliente:=coalesce(new.visible_cliente,new.tipo in ('Lista de asistencia','Informe','Certificado','Material'));
 else
  if not public.es_admin() and (not public.mf_documento_cliente_propio(old.id)
    or (new.tipo,new.nota,new.visible_cliente) is distinct from (old.tipo,old.nota,old.visible_cliente)) then
   raise exception 'Documento no disponible para tu cuenta' using errcode='42501';
  end if;
  if (new.id,new.caso_id,new.archivo_path,new.cotizacion_id,new.subido_por,new.fecha_subida,new.tamano,new.tipo_mime,new.origen)
   is distinct from (old.id,old.caso_id,old.archivo_path,old.cotizacion_id,old.subido_por,old.fecha_subida,old.tamano,old.tipo_mime,old.origen) then
   raise exception 'La identidad del documento no se puede cambiar';
  end if;
 end if;
 if new.cotizacion_id is not null and (new.tipo<>'Cotización' or not exists(
  select 1 from public.mf_cotizaciones q where q.id=new.cotizacion_id and q.caso_id=new.caso_id)) then
  raise exception 'Cotización ajena al caso';
 end if;
 new.nombre:='Documento_'||replace(new.id::text,'-','')||'.'||split_part(new.archivo_path,'.',2);
 return new;
end $$;

-- La tabla mantiene RLS restrictiva solo Administración. El cliente escribe a
-- través de RPC estrechas: no elige origen, cuenta, fecha, ruta ni visibilidad.
create function public.mf_preparar_documento_cliente(p_id uuid,p_caso_id uuid,p_tipo text,
 p_extension text,p_tamano bigint,p_mime text,p_nota text default '') returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.mf_documentos;
begin
 if not public.mf_caso_admite_documentos(p_caso_id) then raise exception 'No puedes enviar documentos a este caso' using errcode='42501'; end if;
 if p_extension not in ('pdf','docx','xlsx','png','jpg','webp') or p_mime is distinct from (case p_extension
  when 'pdf' then 'application/pdf' when 'docx' then 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  when 'xlsx' then 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  when 'jpg' then 'image/jpeg' else 'image/'||p_extension end) then raise exception 'Formato de archivo no permitido'; end if;
 perform 1 from public.mf_casos where id=p_caso_id for update;
 select * into d from public.mf_documentos where id=p_id;
 if found then
  if not public.mf_documento_cliente_propio(p_id) or
   (d.caso_id,d.tamano,d.tipo_mime,d.tipo,d.nota) is distinct from (p_caso_id,p_tamano,p_mime,p_tipo,coalesce(p_nota,''))
   or d.estado_archivo not in ('pendiente','disponible') then raise exception 'No se puede reintentar este documento'; end if;
 else
  insert into public.mf_documentos(id,caso_id,tipo,nombre,archivo_path,tamano,tipo_mime,visible_cliente,subido_por,nota,origen)
  values(p_id,p_caso_id,p_tipo,'Documento.pdf',p_caso_id||'/cliente/'||p_id||'.'||p_extension,
   p_tamano,p_mime,false,auth.uid(),coalesce(p_nota,''),'cliente') returning * into d;
 end if;
 return jsonb_build_object('id',d.id,'nombre',d.nombre,'archivo_path',d.archivo_path,'estado_archivo',d.estado_archivo);
end $$;

create or replace function public.mf_confirmar_documento(p_id uuid) returns public.mf_documentos
language plpgsql security definer set search_path='' as $$
declare d public.mf_documentos;
begin
 select * into d from public.mf_documentos where id=p_id for update;
 if not found or (not public.es_admin() and (not public.mf_documento_cliente_propio(p_id)
  or not public.mf_caso_admite_documentos(d.caso_id))) then raise exception 'Documento no disponible' using errcode='42501'; end if;
 if d.estado_archivo not in ('pendiente','disponible') then raise exception 'Documento no disponible'; end if;
 if not exists(select 1 from storage.objects o where o.bucket_id='documentos-casos' and o.name=d.archivo_path
  and (o.metadata->>'size')::bigint=d.tamano and o.metadata->>'mimetype'=d.tipo_mime) then raise exception 'No se confirmó el archivo completo'; end if;
 update public.mf_documentos set estado_archivo='disponible' where id=p_id returning * into d;
 return d;
end $$;

create function public.mf_eliminar_documento_cliente(p_id uuid,p_finalizar boolean default false) returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.mf_documentos;
begin
 select * into d from public.mf_documentos where id=p_id for update;
 if not found or not public.mf_documento_cliente_propio(p_id) or not public.mf_caso_admite_documentos(d.caso_id)
 then raise exception 'No puedes eliminar este documento' using errcode='42501'; end if;
 if p_finalizar then
  if exists(select 1 from storage.objects where bucket_id='documentos-casos' and name=d.archivo_path) then raise exception 'El archivo todavía no se ha eliminado'; end if;
  update public.mf_documentos set estado_archivo='eliminado' where id=p_id;
 else
  update public.mf_documentos set estado_archivo='eliminando' where id=p_id and estado_archivo<>'eliminado';
 end if;
 return jsonb_build_object('archivo_path',d.archivo_path);
end $$;

create or replace function public.mf_mis_documentos(p_desde integer default 0) returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce(jsonb_agg(fila order by fecha desc,id),'[]'::jsonb) from (
  select c.id,c.created_at fecha,jsonb_build_object('id',c.id,'numero',c.numero,'created_at',c.created_at,
   'cliente',c.cliente,'servicio',c.servicio,'puede_enviar',c.estado<>'Finalizado',
   'documentos',coalesce((select jsonb_agg(jsonb_build_object('id',d.id,'tipo',d.tipo,'nombre',d.nombre,
    'fecha_subida',d.fecha_subida,'tipo_mime',d.tipo_mime,'tamano',d.tamano,'origen',d.origen,
    'es_mio',d.origen='cliente' and d.subido_por=auth.uid(),'estado_archivo',d.estado_archivo)
    order by d.fecha_subida desc,d.id) from public.mf_documentos d where d.caso_id=c.id
    and ((d.visible_cliente and d.estado_archivo='disponible') or
      (d.origen='cliente' and d.subido_por=auth.uid() and d.estado_archivo<>'eliminado'))),'[]'::jsonb)) fila
  from public.mf_casos c where public.mf_caso_documentos_propio(c.id)
  order by c.created_at desc,c.id limit 100 offset greatest(0,coalesce(p_desde,0))
 ) casos;
$$;
create or replace function public.mf_documento_cliente(p_id uuid) returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object('archivo_path',d.archivo_path,'nombre',d.nombre,'tipo_mime',d.tipo_mime)
 from public.mf_documentos d where d.id=p_id and d.estado_archivo='disponible'
 and public.mf_caso_documentos_propio(d.caso_id) and
 (d.visible_cliente or (d.origen='cliente' and d.subido_por=auth.uid()));
$$;
create or replace function public.mf_descarga_documento_permitida(p_path text) returns boolean
language sql stable security definer set search_path='' as $$
 select public.es_admin() or exists(select 1 from public.mf_documentos d where d.archivo_path=p_path
 and public.mf_caso_documentos_propio(d.caso_id) and
 (d.estado_archivo='disponible' and (d.visible_cliente or (d.origen='cliente' and d.subido_por=auth.uid()))
 -- Permite comprobar un objeto de subida propia pendiente antes de reintentar.
 or d.estado_archivo in ('pendiente','eliminando') and d.origen='cliente' and d.subido_por=auth.uid()));
$$;
create function public.mf_operacion_archivo_cliente(p_path text,p_operacion text) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.mf_documentos d where d.archivo_path=p_path
 and d.origen='cliente' and d.subido_por=auth.uid() and public.mf_caso_admite_documentos(d.caso_id)
 and ((p_operacion='insertar' and d.estado_archivo='pendiente') or
 (p_operacion='borrar' and d.estado_archivo='eliminando')));
$$;
drop policy mf_docs_insertar on storage.objects;
drop policy mf_docs_insertar_limite on storage.objects;
create policy mf_docs_insertar on storage.objects for insert to authenticated with check(bucket_id='documentos-casos'
 and ((public.es_admin() and exists(select 1 from public.mf_documentos d where d.archivo_path=name and d.estado_archivo='pendiente'))
 or public.mf_operacion_archivo_cliente(name,'insertar')));
create policy mf_docs_insertar_limite on storage.objects as restrictive for insert to authenticated with check(bucket_id<>'documentos-casos'
 or ((public.es_admin() and exists(select 1 from public.mf_documentos d where d.archivo_path=name and d.estado_archivo='pendiente'))
 or public.mf_operacion_archivo_cliente(name,'insertar')));
drop policy mf_docs_borrar on storage.objects;
drop policy mf_docs_borrar_limite on storage.objects;
create policy mf_docs_borrar on storage.objects for delete to authenticated using(bucket_id='documentos-casos'
 and (public.es_admin() or public.mf_operacion_archivo_cliente(name,'borrar')));
create policy mf_docs_borrar_limite on storage.objects as restrictive for delete to authenticated using(bucket_id<>'documentos-casos'
 or public.es_admin() or public.mf_operacion_archivo_cliente(name,'borrar'));

-- Aviso sin destinatario elegido por el cliente. Lee solo el correo público de
-- contacto de la empresa; nunca correos personales de los usuarios admin.
create function public.mf_aviso_documento_cliente(p_id uuid,p_resultado text default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.mf_documentos; correo text;
begin
 select * into d from public.mf_documentos where id=p_id for update;
 if not found or not public.mf_documento_cliente_propio(p_id) or d.estado_archivo<>'disponible'
 then raise exception 'Documento no disponible' using errcode='42501'; end if;
 if p_resultado is null then
  if d.aviso_estado<>'no_solicitado' then return '{}'::jsonb; end if;
  select datos->>'correo_contacto' into correo from public.mf_configuracion where id='general';
  update public.mf_documentos set aviso_estado='reservado' where id=p_id;
  return jsonb_build_object('correo',coalesce(correo,''));
 end if;
 if p_resultado not in ('enviado','fallido','incierto') then raise exception 'Resultado no válido'; end if;
 update public.mf_documentos set aviso_estado=p_resultado where id=p_id and aviso_estado='reservado';
 return '{}'::jsonb;
end $$;

revoke all on function public.mf_documento_cliente_propio(uuid),public.mf_caso_admite_documentos(uuid),
 public.mf_preparar_documento_cliente(uuid,uuid,text,text,bigint,text,text),public.mf_eliminar_documento_cliente(uuid,boolean),
 public.mf_operacion_archivo_cliente(text,text),public.mf_aviso_documento_cliente(uuid,text) from public,anon;
grant execute on function public.mf_documento_cliente_propio(uuid),public.mf_caso_admite_documentos(uuid),
 public.mf_preparar_documento_cliente(uuid,uuid,text,text,bigint,text,text),public.mf_eliminar_documento_cliente(uuid,boolean),
 public.mf_operacion_archivo_cliente(text,text),public.mf_aviso_documento_cliente(uuid,text) to authenticated;
notify pgrst,'reload schema';
commit;
