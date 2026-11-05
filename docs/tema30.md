# Sistema visual unificado · Prompt 30

Cambios solo de presentación. Sin nuevas dependencias, migraciones SQL ni cambios en datos, cálculos, campos, consentimiento o permisos de las páginas existentes. El logo original y los generadores de cotización Word/PDF y ficha PDF se conservan. La nueva guía visual es administrativa.

## Auditoría previa

Streamlit instalado: **1.65.0**. Ya permite `st.navigation(position="top")`, páginas ocultas con URL estable, `st.fragment(run_every=...)`, componentes nativos y componentes v2. Se mantiene esa navegación: cinco secciones administrativas; dos para clientes. «Mi cuenta» ya era un popover, no otra página.

| Pantalla | Inconsistencia encontrada | Ajuste |
|---|---|---|
| Hoy | Encabezado general de 288 px y margen del marco sumado al de la barra; tarjetas con reglas acumuladas | Es el único encabezado grande (mínimo 190 px); tarjetas de acción conservadas |
| Nueva solicitud / formulario público / Solicitar servicio | Encabezado y tarjetas distintos al Dashboard; reglas duplicadas y espacio superior excesivo | Misma base de encabezado, tarjeta y campos; ilustración en la cabecera; no se cambian pasos ni campos |
| Casos y cotizaciones | Espaciados y tarjetas con sucesivas sobrescrituras; tablas con reglas dispersas | Encabezado compacto, tabla accesible con fichas en celular, mismos filtros y detalle |
| Compartir | Contenedores de enlaces/QR con estilos particulares; riesgo de desborde | Imágenes limitadas al contenedor y bloques de código con scroll propio |
| Dashboard | Encabezado más compacto que el resto; cuatro KPI con otra altura | Encabezado común, cuatro tarjetas; se conserva su cuadrícula de dos KPI por fila en celular |
| Mis documentos / Mi perfil | Encabezado con prefijo de marca duplicado; sin ilustración propia | Etiqueta normalizada y pequeña ilustración integrada; perfil y documentos intactos |
| Login | Panel y tarjeta con reglas de varias etapas; logo raster y favicon muy pesado | Panel de marca, ilustración y tarjeta comunes; favicon SVG de 1 KB |
| Mi cuenta | Ya existía; sin preferencia visual | Conserva identidad y cierre de sesión; agrega Modo ligero y enlace a la guía solo para Administración |
| Todas | CSS de 60,8 KB, efectos continuos, múltiples radios y alturas; logo sobre caja blanca | Tema único, fondo estático, escala de espaciado, logo vectorial transparente y controles táctiles |

Los encabezados compactos tienen mínimo 120 px (112 px en celular); crecen si el texto necesita más espacio, para no cortarlo. Hoy usa 190 px, o 170 px en celular. El contenido tiene un máximo de 1200 px y comienza 16 px debajo de la barra de 64 px. Sin barra, el margen superior es 24 px. Son reglas implementadas; su resultado exacto en navegador está pendiente de revisión visual.

## Archivos y arquitectura

- `ui/tema.py`: variables, todo el CSS del portal y funciones de encabezado, tarjetas, acciones, listas, chips, estados, botones, avisos, tablas, cronología, avatar y esqueletos. Documenta los selectores internos de Streamlit sobrescritos.
- `utils/estilos.py` y `utils/componentes.py`: adaptadores de compatibilidad; importaciones existentes apuntan a la misma implementación, sin copiar CSS.
- `servicios/imagenes.py`: catálogo central y lectura de SVG con caché. `assets/marca-*.svg` y cinco `assets/ilustracion-*.svg`: recursos locales ligeros, sin imágenes externas.
- `utils/modo_ligero.py`: preferencia visual por cuenta/navegador en localStorage; detección de menos movimiento y ahorro de datos, sin temporizador ni consultas. No almacena credenciales.
- `paginas/guia_estilo.py`: muestras con datos ficticios; entrada protegida por rol. Se abre desde Mi cuenta → Guía de estilo y no aparece como sexta sección superior.
- `utils/navegacion_portal.py`, `utils/permisos.py`: registro estable de esa ruta y protección administrativa; navegación de las páginas previas conservada.
- `app.py`, `mente_futuro/presentation.py`: título y favicon pequeños; el logo usado en documentos sigue siendo el original.
- `mente_futuro/ui.py`, `paginas/formulario.py`: activación del modo visual y colocación de ilustraciones, sin cambios de autenticación o guardado.
- `tests/test_tema30.py`: peso, contraste, recursos locales, compatibilidad y protección de la guía. Tres pruebas existentes de menú/cuadrícula se ajustan al nuevo diseño.
- `tests/auditar_tema30.py` y `docs/evidencias_tema30/`: medición reproducible de antes/después con repositorio simulado.

Excepción intencional: el CSS de `quote_html` permanece en el documento imprimible, porque se pidió expresamente no modificar las cotizaciones ni las fichas. Ningún otro archivo de interfaz conserva `<style>` o atributos `style=`.

