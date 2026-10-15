-- Ejecutar una vez en SQL Editor de Supabase con el rol postgres.
-- Tablas nuevas con prefijo mf_: no borra ni modifica la tabla casos del prototipo.
begin;

create table public.mf_perfiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null default '' check (length(nombre) <= 160),
  email text not null default '',
  rol text not null default 'cliente' check (rol in ('cliente','duena')),
  created_at timestamptz not null default now()
);

create function public.mf_es_duena() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists(select 1 from public.mf_perfiles where id = (select auth.uid()) and rol = 'duena');
$$;
revoke all on function public.mf_es_duena() from public, anon;
grant execute on function public.mf_es_duena() to authenticated;

create function public.mf_nuevo_usuario() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  -- El rol nunca se toma de user_metadata: el registro siempre crea un cliente.
  insert into public.mf_perfiles(id,nombre,email)
  values(new.id,left(coalesce(new.raw_user_meta_data->>'nombre',''),160),coalesce(new.email,''));
  return new;
end;
$$;
revoke all on function public.mf_nuevo_usuario() from public, anon, authenticated;
create trigger mf_al_crear_usuario after insert on auth.users
for each row execute function public.mf_nuevo_usuario();
insert into public.mf_perfiles(id,nombre,email)
select id,left(coalesce(raw_user_meta_data->>'nombre',''),160),coalesce(email,'') from auth.users
on conflict(id) do nothing;

