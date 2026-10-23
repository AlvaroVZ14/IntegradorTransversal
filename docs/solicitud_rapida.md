# Registro asistido de solicitudes

## Activar y abrir

1. En Supabase → SQL Editor ejecuta completo `supabase/migrations/202610220002_solicitud_rapida.sql`. Requiere la migración de permisos `202610210001_cliente_solo_solicitud.sql` ya aplicada; **no vuelvas a ejecutar esa migración anterior si ya la aplicaste**. La migración de Deshacer aceptación del 22/10 es independiente de esta funcionalidad.
2. Abre http://127.0.0.1:8502 y recarga. Puede pedir iniciar sesión otra vez, porque no se añadió persistencia de autenticación.
3. En Administración abre **Nueva solicitud**. Puedes buscar una empresa, revisar los datos precargados y elegir **Guardar y cotizar ahora** o **Guardar y registrar otra**. Se conserva también **Enviar solicitud**.

Esta entrega está en el proyecto local y en `output/mente-futuro-solicitud-rapida.zip`. **No se publicó en Streamlit Cloud ni se ejecutó el SQL sobre el proyecto vivo**: esta sesión no tiene una conexión administrativa a PostgreSQL. Si faltan las columnas, el guardado administrativo avisa qué migración ejecutar y conserva el borrador. El RPC anterior de clientes no almacena RUT/cargo; aplica la nueva migración antes de utilizar estos campos.

No hay dependencias nuevas. Se usa Streamlit 1.65.0 instalado y las dependencias existentes de `requirements.txt`; las claves siguen en `st.secrets`. El ZIP no incluye secretos ni datos reales. No se garantiza un tiempo de 30 segundos sin una prueba cronometrada con personas; se reducen los pasos para acercarse a ese objetivo.

## Esquema y comportamiento

Se revisaron `app.py`, `/paginas`, `/servicios`, los componentes compartidos y las migraciones existentes. No hay una tabla de empresas/clientes independiente: **el buscador administrativo usa `mf_casos`**, tomando la ficha más reciente por empresa y correo. La cuenta autenticada se identifica en `mf_perfiles` por `id`, `nombre`, `email` y `rol`. No se inventan otras tablas.

El formulario anterior no incluía RUT, cargo, origen ni los dos accesos rápidos mencionados. Se añadieron; no se retiró ninguno de sus campos, límites, validaciones, secciones, encabezado, consentimiento ni botón de envío. RUT y cargo son opcionales y se guardan en dos columnas nuevas de `mf_casos`. También pueden editarse en Datos y seguimiento mediante el autoguardado existente. El origen conserva los valores históricos y puede modificarse a mano.

- **Buscar empresa o cliente existente:** el selector permite escribir parte de la empresa, el contacto o el correo. Al seleccionar, precarga empresa, RUT, contacto, cargo, correo y teléfono. Los cuadros originales permanecen editables.
- **Cuenta vinculada:** el correo se compara sin distinguir mayúsculas y quitando espacios exteriores. Se vincula únicamente a una cuenta de rol `cliente` cuando la coincidencia es única. Si no coincide con el correo del perfil, puede reutilizar una vinculación previa inequívoca del mismo correo de contacto, siempre que la cuenta siga siendo Cliente. No crea una cuenta ni un ID ficticio si no existe. Un aviso muestra la cuenta; el selector manual permite cambiarla o desvincularla. Ese cambio se respeta hasta modificar el correo.
- **RUT:** la máscara del navegador agrega puntos y guion mientras se escribe; Python vuelve a formatear al salir del campo y valida módulo 11. No elimina letras incorrectas para convertirlas artificialmente en un RUT válido. El dígito verificador se comprueba de nuevo al enviar y mediante una restricción en PostgreSQL. No se consulta la identidad tributaria de la persona.
- **Teléfono:** los tres formatos móviles solicitados se convierten a `+56 9 1234 5678`. Se conservan teléfonos fijos/internacionales válidos, sin anteponer Chile arbitrariamente. Un teléfono vacío sigue siendo válido por ser opcional.
- **Correo:** valida al salir del campo. Las erratas conocidas ofrecen un botón, por ejemplo **Usar camila@gmail.com**. No se modifica el dominio sin pulsarlo ni se verifica que el buzón exista.
- **Temática y sugerencias:** se conserva el selector de una sola temática; esa primera y única selección es la principal. Se sugiere la mediana de horas y participantes de casos de la misma temática y servicio, excluyendo anulados. Si no hay casos, se usan tarifas activas del servicio, aclarando que `mf_tarifas` no tiene temática. **Aplicar sugerencia** es opcional; los valores pueden cambiarse después.
- **Origen:** Llamada, Correo, Reunión, Programa propio, Referido por colega, Formulario web, Otro o No informado. Recuerda el último usado durante la sesión y al registrar otra solicitud. Cliente no recibe ese selector.
- **Duplicados:** avisa sobre casos abiertos de los últimos 30 días con la misma temática y cuenta vinculada, correo o nombre de cliente. Usa los estados internos reales; excluye Finalizado y Cancelado. Permite abrir uno de los cinco más recientes o marcar **Crear otra solicitud de todas formas**. Antes de guardar vuelve a consultar, para reducir carreras entre sesiones. Es una advertencia asistida, no una prohibición transaccional de duplicados simultáneos. El mismo UUID de un reintento se excluye de la advertencia y no genera otro caso.

El catálogo administrativo se conserva hasta 60 segundos en la propia sesión y se invalida con las escrituras existentes. No se comparte entre usuarios. Si hay un fallo de lectura, el formulario sigue disponible a mano, avisa y puede usar el respaldo de esa misma sesión. No permite guardar una consulta fallida como si hubiera sido un envío exitoso.

