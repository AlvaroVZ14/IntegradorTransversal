# Prompt 34 · Hoy decorado, fluido y compacto

Implementación sobre los prompts 30 y 41. No cambia permisos, estados, precios, datos de clientes ni envío de mensajes. No hay dependencias ni imágenes nuevas.

## Antes y después

| Antes | Ahora |
|---|---|
| Encabezado genérico con fecha numérica | Saludo y nombre, fecha larga en español, frase según pendientes, ilustración existente y Nueva solicitud |
| Espacios de componentes invisibles antes de la cabecera | Los puentes de sesión/apariencia/navegación se retiran del flujo visual solo en Hoy; siguen funcionando |
| Tres tarjetas blancas con contexto limitado | Celeste, morado y amarillo; ícono grande, cifra y ayuda breve. Con cero pasan a verde suave y Al día |
| Solicitudes y seguimientos en listas separadas | Para hacer ahora: lista común por días de espera, máximo cinco acciones, con Ver todas |
| Texto corrido del cliente | Tarjeta con avatar estable por cliente, código, nombre, servicio, temática, modalidad, estado y antigüedad |
| Compartir antes de los pendientes | Franja al final con Copiar enlace y Más opciones |
| Sin cronología breve | Últimos cinco eventos reales, con ícono y tiempo relativo |
| Refresco de datos cada 30 s | Un fragmento cada 60 s, con la misma lectura agrupada y caché corto |

Orden: encabezado → tres acciones → Para hacer ahora → actividad reciente → compartir. Las funciones anteriores de completar datos, registrar pagos, recordar pagos, cerrar/deshacer y revisar correos se conservan en **Otros pendientes**, dentro de la sección de acciones. Las sugerencias posteriores al cierre también permanecen.

Las cifras de las tarjetas no vuelven a mostrarse en el encabezado. Distintos indicadores pueden tener el mismo valor (por ejemplo tres ceros); no se duplica el mismo indicador en varios bloques. El encabezado usa una frase sin total, porque algunos pendientes pueden corresponder al mismo caso.

## Comportamiento

- Se reutiliza `pendientes`: los criterios de solicitud, seguimiento, pausa después de contactar, pago y cierre son los anteriores.
- La lista común ordena por mayor antigüedad; solicitudes usan fecha de creación y seguimientos los días desde la emisión. El empate se resuelve de forma estable por fecha e identificador.
- Cotizar y Hacer seguimiento mantienen los flujos previos. Ver caso abre el detalle. Ver todas abre el registro con el filtro combinado Para hacer ahora, sin limitar a cinco.
- Los avatares usan iniciales escapadas y una de tres combinaciones estables según el nombre; no descargan imágenes.
- La fecha y los tiempos se calculan en Chile. Si un registro solo tiene fecha, se muestra Hoy o Hace N días, sin inventar una hora.
- La actividad combina solicitudes, cotizaciones, aceptación/rechazo, ventas, cierres y documentos de cliente disponibles. Venta y evento de venta se muestran una vez. Se omiten eventos deshechos y documentos eliminados o todavía pendientes de subir.
- Si no hay acciones de cotización/seguimiento se muestra la ilustración Todo al día. Si quedan pagos o datos, el texto lo aclara y conserva Otros pendientes.
- Copiar enlace usa Clipboard API y un segundo intento compatible con navegadores que la bloquean. Solo confirma si la copia resultó. Si ambos fallan, ofrece el texto actual para copiarlo manualmente; no muestra una confirmación falsa.

## Fluidez, caché y límites

Se conserva `mf_lectura_en_vivo('hoy')`: **una RPC de datos de negocio por ciclo**, además de la validación de sesión habitual. El compartir usa la URL del mismo snapshot. No se añaden lecturas por tarjeta, avatar, actividad o clic en copiar.

La lectura usa el caché existente de 30–60 s y `dashboard_revision`; las escrituras de casos/cotizaciones/ventas invalidan la revisión como antes. Las pruebas verifican que regresar a Hoy obtiene la escritura sin esperar al ciclo.

