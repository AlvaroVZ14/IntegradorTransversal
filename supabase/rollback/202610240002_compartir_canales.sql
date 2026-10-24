-- Volver primero al código anterior y ejecutar completo.
-- Conserva canales, configuración, casos y textos guardados. No borra datos.
begin;
do $$declare f record;begin
 for f in select definicion from mf_seguridad.compartir_respaldo loop execute f.definicion;end loop;
end $$;
drop function public.mf_configuracion_compartir();
drop function mf_seguridad.normalizar_canal(text);
notify pgrst,'reload schema';
commit;
