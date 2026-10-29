# Verificación en tres tamaños — 29/10/2026

## Alcance real

Se utilizó **Microsoft Edge automatizado mediante Chrome DevTools Protocol**, en 390×844, 768×1024 y 1440×900. Se ejecutó el código local de la aplicación, con sus componentes de navegación, formularios, cookies y restauración de sesión. Solo Auth y el repositorio de datos se sustituyeron por implementaciones ficticias. No se enviaron solicitudes reales, no se crearon cuentas y no se modificó Supabase.

La URL publicada respondió HTTP 200 en una comprobación de lectura. Esto no sustituye una validación de su interfaz ni del ingreso con cuentas reales. No se verificó RLS ni el proveedor Auth en producción.

## Fallo encontrado y corrección

La primera medición encontró áreas táctiles menores de 44 px: pestañas de 40 px; controles de contraseña y ayudas de 16 px; flechas/selectores de 22–40 px; botones de quitar etiquetas de selección múltiple aún menores; enlaces de página de unos 23 px y un enlace de correo de 19 px.

Se informó del fallo antes de corregirlo. El cambio de aplicación se limita a **nueve líneas añadidas en `utils/estilos.py`**: altura mínima de pestañas, áreas de botones nativos, selectores y etiquetas seleccionadas, enlaces de página y enlaces de texto/correo. No cambia iconos, textos, colores, campos, permisos ni comportamiento de negocio.

El enlace de correo se verificó otra vez en los tres tamaños después de ajustar específicamente su selector. Las mediciones históricas conservan el hallazgo; la carpeta de repetición contiene la prueba de su corrección.

## Resultados de presentación

**OK** significa: sin desplazamiento horizontal de la página; sin recortes permanentes ni superposiciones que impidan el uso en las capturas revisadas; áreas de interacción verificadas de al menos 44 px. Las tablas y las pestañas pueden tener desplazamiento dentro de su propio contenedor. Los campos de una línea conservan su edición/desplazamiento interno para valores largos.

| Pantalla / vista | 390×844 | 768×1024 | 1440×900 |
| --- | --- | --- | --- |
| Login y campos de ingreso | OK tras corrección | OK tras corrección | OK tras corrección |
| Crear cuenta de cliente | OK tras corrección | OK tras corrección | OK tras corrección |
| Hoy y pendientes | OK tras corrección del enlace de correo | OK tras corrección del enlace de correo | OK tras corrección del enlace de correo |
| Nueva solicitud interna, paso 1 | OK | OK | OK |
| Nueva solicitud interna, paso 2 | OK | OK | OK |
| Nueva solicitud interna, paso 3 | OK | OK | OK |
| Casos: listado / tarjetas | OK | OK | OK |
| Detalle de caso: campos | OK tras corrección de controles | OK tras corrección de controles | OK tras corrección de controles |
| Cotizador: editor y acción principal | OK tras corrección de controles | OK tras corrección de controles | OK tras corrección de controles |
| Tarifas y servicios | OK tras corrección de controles | OK tras corrección de controles | OK tras corrección de controles |
| Configuración | OK tras corrección de controles | OK tras corrección de controles | OK tras corrección de controles |
| Compartir: enlaces y QR | OK tras corrección de ayudas | OK tras corrección de ayudas | OK tras corrección de ayudas |
| Dashboard y gráfico de ventas | OK tras corrección de ayudas | OK tras corrección de ayudas | OK tras corrección de ayudas |
| Estado del sistema (Administración) | OK | OK | OK |
| Cuenta cliente: formulario | OK | OK tras corrección de ayudas | OK tras corrección de ayudas |
| Formulario público, pasos 1–3 y consentimiento | OK | OK tras corrección de ayudas | OK tras corrección de ayudas |

## Menú, entradas y recargas

| Prueba | 390×844 | 768×1024 | 1440×900 |
| --- | --- | --- | --- |
| Sin sesión, enlace principal y recarga → login | OK | OK | OK |
| Sin sesión, URL de Dashboard y recarga → login | OK | OK | OK |
| Administración, enlace principal y recarga → Hoy | OK | OK | OK |
| Administración: cinco secciones y recarga de sus páginas | OK | OK | OK |
| Menú de Administración: abrir y cerrar | OK, hamburguesa | OK, Mi cuenta / navegación superior | OK, Mi cuenta / navegación superior |
| Cliente, enlace principal y recarga → Nueva solicitud | OK | OK | OK |
| Cliente: nombre y correo bloqueados; sin menú administrativo | OK | OK | OK |
| Menú de Cliente: abrir y cerrar | OK, solo Nueva solicitud y cuenta | OK | OK |
| Cliente abre `/hoy`, `/casos`, `/dashboard`, `/compartir`, `/estado`, también tras recargar → Nueva solicitud | OK | OK | OK |
| Público sin sesión, también tras recargar → formulario sin menú | OK | OK | OK |
| Público con sesión de Administración, también tras recargar → formulario sin menú | OK | OK | OK |
| Público con sesión de Cliente, también tras recargar → formulario sin menú | OK | OK | OK |
| Borrador público en paso 3, recarga → conserva paso y datos sin crear cuenta/sesión | OK | OK | OK |
| Cerrar sesión → login y cookie eliminada | OK | OK | OK |
| Ningún diálogo Page not found en los recorridos comprobados | OK | OK | OK |

Los recorridos principales registraron **63 comprobaciones de navegación y recarga**. Se tomaron 111 capturas en la ronda inicial y 87 en la revisión principal posterior, además de las capturas focalizadas de formularios y controles. Se repitieron capturas de Estado y gráficos que se habían tomado durante la carga, esperando su contenido real antes de evaluarlas.

Se midieron el ancho del documento y del panel principal, las dimensiones de controles, el recorte de etiquetas y el acceso por rol. Se revisaron comparativas visuales de los tres tamaños y capturas de campos, QR, gráficos, menús y final de formulario. Se comprobó que el acceso sin cuenta del login sigue alcanzable al final de la página con el botón fijo y que el consentimiento del formulario puede usarse sin quedar tapado.

## Evidencia y límites

La entrega local contiene una galería HTML con imágenes ampliables, mediciones JSON, resultados de navegación y capturas focalizadas. La evidencia corresponde a datos y cuentas ficticios.

Pendiente de comprobación real: iniciar sesión con cuentas reales en la app publicada y probar Safari/iOS, Chrome/Android y los navegadores internos de Instagram/Facebook, especialmente con teclado virtual abierto y áreas seguras. La emulación de Edge no reproduce esos entornos por completo. Tampoco se probaron envíos reales, correo, descarga de datos de producción ni permisos RLS de la base publicada.
