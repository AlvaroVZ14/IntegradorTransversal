-- Solo en SQL Editor con una cuenta FICTICIA de prueba ya creada/confirmada.
-- Sustituir UUID-CLIENTE-FICTICIO. No probar como postgres: postgres omite RLS.
begin;
set local role authenticated;
select set_config('request.jwt.claim.sub','UUID-CLIENTE-FICTICIO',true);
select set_config('request.jwt.claims','{"sub":"UUID-CLIENTE-FICTICIO","role":"authenticated"}',true);
select id,nombre,email,rol from public.mf_perfiles; -- Solo el propio perfil, rol cliente.
select public.es_admin(); -- false.
do $$ declare t record; filas bigint; begin
  if public.es_admin() or not exists(select 1 from public.mf_perfiles where id=auth.uid() and rol='cliente') then
    raise exception 'La cuenta de prueba debe ser un cliente existente';
  end if;
  for t in select tablename from pg_tables where schemaname='public' and tablename<>'mf_perfiles'
    and (left(tablename,3)='mf_' or tablename in ('casos','cotizaciones','tarifas','programas','ventas','historial','configuracion')) loop
    begin
      execute format('select count(*) from public.%I',t.tablename) into filas;
      if filas<>0 then raise exception 'FALLO: cliente puede leer % filas de %',filas,t.tablename; end if;
      raise notice 'OK: % devuelve 0 filas',t.tablename;
    exception when insufficient_privilege then raise notice 'OK: % deniega permiso',t.tablename;
    end;
  end loop;
  begin
    update public.mf_perfiles set rol='admin' where id=auth.uid();
    raise exception 'FALLO: el cliente pudo ejecutar un cambio de rol';
  exception when insufficient_privilege then raise notice 'OK: cambio de rol denegado';
  end;
end $$;
rollback;
