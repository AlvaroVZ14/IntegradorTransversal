# Documento descargable de cotización

## Referencias revisadas antes de implementar

No existe `referencias/` en esta copia del proyecto. Se revisaron los tres PDF
compartidos anteriormente, desde Descargas, sin copiarlos al repositorio:

| Documento | Estructura y tipografías |
| --- | --- |
| Cotizacion_Mente_y_Futuro.pdf | A4 vertical, 2 páginas. Logo superior izquierdo, franja azul oscura con título, folio/emisión/vigencia, destinatario, alcance, incluye, tabla concepto/valor, descuento, IVA, total y condiciones. Pie con empresa y numeración. Principalmente Calibri; incluye Times New Roman. |
| Cotización Tectramin Scape Room | Vertical, 2 páginas. Logo y título, fecha/cliente/servicio, objetivos y metodología; alcance, tabla ítem/descripción/valor y condiciones generales. Encabezados oscuros y líneas de sección. Fuentes Calibri, Times New Roman, Aptos Display y Arial. |
| Propuesta coaching individual + Promo Duo | Folleto horizontal, 5 páginas. Portada con logo y fotografía, presentación, objetivos y tarjetas de planes con precios; pie de contacto, redes y franjas de marca. Rubik, Open Sans y fuentes decorativas. |

No se observó bloque de firma en los documentos. No se reproduce ni inventa una
firma. El PDF comercial vertical es la base más adecuada para una cotización
individual; el folleto horizontal se considera referencia de marca, no plantilla
de cotización. Todos son PDF, no plantillas Word editables.

## Implementación

Se utiliza ReportLab, ya incluido en las dependencias. La estructura reproduce
la cotización vertical: logo y contacto, título en franja oscura, folio/fechas,
cliente, alcance, secciones del programa, tabla de inversión, descuento, IVA,
total destacado, condiciones, datos del emisor y pie numerado.

Se usa Helvetica, disponible de forma portable en PDF, como sustitución de las
fuentes originales que no están incluidas como archivos en el proyecto. No es
una réplica tipográfica exacta. Los textos son seleccionables; no se rasteriza
el documento ni se usan los PDF originales como fondo con datos reales.

El botón **Descargar cotización** del historial ahora entrega PDF directamente,
en lugar del HTML que exigía imprimir desde el navegador. Se conservan las
descargas adicionales Word/PDF y las acciones anteriores. No se agregan envíos
ni vista previa. Los nombres incluyen folio y cliente, saneados para que no
contengan separadores de rutas o caracteres inválidos.

Los borradores nuevos capturan los campos de marca existentes de Configuración
(`nombre`, `sitio_web`, `correo_contacto` y `logo_base64`, si están definidos),
junto al emisor y las condiciones ya guardados. El logo instalado de la app es
el respaldo si no hay imagen configurada. No se agrega una pantalla ni un campo
de logo. Si existe `logo_base64`, acepta PNG/JPEG y valida formato y tamaño.

Las versiones con snapshot conservan sus datos. En documentos históricos sin
emisor o marca, la descarga completa esos datos desde Configuración solo en
memoria, sin reescribir la cotización. Nunca reemplaza las condiciones específicas
ya guardadas por las condiciones actuales.

El modelo actual representa un servicio principal con precio global y detalle
libre. La prueba de varios componentes usa líneas de detalle con sus cantidades;
no inventa precios por línea, subtotales independientes ni un modelo de servicios
múltiples. Implementar una grilla de varios servicios con precios separados sería
otro cambio de lógica y no forma parte de esta entrega.

## Archivos modificados

- `servicios/documentos_cotizacion.py`: formato PDF, configuración para documentos
  históricos y nombre de archivo seguro.
- `servicios/cotizacion_asistida.py`: captura opcional de marca desde configuración.
- `paginas/gestion.py`: descarga principal como PDF.
- `paginas/acciones_cotizacion.py`: configuración de respaldo en descargas y nombres
  descriptivos para los archivos existentes.
- `tests/test_documentos_pdf.py`: tres ejemplos ficticios, verificación de contenido,
  fechas, totales, paginación, snapshots y nombre de archivo.
- Este documento de análisis y comprobación.

Sin cambios de esquema, permisos, cálculos comerciales o dependencias de la app.
Para la revisión visual local se instaló `pypdfium2`; no se requiere en Streamlit.

## Pruebas

Los archivos y capturas están en `output/pdf/`, ignorado por Git. Todos los datos
de las pruebas son ficticios y las direcciones de contacto utilizan example.test.

| Ejemplo | Resultado visual y de contenido |
| --- | --- |
| COT-2026-0001: un servicio | 2 páginas. Cliente, alcance, programa y condiciones completos; total $1.250.000. |
| COT-2026-0002: varios componentes en el detalle | 2 páginas. Taller, charla y seguimiento con horas y participantes; valor global $1.250.000 sin inventar precios individuales. |
| COT-2026-0003: descuento y textos largos | 4 páginas. Descuento 15%, IVA 19%, total $1.264.375. Los 35 objetivos y las 24 cláusulas llegan completos al PDF; se verifican sus marcadores finales. |

Se renderizaron y revisaron las ocho páginas, comparando encabezado, jerarquía,
tabla y condiciones con los originales. Una comprobación geométrica con PyMuPDF
encontró **cero textos fuera de los márgenes**. La imagen `comparacion_pruebas.png`
reúne las páginas. También se generaron representaciones a 390 px: documento
completo sin recortes laterales. Un PDF A4 necesita ampliación para una lectura
cómoda en celular; no se afirma una prueba en un teléfono físico.

Comandos desde la raíz:

Resultado de esta entrega: **185 pruebas Python aprobadas**, incluidas 14 del
cotizador y 3 del documento PDF. Se revisaron además las ocho páginas renderizadas.

```powershell
python -m unittest discover -s tests -p test_documentos_pdf.py -v
python -m unittest discover -s tests -p test_cotizador.py -q
python -m unittest discover -s tests -p 'test_*.py' -q
```

En la app: Administración → Casos y cotizaciones → abrir un caso → Cotizaciones
→ generar o abrir una versión → **Descargar cotización**. Debe descargar un PDF
con folio y cliente en su nombre, sin pedir datos de configuración nuevamente.
Abrirlo en un visor de PDF y ampliar para leer. No se crearon cotizaciones reales
ni se probaron descargas con datos de producción.