El fragmento de 60 s incluye el contenido de Hoy, también encabezado/tarjetas, para que sus cifras no se queden antiguas mientras se actualiza la lista. No recarga la navegación ni el navegador. Es una ampliación del refresco pedido solo para lista y actividad: todo usa el mismo snapshot y conserva consistencia. Los diálogos suspenden ese refresco. Los clics que navegan o cierran un diálogo conservan el rerender de aplicación necesario del flujo existente; no se promete que toda interacción evite ese rerender.

Los esqueletos/spinner existentes se usan en la primera carga; los siguientes ciclos conservan la lectura anterior si falla la red. No se agregan pantallas completas de carga. El mecanismo de Deshacer conserva su temporizador propio, sin consultas de datos por segundo.

CSS general y componentes: **20.384 bytes**. CSS adicional exclusivo de Hoy: **3.074 bytes**; solo se carga ahí. Las ilustraciones ya existentes pesan menos de 2 KB y se leen con caché. No se agregan fuentes, librerías ni animaciones continuas. Modo ligero y reducir movimiento siguen aplicándose.

Cabecera: mínimo aproximado de 200 px en computador y 150 px en móvil; puede crecer si el nombre o el texto lo requieren para no cortarlos. En menos de 430 px se oculta la ilustración y su espacio reservado. El atajo flotante solo aparece en móvil, mide 48 px y respeta el área segura.

## SQL: único paso pendiente en la base publicada

La app funciona con el snapshot anterior, pero **los documentos de cliente no aparecen en la actividad hasta aplicar la ampliación SQL**. No se ejecutó en Supabase publicado: no hay acceso de administración de base de datos disponible desde este entorno.

1. Abre Supabase → SQL Editor → New query.
2. Pega el archivo completo `supabase/migrations/202611050001_hoy_actividad.sql` y pulsa Run.
3. Debe aparecer **Success. No rows returned**. Después abre Hoy y espera un minuto o vuelve a entrar. Las subidas recientes de clientes ya podrán formar parte de los cinco últimos eventos.

Este SQL solo reemplaza la función de lectura, sin actualizar ni borrar tablas o registros. Conserva `SECURITY INVOKER`, `es_admin()`, la validación de vista y las restricciones para clientes/visitantes. Solo añade a Hoy hasta cinco metadatos de documentos del cliente; no devuelve rutas de Storage, nombres de archivo ni contenido.

Compatible con la ausencia de la tabla Documentos; si no existe, devuelve lista vacía. Si el campo origen todavía no existe, no inventa subidas del cliente. Para subir documentos siguen siendo necesarias las migraciones del módulo anterior.

Para revertir solo la ampliación: ejecuta `supabase/rollback/202611050001_hoy_actividad.sql`. Restaura el snapshot anterior; no elimina documentos, casos ni ventas. El diseño de Hoy sigue funcionando.

## Hoja de cálculo: lugar preparado

No está aplicada la integración del Prompt 38 en este proyecto. Por eso **no se muestra un aviso real de hoja sin sincronizar**, ni se crea una sincronización ficticia.

El adaptador `avisos_automatizacion` acepta, cuando exista esa integración, `automatizaciones.hoja_calculo` en el snapshot con `integrada: true`, `ultima_sincronizacion` ISO y `estado_correo`. Solo entonces avisa si pasan más de 24 horas o falla el aviso. Sin integración, no muestra nada. Es un contrato para el Prompt 38, no una configuración que la socia deba rellenar ahora. Los correos de cotización con problemas siguen disponibles en Otros pendientes como antes.

## Archivos completos modificados

