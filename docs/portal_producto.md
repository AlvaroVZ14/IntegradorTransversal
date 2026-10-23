# Presentación del portal · 22/10/2026

Esta entrega cambia la presentación. No agrega migraciones, consultas ni cálculos comerciales. No modifica registros en Supabase y no agrega dependencias.

## Cómo verlo

Desde la carpeta del proyecto:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abre `http://localhost:8501`. Si ya tenías Streamlit ejecutándose, detenlo con Ctrl+C y vuelve a iniciarlo para que lea `.streamlit/config.toml`. La conexión sigue usando los valores existentes de `.streamlit/secrets.toml`; no los subas a GitHub.

Para esta revisión se inició una instancia actualizada en **http://127.0.0.1:8502**, porque el puerto 8501 ya estaba ocupado. Para iniciarla nuevamente en ese puerto: `python -m streamlit run app.py --server.port 8502`.

Los cambios locales no actualizan por sí solos la aplicación en `.streamlit.app`. Community Cloud se actualiza cuando los archivos se publican en la rama configurada del repositorio. Esta entrega no se publicó. Antes de publicar el conjunto de cambios pendientes del proyecto, conserva la comprobación de permisos descrita en [cliente_solo_solicitud.md](cliente_solo_solicitud.md).

## Qué cambió

- Login en tarjeta blanca centrada, logo original, fondo suave azul/morado, botón amarillo de ancho completo y los tres pasos del proceso de solicitud.
- Título de pestaña `Mente y Futuro · Portal`, favicon SVG que muestra la ampolleta del logo original y pie `Mente y Futuro · Sistema de gestión`.
- Navegación con íconos, selección lavanda y borde morado; nombre y rol del usuario, con Cerrar sesión al final de la barra lateral. Los clientes siguen teniendo únicamente Nueva solicitud.
- Badges compartidos en listado, detalle y solicitudes del dashboard. El embudo utiliza los mismos colores principales. Incluyen texto, además del color.
- Listados de casos adaptados a fichas debajo de 768 px, conservando el detalle y la exportación CSV. En tablet y escritorio se muestran como tabla.
- Fechas visibles de cotizaciones y ventas en `dd/mm/aaaa`.
- Ayudas de los KPI: Por revisar cuenta Solicitud y la subetapa heredada En revisión; En desarrollo cuenta Aceptada y En seguimiento. Las sumas son las originales.
- Errores de servicio con mensajes amables y una salida al ingreso. No se muestran detalles de excepciones ni instrucciones SQL a los visitantes.
- Ejemplos locales con nombres ficticios de organizaciones y personas. No se encontró `Prueba01` en el código del proyecto; no se renombraron ni eliminaron datos reales.

Los seis badges son Solicitud (azul), Cotizada (morado), Aceptada (verde), En seguimiento (amarillo), Cerrada (gris) y Rechazada (rojo suave). Los valores internos de la base de datos se conservan. La antigua subetapa En revisión se presenta con badge Solicitud y ayuda “Solicitud en revisión”; en selectores se distingue como “Solicitud · en revisión”. Su conteo separado en el dashboard se conserva fuera del embudo para no cambiar los cálculos existentes.

## Controles de Streamlit: alcance real

