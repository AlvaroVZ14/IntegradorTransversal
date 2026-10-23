# Unificación visual · Mente y Futuro

Esta entrega unifica la presentación sin cambiar el flujo de solicitudes, cotizaciones, ventas ni permisos. No requiere SQL, datos nuevos ni dependencias adicionales. Las pruebas usan exclusivamente datos ficticios y repositorios aislados.

## Cómo verlo ahora

Abre **http://127.0.0.1:8502** y actualiza con **Ctrl + F5**. Es la instancia local que ya tiene conexión a Supabase. Usa tu cuenta habitual; no se cambió el acceso. Estos archivos todavía no se han publicado en Community Cloud.

Para ejecutar el proyecto por tu cuenta, desde su carpeta:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8502
```

Si ese puerto ya está ocupado, utiliza la instancia existente o detén tu proceso anterior con Ctrl+C antes de volver a iniciarlo. La conexión usa los valores existentes de `.streamlit/secrets.toml`; ese archivo no está en la entrega.

## Qué deberías ver

| Página | Resultado esperado |
| --- | --- |
| Nueva solicitud | Banner azul/morado con etiqueta SOLICITUDES, título e ícono. El mensaje de bienvenida está dentro del banner. Tres tarjetas: datos de contacto, experiencia y confirmación, con número en círculo de degradado. Un único botón amarillo envía el formulario completo. |
| Nueva solicitud como Cliente | Mismo diseño, nombre y correo bloqueados, consentimiento obligatorio y ningún campo interno. Tras enviar, comprobante y mensaje de 48 horas hábiles; sin listado. |
| Casos y cotizaciones | Mismo banner con etiqueta SEGUIMIENTO, tres KPI con el componente del Dashboard, pestañas con indicador de degradado y badges de estado habituales. Formularios con encabezados numerados y botones amarillos. |
| Tarifas y servicios | Dentro de su pestaña original: tabla con encabezado lavanda y el formulario de tarifa con el mismo estilo del resto. En celular, las filas se convierten en fichas. |
| Dashboard | El mismo banner, conservando “Una mirada a tu negocio” y el período elegido. Actualizar está a la derecha en escritorio y debajo del texto en celular. Los filtros, cálculos, caché de 60 segundos y gráficos mantienen su funcionamiento. |
| Login | Tarjeta blanca centrada con línea de marca arriba, logo original, fondo radial tenue azul/morado, pestañas comunes y botón amarillo de ancho completo. |

En todas las páginas: fondo #F6F8FC con luces muy tenues en las esquinas, bordes #E4E9F2, tarjetas blancas, foco azul, texto #0B2545 y texto secundario #5B6B82. La paleta original se conserva. Las tarjetas se elevan 3 px al pasar el mouse y muestran borde de degradado. El botón amarillo se eleva y recibe un brillo que cruza una vez por entrada del mouse; los secundarios tienen borde azul y hover lavanda. Los botones deshabilitados no se animan.

Los banners comparten radio, márgenes, padding y altura mínima: 224 px en escritorio y 264 px debajo de 768 px. Se permite crecer con textos largos o zoom para no recortar contenido. Las tres luces del mesh y el brillo son CSS; no se agregaron imágenes.

Las entradas duran 300 ms con retrasos de 0/50/100 ms: como máximo 400 ms por bloque. Los skeletons aparecen durante las consultas y se retiran incluso si hay error. La preferencia del sistema de movimiento reducido desactiva entradas, elevaciones, brillo y shimmer. No se agregan esperas artificiales para mostrar la animación.

## Archivos completos

- `utils/estilos.py`: una sola hoja de estilos, variables de marca en `:root`, tarjetas comunes, mesh, botones, formularios, tablas, pestañas, alertas, responsive y movimiento reducido. Los comentarios identifican los selectores internos de Streamlit/BaseWeb que se sobrescriben.
- `utils/componentes.py`: `encabezado_pagina`, contenido HTML escapado, secciones numeradas y contexto de carga. Se reutilizan `tarjeta_kpi`, tablas, badges y skeletons.
- `paginas/nueva_solicitud.py`: encabezado y tres secciones dentro del **mismo** `st.form`; mismos campos, límites, consentimiento, validaciones y envío.
- `paginas/gestion.py`: encabezado, KPI comunes, títulos de sección, carga y tabla de tarifas con el componente existente.
- `paginas/dashboard.py`: encabezado común y botón Actualizar como acción nativa. Se conservan el callback y los filtros.
- `mente_futuro/ui.py`: la función anterior `header` delega al nuevo componente, por compatibilidad; el login recibe los estilos comunes sin cambiar Auth.
- `utils/graficos_dashboard.py`: se retira el único `style` HTML en la etiqueta central de las donas; dos anotaciones nativas de Plotly conservan el total y la descripción. No cambia ninguna suma ni consulta.
- `tests/test_app.py` y `tests/test_componentes_producto.py`: pruebas de los encabezados, formulario reorganizado y escape HTML.

La cotización HTML descargable conserva su hoja de impresión independiente; no es una página de la app y no se alteró.

El ZIP `output/mente-futuro-lenguaje-visual.zip` contiene los archivos completos del proyecto, incluida esta guía, sin `.streamlit/secrets.toml`, contraseñas ni directorios temporales. No hay nuevas dependencias respecto de la entrega anterior; se mantienen las de `requirements.txt`.

Para una futura página privada, valida primero sus permisos y llama una sola vez:

```python
from utils.componentes import encabezado_pagina

