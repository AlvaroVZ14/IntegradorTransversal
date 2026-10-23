"""Fixture compartido por pruebas y revisión de documentos; no son datos reales."""
from servicios.cotizacion_asistida import prellenar,configuracion,datos_emision
from mente_futuro.domain import today,quote_total


def ejemplo():
    caso=dict(id='10000000-0000-0000-0000-000000000001',numero=1,version=1,estado='Solicitud',
        cliente='Fundación Horizonte Norte',contacto='Daniela Soto',email='daniela@example.test',telefono='+56 9 1234 5678',
        servicio='Taller de trabajo en equipo',tematica='Trabajo en equipo',participantes=20,horas=4.0,
        modalidad='Presencial',lugar='Antofagasta',detalle='Fortalecer la colaboración y la comunicación entre los equipos de trabajo.')
    emisor=dict(razon_social='Consultora Horizonte SpA',rut='12.345.678-5',giro='Capacitación y consultoría',
        direccion='Calle Ficticia 123',comuna='Antofagasta',correo='consultora@example.test',telefono='+56 9 1234 5678',
        representante='Camila Rojas',cuenta_bancaria='Banco ficticio · Cuenta corriente 123456')
    config=configuracion(dict(emisor=emisor))
    tarifa=dict(id='tarifa-ficticia',nombre='Taller de colaboración',servicio=caso['servicio'],tematica=caso['tematica'],
        horas=4,participantes=20,monto_clp=1250000,tratamiento_iva='Exento',detalle='Taller presencial con actividades prácticas de colaboración.',activa=True)
    d=prellenar(caso,[tarifa],[],config)
    d['descuento_pct']=10.0;d['descuento_motivo']='Convenio institucional ficticio'
    d['textos'].update(descripcion='Experiencia de aprendizaje para fortalecer la colaboración del equipo.',
        metodologia='Actividades participativas, desafíos en grupos pequeños y reflexión guiada.',
        incluye='4 horas de facilitación, materiales de trabajo y una síntesis de los acuerdos del equipo.')
    q=dict(datos_emision(d),id='cotizacion-ficticia',caso_id=caso['id'],numero=1,version_cotizacion=1,
        snapshot=caso,created_at=today().isoformat(),fecha_emision=today().isoformat(),total_clp=quote_total(d['base_clp'],10,0))
    return caso,d,q


if __name__=='__main__':
    from pathlib import Path
    from servicios.documentos_cotizacion import generar_word,generar_pdf
    _,_,q=ejemplo()
    out=Path('output/cotizador');out.mkdir(parents=True,exist_ok=True)
    (out/'cotizacion-ficticia.docx').write_bytes(generar_word(q))
    (out/'cotizacion-ficticia.pdf').write_bytes(generar_pdf(q))
    print('Documentos ficticios generados para revisión.')
