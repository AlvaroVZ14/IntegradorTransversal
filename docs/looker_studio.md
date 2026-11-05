# Informe avanzado de Mente y Futuro · Prompt 39

Esta guía es para el equipo que configura el informe una vez. Después, la socia solo lo consulta desde Dashboard → Informe avanzado. No cambia el Dashboard actual ni las ventas guardadas. No requiere SQL, dependencias nuevas ni una suscripción Pro.

## Antes de empezar

El prompt 38 ya funciona: sincronización desde la app y ejecución manual de GitHub verificadas. En la revisión de la hoja del 05/11/2026 se observaron encabezados únicos de 25, 18 y 19 columnas, respectivamente, filas contiguas, fechas como números de fecha de Sheets, cantidades y montos numéricos y períodos calculados. Ventas no tenía registros: no se agregaron ventas ficticias para llenar el informe. Casos y Cotizaciones sí tenían registros. No se copiaron datos de clientes a este documento.

El generador no combina celdas ni inserta totales entre registros. La revisión del conector confirma las celdas y tipos del rango ocupado; no expone una lista completa de combinaciones manuales de celdas. Antes de conectar, revisa visualmente que nadie haya combinado celdas en las tres pestañas. Las filas vacías al final son normales y permiten crecer; no son huecos entre registros. No conectes Resumen, Leyenda ni Registro como tablas comerciales.

La hoja sigue restringida. El informe también debe ser privado. No pegues claves, conexiones PostgreSQL ni archivos JSON en Looker: aquí se usa tu sesión de Google para leer Sheets. La URL real del informe se guarda exclusivamente en los secretos de Streamlit.

## 1. Crear el informe y sus tres fuentes