- `paginas/hoy.py`: estructura compacta, lista única, cronología, atajos y fragmento de 60 s; acciones anteriores conservadas.
- `servicios/hoy_vista.py`: funciones puras para fecha, urgencia, actividad y avisos futuros.
- `servicios/hoy.py`: filtro combinado que reutiliza las mismas reglas del registro.
- `paginas/gestion.py`: ayuda del selector ajustada al nuevo filtro.
- `ui/tema.py`: CSS exclusivo de Hoy, encabezado reutilizable, tarjetas con contexto y avatar por cliente; todo en el tema común.
- `paginas/compartir.py`: franja compacta, Más opciones y URL reutilizada, sin consulta extra.
- `utils/mensaje_listo.py`, `utils/mensaje_listo.js`: copia y alternativa manual con texto actualizado; JavaScript cacheado.
- `supabase/migrations/202611050001_hoy_actividad.sql` y su rollback: lectura ampliada de documentos, sin cambios de datos.
- `tests/test_hoy34.py`, `tests/test_copiar34.mjs`: escenarios nuevos.
- `tests/test_hoy_registro25.py`: adapta las expectativas a la lista común y al enlace Más opciones.
- `tests/test_en_vivo_sql.mjs`: prueba el snapshot nuevo en PostgreSQL efímero con casos/documentos ficticios, permisos y reversión.

## Pruebas y qué debería verse

Suite completa: **278 pruebas Python aprobadas (182,302 s)**. También pasaron los tres escenarios JavaScript del portapapeles y la prueba PostgreSQL efímera de snapshot, permisos y rollback. No son mediciones de velocidad en producción.

| Escenario | Resultado automático / resultado esperado en pantalla |
|---|---|
| Sin solicitudes | Sin errores; tres tarjetas en cero y Al día, ilustración y sin lista de acciones |
| Una solicitud | Una acción Cotizar, con avatar/código/estado/antigüedad y Ver caso |
| Diez solicitudes | La tarjeta cuenta diez; solo cinco acciones ordenadas por espera; Ver todas conserva las diez en el registro |
| Cotización sin respuesta >5 días | Se mezcla en la lista por urgencia; Hacer seguimiento abre el mensaje preparado y no registra contacto hasta confirmarlo |
| Pago / dato faltante / cierre / correo | Acciones anteriores comprobadas; se encuentran en Otros pendientes |
| Escribir y volver a Hoy | Caché invalidado por revisión: tarjetas y lista muestran los datos nuevos |
| Refrescar sin cambios | Reutiliza lectura del ciclo, sin una consulta por elemento |
| Actividad | Máximo cinco, orden temporal, venta sin doble evento y solo documentos de cliente disponibles |
| Hoja sin sincronizar | Prueba del contrato con datos ficticios: aviso amarillo después de un día; en producción no aparece sin Prompt 38 |
| Copiar enlace | JS probado con API normal, segundo intento y bloqueo; solo confirma copias exitosas; alternativa manual ofrece el texto actual |
| PostgreSQL local | 1.001 casos y nueve fixtures de documento; cinco documentos recientes sin rutas, exclusión de socia/pendientes, bloqueo de cliente/visitante y rollback sin pérdida |
| 375 / 768 / 1280 px | **Pendiente revisión visual**; no se presentan capturas de navegador como si se hubieran tomado |

El acceso automatizado al navegador devolvió «The browser access host is unavailable». Se completaron AppTest, pruebas JavaScript y PostgreSQL efímero; no equivalen a medir el CSS real, el scroll ni el portapapeles de un teléfono físico.

Para la revisión manual: abre Hoy como Administración con cada ancho, zoom 100 %, desplázate hasta Compartir y comprueba que no hay scroll horizontal ni elementos tapados. Prueba menú, Nueva solicitud y atajo flotante; revisa que tarjetas/acciones se apilen en móvil. Pulsa Copiar enlace y pégalo en Notas; debe ser el formulario público. Abre Hacer seguimiento y espera un minuto: lo escrito debe conservarse.

Pruebas locales, sin usar datos reales:

```powershell
python -m unittest discover -s tests
node tests/test_copiar34.mjs
node tests/test_en_vivo_sql.mjs
```

La prueba SQL usa el PGlite que ya existe en el entorno de desarrollo; no se instala en Streamlit ni se incorpora una dependencia de producción. Sus fixtures históricas desactivan temporalmente un trigger solo dentro de esa base efímera para fijar fechas/origen; el SQL de producción no desactiva ningún trigger ni altera validaciones de subida.