## Apariencia y modo ligero

Se conservan celeste, morado, amarillo y azul marino. El degradado de controles usa derivados más oscuros para que el texto blanco tenga contraste AA; los tonos originales aparecen en decoración y superficies claras. Las combinaciones de texto, estados y extremos del degradado se verifican con luminancia WCAG (mínimo 4,5:1). No se ha hecho una auditoría completa del contraste compuesto de todos los píxeles en navegador.

No se descargan fuentes web: Poppins e Inter se usan si están disponibles; en caso contrario, la fuente del sistema. El fondo usa degradados y puntos SVG, sin blur ni animación continua. Solo hay transiciones breves de hover/foco. Los esqueletos son estáticos.

Mi cuenta → **Modo ligero** elimina manchas, puntos e ilustraciones decorativas. El navegador también lo activa si solicita menos movimiento o ahorro de datos. Se recuerda en ese navegador, por cuenta, sin sincronización entre equipos. Si el navegador bloquea el almacenamiento, la app sigue funcionando. La preferencia no interviene en la sesión ni en los permisos.

El SVG de cabecera es una representación provisional del motivo existente; reemplazarlo por el logo transparente oficial cuando lo entregue la socia. El JPG original se conserva en login y documentos.

## Medición y límites

Los JSON guardados son evidencia de **AppTest local con datos ficticios**. Miden tiempo de ejecución Python y CSS emitido, no transferencia real, renderizado del navegador, latencia de Supabase ni arranque de Community Cloud. La primera medición incluye el marco y la navegación; la segunda usa cachés. Las diferencias pequeñas pueden deberse al equipo y a procesos concurrentes; no prueban una mejora del tiempo visible para clientes. La tabla usa la medición final sin la suite ejecutándose a la vez. Se conserva además `despues_concurrente.json`, para mostrar el efecto de esa carga y no descartar silenciosamente resultados.

La tabla numérica detallada está al final. No se promete que todas las pantallas carguen más rápido: donde una muestra empeora, se conserva el número real. Queda pendiente medir carga y scroll en navegador y celular físico.

No se agregó ninguna consulta de negocio. Con caché caliente la auditoría simulada observa como máximo tres operaciones de datos por pantalla (incluida lectura de perfil; excluye Auth). **Esto no demuestra el límite de tres consultas en carga fría real**. Por ejemplo, Nueva solicitud interna conserva las tres lecturas de sugerencias, más perfil y catálogos/configuración si no están cacheados. Reducirlas exige agrupar consultas existentes; se deja pendiente para no cambiar datos/lógica/SQL en este trabajo visual. Hoy/Dashboard/Casos conservan su lectura agrupada e intervalos anteriores.

## Cómo probar

1. Ejecuta `python -m streamlit run app.py` desde la carpeta del proyecto. No necesitas SQL ni instalar librerías nuevas.
2. Como Administración: abre Hoy, Nueva solicitud, Casos y cotizaciones, Compartir y Dashboard. Debes ver barra oscura, marca sin caja blanca y las cinco opciones actuales. Solo Hoy tiene cabecera grande.
3. En Mi cuenta activa Modo ligero, recarga y vuelve a entrar: debe mantenerse en el mismo navegador. Desactívalo; si el sistema pide menos movimiento/ahorro, la decoración sigue reducida.
4. En Mi cuenta abre Guía de estilo. Debes ver componentes y ejemplos ficticios, sin escrituras ni envíos.
5. Como cliente: solo Solicitar servicio y Mis documentos. La URL `/guia-estilo` debe volver a Mis documentos; no mostrar componentes administrativos.
6. Sin sesión: abre `?vista=solicitud`, completa los pasos y prueba errores. El guardado, consentimiento y datos son los de antes. Abre `?vista=acceso` para revisar login.
7. En DevTools → dispositivo personalizado prueba **375 × 844**, **768 × 1024**, **1280 × 900**, zoom 100 %. Recorre cada pantalla y todos los pasos del formulario; también detalle de un caso, cotización, venta, documentos y pestaña Tarifas y servicios.
8. Comprueba: nada se tapa bajo la barra; no hay scroll horizontal de la página; los textos se leen completos; tablas/código se desplazan dentro de su contenedor; botones ≥44 px; menú móvil abre, navega y cierra. En celular los campos se apilan y los cuatro KPI del Dashboard quedan en dos filas. En tableta puede aparecer Más, sin perder destinos.
9. Repite la recarga con cada rol, activa la opción del navegador «reducir movimiento» y prueba Modo ligero con el almacenamiento bloqueado. La navegación y formularios deben seguir disponibles.
10. Genera Word/PDF y ficha con datos ficticios: deben mantener el formato anterior, sin las nuevas ilustraciones del portal.

### Estado de las pruebas

