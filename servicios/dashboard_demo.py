"""Demostración ficticia en memoria. Nunca escribe ni modifica un repositorio."""
from datetime import timedelta
from servicios.periodos import periodo_anterior, validar_rango


def datos_demo(desde, hasta):
    desde, hasta = validar_rango(desde, hasta)
    casos, ventas = [], []
    estados = ('Solicitud', 'Cotizado', 'Vendido', 'En ejecución', 'Finalizado', 'Cancelado')
    for bloque, (inicio, fin), cantidad in (
            ('actual', (desde, hasta), 12), ('anterior', periodo_anterior(desde, hasta), 6)):
        for i in range(cantidad):
            dia = inicio + timedelta(days=(fin-inicio).days*i//(cantidad-1))
            identificador = f'demo-{bloque}-{i}'
            casos.append(dict(id=identificador, numero=i+1, cliente=f'Empresa ficticia {i+1}',
                created_at=f'{dia}T15:00:00Z', servicio=('Taller', 'Charla', 'Coaching individual')[i%3],
                tematica=('Liderazgo', 'Trabajo en equipo', 'Comunicación efectiva', 'Gestión emocional')[i%4],
                estado=estados[i%6], origen=('Formulario web', 'Referido por colega', 'Correo', 'Llamada')[i%4],
                modalidad='Online'))
            if i % 3 != 2:
                monto = (i+1)*85000 if bloque == 'actual' else (i+1)*60000
                ventas.append(dict(caso_id=identificador, fecha_venta=str(dia), monto_clp=monto,
                    anulada=False, estado_pago='Pendiente' if i%2 else 'Pagado',
                    reserva_clp=monto//2, remuneracion_clp=monto-monto//2))
    return casos, ventas
