"""Calendario del Dashboard. Funciones puras, sin consultas ni Streamlit."""
from calendar import monthrange
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

AGRUPACIONES = ('Mensual', 'Trimestral', 'Semestral', 'Anual')
AGRUPACIONES_SERIE = ('Semanal', *AGRUPACIONES)
MESES = ('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic')
MESES_COMPLETOS = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
                  'septiembre', 'octubre', 'noviembre', 'diciembre')
MESES_POR_PERIODO = {'Mensual': 1, 'Trimestral': 3, 'Semestral': 6, 'Anual': 12}


def fecha_chile(valor):
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor.replace('Z', '+00:00')) if 'T' in valor or ' ' in valor else date.fromisoformat(valor)
    if isinstance(valor, datetime):
        return (valor.astimezone(ZoneInfo('America/Santiago')) if valor.tzinfo else valor).date()
    if not isinstance(valor, date):
        raise ValueError('Elige una fecha válida.')
    return valor


def validar_rango(desde, hasta):
    desde, hasta = fecha_chile(desde), fecha_chile(hasta)
    if desde > hasta:
        raise ValueError('Desde no puede ser posterior a Hasta. Revisa las fechas; mantenemos el último período válido.')
    return desde, hasta


def inicio_periodo(fecha, agrupacion):
    fecha = fecha_chile(fecha)
    if agrupacion not in AGRUPACIONES_SERIE:
        raise ValueError('Selecciona una agrupación válida.')
    if agrupacion == 'Semanal':
        return fecha - timedelta(days=fecha.weekday())
    meses = MESES_POR_PERIODO[agrupacion]
    return date(fecha.year, (fecha.month - 1) // meses * meses + 1, 1)


def mover_periodo(fecha, cantidad, agrupacion):
    fecha = fecha_chile(fecha)
    if agrupacion not in AGRUPACIONES_SERIE:
        raise ValueError('Selecciona una agrupación válida.')
    if agrupacion == 'Semanal':
        return fecha + timedelta(weeks=cantidad)
    indice = fecha.year * 12 + fecha.month - 1 + cantidad * MESES_POR_PERIODO[agrupacion]
    anio, mes = divmod(indice, 12)
    return date(anio, mes + 1, min(fecha.day, monthrange(anio, mes + 1)[1]))


def fin_periodo(fecha, agrupacion):
    inicio = inicio_periodo(fecha, agrupacion)
    if agrupacion == 'Semanal':
        return inicio + timedelta(days=6)
    ultimo_mes = inicio.month + MESES_POR_PERIODO[agrupacion] - 1
    return date(inicio.year, ultimo_mes, monthrange(inicio.year, ultimo_mes)[1])


def periodo_vigente(agrupacion, hoy):
    return inicio_periodo(hoy, agrupacion), fin_periodo(hoy, agrupacion)


def periodos_del_rango(desde, hasta, agrupacion):
    desde, hasta = validar_rango(desde, hasta)
    actual, ultimo = inicio_periodo(desde, agrupacion), inicio_periodo(hasta, agrupacion)
    periodos = []
    while True:
        periodos.append(actual)
        if actual == ultimo:
            return periodos
        actual = mover_periodo(actual, 1, agrupacion)


def periodo_anterior(desde, hasta):
    """Bloque inmediatamente anterior con igual número de días inclusivos.

    Navegar a otro mes es calendario; comparar KPI conserva la duración exacta.
    Ejemplo: 01–30 noviembre compara con 02–31 octubre, no con 31 días.
    """
    desde, hasta = validar_rango(desde, hasta)
    return desde - timedelta(days=(hasta - desde).days + 1), desde - timedelta(days=1)


def navegar_periodo(desde, agrupacion, direccion, hoy):
    if direccion not in (-1, 1):
        raise ValueError('Elige Anterior o Siguiente.')
    destino = mover_periodo(inicio_periodo(desde, agrupacion), direccion, agrupacion)
    if destino > inicio_periodo(hoy, agrupacion):
        raise ValueError('No puedes avanzar a un período futuro.')
    return periodo_vigente(agrupacion, destino)


def puede_avanzar(desde, agrupacion, hoy):
    return mover_periodo(inicio_periodo(desde, agrupacion), 1, agrupacion) <= inicio_periodo(hoy, agrupacion)


def etiqueta_periodo(inicio, agrupacion):
    inicio = inicio_periodo(inicio, agrupacion)
    fin = fin_periodo(inicio, agrupacion)
    if agrupacion == 'Semanal':
        tramo = (f'{inicio.day}–{fin.day} {MESES[fin.month-1]}' if inicio.month == fin.month else
                 f'{inicio.day} {MESES[inicio.month-1]}–{fin.day} {MESES[fin.month-1]}')
        return f'Sem {inicio.isocalendar().week:02d} · {tramo}'
    if agrupacion == 'Mensual':
        return f'{MESES[inicio.month-1]} {inicio.year}'
    if agrupacion == 'Trimestral':
        return f'T{(inicio.month-1)//3+1} · {inicio.year}'
    if agrupacion == 'Semestral':
        return f'S{(inicio.month-1)//6+1} · {inicio.year}'
    return str(inicio.year)


def etiqueta_rango(desde, hasta, agrupacion, personalizado=False):
    desde, hasta = validar_rango(desde, hasta)
    if personalizado or (desde, hasta) != periodo_vigente(agrupacion, desde):
        nombre = 'Rango personalizado'
    elif agrupacion == 'Mensual':
        nombre = f'Mes: {MESES_COMPLETOS[desde.month-1]} {desde.year}'
    elif agrupacion == 'Trimestral':
        nombre = f'Trimestre {(desde.month-1)//3+1} de {desde.year}'
    elif agrupacion == 'Semestral':
        nombre = f'Semestre {(desde.month-1)//6+1} de {desde.year}'
    else:
        nombre = f'Año {desde.year}'
    return f'{nombre} · {desde:%d/%m/%Y} – {hasta:%d/%m/%Y}'


def agrupacion_evolucion(desde, hasta, agrupacion):
    if agrupacion != 'Semanal' and inicio_periodo(desde, agrupacion) == inicio_periodo(hasta, agrupacion):
        return 'Semanal' if agrupacion == 'Mensual' else 'Mensual'
    return agrupacion
