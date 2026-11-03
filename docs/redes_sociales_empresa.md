# Redes sociales de la empresa — Prompt 27

## Activación

1. Ejecutar completo y una sola vez `supabase/migrations/202611020004_redes_sociales.sql` en Supabase → SQL Editor, después de las migraciones existentes (incluida Mis documentos).
2. Usar la versión actual de la app y recargar. El catálogo público cambia a versión 4; su caché anterior puede durar hasta 60 segundos.
3. No hay dependencias ni secretos nuevos. Se reutilizan ReportLab, pypdf y los componentes de Streamlit ya instalados.

No se ejecutó SQL en Supabase publicado ni se enviaron solicitudes o documentos reales. Las pruebas SQL usan PostgreSQL efímero y las pruebas de interfaz usan cuentas ficticias.

## Decisión de datos

El esquema no tiene una tabla independiente de empresas/clientes: antes, las sugerencias se obtenían del último caso por empresa y correo. Se agrega:

- `mf_casos.redes_sociales`: JSON de cinco campos opcionales. Cada caso conserva lo que se solicitó y sus correcciones administrativas. No se altera ningún valor comercial existente ni se borra ningún caso.
- `mf_empresas_redes`: registro reutilizable, único por correo normalizado y nombre de empresa normalizado. Tiene `id`, `correo`, `empresa`, `empresa_clave`, `redes_sociales`, `confirmadas` y `updated_at`. Un envío posterior actualiza el mismo registro, conservando las copias históricas de los casos anteriores.
- `mf_mis_redes_empresa(p_empresa)`: consulta privada para precargar el formulario y reutilizar en el futuro perfil. El correo se obtiene de Auth y debe estar confirmado; no se acepta un correo arbitrario como parámetro. Con varias empresas se exige indicar cuál, para evitar mezclar sus datos.

Un registro anónimo puede actualizar otro registro anónimo de esa empresa/correo, sin leerlo. **Nunca sobrescribe uno confirmado por Administración o por el propio cliente autenticado**. La precarga de una cuenta usa únicamente los registros confirmados; una solicitud anónima aislada no altera el perfil de otra persona. Las redes igualmente quedan guardadas en el caso recibido. Administración puede revisarlas y corregirlas.

La tabla reutilizable no concede acceso directo a clientes ni visitantes. Solo Administración puede consultarla directamente; las escrituras ocurren por los triggers de casos autorizados. Las RPC existentes conservan sus roles, identidad, consentimiento, honeypot, límites e idempotencia. Las redes no conceden acceso a documentos ni a ninguna ruta.

El nuevo registro entra en el respaldo automático/manual privado. El ZIP también sigue aceptando respaldos del esquema anterior, sin esta tabla opcional.

## Formulario compartido

La sección **Redes sociales de la empresa (opcional)** aparece después de los datos de contacto, con la ayuda solicitada, cinco íconos, dos columnas en escritorio y una en celular. Sigue habiendo tres pasos. Se aplica a formulario público, cliente autenticado y Nueva solicitud administrativa.

Instagram acepta usuario, @usuario o URL de perfil y se convierte a `https://www.instagram.com/usuario/`. LinkedIn, Facebook y Sitio web reciben `https://` si falta. Se validan dominio, credenciales, puerto, controles, esquemas y longitud; los errores nombran el campo. Se rechazan javascript, data, file, vbscript y otros esquemas que no sean HTTP/HTTPS en enlaces.

**Otra red conserva el texto libre solicitado**, por ejemplo `TikTok: @empresa`. Si se ingresa una URL, se valida igual que las otras. El texto libre no se convierte en enlace clicable. Cada entrada y su URL normalizada tienen como máximo 200 caracteres. Vacío es válido y nunca cuenta como Faltan datos.

La cuenta de cliente precarga sus redes reutilizables al crear el borrador. Al cambiar de empresa se consultan las de esa empresa, salvo que ya haya editado redes manualmente. Un borrador recuperado mantiene prioridad sobre la precarga. La administradora conserva Buscar empresa o cliente existente; elegirlo también carga sus redes guardadas en el caso de referencia.

El consentimiento menciona las redes opcionales y excluye marketing. Las solicitudes nuevas con consentimiento registran la versión `2026-11-02-redes`; no se cambia el consentimiento histórico. Los campos también forman parte del resumen y del respaldo de borrador existente en la pestaña.

## Caso y PDF

En Datos y seguimiento se muestra **Redes sociales**, enlaces que se abren en otra pestaña o **Sin redes registradas**. Editar redes sociales usa el autoguardado y los reintentos existentes. Lo inválido permanece escrito con su error; los demás campos del caso se pueden guardar. Se conserva el control de cambios concurrentes.

