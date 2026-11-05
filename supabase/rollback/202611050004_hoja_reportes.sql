-- Detener la integración sin borrar datos comerciales ni la cola pendiente.
-- Antes: desactivar HOJA_SYNC_ENABLED en GitHub y activada=false en Streamlit.
begin;
drop trigger if exists mf_hoja_casos on public.mf_casos;
drop trigger if exists mf_hoja_cotizaciones on public.mf_cotizaciones;
drop trigger if exists mf_hoja_ventas on public.mf_ventas;
drop trigger if exists mf_hoja_eventos on public.mf_eventos_caso;
alter role mfy_hoja nologin;
revoke execute on all functions in schema reportes from mfy_hoja;
revoke select on all tables in schema reportes from mfy_hoja;
revoke execute on function public.mf_estado_hoja() from authenticated;
-- reportes permanece privado para conservar registros y facilitar diagnóstico.
notify pgrst,'reload schema';
commit;