encabezado_pagina("Título", "Subtítulo breve", "SECCIÓN", "✦")
```

`acciones`, si se necesita, es una función que dibuja botones de Streamlit. No recibe HTML ni JavaScript de acciones. Ejemplo: `acciones=lambda: st.button("Actualizar", on_click=actualizar, width="stretch")`. Ocultar opciones o presentar un encabezado no concede permisos de acceso.

## Pruebas realizadas

```powershell
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
```

**55 pruebas aprobadas.** Incluyen recorrido de solicitud, cotización y venta, identidad bloqueada y consentimiento del cliente, guardias por URL, KPI de casos, todas las agrupaciones del Dashboard, rango vacío y una venta, callback de Actualizar, salida de sesión y escape HTML. También comprueban un único encabezado común por página y un único envío después de reorganizar el formulario en tres secciones.

Se compararon con la entrega anterior y siguen idénticos `servicios/dashboard.py`, `servicios/repositorio.py`, `servicios/dashboard_cache.py`, `mente_futuro/domain.py`, `utils/permisos.py`, `utils/estados.py` y `requirements.txt`.

## Revisión visual en navegador: pendiente

La herramienta devolvió “No browser is available”. AppTest comprueba widgets y recorridos, pero no renderiza CSS. Por eso no se afirma haber aprobado una revisión visual real en los tres tamaños.

En el navegador, activa la vista adaptable y comprueba:

| Ancho | Qué revisar |
| --- | --- |
| 375 px | Banner con texto completo y acciones debajo; tarjetas, campos y gráficos en una columna; botón de abrir menú lateral disponible; filtros del Dashboard plegables; casos y tarifas en fichas sin desplazamiento horizontal. Login y consentimiento legibles; controles de al menos 44 px. |
| 768 px | Banner y contenido sin cortes; columnas legibles; tablas con encabezado lavanda; menú lateral accesible aunque Streamlit lo contraiga. No confundir este tamaño con el breakpoint móvil, que termina en 767 px. |
| 1280 px o más | Banners iguales al navegar entre páginas, acción Actualizar a la derecha, formularios y gráficos en columnas, KPI del mismo estilo, elevación de tarjetas y brillo único del botón al pasar el mouse. |

Repite como Administración y Cliente. Cliente debe ver únicamente Nueva solicitud, también al intentar `?pagina=Dashboard` o `?pagina=Casos%20y%20cotizaciones`. Administración conserva las tres páginas y las pestañas originales. No uses datos reales para pruebas de escritura.

Con el teclado, comprueba el foco visible y el alcance del botón de envío. Activa movimiento reducido en el sistema o emúlalo desde el navegador: no debe haber entradas, elevaciones, brillos ni shimmer. Con datos vacíos deben aparecer mensajes amables; con una venta el monto y las fechas deben seguir en formato chileno.

Los selectores `data-testid` y `data-baseweb` son internos de Streamlit: deberán revisarse al actualizar su versión. La app conserva el encabezado nativo necesario para abrir el menú móvil y no modifica los controles externos de Community Cloud.
