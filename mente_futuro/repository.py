"""Acceso con JWT de cada usuario. Nunca se comparte un cliente entre sesiones."""
import base64
import json
import os

import streamlit as st
from supabase import create_client, ClientOptions


class ConfigurationError(Exception):
    pass


def public_client():
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
    return create_client(url, key, options=ClientOptions(auto_refresh_token=True, persist_session=False))


class Repository:
    def __init__(self, client, user, profile):
        self.client = client
        self.user = user
        self.profile = profile
        self.is_owner = profile.get("rol") == "duena"

    def owner_only(self):
        if not self.is_owner:
            raise PermissionError("Esta acción está disponible solo para la dueña.")

    def rows(self, table, order="created_at", **filters):
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
        filters = {} if self.is_owner else {"cliente_id": self.user.id}
        return self.rows("mf_casos", **filters)

    def tariffs(self):
        self.owner_only()
        return self.rows("mf_tarifas")

    def quotes(self, case_id):
        return self.rows("mf_cotizaciones", caso_id=case_id)

    def sales(self):
        self.owner_only()
        return self.rows("mf_ventas")

    def create_request(self, data, request_id):
        # UUID estable por formulario: un reintento no crea un segundo caso.
        existing = self.client.table("mf_casos").select("*").eq("id", request_id).execute().data
        if existing:
            return existing[0]
        payload = {**data, "id": request_id, "creado_por": self.user.id,
                   "cliente_id": data.get("cliente_id") if self.is_owner else self.user.id}
        result = self.client.table("mf_casos").insert(payload).execute().data
        if not result:
            raise RuntimeError("No se confirmó el guardado de la solicitud.")
        return result[0]

    def update_case(self, case, changes):
        self.owner_only()
        result = self.client.table("mf_casos").update(changes).eq("id", case["id"]).eq("version", case["version"]).execute().data
        if not result:
            raise ValueError("Este caso cambió en otra sesión. Actualiza la página antes de guardar.")

    def save_tariff(self, data, tariff=None):
        self.owner_only()
        if tariff:
            result = self.client.table("mf_tarifas").update(data).eq("id", tariff["id"]).eq("version", tariff["version"]).execute().data
        else:
            result = self.client.table("mf_tarifas").insert(data).execute().data
        if not result:
            raise ValueError("La tarifa cambió en otra sesión. Actualiza antes de guardar.")

    def issue_quote(self, case, data, operation_id):
        self.owner_only()
        return self.client.rpc("mf_emitir_cotizacion", {
            "p_caso_id": case["id"], "p_version": case["version"],
            "p_operacion_id": operation_id, "p_datos": data,
        }).execute().data

    def record_sale(self, case, quote, sale_date, payment):
        self.owner_only()
        return self.client.rpc("mf_registrar_venta", {
            "p_caso_id": case["id"], "p_cotizacion_id": quote["id"],
            "p_fecha": sale_date.isoformat(), "p_estado_pago": payment,
        }).execute().data

    def update_sale(self, sale, payment, annulled):
        self.owner_only()
        result = self.client.table("mf_ventas").update({"estado_pago": payment, "anulada": annulled}).eq("id", sale["id"]).eq("version", sale["version"]).execute().data
        if not result:
            raise ValueError("La venta cambió en otra sesión. Actualiza antes de guardar.")

    def profiles(self):
        self.owner_only()
        return self.rows("mf_perfiles")
