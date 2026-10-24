"""Acceso con JWT de cada usuario. Nunca se comparte un cliente entre sesiones."""
import base64
import json
import os

import streamlit as st
from supabase import create_client, ClientOptions
from utils.permisos import es_admin


class ConfigurationError(Exception):
    pass


def fila_rpc(resultado):
    """PostgREST puede representar un retorno compuesto como una fila en lista."""
    if isinstance(resultado,list):
        if len(resultado)!=1:raise RuntimeError('No se confirmó una única fila de respuesta.')
        resultado=resultado[0]
    if not isinstance(resultado,dict) or not resultado:
        raise RuntimeError('No se confirmó el resultado de la operación.')
    return resultado


def escritura_confirmada(resultado):
    if not resultado:
        raise RuntimeError("No se confirmó el guardado. Conservamos el borrador para reintentar.")
    resultado=fila_rpc(resultado)
    from servicios.dashboard_cache import invalidar_dashboard
    invalidar_dashboard()
    return resultado


def public_client(timeout=8):
    def setting(name):
        value = os.environ.get(name)
        if value:
            return value
        try:
            return st.secrets.get(name, "")
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            return ""

    url, key = setting("SUPABASE_URL"), setting("SUPABASE_KEY")
    if not url or not key or "TU-" in url or "TU-" in key:
        raise ConfigurationError("Falta configurar la conexión con Supabase.")
    if key.startswith("sb_secret_"):
        raise ConfigurationError("Utiliza una clave publicable de Supabase para respetar los permisos de cada usuario.")
    if key.count(".") == 2:
        try:
            payload = json.loads(base64.urlsafe_b64decode(key.split(".")[1] + "==="))
        except (ValueError, UnicodeError):
            raise ConfigurationError("La clave de Supabase no tiene un formato válido.") from None
        if payload.get("role") != "anon":
            raise ConfigurationError("Utiliza la clave anon o publicable, nunca service_role.")
    # La rotación se realiza al consultar get_session en el marco de la app,
    # para actualizar también la cookie y no dejar un refresh token antiguo.
    return create_client(url, key, options=ClientOptions(auto_refresh_token=False, persist_session=False,postgrest_client_timeout=timeout))