| Prueba | Resultado / alcance |
|---|---|
| Nueve pantallas principales, datos ficticios, primera carga y recarga | AppTest sin errores; evidencia JSON |
| Menú de cinco opciones administrativas y dos de cliente | Verificado en AppTest |
| Guía solo Administración y cliente por URL | Verificado en AppTest |
| Modo ligero manual sin nuevas lecturas de negocio | Verificado en AppTest; persistencia localStorage y señales del dispositivo requieren navegador |
| CSS <20.000 bytes, SVG <10.000 bytes, combinaciones de contraste | Pruebas automáticas |
| Cotizaciones, ficha, guardado y roles existentes | Suite de regresión Python con datos ficticios |
| 375 px: todas las pantallas y roles | **Pendiente visual**; reglas responsive presentes, no equivalente a captura |
| 768 px: todas las pantallas y roles | **Pendiente visual** |
| 1280 px: todas las pantallas y roles | **Pendiente visual** |
| Safari, Android y navegador interno de redes; fluidez en celular modesto | **Pendiente en dispositivo real** |

La automatización de navegador terminó porque no pudo determinar la URL actual con suficiente certeza para aplicar su política de seguridad. No se continuó mediante otro control de navegador. No hay capturas ni se declara una revisión visual que no ocurrió.

## Imágenes para pedir a la socia

| Recurso | Formato / tamaño recomendado | Uso |
|---|---|---|
| Logo oficial horizontal transparente | SVG limpio sin scripts ni fuentes externas; alternativa PNG transparente 800 × 240 | Barra superior |
| Ampolleta/cerebro oficial sin texto | SVG cuadrado; alternativa PNG 256 × 256 | Favicon y marca de agua |
| Una ilustración principal oficial | SVG <10 KB o WebP 1200 × 800, ≤150 KB | Hoy, bienvenida y formulario |
| Tres o cuatro imágenes de apoyo | SVG <10 KB o WebP 640 × 480, ≤100 KB cada una | Sin datos, documentos, confirmación |
| Descripción breve y autorización de uso | Una frase por imagen | Texto alternativo y procedencia |

No son necesarias para que la app funcione: ya hay sustitutos vectoriales. Evitar fotos de personas sin consentimiento. Para reemplazar recursos basta actualizar el catálogo de `servicios/imagenes.py`, sin tocar formularios ni documentos.

## Repetir las pruebas locales

```powershell
python -m unittest discover -s tests
python tests/auditar_tema30.py output/tema30_actual.json
```

La auditoría usa los dobles de prueba existentes; no consulta ni escribe en Supabase. Crear `output` si no existe. Los resultados no son mediciones de producción.

## Resultados numéricos

| Recurso | Antes | Después |
|---|---:|---:|
| CSS portal | 60.825 bytes | 19.444 bytes |
| CSS componentes aislados | 1.563 bytes | 500 bytes |
| CSS total | 62.388 bytes | 19.944 bytes |
| Favicon | 89.161 bytes | 1.039 bytes |
| Marca barra superior | 66.728 bytes | 1.474 bytes |
| Logo original login/documentos | 66.728 bytes | 66.728 bytes |

Cada pantalla emite el mismo CSS del portal indicado arriba. Las ilustraciones pesan 1.039–1.493 bytes por SVG. El conjunto completo de recursos nuevos pesa 9879 bytes; incluso con el logo original se mantiene bajo 400 KB por pantalla. Son tamaños de archivos sin comprimir, no un waterfall de transferencia.

| Pantalla / rol | Primera antes → después (s) | Repetida antes → después (s) | Operaciones simuladas con caché antes → después |
|---|---:|---:|---:|
| Hoy / admin | 2.679 → 1.238 | 0.105 → 0.070 | 1 → 1 |
| Nueva solicitud / admin | 0.507 → 0.491 | 0.072 → 0.043 | 1 → 1 |
| Casos y cotizaciones / admin | 0.570 → 0.515 | 0.104 → 0.084 | 2 → 2 |
| Compartir / admin | 0.464 → 0.453 | 0.070 → 0.041 | 3 → 3 |
| Dashboard / admin | 0.618 → 0.623 | 0.211 → 0.156 | 1 → 1 |
| Solicitar servicio / cliente | 0.387 → 0.284 | 0.061 → 0.032 | 1 → 1 |
| Mis documentos / cliente | 0.441 → 0.360 | 0.059 → 0.041 | 3 → 3 |
| Formulario / publico | 0.331 → 0.329 | 0.065 → 0.027 | 0 → 0 |
| Login / publico | 0.322 → 0.350 | 0.052 → 0.053 | 0 → 0 |

Hay variabilidad y algunas muestras tardan más; no se etiqueta el criterio de carga como aprobado. Se necesita medición real secuencial en navegador para confirmarlo. Las lecturas simuladas no incluyen consultas internas de cada RPC, Auth ni configuración pública sustituida en pruebas.

**Suite final:** 263 pruebas, 147,150 s, OK. Incluye cotizaciones, documentos, permisos, recargas y seis pruebas nuevas del tema. No equivale a pruebas de RLS contra la base publicada ni a revisión visual.
