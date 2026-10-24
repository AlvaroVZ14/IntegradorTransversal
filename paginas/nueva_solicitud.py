"""El servidor elige el modo por el perfil verificado; no se lee de la URL."""
from paginas.formulario import formulario
from servicios.formulario import modo_servidor


def request_page(repo):
    formulario(modo=modo_servidor(repo),repo=repo)


if __name__=='__main__':
    from utils.permisos import proteger_pagina
    request_page(proteger_pagina('Nueva solicitud'))