Se configuró `toolbarMode = "minimal"`. Según la [documentación oficial](https://docs.streamlit.io/develop/api-reference/configuration/config.toml), ese modo todavía permite controles añadidos externamente por Community Cloud. Por eso el CSS oculta también `stToolbarActions`, `stAppDeployButton`, `stMainMenu`, `#MainMenu` y el pie nativo. Se comprobaron esos identificadores contra los recursos de Streamlit instalado; son selectores internos y podrían cambiar en futuras versiones.

El encabezado no se oculta: debe seguir disponible el botón que abre la navegación en celular. Tampoco se ocultan el estado de ejecución ni el botón de detener un proceso.

**Manage app no pertenece al contenido de la aplicación.** Es un control de Community Cloud disponible al propietario conectado a esa plataforma. No se garantiza ocultarlo mediante el CSS de esta app. Ver [gestión de aplicaciones en Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app). Para revisar la vista de visitante, usa una ventana privada sin sesión de Streamlit Cloud; la sesión del portal es independiente.

## Archivos completos

La implementación está en `app.py`, `.streamlit/config.toml`, `mente_futuro/ui.py`, `mente_futuro/presentation.py`, `paginas/gestion.py`, `paginas/dashboard.py`, `utils/estilos.py`, `utils/componentes.py`, `utils/estados.py`, `utils/graficos_dashboard.py` y `assets/favicon-mente-y-futuro.svg`. Las pruebas y los ejemplos están en `tests/`. La entrega completa, sin secretos, está en `output/mente-futuro-portal-producto.zip`.

## Validación automática realizada

```powershell
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
```

Resultado: **52 pruebas aprobadas**. Cubren cliente con acceso solo a Nueva solicitud, guardias por URL, consentimiento e identidad bloqueada, solicitud/cotización/venta de Administración, filtros y cálculos del dashboard, datos vacíos y una venta, KPI de casos con los siete valores internos existentes, cierre de sesión, texto de errores y escape HTML en los nuevos listados. Todos los datos son ficticios y el repositorio está aislado: no se escriben datos de prueba en Supabase.

Se compararon con la entrega anterior y siguen idénticos `servicios/dashboard.py`, `servicios/repositorio.py`, `mente_futuro/domain.py` y `utils/permisos.py`.

## Revisión visual pendiente en navegador

La herramienta de navegador de esta sesión no tiene superficies conectadas; AppTest no renderiza CSS ni simula tamaños reales. Por tanto, las siguientes pruebas visuales quedan pendientes de ejecutar en un navegador y no se presentan como aprobadas.

Abre las herramientas del navegador, activa la vista adaptable y configura cada ancho:

| Pantalla | 375 px | 768 px | Escritorio (1280 px o más) |
| --- | --- | --- | --- |
| Login | Una tarjeta, campos sin desbordar, botón amarillo completo, pestañas legibles. | Tarjeta centrada y pasos debajo. | Tarjeta centrada con espacio alrededor. |
| Navegación | Se abre con el botón de la barra lateral; controles táctiles de al menos 44 px. | Menú accesible incluso si Streamlit lo contrae. | Menú lateral; selección lavanda y borde morado. |
| Identidad y sesión | Nombre y rol legibles; Cerrar sesión al final del menú y alcanzable mediante desplazamiento si hace falta. | Igual. | Igual. |
| Registro de casos | Cada caso en ficha con campos y badge; sin desplazamiento horizontal del listado. | Tabla de casos. | Tabla de casos con espacio entre columnas. |
| Detalle / Tarifas | Formularios y botones sin cortar, fechas chilenas. | Columnas con etiquetas legibles. | Formularios en columnas, espacio entre secciones. |
| Dashboard | Filtros plegables, gráficos en una columna, badges sin cortar. | Tarjetas y gráficos legibles en columnas. | Cuadrícula de gráficos y filtros superiores. |

Repite como Cliente y Administración. Cliente: solo Nueva solicitud, sin Casos, Tarifas ni Dashboard, incluso con `?pagina=Dashboard`. Administración: las tres páginas, Registro de casos y Tarifas y servicios. Envía solicitudes exclusivamente con datos ficticios en un ambiente de prueba si deseas comprobar persistencia real.

Con datos: colores oficiales iguales en lista, detalle y dashboard; Por revisar = Solicitud + En revisión; En desarrollo = Aceptada + En seguimiento. Sin datos: mensajes de bienvenida/estado vacío, KPI de casos en cero y sin ejes vacíos en los gráficos. Comprueba que los textos largos se ajustan, el foco de teclado es visible y la preferencia de movimiento reducido desactiva las animaciones.

En una ventana privada del sitio publicado comprueba además que no se ven Share, GitHub, lápiz, menú ni pie nativo. Esa comprobación en Community Cloud sigue pendiente; el CSS no puede controlar elementos que la plataforma renderice fuera de la app.