## Flujos y permisos

**Guardar y cotizar ahora** crea el caso y abre Casos y cotizaciones con la pestaña Cotizaciones seleccionada. No emite una propuesta sin revisarla. **Guardar y registrar otra** confirma el código, limpia el formulario y mantiene el origen. **Enviar solicitud** conserva el flujo administrativo anterior hacia el detalle del caso.

Cliente sigue teniendo únicamente Nueva solicitud. Nombre de cuenta, contacto y correo se reconstruyen desde su identidad y permanecen bloqueados. No recibe el buscador de empresas, selector de vinculación, origen, sugerencias basadas en casos, accesos rápidos administrativos ni listado de duplicados. Su envío mantiene consentimiento obligatorio y la pantalla de éxito con el código y las 48 horas hábiles. No existe un formulario anónimo nuevo: se conserva el ingreso con cuenta del proyecto.

El SQL reemplaza `registrar_solicitud` con su misma firma y conserva sus comprobaciones: usuario confirmado, rol Cliente, identidad y vinculación reconstruidas en el servidor, consentimiento, origen Formulario web e idempotencia. Añade solo RUT/cargo a los datos admitidos. No cambia roles, RLS ni permisos de las tablas privadas.

## Borrador y recarga

Los valores se conservan en un diccionario de `st.session_state` independiente de los widgets. Un componente del navegador respalda el borrador en **sessionStorage de la misma pestaña**, separado por usuario. Los textos se capturan mientras se escriben; selectores, números y fecha se incorporan al recibir sus cambios en el servidor. Incluye el UUID estable del envío para reintentar sin duplicar una solicitud.

Tras recargar e iniciar sesión con la misma cuenta, vuelve a Nueva solicitud: se recupera el borrador. La identidad bloqueada de Cliente nunca se restaura desde el navegador. **El consentimiento no se respalda**: hay que volver a marcarlo. Confirmar un envío limpia el borrador anterior; Cerrar sesión elimina el respaldo de esa cuenta incluso desde otra página.

Límites: no es un modo offline completo. Si se corta la red antes de que llegue un cambio de selector/número/fecha, su último cambio puede no estar en el respaldo. La recuperación depende de que sessionStorage esté disponible; cerrar la pestaña, borrar sus datos o usar otro dispositivo no garantiza conservarlo. Un script del mismo origen o una persona que acceda al navegador podría leer los datos de contacto del borrador. No almacena contraseñas ni tokens y no mantiene abierta la sesión autenticada.

## Pruebas con datos ficticios

Resultado: **84 pruebas Python aprobadas**, más los ensayos JavaScript del borrador y las pruebas SQL de RUT, idempotencia, identidad, RLS y compatibilidad con Deshacer aceptación. No se modificaron cálculos del Dashboard, roles ni dependencias respecto de la entrega anterior.

| Prueba | Qué hacer | Qué debe verse |
| --- | --- | --- |
| Cliente existente | Busca Fundación Horizonte en el selector y selecciónala. | Precarga los seis campos disponibles de su ficha más reciente; todos se pueden editar. Si tiene cuenta, aparece el aviso de vinculación. Si no tiene, permanece Sin cuenta vinculada. |
| Cliente nuevo con cuenta | Escribe una empresa nueva y el correo de una cuenta Cliente existente. Sal del correo. | Vinculación automática; puedes elegir otra cuenta o dejarla sin vincular a mano. No se crean usuarios nuevos. |
| RUT incorrecto | Escribe `123456789`, intenta enviar, luego corrige a `123456785`. | Primero muestra error de dígito verificador y no crea el caso; después queda `12.345.678-5` y permite continuar si el resto es válido. |
| Teléfono en tres formatos | Prueba `912345678`, `+56912345678` y `9 1234 5678`. | Al salir, los tres muestran `+56 9 1234 5678`. |
| Solicitud duplicada | Usa cliente y temática de un caso abierto creado hace menos de 30 días. | Aparece ¿Es la misma solicitud?, un botón para abrir el caso y una casilla para crear otro deliberadamente. Sin marcarla no crea otro. |
| Recarga a medio llenar | Completa textos, horas y temática; espera a que terminen sus cambios. Recarga en la misma pestaña, ingresa y abre Nueva solicitud. | Recupera los valores y el UUID del borrador. Como Cliente, nombre/correo siguen siendo los de su cuenta y el consentimiento aparece desmarcado. |
| Guardar y registrar otra | Elige Referido por colega y guarda un caso ficticio. | Confirma el código, limpia los campos y mantiene Referido por colega. |
| Guardar y cotizar ahora | Completa un caso válido y pulsa ese botón. | Abre el nuevo caso con Cotizaciones seleccionada; aún no se ha emitido ninguna cotización. |

Comandos desde la raíz:

```powershell
$env:TEMP = Join-Path (Get-Location) 'tmp/tests'
$env:TMP = $env:TEMP
python -m unittest discover -s tests -v
node tests/test_solicitud_borrador.mjs
node tests/test_solicitud_rapida.mjs
node tests/test_borrador_local.mjs
node tests/test_menu_movil.mjs
node tests/test_deshacer_aceptacion.mjs
```

Los ensayos SQL utilizan PGlite en PostgreSQL efímero, con la dependencia de pruebas ya existente en `tmp/db-test/node_modules`, no Supabase real ni una dependencia nueva de producción. Si se ejecutan desde un ZIP limpio, puede instalarse únicamente para pruebas con `npm install --prefix tmp/db-test @electric-sql/pglite`. Las simulaciones de JavaScript cubren recarga, captura de texto, máscara de RUT, reconexión y limpieza; AppTest cubre los controles y los recorridos de ambos roles. No se presentan como una revisión visual real a 375 px ni como una medición física del tiempo de registro.