class Repository:
    def __init__(self, client, user, profile):
        self.client = client
        self.user = user
        self.profile = profile
        self.is_owner = es_admin(profile)

    def owner_only(self):
        if not self.is_owner:
            raise PermissionError("Esta acción está disponible solo para la dueña.")

    def rows(self, table, order="created_at", **filters):
        self.owner_only()
        # Paginación: Supabase limita por defecto las respuestas a 1.000 registros.
        data, offset, size = [], 0, 500
        while True:
            query = self.client.table(table).select("*")
            for key, value in filters.items():
                query = query.eq(key, value)
            page = query.order(order, desc=True).order("id").range(offset, offset + size - 1).execute().data
            data.extend(page)
            if len(page) < size:
                return data
            offset += size

    def cases(self):
        return self.rows("mf_casos")

    def request_notifications(self):
        return self.rows('mf_avisos_solicitud')

    def live_snapshot(self, vista):
        self.owner_only()
        return fila_rpc(self.client.rpc('mf_lectura_en_vivo', {'p_vista': vista}).execute().data)

    def tariffs(self):
        self.owner_only()
        return self.rows("mf_tarifas")

    def quotes(self, case_id):
        return self.rows("mf_cotizaciones", caso_id=case_id)

    def sales(self):
        self.owner_only()
        return self.rows("mf_ventas")

    def create_request(self, data, request_id):
        response=fila_rpc(self.client.rpc('registrar_solicitud',{
            'p_solicitud_id':request_id,'p_datos':data}).execute().data)
        if not response.get('codigo'):raise RuntimeError('No se confirmó el guardado de la solicitud.')
        return escritura_confirmada(response['caso'] if self.is_owner else response)

    def create_request_legacy(self,data,request_id):
        """Compatibilidad con el esquema anterior, solo para administración."""
        self.owner_only()
        # UUID estable por formulario: un reintento no crea un segundo caso.
        existing = self.client.table("mf_casos").select("*").eq("id", request_id).execute().data
        if existing:
            return escritura_confirmada(existing[0])
        payload = {**data, "id": request_id, "creado_por": self.user.id,
                   "cliente_id": data.get("cliente_id"), "registrado_por": "Administración"}
        result = self.client.table("mf_casos").insert(payload).execute().data
        if not result:
            raise RuntimeError("No se confirmó el guardado de la solicitud.")
        return escritura_confirmada(result[0])

    def get_case(self, case_id):
        self.owner_only()
        rows=self.client.table("mf_casos").select("*").eq("id",case_id).limit(1).execute().data
        if not rows:
            raise ValueError("Este caso ya no está disponible para tu cuenta.")
        return rows[0]

    def update_case(self, case, changes):
        self.owner_only()
        result = self.client.table("mf_casos").update(changes).eq("id", case["id"]).eq("version", case["version"]).execute().data
        if not result:
            raise ValueError("Este caso cambió en otra sesión. Actualiza la página antes de guardar.")
        return escritura_confirmada(result[0])

    def save_tariff(self, data, tariff=None):
        self.owner_only()
        if tariff:
            result = self.client.table("mf_tarifas").update(data).eq("id", tariff["id"]).eq("version", tariff["version"]).execute().data
        else:
            result = self.client.table("mf_tarifas").insert(data).execute().data
        if not result:
            raise ValueError("La tarifa cambió en otra sesión. Actualiza antes de guardar.")
        return escritura_confirmada(result[0])

    def issue_quote(self, case, data, operation_id):
        self.owner_only()
        return escritura_confirmada(self.client.rpc("mf_emitir_cotizacion", {
            "p_caso_id": case["id"], "p_version": case["version"],
            "p_operacion_id": operation_id, "p_datos": data,
        }).execute().data)

    def record_sale(self, case, quote, sale_date, payment):
        self.owner_only()
        return escritura_confirmada(self.client.rpc("mf_registrar_venta", {
            "p_caso_id": case["id"], "p_cotizacion_id": quote["id"],
            "p_fecha": sale_date.isoformat(), "p_estado_pago": payment,
        }).execute().data)

    def update_sale(self, sale, payment, annulled):
        self.owner_only()
        result = self.client.table("mf_ventas").update({"estado_pago": payment, "anulada": annulled}).eq("id", sale["id"]).eq("version", sale["version"]).execute().data
        if not result:
            raise ValueError("La venta cambió en otra sesión. Actualiza antes de guardar.")
        return escritura_confirmada(result[0])

    def undo_acceptance(self,sale_id,version):
        self.owner_only()
        return escritura_confirmada(self.client.rpc("mf_deshacer_aceptacion",{
            "p_venta_id":sale_id,"p_version":version}).execute().data)

    def profiles(self):
        self.owner_only()
        return self.rows("mf_perfiles")

    def quote_settings(self):
        self.owner_only()
        rows=self.client.table('mf_configuracion').select('*').eq('id','general').execute().data
        return rows[0] if rows else {'datos':{},'version':0}

    def sharing_settings(self):
        self.owner_only()
        return fila_rpc(self.client.rpc('mf_configuracion_compartir',{}).execute().data)

    def save_quote_settings(self,data,version):
        self.owner_only()
        result=self.client.table('mf_configuracion').update({'datos':data}).eq('id','general').eq('version',version).execute().data
        return escritura_confirmada(result[0] if result else None)

    def program_templates(self):
        return self.rows('mf_plantillas_programa')

    def save_program_template(self,data):
        self.owner_only()
        rows=self.client.table('mf_plantillas_programa').insert(data).execute().data
        return escritura_confirmada(rows[0] if rows else None)

    def quote_draft(self,case_id):
        self.owner_only()
        rows=self.client.table('mf_borradores_cotizacion').select('*').eq('id',case_id).execute().data
        return rows[0] if rows else None

    def save_quote_draft(self,case_id,data,version):
        self.owner_only()
        # Un borrador no altera casos ni invalida ventas/dashboard.
        return fila_rpc(self.client.rpc('mf_guardar_borrador',{'p_caso_id':case_id,'p_version':version,'p_datos':data}).execute().data)

    def quote_events(self,case_id):
        return self.rows('mf_eventos_caso',caso_id=case_id)

    def decide_quote(self,case,quote,data,operation_id):
        self.owner_only()
        return escritura_confirmada(self.client.rpc('mf_decidir_cotizacion',{'p_caso_id':case['id'],
            'p_cotizacion_id':quote['id'],'p_version':case['version'],'p_operacion_id':operation_id,'p_datos':data}).execute().data)

    def undo_quote_decision(self,event_id):
        self.owner_only()
        return escritura_confirmada(self.client.rpc('mf_deshacer_decision',{'p_evento_id':event_id}).execute().data)

    def prepare_quote_send(self,quote_id,operation_id,channel,recipient):
        self.owner_only()
        return fila_rpc(self.client.rpc('mf_preparar_envio',{'p_id':operation_id,'p_cotizacion_id':quote_id,
            'p_canal':channel,'p_destinatario':recipient}).execute().data)

    def confirm_quote_send(self,operation_id,status):
        self.owner_only()
        return escritura_confirmada(self.client.rpc('mf_confirmar_envio',{'p_id':operation_id,'p_estado':status}).execute().data)

    def all_quotes(self):
        return self.rows('mf_cotizaciones')

    def today_ready(self):
        self.owner_only()
        self.client.table('mf_casos').select('id,fecha_realizacion').limit(1).execute()
        return True

    def today_events(self):
        return self.rows('mf_eventos_caso')

    def email_attempts(self):
        return self.rows('mf_envios_cotizacion')

    def record_today_contact(self,case_id,quote_id,kind,operation_id,data=None):
        self.owner_only()
        return escritura_confirmada(self.client.rpc('mf_registrar_contacto_hoy',{
            'p_caso_id':case_id,'p_cotizacion_id':quote_id,'p_operacion_id':operation_id,'p_tipo':kind,'p_datos':data or {}}).execute().data)

    def close_case_today(self,case,sale,operation_id):
        self.owner_only()
        return escritura_confirmada(self.client.rpc('mf_cerrar_caso_hoy',{'p_caso_id':case['id'],
            'p_version':case['version'],'p_venta_version':sale['version'],'p_operacion_id':operation_id}).execute().data)

    def undo_close_today(self,event_id):
        self.owner_only()
        return escritura_confirmada(self.client.rpc('mf_deshacer_cierre_hoy',{'p_evento_id':event_id}).execute().data)

    def backup_snapshot(self):
        self.owner_only()
        return fila_rpc(self.client.rpc('mf_exportar_respaldo',{}).execute().data)

    def maintenance_latest(self,tipo,solo_ok=False):
        self.owner_only()
        q=self.client.table('mf_mantenimiento').select('*').eq('tipo',tipo)
        if solo_ok:q=q.eq('estado','ok')
        rows=q.order('created_at',desc=True).limit(1).execute().data
        return rows[0] if rows else None

    def latest_case(self):
        self.owner_only()
        rows=self.client.table('mf_casos').select('numero,created_at').order('created_at',desc=True).order('id').limit(1).execute().data
        return rows[0] if rows else None

    def connection_check(self):
        self.owner_only()
        self.client.table('mf_perfiles').select('id').eq('id',self.user.id).limit(1).execute()
        return True