1. Abre [Looker Studio](https://lookerstudio.google.com/) con la cuenta de Google que puede abrir la hoja. Google puede mostrar el nombre «Data Studio» en su interfaz/documentación actual.
2. Elige **Crear → Informe**. Selecciona diseño **Responsivo** si aparece al crear; es más sencillo hacerlo antes de agregar gráficos.
3. Elige el conector de Google **Hojas de cálculo de Google / Google Sheets**. Autoriza el acceso con tu cuenta si lo pide.
4. Selecciona **Mente y Futuro · Datos → Casos**, marca **Usar la primera fila como encabezados** e incluye las celdas filtradas para que un filtro visual de Sheets no cambie los totales. Conecta toda la pestaña, sin un límite fijo de filas. Pulsa **Añadir → Añadir al informe**. Debes ver `codigo`, `fecha_solicitud`, `estado`, etc., como campos.
5. Ponle al informe **Mente y Futuro · Informe de gestión** y a esta fuente **Casos**.
6. En **Recurso → Administrar fuentes de datos añadidas → Añadir una fuente**, repite con **Cotizaciones** y con **Ventas**. Ponles esos nombres. Cada conexión corresponde a una pestaña, no al libro completo. [Referencia del conector](https://docs.cloud.google.com/data-studio/connect-to-google-sheets).

**Qué deberías ver:** tres fuentes, con Casos como principal. Si Ventas está vacía, «Sin datos» es correcto. No escribas una venta en Sheets para resolverlo: registra la operación en la app cuando corresponda.

## 2. Revisar los tipos y las fechas que filtran

En **Recurso → Administrar fuentes de datos añadidas → Editar**, ajusta Tipo y Agregación. Conserva exactamente los nombres de la fila 1: las fórmulas siguientes los usan.

| Fuente | Campo(s) | Tipo / agregación |
|---|---|---|
| Casos | `codigo`, empresa, tipo_servicio, tematica, modalidad, origen_pedido, canal_captacion, registrado_por, estado, motivo_rechazo, faltan_datos, tiene_venta, estado_pago | Texto / ninguna |
| Casos | fecha_solicitud, fecha_ultimo_cambio | Fecha completa / ninguna; dimensión de intervalo: **fecha_solicitud** |
| Casos | participantes, horas, dias_en_estado | Número; promedio cuando corresponda, no sumar participantes en tablas combinadas |
| Casos | monto_cotizado, monto_vendido, monto_pendiente | Moneda → CLP; 0 decimales. No usar estos montos para ventas por fecha de venta |
| Cotizaciones | numero, version | Número entero / ninguna, identificadores, no sumarlos |
| Cotizaciones | codigo_caso, empresa, servicio, tematica, exento_iva, estado_cotizacion | Texto / ninguna; exento_iva contiene SI/NO |
| Cotizaciones | fecha_emision, fecha_envio | Fecha completa / ninguna; dimensión de intervalo: **fecha_emision** |
| Cotizaciones | monto_bruto, monto_total | Moneda → CLP / suma; 0 decimales |
| Cotizaciones | descuento_pct, dias_sin_respuesta | Número / promedio; descuento_pct viene de 0 a 100 |
| Ventas | id_venta, codigo_caso, empresa, tipo_servicio, tematica, modalidad, estado_pago | Texto / ninguna |
| Ventas | fecha_venta | Fecha completa / ninguna; dimensión de intervalo: **fecha_venta** |
| Ventas | participantes | Número / ninguna o promedio |
| Ventas | monto_vendido, monto_reserva, monto_remuneracion, monto_pendiente | Moneda → CLP / suma; 0 decimales |
| Ventas | pct_reserva, pct_remuneracion | Número / promedio, valores de 0 a 100; no marcarlos directamente como porcentaje |
| Las tres | año | Número entero / ninguna |
| Las tres | mes, trimestre, semestre | Texto / ninguna: AAAA-MM, AAAA-T#, AAAA-S# |

Si la fuente vacía fue detectada como texto, cambia los tipos manualmente y vuelve a revisar al registrar la primera operación. No conviertas fechas numéricas de Sheets en texto con fórmulas de presentación. El formato visible puede ser dd/mm/aaaa, pero el tipo debe seguir siendo Fecha.

En **Archivo → Configuración del informe**, usa región Español (Chile), moneda CLP y **Este año** como intervalo predeterminado. Si la interfaz solo ofrece «Año hasta la fecha», elígelo y deja esa etiqueta visible; no lo llames año completo. En cada gráfico deja el intervalo en **Automático**, con la dimensión indicada en la tabla. Un gráfico con fechas fijas ignoraría el calendario. [Configuración de fechas](https://docs.cloud.google.com/data-studio/set-report-date-ranges).

**Qué deberías ver:** $1.250.000, cantidades enteras y fechas completas. Un mes o semestre de texto no reemplaza una dimensión de fecha para filtrar.

## 3. Campos calculados exactos

Para cada fórmula: abre la fuente indicada → **Añadir un campo**, escribe el nombre, pega la fórmula y guarda. Las palabras de las funciones van en inglés, aunque la interfaz esté en español. Donde se indica «gráfico combinado», crea el campo en ese gráfico, no en la fuente original. No se mezclan solicitudes con ventas mediante una simple división de totales de fuentes distintas.

### Ticket promedio (mostrar como «Venta promedio») · Ventas

```text
CASE
  WHEN COUNT_DISTINCT(id_venta) = 0 THEN NULL
  ELSE SUM(monto_vendido) / COUNT_DISTINCT(id_venta)
END
```

Tipo Moneda CLP, 0 decimales. Es total vendido / ventas no anuladas del rango, por fecha de venta. Sin ventas queda vacío o «Sin datos», no un ticket de $0.

### Monto pendiente de cobro · Ventas

```text
SUM(monto_pendiente)
```

Tipo Moneda CLP. Conserva el significado de la app: monto completo de ventas cuyo pago no está terminado, incluidos anticipos. **No es el saldo exacto**, porque la app no registra el importe del abono. Añade esa frase como ayuda bajo la tarjeta. Las ventas anuladas ya están excluidas de la fuente.

### Clave cotización · Cotizaciones

```text
CONCAT(CAST(numero AS TEXT), "-", CAST(version AS TEXT))
```

Tipo Texto / ninguna. Cada versión es una propuesta emitida; los borradores no entran en esta hoja.

### Tasa de aceptación · Cotizaciones

```text
CASE
  WHEN COUNT_DISTINCT(Clave cotización) = 0 THEN NULL
  ELSE COUNT_DISTINCT(
    CASE WHEN estado_cotizacion = "Aceptada" THEN Clave cotización ELSE NULL END
  ) / COUNT_DISTINCT(Clave cotización)
END
```

Tipo Porcentaje, 1 decimal. Denominador: versiones emitidas en el rango; numerador: esas versiones actualmente aceptadas. No es la conversión de solicitudes ni una reconstrucción histórica de la decisión en la fecha de cierre del rango. No uses el estado actual del caso para decidir si una versión fue aceptada.

### Días promedio sin respuesta · Cotizaciones

```text
AVG(
  CASE
    WHEN estado_cotizacion = "Aceptada" OR estado_cotizacion = "Rechazada" THEN NULL
    ELSE dias_sin_respuesta
  END
)
```

Tipo Número, 1 decimal. Promedia propuestas sin decisión; no añade ceros de las ya aceptadas/rechazadas. Sigue la antigüedad desde emisión que usa la app, no supone una fecha de envío inexistente.

### Porcentaje de descuento promedio · Cotizaciones

```text
AVG(descuento_pct) / 100
```

Tipo Porcentaje, 1 decimal. Es el promedio simple de versiones, no ponderado por monto; incluye descuentos cero. Dividir por 100 evita mostrar 10% como 1.000%.

### Tasa de conversión · combinación «Conversión por solicitudes»

1. Crea una combinación desde **Recurso → Administrar combinaciones → Añadir combinación**.
2. Tabla izquierda **Casos**: dimensiones `codigo`, `fecha_solicitud`, `tematica`; intervalo Automático por fecha_solicitud. Conserva codigo como dimensión para no colapsar filas.
3. Tabla derecha **Ventas**: dimensiones `id_venta`, `codigo_caso`, `fecha_venta`; intervalo Automático por fecha_venta. No añadas Cotizaciones a esta combinación.
4. Unión **Externa izquierda**: `Casos.codigo = Ventas.codigo_caso`. Mantiene solicitudes sin venta. Guarda como **Conversión por solicitudes**. Si exige una métrica para cada tabla, añade recuento distinto del identificador; conserva además los identificadores como dimensiones.
5. En la tarjeta basada en esa combinación crea **Tasa de conversión**:

```text
CASE
  WHEN COUNT_DISTINCT(codigo) = 0 THEN NULL
  ELSE COUNT_DISTINCT(
    CASE WHEN id_venta IS NOT NULL THEN codigo ELSE NULL END
  ) / COUNT_DISTINCT(codigo)
END
```

Tipo Porcentaje, 1 decimal. El calendario debe filtrar ambas tablas **antes de unirlas**. Comprueba con una solicitud dentro del rango vendida después: no debe entrar en el numerador. Una solicitud antigua vendida dentro del rango sí suma a Total vendido, pero no al denominador de esta cohorte. Esta diferencia es intencional y coincide con el criterio del Dashboard.

La unión nunca debe multiplicar casos: una fila por codigo y una venta no anulada por caso. No sustituyas esta métrica por `COUNT(ventas)/COUNT(casos)` mezclando versiones: inflaría resultados. [Filtros y claves en combinaciones](https://docs.cloud.google.com/data-studio/blending-tips-and-advanced-concepts).

### Días promedio hasta cotizar · combinación «Tiempo primera cotización»

1. Crea otra combinación: izquierda **Cotizaciones**, filtro **Incluir version = 1**, dimensiones `Clave cotización`, `codigo_caso`, `fecha_emision`, intervalo Automático por fecha_emision.
2. Derecha **Casos**: dimensiones `codigo`, `fecha_solicitud`. Dale un rango fijo amplio, 01/01/1900–31/12/2100, para recuperar también solicitudes antiguas; no debe heredar el rango de emisión de las cotizaciones.
3. Unión Externa izquierda: `codigo_caso = codigo`. Añade los identificadores como dimensiones para conservar cada fila.
4. Crea en el gráfico la métrica:

```text
AVG(
  CASE
    WHEN fecha_solicitud IS NULL OR fecha_emision < fecha_solicitud THEN NULL
    ELSE DATETIME_DIFF(fecha_emision, fecha_solicitud, DAY)
  END
)
```

Tipo Número, 1 decimal. Promedio de días calendario hasta la primera cotización de los casos cuya primera emisión cae en el rango. Las revisiones no vuelven a contar; falta de fecha o fecha incoherente queda fuera. No calcules con fecha_ultimo_cambio: puede representar otra acción. [DATETIME_DIFF para fechas completas](https://docs.cloud.google.com/data-studio/datetimediff).

## 4. Agrupar por y calendario

En **Ventas → Añadir un parámetro** crea **Agrupar por**, tipo Texto, valores permitidos **Mensual, Trimestral, Semestral, Anual** y valor inicial **Mensual**. Crea el campo **Período**:

```text
CASE
  WHEN Agrupar por = "Trimestral" THEN trimestre
  WHEN Agrupar por = "Semestral" THEN semestre
  WHEN Agrupar por = "Anual" THEN CAST(año AS TEXT)
  ELSE mes
END
```

En Resumen agrega un control de **Lista desplegable**, campo de control **Agrupar por**, fuente Ventas. Usa Período como dimensión de las barras de ventas y orden ascendente. En las páginas de solicitudes y cotizaciones repite el parámetro y el campo en su propia fuente, con el mismo nombre visible y opciones. Un parámetro pertenece a su fuente: un control de Ventas no cambia automáticamente parámetros homónimos de Casos o Cotizaciones. Pon en cada página el control de su fuente principal; no prometas un selector único global para fuentes distintas. [Parámetros](https://docs.cloud.google.com/data-studio/parameters).

Agrega en cada página un **Control de intervalo de fechas**, predeterminado Este año. Configura los gráficos para heredar ese calendario usando su fecha correspondiente. Trimestres y semestres de las hojas ya son calendario: ene-mar / abr-jun / jul-sep / oct-dic y ene-jun / jul-dic.

Junto al calendario coloca un cuadro de texto **«Período activo»**. El propio calendario muestra las fechas exactas seleccionadas y es la etiqueta dinámica. Un cuadro de texto normal no recibe automáticamente sus fechas en el conector Sheets; no uses MIN/MAX de registros como sustituto, porque no coinciden con los límites elegidos cuando hay días sin datos. Los controles del informe son independientes de los del Dashboard de la app.

Si no hay operaciones en un período, no inventes filas de ventas para rellenar el gráfico. El Dashboard propio conserva su calendario con ceros; las barras por Período de Looker muestran los períodos con registros y un estado Sin datos si el rango está vacío.

**Qué deberías ver:** cambiar Agrupar por modifica el tamaño de los grupos; cambiar el calendario modifica qué registros entran. Son decisiones diferentes.

## 5. Tema y estados

Abre **Tema y diseño → Personalizar**. Usa fondo claro, tarjetas blancas, fuente legible (Inter si está disponible; Arial como alternativa), texto #0B2545. Ventas azul/celeste #6699FF, solicitudes morado #9966FF y resaltes amarillo #FFCC00. Nunca pongas texto blanco pequeño sobre amarillo. Conserva números y etiquetas para no depender solo del color.

Asigna manualmente estos colores por valor de dimensión, tomados de `ui/estados.py`:

| Tipo | Estado | Color sólido | Fondo / texto para tabla |
|---|---|---|---|
| Caso | Solicitud | #6699FF | #EAF1FF / #244FAF |
| Caso | Cotizada | #9966FF | #F1ECFF / #6533A8 |
| Caso | Aceptada | #32956B | #E7F5ED / #216342 |
| Caso | En seguimiento | #FFCC00 | #FFF6D1 / #705800 |
| Caso | Cerrada | #8793A5 | #EDF0F4 / #4D5C71 |
| Caso | Rechazada | #E99A9F | #FCECEE / #963D47 |
| Pago | Pendiente | #FFCC00 | #FFF6D1 / #705800 |
| Pago | Anticipo pagado | #6699FF | #EAF1FF / #244FAF |
| Pago | Pagado | #32956B | #E7F5ED / #216342 |
| Cotización | Generada | #8793A5 | #EDF0F4 / #4D5C71 |
| Cotización | Enviada | #9966FF | #F1ECFF / #6533A8 |
| Cotización | Sin respuesta | #E9A45D | #FFF0E0 / #8A4800 |
| Cotización | Vencida | #E99A9F | #FCECEE / #963D47 |
| Cotización | Aceptada | #32956B | #E7F5ED / #216342 |
| Cotización | Rechazada | #E99A9F | #FCECEE / #963D47 |

Generada usa el tono neutro del catálogo: significa sin evidencia de envío. La hoja no exporta borradores. Los estados son el estado actual, incluso al consultar fechas antiguas; no son una fotografía histórica del embudo.

## 6. Páginas y gráficos: receta de construcción

Cada gráfico se agrega con **Añadir gráfico**, se coloca en una sección y se configura con la tabla siguiente. En todos, intervalo Automático, sin filtros fijos de prueba. Agrega debajo una línea con el significado. `COUNT_DISTINCT` significa recuento distinto en el selector de agregación.

| Página / gráfico | Fuente | Dimensión | Métrica | Filtros y fecha |
|---|---|---|---|---|
| Resumen · Total vendido | Ventas | Ninguna (tarjeta) | SUM(monto_vendido) | fecha_venta; ventas anuladas ya excluidas |
| Resumen · Venta promedio | Ventas | Ninguna | Ticket promedio | fecha_venta |
| Resumen · Conversión | Conversión por solicitudes | Ninguna | Tasa de conversión | Dos fechas automáticas antes de la unión |
| Resumen · Pago pendiente | Ventas | Ninguna | Monto pendiente de cobro | fecha_venta; ayuda sobre anticipos |
| Resumen · Ventas por período (barras) | Ventas | Período, orden ascendente | SUM(monto_vendido) | fecha_venta |
| Resumen · Ventas por temática (barras horizontales) | Ventas | tematica | SUM(monto_vendido) | fecha_venta |
| Resumen · Ventas por servicio (barras horizontales) | Ventas | tipo_servicio | SUM(monto_vendido) | fecha_venta |
| Solicitudes y embudo · Casos por estado | Casos | estado, orden oficial | COUNT_DISTINCT(codigo) | fecha_solicitud; incluir Rechazada como categoría separada |
| Solicitudes y embudo · Canal (barras) | Casos | canal_captacion | COUNT_DISTINCT(codigo) | fecha_solicitud; conservar Sin canal registrado |
| Solicitudes y embudo · Origen (barras) | Casos | origen_pedido | COUNT_DISTINCT(codigo) | fecha_solicitud; incluye Referido por colega |
| Solicitudes y embudo · Modalidad (dona) | Casos | modalidad | COUNT_DISTINCT(codigo) | fecha_solicitud; conservar Por definir |
| Solicitudes y embudo · Tamaño del grupo (barras) | Casos | Tamaño del grupo (fórmula abajo) | COUNT_DISTINCT(codigo) | fecha_solicitud |
| Cotizaciones · Estado (barras) | Cotizaciones | estado_cotizacion | COUNT_DISTINCT(Clave cotización) | fecha_emision |
| Cotizaciones · Sin respuesta (tabla) | Cotizaciones | Clave cotización, empresa, estado_cotizacion | MAX(dias_sin_respuesta) | Excluir Aceptada y Rechazada; fecha_emision |
| Cotizaciones · Descuento por período | Cotizaciones | Período | Porcentaje de descuento promedio | fecha_emision |
| Cotizaciones · Montos por período | Cotizaciones | Período | SUM(monto_total) | fecha_emision; versiones emitidas, no ventas |
| Cotizaciones · Aceptación / tiempo | Cotizaciones / Tiempo primera cotización | Ninguna (tarjetas separadas) | Tasa de aceptación / Días promedio hasta cotizar | Según definiciones de cada métrica |
| Pérdidas · Motivos de rechazo (barras) | Casos | motivo_rechazo | COUNT_DISTINCT(codigo) | estado = Rechazada; fecha_solicitud |
| Pérdidas · Rechazos por temática | Casos | tematica | COUNT_DISTINCT(codigo) | estado = Rechazada; fecha_solicitud |
| Pérdidas · Rechazos por canal | Casos | canal_captacion | COUNT_DISTINCT(codigo) | estado = Rechazada; fecha_solicitud |
| Oportunidades · Temas solicitados y vendidos (barras agrupadas) | Conversión por solicitudes | tematica | COUNT_DISTINCT(codigo) y COUNT_DISTINCT(CASE WHEN id_venta IS NOT NULL THEN codigo ELSE NULL END) | Cohorte por fecha_solicitud y ventas en el mismo rango; no mezclar CLP con conteos |
| Detalle · Tabla de casos | Casos | codigo, empresa, fecha_solicitud, tipo_servicio, tematica, estado | participantes, horas con MAX, no sumar por combinación | fecha_solicitud; colores por estado; paginación; exportación habilitada para el equipo autorizado |

Para Tamaño del grupo, crea en Casos:

```text
CASE
  WHEN participantes <= 10 THEN "01 · 1 a 10"
  WHEN participantes <= 25 THEN "02 · 11 a 25"
  WHEN participantes <= 50 THEN "03 · 26 a 50"
  ELSE "04 · Más de 50"
END
```

Para ordenar estados, crea **Orden estado** y ordena por él ascendente:

```text
CASE
  WHEN estado = "Solicitud" THEN 1
  WHEN estado = "Cotizada" THEN 2
  WHEN estado = "Aceptada" THEN 3
  WHEN estado = "En seguimiento" THEN 4
  WHEN estado = "Cerrada" THEN 5
  ELSE 6
END
```

Si usas un gráfico de embudo, titúlalo **Casos por estado actual**; no interpretes sus escalones como una conversión histórica acumulativa. Si el gráfico exige cantidades decrecientes, usa barras horizontales en el mismo orden. Una cotización totalizada por versión no equivale a ingreso: no mezcles SUM(monto_total) con Total vendido.

En Detalle → Estilo → Formato condicional, crea una regla por estado, aplicando los fondos/textos anteriores. En modo Ver, el menú del gráfico permite exportar datos si el propietario lo habilitó. La exportación contiene únicamente las columnas sanitizadas de la hoja.

## 7. Cuándo se ven los cambios

Edita cada fuente → **Frescura de datos → Cada 15 minutos**, el mínimo documentado para Google Sheets. El umbral es una caché de consultas: no es un reloj que garantice repintar cada 15 minutos una pestaña abandonada. Como orientación, un guardado normal tarda menos de un minuto en llegar a Sheets y hasta unos 15 minutos adicionales en una consulta renovada del informe; no es un SLA. Si la app duerme o Google falla, la recuperación puede tardar más. [Frescura de Sheets](https://docs.cloud.google.com/data-studio/manage-data-freshness).

La actualización automática periódica de un informe abierto es una función Pro. En la opción gratuita, abrir el informe o cambiar su vista provoca consultas sujetas a la caché; en una pantalla inmóvil puede ser necesario recargar. Dentro de la inserción no está el menú de actualizar datos, por eso la app conserva Abrir en una pestaña nueva. [Actualización de informes](https://docs.cloud.google.com/data-studio/manage-auto-refresh-for-a-report).

La hora que muestra la app es la última copia correcta a Sheets, no la hora de la caché de Looker. No confundas los dos momentos.

## 8. Acceso privado e inserción en la app

1. En el informe, **Compartir → Administrar acceso**: Acceso general **Restringido**. Añade solo los correos de la socia y del equipo que autorice el usuario, como Lectores. Conserva editores solo para quienes construirán el informe.
2. Revisa también las fuentes y la hoja: acceso restringido. Si usas credenciales del propietario, los lectores pueden ver el conjunto que el informe expone sin acceso directo a Sheets; por eso los editores y destinatarios deben ser de confianza. No compartas con todo el dominio universitario.
3. Editando el informe, abre **Archivo → Insertar informe** (o el botón Insertar) y activa **Habilitar inserción**. Esto permite incrustarlo; no lo vuelve público ni elimina el inicio de sesión de Google.
4. Copia solamente la dirección `src` del iframe generado, que contiene `/embed/reporting/`. No copies el HTML completo ni el enlace normal de Compartir. [Inserción de informes privados](https://docs.cloud.google.com/data-studio/embed-a-report).
5. En Streamlit → Manage app → Settings → Secrets agrega al final, conservando las secciones anteriores:

```toml
[looker]
url = ""
```

6. Pega la URL de inserción dentro de esas comillas y guarda. No la pongas en código, SQL, README ni GitHub. Debe ser HTTPS de lookerstudio.google.com o datastudio.google.com, sin parámetros ni fragmentos adicionales. La app valida el dominio y la ruta; si pegas el enlace equivocado, conserva el tablero y muestra una indicación.
7. Entra como Administración → Dashboard: ahora aparecen **Dashboard** e **Informe avanzado**. La primera pestaña mantiene filtros y gráficos. El iframe se crea solo al abrir la segunda. Sin URL, el Dashboard conserva su vista habitual y no muestra esa pestaña.

**Qué deberías ver:** el informe al abrir su pestaña con la cuenta Google autorizada. Si Google bloquea cookies o pide inicio de sesión, usa **Abrir en una pestaña nueva**. Un cliente no puede abrir Dashboard ni leer su URL desde la app; Google aplica además su propio acceso fuera de la app. Conocer una URL nunca reemplaza esos permisos.

## 9. PDF semanal gratuito

Con el informe abierto en modo Ver: **Compartir → Programar entrega**. Elige las páginas, añade solo a la socia y a destinatarios autorizados, establece el próximo lunes a las **08:00** y repetición semanal. Comprueba que el sistema del equipo esté en **America/Santiago**, porque el horario depende de la zona del sistema. Confirma la programación.

Está disponible sin Pro: un programa por informe, con destinatario creador incluido y frecuencia máxima diaria, suficiente para este envío semanal. La personalización avanzada y varios programas requieren Pro. No se envió ni se programó ningún correo durante este desarrollo. El PDF usa los filtros predeterminados de la programación: revísalos. [Disponibilidad y límites oficiales](https://docs.cloud.google.com/data-studio/schedule-automatic-report-delivery).

**Qué deberías ver:** una programación activa para el lunes. Si la política de la universidad impide programar, no cambies permisos de organización: usa descarga manual o consulta a su administrador.

## 10. Celular y ayuda de la socia

El diseño [Responsivo](https://docs.cloud.google.com/data-studio/create-a-responsive-report) ya está disponible: usa secciones, máximo dos tarjetas por fila y tablas paginadas. Comprueba la vista previa en 375 px. Si tu interfaz no lo ofrece, crea una página **Resumen móvil** de unos 360 px de ancho con cuatro tarjetas en dos columnas, un calendario y un gráfico por fila; deja Detalle para una pestaña nueva. No reduzcas las letras para que quepa todo.

La app ajusta la altura del iframe al alto de pantalla y conserva su ancho dentro del contenedor. La responsividad interna depende del informe que construyas: CSS de Streamlit no puede reorganizar gráficos de otro dominio.

El panel **Ayuda · Informe avanzado** ya incluye estas respuestas:

- **Cambiar período:** usa Agrupar por y el calendario dentro del informe.
- **Descargar PDF:** Abrir en una pestaña nueva → Compartir → Descargar informe → PDF.
- **Si no carga:** abre una pestaña nueva, inicia sesión con la cuenta autorizada y revisa la conexión; conserva el informe privado.

## Verificación y archivos entregados

| Prueba | Qué debería pasar | Estado de esta entrega |
|---|---|---|
| Sin URL en secretos | No hay pestaña ni iframe; Dashboard habitual | Automatizada |
| URL incorrecta | Mensaje amable, Dashboard disponible, sin contenido externo | Automatizada |
| URL válida, pestaña Dashboard | No se crea iframe ni se consulta el informe | Automatizada |
| Abrir Informe avanzado y volver | Iframe solo al abrir, botón siempre disponible, rango del Dashboard conservado | Automatizada |
| Cliente intenta Dashboard | Redirección por rol; no se leen secretos del informe | Automatizada |
| Fechas y tipos de Sheets | Encabezados y filas coherentes; valores de fechas/monedas numéricos | Revisión directa de las tres pestañas; Ventas aún sin filas |
| Fórmulas y valores dentro de Looker | Crear campos, comparar ventas/conversión con app y probar cero solicitudes/ventas | Pendiente de creación manual del informe |
| Acceso privado | Cuenta autorizada lo abre; cuenta no invitada no ve datos | Pendiente de configurar permisos en Google |
| Dato nuevo → informe | Tras copiarse a Sheets y vencer caché, aparece en una consulta nueva | Pendiente del informe, no certificado como tiempo real |
| Celular y PDF semanal | Controles utilizables y PDF privado recibido el lunes | Pendiente de configurar informe/programación |

Archivos: `paginas/dashboard.py` integra las pestañas; `paginas/informe_avanzado.py` presenta informe y ayuda; `servicios/informe_avanzado.py` valida URL y formatea la hora; `ui/tema.py` centraliza la adaptación del iframe; `secrets.toml.example` agrega la sección vacía; `tests/test_looker39.py` prueba carga bajo demanda, roles y estado. Esta guía es `docs/looker_studio.md`. No hay migración SQL ni librerías nuevas.

Para probar el código con datos ficticios: `python -m unittest discover -s tests -p test_looker39.py`. Usa una URL ficticia y un doble del iframe; no crea un informe real ni cambia sus permisos.

Lista corta de lo que falta hacer en tu cuenta: crear las tres fuentes y el informe; configurar campos/gráficos con esta receta; restringir el acceso; copiar el src de inserción a Secrets; probar con dos cuentas; programar el PDF del lunes. La app queda preparada aunque esos pasos todavía no se hayan hecho.
