// Solo para PostgreSQL efímero: tablas mínimas del servicio Storage de Supabase.
export async function prepararStorage(db) {
 await db.exec(`create schema storage;
 create table storage.buckets(id text primary key,name text,public boolean default false,file_size_limit bigint,allowed_mime_types text[]);
 create table storage.objects(id uuid default gen_random_uuid(),bucket_id text references storage.buckets(id),name text,metadata jsonb,unique(bucket_id,name));
 alter table storage.objects enable row level security;
 grant usage on schema storage to authenticated,anon,service_role;
 grant select,insert,update,delete on storage.objects to authenticated,anon,service_role;
 grant select on storage.buckets to authenticated,anon,service_role;`);
}
