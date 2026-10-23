"""Etiquetas compartidas: no cambia los valores existentes en PostgreSQL."""
ETIQUETAS = {
    "Solicitud": "Solicitud", "En revisión": "En revisión", "Cotizado": "Cotizada",
    "Vendido": "Aceptada", "En ejecución": "En seguimiento", "Finalizado": "Cerrada",
    "Cancelado": "Rechazada",
}


def etiqueta_estado(estado):
    return ETIQUETAS.get(estado, estado)


def estado_visual(estado):
    """La revisión es una subetapa heredada de Solicitud, sin cambiar su valor."""
    return "Solicitud" if estado == "En revisión" else etiqueta_estado(estado)


def etiqueta_opcion_estado(estado):
    return "Solicitud · en revisión" if estado == "En revisión" else etiqueta_estado(estado)
