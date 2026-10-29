# Reportes por período

## Ubicación y alcance

No existía una página de Reportes: solo Exportar resumen por período del
Dashboard. Se conserva esa exportación y se agrega **Dashboard → Reportes por
período**, una sección desplegable de Administración. No hay ruta ni permisos
nuevos. La integración en Dashboard es una llamada al componente de reportes,
fuera de su fragmento de actualización.

Los filtros son independientes del tablero y consideran todos los servicios y
temáticas, como se indica junto a la tabla. El rango inicial es del 1 de enero
del año en curso hasta hoy en Chile. Generar reporte aplica los filtros. Si
Desde es posterior a Hasta, muestra un aviso. No amplía rangos cortos: un día
es válido y ambos extremos son inclusivos.

## Indicadores

| Indicador | Definición |
| --- | --- |
| Solicitudes | Casos por fecha de creación convertida a America/Santiago. |
| Cotizaciones emitidas | Registros/versiones por fecha de emisión; si falta en un documento histórico, utiliza la creación en Chile. No incluye borradores. |
| Ventas cerradas | Ventas no anuladas vinculadas a casos existentes, por fecha de venta. No cuenta casos en estado Cerrada. |
| Total vendido | Suma de monto_clp de esas ventas, igual que en Dashboard. |
| Ventas con pago pendiente | Monto completo de esas ventas si su pago no es Pagado, incluidos abonos; no es saldo restante. |

Todos son aditivos: la suma de los períodos coincide con el total del rango.
No se suman promedios ni conversiones como si fueran montos o conteos. Los
indicadores analíticos del Dashboard permanecen sin cambios.

Mensual, Trimestral, Semestral y Anual siguen el calendario: trimestres ene-mar,
abr-jun, jul-sep, oct-dic; semestres ene-jun y jul-dic. Los períodos parciales
cuentan solo los días seleccionados y muestran sus límites efectivos. Los
períodos vacíos siempre tienen fila y valores cero.

Los campos DATE mantienen su día comercial. Los timestamps con zona se convierten
a Chile y los timestamps sin zona se interpretan como UTC, igual que las fechas
de creación del tablero. Esto respeta medianoche y cambios de horario.

## Interfaz, exportación y consultas

- Tabla nativa con scroll horizontal/vertical interno, fechas dd/mm/aaaa, montos
  como $1.250.000 y fila Total del rango.
- Gráfico de barras con selector de los cinco indicadores, tema y colores
  existentes. En rangos largos reduce etiquetas, conservando todos los datos
  y el período/valor de cada barra en su tooltip.
- CSV UTF-8 con BOM y punto y coma para abrir en Excel. Exporta una fila por
  período, con montos numéricos. No incluye una segunda fila de total que
  duplicaría la suma al abrirlo en una planilla.
- Solo carga cotizaciones al abrir la sección, mediante el método existente
  `all_quotes()`. Caché de 60 s aislado por usuario/sesión, con invalidación por
  la revisión de escrituras ya existente. Usa casos y ventas de la lectura
  disponible del Dashboard; no consulta por fila ni período.
- La comprobación de Administración ocurre antes de leer datos o caché.

Sin cambios SQL, permisos, cálculos comerciales, colores ni dependencias nuevas.

## Pruebas con datos ficticios

| Prueba | Resultado |
| --- | --- |
| Cuatro agrupaciones, 2024 completo | 5 solicitudes, 6 versiones, 5 ventas, $1.500.000 vendidos y $800.000 en ventas no pagadas. Iguales entre agrupaciones y coherentes con los cálculos del Dashboard. |
| Trimestres | $300.000, $300.000, $400.000 y $500.000; límites en enero, abril, julio y octubre. |
| Semestres | $600.000 y $900.000; límites en enero y julio. |
| Períodos vacíos | Febrero queda en cero. Tres años vacíos generan 36 meses, 12 trimestres, 6 semestres o 3 años, todos en cero. |
| Un día: 31/03/2024 | Una fila en cada agrupación: 2 solicitudes, 2 cotizaciones y 1 venta por $200.000. |
| Medianoche de Chile | 01/04/2024 02:59:59 UTC queda en marzo; un DATE 01/04/2024 permanece en abril. |
| Varios años: 31/12/2023 a 01/01/2025 | Suma $2.800.000 en las cuatro agrupaciones y conserva los límites parciales. |
| Venta anulada | Registro ficticio de $999.999 excluido de cantidad y montos. |
| CSV | Se vuelve a leer con BOM y punto y coma: suma $1.500.000 y fechas chilenas. |
| Administración y rerun | AppTest conserva filtros y genera tabla/gráfico/CSV. Rango invertido muestra aviso y no tabla. |
| Integración | Sección cerrada sin tabla; al abrirla en Dashboard aparece el reporte. |
| Cliente | Falla antes de consultar cotizaciones; permisos existentes intactos. |
| Navegador: 390, 768 y 1440 px | Cero scroll horizontal de página y errores visibles. Tabla y gráfico dentro del ancho; scroll de tabla interno a 390 y 768 px. |

Se revisaron capturas de celular, gráfico de celular y escritorio. Las capturas,
mediciones JSON y CSV ficticios están en `output/reportes/`, ignorado por Git.
Se usó Edge automatizado con viewport emulado: no se probó un teléfono físico
ni se crearon datos en Supabase de producción.

Resultado de la suite completa: **195 pruebas aprobadas**, incluidas las nueve
pruebas nuevas de reportes.

## Archivos y cómo probar

- `servicios/reportes.py`: calendario, agrupaciones, totales y CSV.
- `paginas/reportes.py`: filtros, tabla, gráfico, descarga y carga protegida.
- `paginas/dashboard.py`: integración en el Dashboard.
- `tests/test_reportes.py`: límites, agrupaciones, CSV, UI y rol.
- Este informe.

```powershell
python -m unittest discover -s tests -p test_reportes.py -v
python -m unittest discover -s tests -p 'test_*.py' -q
```

En la app: Administración → Dashboard → Reportes por período → elegir
agrupación, Desde y Hasta → Generar reporte. Revisar Total del rango y descargar
CSV. Para un día usar la misma fecha en ambos campos; para varios años elegir
años distintos. En celular, deslizar la tabla para ver las demás columnas sin
mover la página lateralmente.
