"""El rol siempre procede de mf_perfiles, nunca de la URL o user_metadata."""
ADMIN_PAGES = ("Hoy", "Nueva solicitud", "Casos y cotizaciones", "Dashboard")
CLIENT_PAGE = "Nueva solicitud"


def es_admin(profile):
    return profile.get("rol") == "admin"


def require_admin(repo):
    if not es_admin(repo.profile):
        raise PermissionError("Esta sección está disponible solo para Administración.")


def allowed_pages(profile):
    return list(ADMIN_PAGES) if es_admin(profile) else [CLIENT_PAGE]


def guard_route(profile, route):
    pages = allowed_pages(profile)
    if es_admin(profile) and route == 'Estado':
        return route
    return route if route in pages else CLIENT_PAGE