create table public.mf_tarifas (
  id uuid primary key default gen_random_uuid(),
  nombre text not null check (length(trim(nombre)) between 2 and 180),
  servicio text not null,
  monto_clp bigint not null check (monto_clp >= 0 and monto_clp <= 100000000000),
  participantes integer not null check (participantes between 1 and 10000),
  horas numeric(8,2) not null check (horas between 0.5 and 1000),
  tratamiento_iva text not null default 'Por confirmar' check (tratamiento_iva in ('Por confirmar','Exento','IVA 19%')),
  detalle text not null default '' check (length(detalle) <= 5000),
  fuente text not null default '' check (length(fuente) <= 500),
  activa boolean not null default true,
  version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.mf_casos (
  id uuid primary key default gen_random_uuid(),
  numero bigint generated always as identity unique,
  creado_por uuid not null default auth.uid() references auth.users(id),
  cliente_id uuid references auth.users(id),
  cliente text not null check (length(trim(cliente)) between 2 and 180),
  contacto text not null check (length(trim(contacto)) between 2 and 160),
  email text not null check (length(email) <= 254 and email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'),
  telefono text not null default '' check (length(telefono) <= 40),
  servicio text not null check (servicio in ('Coaching individual','Coaching dúo','Taller de trabajo en equipo','Charla de liderazgo','Otro servicio')),
  tematica text not null check (tematica in ('Liderazgo','Trabajo en equipo','Comunicación efectiva','Desarrollo personal','Gestión emocional','Otro')),
  participantes integer not null check (participantes between 1 and 10000),
  horas numeric(8,2) not null check (horas between 0.5 and 1000),
  modalidad text not null check (modalidad in ('Presencial','Online','Por definir')),
  lugar text not null default '' check (length(lugar) <= 250),
  fecha_preferida date,
  detalle text not null default '' check (length(detalle) <= 5000),
  estado text not null default 'Solicitud' check (estado in ('Solicitud','En revisión','Cotizado','Vendido','En ejecución','Finalizado','Cancelado')),
  version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index mf_casos_cliente_idx on public.mf_casos(cliente_id);
create index mf_casos_fecha_idx on public.mf_casos(created_at);

create table public.mf_cotizaciones (
  id uuid primary key default gen_random_uuid(),
  numero bigint generated always as identity unique,
  operacion_id uuid not null unique,
  caso_id uuid not null references public.mf_casos(id),
  tarifa_id uuid references public.mf_tarifas(id),
  base_clp bigint not null check (base_clp >= 0 and base_clp <= 100000000000),
  descuento_pct numeric(5,2) not null default 0 check (descuento_pct between 0 and 100),
  iva_pct integer not null check (iva_pct in (0,19)),
  total_clp bigint generated always as (round(base_clp::numeric * (1 - descuento_pct/100) * (1 + iva_pct::numeric/100))) stored,
  detalle text not null check (length(trim(detalle)) between 2 and 5000),
  condiciones text not null default '' check (length(condiciones) <= 5000),
  fecha_emision date not null default (now() at time zone 'America/Santiago')::date,
  valida_hasta date not null check (valida_hasta >= fecha_emision),
  snapshot jsonb not null,
  creado_por uuid not null default auth.uid() references auth.users(id),
  created_at timestamptz not null default now(),
  unique (id,caso_id)
);
create index mf_cotizaciones_caso_idx on public.mf_cotizaciones(caso_id);

create table public.mf_ventas (
  id uuid primary key default gen_random_uuid(),
  caso_id uuid not null unique references public.mf_casos(id),
  cotizacion_id uuid not null,
  monto_clp bigint not null check (monto_clp >= 0),
  fecha_venta date not null,
  estado_pago text not null default 'Pendiente' check (estado_pago in ('Pendiente','Abono recibido','Pagado')),
  anulada boolean not null default false,
  creado_por uuid not null default auth.uid() references auth.users(id),
  version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key(cotizacion_id,caso_id) references public.mf_cotizaciones(id,caso_id)
);
create index mf_ventas_fecha_idx on public.mf_ventas(fecha_venta);

create function public.mf_actualizar_version() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.version := old.version + 1;
  new.updated_at := now();
  return new;
end;
$$;
revoke all on function public.mf_actualizar_version() from public, anon, authenticated;
create trigger mf_version_caso before update on public.mf_casos for each row execute function public.mf_actualizar_version();
create trigger mf_version_tarifa before update on public.mf_tarifas for each row execute function public.mf_actualizar_version();
create trigger mf_version_venta before update on public.mf_ventas for each row execute function public.mf_actualizar_version();

alter table public.mf_perfiles enable row level security;
alter table public.mf_casos enable row level security;
alter table public.mf_tarifas enable row level security;
alter table public.mf_cotizaciones enable row level security;
alter table public.mf_ventas enable row level security;
revoke all on public.mf_perfiles,public.mf_casos,public.mf_tarifas,public.mf_cotizaciones,public.mf_ventas from anon,authenticated;
grant select on public.mf_perfiles to authenticated;
-- Sin INSERT/UPDATE de perfiles: nadie puede elevar su rol desde la aplicación.
grant select on public.mf_casos to authenticated;
grant insert(id,creado_por,cliente_id,cliente,contacto,email,telefono,servicio,tematica,participantes,horas,modalidad,lugar,fecha_preferida,detalle) on public.mf_casos to authenticated;
grant update(cliente_id,cliente,contacto,email,telefono,servicio,tematica,participantes,horas,modalidad,lugar,fecha_preferida,detalle,estado) on public.mf_casos to authenticated;
grant select,insert on public.mf_tarifas to authenticated;
grant update(nombre,servicio,monto_clp,participantes,horas,tratamiento_iva,detalle,fuente,activa) on public.mf_tarifas to authenticated;
grant select on public.mf_cotizaciones,public.mf_ventas to authenticated;
grant update(estado_pago,anulada) on public.mf_ventas to authenticated;
grant usage on sequence public.mf_casos_numero_seq to authenticated;

create policy mf_perfil_lectura on public.mf_perfiles for select to authenticated
using(id=(select auth.uid()) or (select public.mf_es_duena()));
create policy mf_caso_lectura on public.mf_casos for select to authenticated
using(cliente_id=(select auth.uid()) or (select public.mf_es_duena()));
create policy mf_caso_alta on public.mf_casos for insert to authenticated
with check (
  creado_por=(select auth.uid()) and estado='Solicitud' and version=1
  and ((select public.mf_es_duena()) or cliente_id=(select auth.uid()))
);
create policy mf_caso_edicion on public.mf_casos for update to authenticated
using((select public.mf_es_duena())) with check((select public.mf_es_duena()));
create policy mf_tarifa_lectura on public.mf_tarifas for select to authenticated using((select public.mf_es_duena()));
create policy mf_tarifa_alta on public.mf_tarifas for insert to authenticated with check((select public.mf_es_duena()));
create policy mf_tarifa_edicion on public.mf_tarifas for update to authenticated using((select public.mf_es_duena())) with check((select public.mf_es_duena()));
create policy mf_cotizacion_lectura on public.mf_cotizaciones for select to authenticated
using((select public.mf_es_duena()) or exists(select 1 from public.mf_casos c where c.id=caso_id and c.cliente_id=(select auth.uid())));
create policy mf_venta_lectura on public.mf_ventas for select to authenticated using((select public.mf_es_duena()));
create policy mf_venta_edicion on public.mf_ventas for update to authenticated using((select public.mf_es_duena())) with check((select public.mf_es_duena()));

-- Emisión atómica, con copia inmutable de los datos y reintento idempotente.
create function public.mf_emitir_cotizacion(p_caso_id uuid,p_version integer,p_operacion_id uuid,p_datos jsonb)
returns public.mf_cotizaciones language plpgsql security definer set search_path = '' as $$
declare c public.mf_casos; q public.mf_cotizaciones;
begin
  if not coalesce(public.mf_es_duena(),false) then raise exception 'Acceso denegado' using errcode='42501'; end if;
  select * into c from public.mf_casos where id=p_caso_id for update;
  if not found then raise exception 'Caso no encontrado'; end if;
  select * into q from public.mf_cotizaciones where operacion_id=p_operacion_id;
  if found then
    if q.caso_id <> p_caso_id then raise exception 'Operación no válida'; end if;
    return q;
  end if;
  if c.version <> p_version then raise exception 'El caso cambió. Actualiza antes de emitir.'; end if;
  if c.estado in ('Vendido','En ejecución','Finalizado','Cancelado') or exists(select 1 from public.mf_ventas where caso_id=c.id) then
    raise exception 'No se puede cotizar un caso cerrado o con venta registrada.';
  end if;
  insert into public.mf_cotizaciones(operacion_id,caso_id,tarifa_id,base_clp,descuento_pct,iva_pct,detalle,condiciones,valida_hasta,snapshot,creado_por)
  values(p_operacion_id,c.id,nullif(p_datos->>'tarifa_id','')::uuid,(p_datos->>'base_clp')::bigint,
    (p_datos->>'descuento_pct')::numeric,(p_datos->>'iva_pct')::integer,
    p_datos->>'detalle',coalesce(p_datos->>'condiciones',''),(p_datos->>'valida_hasta')::date,
    jsonb_build_object('cliente',c.cliente,'contacto',c.contacto,'email',c.email,'telefono',c.telefono,
      'servicio',c.servicio,'tematica',c.tematica,'participantes',c.participantes,'horas',c.horas,
      'modalidad',c.modalidad,'lugar',c.lugar,'fecha_preferida',c.fecha_preferida,'caso_numero',c.numero),auth.uid())
  returning * into q;
  update public.mf_casos set estado='Cotizado' where id=c.id;
  return q;
end;
$$;

create function public.mf_registrar_venta(p_caso_id uuid,p_cotizacion_id uuid,p_fecha date,p_estado_pago text)
returns public.mf_ventas language plpgsql security definer set search_path = '' as $$
declare c public.mf_casos; q public.mf_cotizaciones; v public.mf_ventas;
begin
  if not coalesce(public.mf_es_duena(),false) then raise exception 'Acceso denegado' using errcode='42501'; end if;
  select * into c from public.mf_casos where id=p_caso_id for update;
  if not found then raise exception 'Caso no encontrado'; end if;
  select * into q from public.mf_cotizaciones where id=p_cotizacion_id and caso_id=p_caso_id;
  if not found then raise exception 'La cotización no corresponde a este caso'; end if;
  select * into v from public.mf_ventas where caso_id=p_caso_id;
  if found then
    if v.cotizacion_id=p_cotizacion_id and v.fecha_venta=p_fecha and v.estado_pago=p_estado_pago and not v.anulada then return v; end if;
    raise exception 'Este caso ya tiene una venta registrada';
  end if;
  if c.estado in ('Cancelado','Finalizado') then raise exception 'El caso está cerrado'; end if;
  if p_fecha > (now() at time zone 'America/Santiago')::date or p_fecha < q.fecha_emision or p_fecha > q.valida_hasta then
    raise exception 'La fecha de venta debe estar dentro de la vigencia de la cotización y no ser futura';
  end if;
  insert into public.mf_ventas(caso_id,cotizacion_id,monto_clp,fecha_venta,estado_pago,creado_por)
  values(p_caso_id,p_cotizacion_id,q.total_clp,p_fecha,p_estado_pago,auth.uid()) returning * into v;
  update public.mf_casos set estado='Vendido' where id=p_caso_id;
  return v;
end;
$$;
revoke all on function public.mf_emitir_cotizacion(uuid,integer,uuid,jsonb) from public,anon;
revoke all on function public.mf_registrar_venta(uuid,uuid,date,text) from public,anon;
grant execute on function public.mf_emitir_cotizacion(uuid,integer,uuid,jsonb) to authenticated;
grant execute on function public.mf_registrar_venta(uuid,uuid,date,text) to authenticated;

-- Referencias históricas de los documentos entregados. Sin descuentos automáticos.
insert into public.mf_tarifas(nombre,servicio,monto_clp,participantes,horas,tratamiento_iva,detalle,fuente) values
('Individual · 4 sesiones','Coaching individual',420000,1,4,'Por confirmar','4 sesiones de 60 minutos. Reunión diagnóstica, cuadernillo e informe final.','Propuesta coaching individual + Promo Duo, página 4'),
('Individual · 6 sesiones','Coaching individual',580000,1,6,'Por confirmar','6 sesiones de 60 minutos. Reunión diagnóstica, cuadernillo e informe final.','Propuesta coaching individual + Promo Duo, página 4'),
('Individual · 8 sesiones','Coaching individual',740000,1,8,'Por confirmar','8 sesiones de 60 minutos. Reunión diagnóstica, cuadernillo e informe final.','Propuesta coaching individual + Promo Duo, página 4'),
('Dúo separado · 4 sesiones por persona','Coaching dúo',714000,2,8,'Por confirmar','Total por 2 personas. 4 sesiones individuales de 60 minutos para cada persona; 8 horas de atención en total. Incluye diagnóstico, cuadernillos e informe.','Propuesta coaching individual + Promo Duo, página 5'),
('Dúo separado · 6 sesiones por persona','Coaching dúo',986000,2,12,'Por confirmar','Total por 2 personas. 6 sesiones individuales de 60 minutos para cada persona; 12 horas de atención en total. Incluye diagnóstico, cuadernillos e informe.','Propuesta coaching individual + Promo Duo, página 5'),
('Dúo separado · 8 sesiones por persona','Coaching dúo',1258000,2,16,'Por confirmar','Total por 2 personas. 8 sesiones individuales de 60 minutos para cada persona; 16 horas de atención en total. Incluye diagnóstico, cuadernillos e informe.','Propuesta coaching individual + Promo Duo, página 5'),
('Dúo conjunto · 4 sesiones','Coaching dúo',546000,2,4,'Por confirmar','Total por 2 personas. 4 sesiones conjuntas de 60 minutos. Incluye diagnóstico, cuadernillos e informe.','Propuesta coaching individual + Promo Duo, página 5'),
('Dúo conjunto · 6 sesiones','Coaching dúo',754000,2,6,'Por confirmar','Total por 2 personas. 6 sesiones conjuntas de 60 minutos. Incluye diagnóstico, cuadernillos e informe.','Propuesta coaching individual + Promo Duo, página 5'),
('Dúo conjunto · 8 sesiones','Coaching dúo',962000,2,8,'Por confirmar','Total por 2 personas. 8 sesiones conjuntas de 60 minutos. Incluye diagnóstico, cuadernillos e informe.','Propuesta coaching individual + Promo Duo, página 5'),
('Team building · Escape room · 8 horas','Taller de trabajo en equipo',4580000,56,8,'Exento','Referencia para 56 participantes y 2 jornadas de 4 horas. Incluye diagnóstico, materiales, diplomas y reunión de cierre. Descuento histórico de aniversario de 15% NO aplicado.','Cotización Tectramin, 18 de agosto de 2026'),
('Charla motivacional de liderazgo · 60 minutos','Charla de liderazgo',2650000,300,1,'Exento','Referencia para hasta 300 personas, presencial. Incluye adaptación, coordinación, material digital, materiales para dinámica y traslados. Descuento histórico de 15% NO aplicado.','Cotización Mente y Futuro, 25 de agosto de 2026');

commit;
