-- Revertir primero el código de la app. No elimina datos ni modifica RLS.
begin;
drop function if exists public.mf_lectura_en_vivo(text);
notify pgrst,'reload schema';
commit;
