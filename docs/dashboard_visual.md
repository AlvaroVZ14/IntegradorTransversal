# Dashboard visual de Mente y Futuro

Entrega del 22/10/2026. Implementada localmente; todavía no publicada en Streamlit.

## Archivos completos

- `paginas/dashboard.py`: encabezado, filtros, seis KPI, cuadrícula, gráficos secundarios y exportación.
- `utils/estilos.py`: única fuente de CSS, paleta, Inter/Poppins, tarjetas, animaciones, tamaños táctiles y reduced motion.
- `utils/componentes.py`: encabezado, chips, tarjeta_kpi, tarjeta_grafico, estado vacío, dato destacado y esqueletos.
- `utils/plotly_tema.py`: plantilla común, fondo transparente, separadores chilenos, colores y transiciones.
- `utils/graficos_dashboard.py`: construcción de los ocho gráficos.
- `utils/responsive.py`: ancho de pantalla y preferencia de movimiento.
- `servicios/dashboard_cache.py`: caché de 60 segundos con aislamiento por sesión.

Los archivos estilos.py y componentes.py no existían. Se trasladó el CSS desde mente_futuro/presentation.py y se conservó la importación anterior como adaptador, sin dos copias de los estilos.

## Cálculos y consultas

Se compararon byte a byte con el paquete anterior: `servicios/dashboard.py`, `servicios/repositorio.py` y `mente_futuro/domain.py` son idénticos. Los indicadores, agrupaciones, filtros y criterios de fechas se mantienen. Origen y modalidad provienen de las mismas filas de casos ya consultadas, restringidas a los IDs del filtro actual.

La caché no existía en el código recibido. Se agregó `st.cache_data(ttl=60)` sin cambiar las consultas. Su clave incluye un alcance aleatorio por sesión y una revisión: no comparte datos entre sesiones. Actualizar, Actualizar información y las escrituras exitosas invalidan esa revisión. Se sigue validando el rol antes del acceso.

## Con datos

Banda azul a morado con título y rango, tarjeta de filtros y chips activos. Seis KPI con íconos circulares, valor, variación y ayuda; se elevan al pasar el mouse.

1. Ventas: línea azul con puntos cero, área degradada, promedio por período punteado amarillo y mejor período marcado. Ese promedio visual no sustituye Venta promedio por caso vendido.
2. Solicitudes vs ventas: barras moradas y línea azul con eje secundario de cantidad de ventas cerradas.
3. Temáticas: dona con cinco principales y Otras, porcentajes, leyenda y total central.
4. Embudo: distribución actual en Solicitud, Cotizada, Aceptada, En seguimiento y Cerrada. No representa una conversión histórica acumulada. Rechazadas y En revisión se informan por separado.
5. Origen: barras ordenadas con cantidad y porcentaje. Referido por colega está contemplado con cero si no está registrado; No informado conserva los casos sin origen.
6. Modalidad: dona con las modalidades registradas, incluida Por definir cuando corresponda.
7. Reserva vs remuneración: dona solo con valores completos registrados en `reserva_clp` y `remuneracion_clp`; nunca se presupone un reparto.
8. Servicio: barras horizontales con cantidades y porcentajes.

Los primeros cinco están a la vista. Los otros tres están en Ver más gráficos. Se usan dos columnas en escritorio y una en celular. El dato destacado muestra el mejor período vendido o, si no hay ventas, la temática más solicitada.

## Sin datos

Los KPI conservan sus reglas: cero en totales/conteos y — en promedios/conversión sin denominador. Las tarjetas muestran íconos suaves y mensajes amables; no se construyen gráficos con ejes vacíos ni donas con total cero.

Durante la carga se ven esqueletos y Preparando tu tablero. `prefers-reduced-motion` desactiva animaciones CSS y transiciones Plotly. Los botones y controles de expansión tienen al menos 44 px. Si las fuentes remotas no cargan se usa sans-serif.

## Datos que aún no existen

El esquema real versionado no contiene reserva ni remuneración. Por eso esa tarjeta mostrará El reparto de reserva y remuneración aún no está registrado, incluso con ventas. No se agregó SQL ni una regla de reparto.

La modalidad actual admite Presencial, Online y Por definir; no Híbrida. La visualización contempla Híbrida con cero, pero esta entrega no altera la restricción ni el formulario. No se eliminan las modalidades existentes del total.

## Instalación y prueba

Dependencia nueva: `plotly>=6.1,<7`, incorporada en requirements.txt.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Ingresa como Administración y abre Dashboard. La migración de roles anterior sigue siendo necesaria; esta mejora visual no requiere SQL adicional.

Para una muestra sin cuenta ni base de datos abre `output/dashboard-vista-ficticia.html`. Incluye Plotly dentro del archivo y datos completamente ficticios. Es una muestra de los gráficos; el reparto ilustrado no representa una regla del negocio.

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python tests/generar_preview_dashboard.py
```

Resultado: 47 pruebas correctas. Incluyen puntos cero, conservación de totales, Otras, denominadores vacíos, plantilla, modalidad no definida, reparto sin datos, reduced motion, caché/actualización y recorrido administrativo completo.

La revisión visual real a 375 px está pendiente porque no hay navegador conectado. AppTest comprueba estructura y flujo, pero no sustituye esa inspección.

Referencias técnicas: [plantillas Plotly](https://plotly.com/python/templates/), [áreas con degradado](https://plotly.com/python/filled-area-plots/) y [tema Plotly en Streamlit](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart).
