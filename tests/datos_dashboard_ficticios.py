"""Muestra independiente de las cuentas reales; no se sube a Supabase."""
from mente_futuro.domain import STATES


def datos_ficticios():
    nombres = ["Fundación Horizonte Norte", "Cooperativa Semilla Azul", "Colegio Valle del Sol",
        "Centro Comunitario Los Aromos", "Servicios Viento Sur", "Agrupación Nueva Ruta",
        "Academia Brisa del Mar", "Corporación Puente Andino", "Biblioteca Las Acacias",
        "Consultora Sendero Claro", "Talleres Raíces del Norte", "Red Vecinal Los Cerezos"]
    casos=[]
    for i in range(12):
        mes=5+i//2
        casos.append(dict(id=f"ficticio-{i}",numero=i+1,cliente=nombres[i],
            created_at=f"2026-{mes:02d}-05T15:00:00Z",servicio=["Coaching individual","Charla de liderazgo"][i%2],
            tematica=["Liderazgo","Trabajo en equipo","Comunicación efectiva","Desarrollo personal","Gestión emocional","Otro"][i%6],
            estado=STATES[i%len(STATES)],origen=["Formulario web","Referido por colega","Contacto directo"][i%3],
            modalidad=["Presencial","Online","Por definir"][i%3]))
    ventas=[]
    for i,valor in [(0,420000),(1,2650000),(4,580000),(8,740000),(9,2650000),(10,420000)]:
        mes=5+i//2
        ventas.append(dict(caso_id=f"ficticio-{i}",fecha_venta=f"2026-{mes:02d}-10",monto_clp=valor,
            anulada=False,estado_pago="Pagado" if i%2 else "Pendiente",
            reserva_clp=valor//4,remuneracion_clp=valor-valor//4))
    return casos,ventas