**Los prompts 26 y 28 no estaban implementados en este checkout.** Se añadió una ficha PDF básica administrativa con logo, código/fecha, empresa/contacto, servicio, detalle y redes, y el botón Descargar ficha del caso. No se afirma que esta ficha implemente otros requisitos de un prompt 26 no disponible. La consulta privada queda disponible para el futuro perfil del prompt 28, sin agregar una pantalla de perfil en esta entrega.

La ficha solo usa datos guardados y se genera al descargar. Los enlaces son clicables; los largos se ajustan dentro de la tabla y los detalles extensos continúan en otras páginas. No se incluye el bloque en Word/PDF de cotizaciones ni se cambian sus generadores.

## Archivos modificados completos

| Archivo | Cambio |
|---|---|
| servicios/redes_sociales.py | Contrato de campos, normalización, validación y precarga privada. |
| utils/formulario_config.py | Cinco campos opcionales, valores iniciales y consentimiento. |
| paginas/formulario.py | Sección compartida, íconos, normalización al editar, precarga por empresa y autocompletado interno. |
| servicios/formulario.py | Validación y envío de redes como JSON; compatibilidad con backend anterior si están vacías. |
| utils/formulario_borrador.py | Precarga sin sustituir un borrador ni hacer pública una consulta privada. |
| utils/validaciones.py | Validaciones por red y del conjunto editable del caso. |
| servicios/autoguardado.py | Admite el conjunto de redes con validación, conflictos y reintento. |
| paginas/edicion_caso.py, paginas/redes_caso.py | Enlaces, edición y descarga administrativa. |
| servicios/ficha_caso.py | Ficha PDF básica, separada de las cotizaciones. |
| utils/estilos.py | Columnas de redes apiladas en celular; colores existentes. |
| servicios/respaldos.py | Incluye la tabla reutilizable cuando esté presente, manteniendo compatibilidad anterior. |
| supabase/migrations/202611020004_redes_sociales.sql | Columna, entidad reutilizable, validación, RLS, RPC, triggers, consentimiento y respaldo. |
| tests/test_redes_sociales.py, tests/test_redes_sociales.mjs | Pruebas ficticias de datos, interfaz, seguridad, PDF y persistencia. |
| tests/test_app.py | Usa el texto vigente de consentimiento del contrato compartido. |

## Pruebas

| Prueba | Resultado esperado |
|---|---|
| Enviar con las cinco redes | Se guardan normalizadas, se muestran en el caso y aparecen en la ficha. |
| Enviar sin redes | Se guarda normalmente; caso muestra Sin redes registradas. No suma pendientes. |
| Instagram @empresa_norte | Al salir del campo muestra su URL completa y la guarda así. |
| URL inválida o javascript | Mensaje que identifica el campo; conserva lo escrito. No permite enviar el enlace peligroso. La base también lo rechaza. |
| Solicitud interna parcial | Guarda lo permitido como antes; redes vacías no figuran en datos pendientes. |
| Editar posteriormente el caso | Autoguarda, actualiza sus enlaces y el registro reutilizable. Un enlace inválido no reemplaza el anterior guardado. |
| Segundo envío de empresa/correo idénticos | Un solo registro actual, con copia en cada caso. |
| Anónimo intenta cambiar redes de una cuenta confirmada | Su solicitud queda registrada; el registro confirmado y la precarga de la cuenta no cambian. |
| Cliente A y cliente B | A no puede precargar las redes de B ni leer la tabla maestra. Sin correo confirmado tampoco hay precarga. |
| PDF con enlaces largos y mucho detalle | Textos completos, enlaces clicables, márgenes respetados y páginas numeradas; sin redes en cotización. |
| 375 px | Cinco campos apilados y controles de tamaño táctil, sin un paso nuevo. Revisión física en móvil pendiente. |

```powershell
python -m unittest discover -s tests -p test_redes_sociales.py
python -m unittest discover -s tests
node tests/test_redes_sociales.mjs
node tests/test_formulario_unificado_sql.mjs
node tests/test_publico_sql.mjs
node tests/test_en_vivo_sql.mjs
```

El SQL usa la instalación local de PGlite en `tmp/db-test/node_modules`. No es dependencia del despliegue.

Se generó y revisó visualmente `output/pdf/ficha_redes_ficticia.pdf` (tres páginas), con un enlace largo y Otra red extensa. La revisión automatizada comprueba anotaciones de enlaces, texto final y límites de página. Los PNG de revisión están en `tmp/pdfs/redes`.

Pendiente de activación: aplicar la migración en el Supabase real y probar el formulario desde un teléfono. No se verificó una conexión real ni se guardaron clientes reales durante estas pruebas.
