"""La cuenta de cliente utiliza el mismo formulario y sus mismas validaciones."""
from paginas.nueva_solicitud import request_page
from utils.permisos import proteger_pagina

if __name__ == '__main__':
    request_page(proteger_pagina('Solicitar servicio'))
