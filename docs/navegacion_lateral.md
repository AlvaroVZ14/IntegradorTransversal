# Navegación lateral nativa · Mente y Futuro

## Cómo verla

Abre **http://127.0.0.1:8502** y recarga con **Ctrl + F5**. La instancia local sigue disponible con su conexión existente a Supabase. Inicia sesión con tu cuenta habitual. Estos cambios son locales; no se publicaron en Community Cloud.

Para iniciar el proyecto desde su carpeta si no está ejecutándose:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8502
```

No se modificaron las credenciales ni se incluyen secretos en el ZIP.

## Tecnología y dependencias

Se verificó la instalación local: **Streamlit 1.65.0**. Tiene `st.navigation`, `st.Page`, íconos Material, `st.logo` y `st.page_link`. Se usan esas APIs nativas; no se añadió `streamlit-option-menu` ni ninguna dependencia nueva. `requirements.txt` se conserva.

El menú se construye después de comprobar Supabase Auth y consultar el perfil real. `allowed_pages` y `guard_route`, en `utils/permisos.py`, siguen siendo la fuente de autorización. La navegación nativa recibe únicamente las páginas que ese rol permite. No hay páginas administrativas ocultas registradas para clientes.

Referencias oficiales: [st.navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation), [st.Page](https://docs.streamlit.io/develop/api-reference/navigation/st.page) y [st.logo](https://docs.streamlit.io/develop/api-reference/media/st.logo).

Streamlit oculta el menú lateral nativo si tiene una sola página. Por eso el cliente recibe **un único `st.Page`**, y ve su enlace mediante `st.page_link`, con el mismo ícono Material y estilo. No se registraron páginas adicionales para forzar un menú. Ya no se utiliza `st.radio`.

## Qué debería ver cada cuenta

| Cuenta | Páginas y grupos visibles |
| --- | --- |
| Administración | GESTIÓN: Nueva solicitud y Casos y cotizaciones. ANÁLISIS: Dashboard. Se conserva Dashboard como entrada inicial. |
| Cliente | GESTIÓN: únicamente Nueva solicitud. No hay ANÁLISIS, Dashboard, Casos ni Tarifas. |
| Sin sesión o sin poder verificar el perfil | Pantalla de ingreso o mensaje de error, sin navegación privada registrada. |

La barra tiene fondo #0B2545 → #1B2F6B y luz morada tenue abajo. El logo original aparece arriba sobre blanco, con esquinas redondeadas. Los enlaces tienen íconos Material de 24 px y una altura mínima de 48 px. El activo tiene texto blanco en negrita, degradado azul/morado, ícono amarillo y una barra amarilla a la izquierda. La pequeña capa marina sobre el degradado mejora el contraste sin sustituir sus colores base.

Abajo aparecen la tarjeta de usuario, avatar con iniciales, nombre, rol y Cerrar sesión con ícono. **Actualizar información se eliminó.** Actualizar se conserva únicamente dentro del Dashboard, con su callback y caché originales.

La barra activa, la negrita y `aria-current="page"` en el menú nativo distinguen la selección sin depender solamente del color. El enlace único del cliente tiene además una indicación accesible de página actual. Los enlaces y Cerrar sesión tienen foco visible.

## Paleta clara opcional

En `utils/estilos.py` cambia una sola constante:

```python
TEMA_BARRA_LATERAL = "claro"  # Predeterminado: "oscuro"
```

Ambas paletas están declaradas como variables CSS `--mfy-nav-dark-*` y `--mfy-nav-light-*` en `:root`. Los alias `--mfy-nav-*` seleccionan la paleta. En claro, el fondo es blanco, el texto es marino y el activo usa lavanda con indicador e ícono morados. No cambia ningún permiso ni comportamiento.

## Celular y movimiento reducido

Debajo de 768 px, el menú abierto ocupa `100vw - 20px`, hasta 420 px de ancho: a 375 px ocupa 355 px. Se conserva el botón nativo para abrirlo y cerrarlo.

La navegación nativa ya cierra el menú en dispositivos móviles. Un componente pequeño complementa ese comportamiento por ancho de pantalla y para el enlace único del cliente: tras pulsar un enlace, utiliza el botón nativo de cierre si la barra sigue abierta. Respeta clics modificados para abrir otra pestaña, no evita la navegación y no modifica rutas, formularios ni datos.

El componente usa selectores internos comprobados en Streamlit 1.65 (`stSidebarNavLink`, `stPageLink-NavLink`, `stSidebarCollapseButton`). Si esos controles no existen, no hace nada. Devuelve una limpieza del listener para no acumular eventos entre páginas. Los selectores CSS internos están comentados en `utils/estilos.py`.

Las transiciones del menú duran 200 ms. `prefers-reduced-motion` desactiva su desplazamiento y sus transiciones, conservando el estado activo y el foco.

## Archivos completos

- `app.py`: registro según rol, navegación nativa, logo, enlace único del cliente y cierre de sesión. Los parámetros antiguos `?pagina=...` y `pending_navigation` se resuelven mediante la misma guardia existente.
- `utils/navegacion.py`: metadatos de páginas, grupos e íconos; complemento de cierre móvil.
- `utils/estilos.py`: paletas, barra lateral, enlaces activos, foco, logo y adaptación móvil. Todo el CSS sigue centralizado.
- `utils/componentes.py`: avatar de iniciales y tarjeta de usuario; se retiraron los íconos de texto anteriores.
- `paginas/nueva_solicitud.py`, `paginas/gestion.py`, `paginas/dashboard.py`: entradas nativas al final de los archivos, que llaman las funciones de página existentes. El repositorio se verifica y renueva desde `app.py` en cada ejecución; las páginas administrativas conservan sus guardias iniciales.
- `tests/test_app.py`: recorridos adaptados al registro y cambio de página nativos, más pruebas de rutas privadas, cambio de rol y cierre de sesión.
- `tests/test_menu_movil.mjs`: escenarios aislados del cierre complementario.

El proyecto completo está en `output/mente-futuro-navegacion-lateral.zip`, sin secretos ni directorios temporales.

## Pruebas realizadas

```powershell
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
node tests/test_menu_movil.mjs
```

**59 pruebas Python aprobadas** y **10 escenarios de cierre móvil aprobados**. Node se necesita solamente para esa prueba de JavaScript, no para ejecutar la app.

Las pruebas comprueban que:

- Administración registra tres páginas con los íconos correctos; Cliente registra solo Nueva solicitud, sin radios ni botón Actualizar información.
- Un cliente no puede seleccionar archivos de páginas privadas ni abrirlos utilizando los identificadores de rutas de una cuenta administrativa.
- Al pasar una sesión de Administración a Cliente, las páginas privadas desaparecen antes de leer casos, ventas u otros perfiles.
- Si falla la consulta del perfil, no se conserva el registro privado anterior. Cerrar sesión también lo elimina.
- Solicitud, cotización, venta, filtros, Actualizar, caché, consentimiento y validaciones mantienen sus recorridos.
- El cierre móvil no reabre una barra que la navegación nativa ya cerró, no actúa en escritorio y no acumula listeners.

Se compararon con la entrega anterior y permanecen idénticos los archivos de consultas, cálculos, caché, permisos, estados y dependencias. No se ejecutó SQL ni se escribieron datos ficticios en Supabase.

Se calcularon contrastes de los colores definidos: blanco sobre el extremo marino 12,61:1; texto secundario 8,30:1; blanco sobre los extremos del activo al menos 4,88:1; ícono amarillo al menos 3,23:1. Esto comprueba los colores; no sustituye una inspección visual renderizada.

## Revisión manual pendiente

La herramienta respondió “No browser is available”; AppTest no renderiza CSS. El diseño a tamaños reales y el cierre en un navegador real quedan pendientes de inspección y no se presentan como pruebas visuales aprobadas.

1. Como Administración, recorre las tres páginas. Comprueba los grupos, el activo, los íconos, la tarjeta de usuario y Cerrar sesión al final. Prueba también enviar una solicitud ficticia: debe continuar al detalle del caso como antes.
2. Como Cliente, comprueba que solo se ve Nueva solicitud. Intenta `/casos`, `/dashboard`, `?pagina=Dashboard` y `?pagina=Casos%20y%20cotizaciones`: nunca debe mostrar contenido privado. Una ruta nativa no registrada puede mostrar el aviso de página inexistente de Streamlit y volver a Nueva solicitud.
3. A **375 px**, abre el menú con el control nativo: debe ocupar casi toda la pantalla, mostrar controles amplios y cerrarse al elegir un enlace, incluido el único del cliente.
4. A **768 px** y en **escritorio**, comprueba el ancho, el logo, los textos completos y que el menú pueda seguir abierto al navegar. En ventanas de poca altura, todo debe seguir siendo alcanzable por desplazamiento.
5. Con Tab y Enter, selecciona enlaces y Cerrar sesión. Comprueba el contorno de foco. Activa movimiento reducido: no debe haber desplazamiento al hover ni transiciones.
6. En la paleta clara, comprueba fondo blanco, activo lavanda e indicador morado. Vuelve a `"oscuro"` para conservar el valor predeterminado.
