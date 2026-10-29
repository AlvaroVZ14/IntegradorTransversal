"""Compatibilidad para importaciones anteriores; la app usa navegacion_portal.

Mantener este archivo evita romper integraciones y pruebas históricas. No
contiene una segunda implementación de navegación ni decide permisos.
"""
from utils.navegacion_portal import (
    PAGINAS,inicio,crear_paginas,registrar_navegacion,barra_publica,barra_cuenta,
    ajustar_menu_superior,rutas_para_perfil,resolver_ruta_desconocida,
    menu_lateral,cerrar_menu_movil_al_navegar,
)
