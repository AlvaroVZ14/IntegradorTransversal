# Login y solicitudes desde el sitio o Instagram

La dueña mantiene Hoy, Nueva solicitud, Casos y cotizaciones, Dashboard y sus funciones internas. El cliente con cuenta conserva Nueva solicitud con nombre y correo bloqueados. Además, el enlace `/?vista=solicitud` permite enviar **sin cuenta**. Ese canal no consulta perfiles ni reutiliza una sesión administrativa, aunque esté abierta en otra pestaña.

## Activación en la app publicada

El código puede publicarse por GitHub, pero la clave publicable de la aplicación **no permite ejecutar migraciones**. Para activar los envíos sin cuenta:

1. En Supabase del proyecto existente, abre **SQL Editor → New query**.
2. Ejecuta completo [202610230002_formulario_publico.sql](../supabase/migrations/202610230002_formulario_publico.sql), una vez, después de las migraciones anteriores del proyecto. No vuelvas a ejecutar la migración inicial. Si falla, la transacción no aplica cambios parciales.
3. Abre el enlace de la aplicación agregando `?vista=solicitud`. Debe mostrar tres pasos sin login. Antes de aplicar este SQL el formulario puede verse, pero no confirmará envíos.
4. En una prueba autorizada usa solo información ficticia. Tras enviar, verifica el código en **Casos y cotizaciones** con Administración. La solicitud tiene estado Solicitud, origen Formulario web y registrado por Cliente.

No hay dependencias nuevas. Se utiliza Streamlit 1.65, el componente v2 ya disponible y el cliente Supabase existente. Las claves continúan en `st.secrets`.

## Contacto y redes

La tabla real es `public.mf_configuracion`, fila `id = 'general'`, columna JSON `datos`. Se leen exclusivamente estas claves existentes:

- `sitio_web`: URL del sitio.
- `redes.facebook` y `redes.instagram`: URL de cada perfil.
- `correo_contacto`: correo público de contacto, mostrado debajo del formulario.

Si están vacías, se omiten los enlaces. No se inventan direcciones ni se sustituyen por valores del emisor. Para completar una clave que falte, edita únicamente esa propiedad del JSON en Table Editor, preservando todas las demás. No pegues aquí contraseñas SMTP. La función `mf_configuracion_publica()` proyecta solo estas tres claves; nunca entrega el resto de la configuración.

## Qué cambia

Login dividido en escritorio y apilado en tablet/celular: panel de marca con ampolleta, frase y tres pasos; tarjeta con las dos pestañas habituales. El botón de ingreso y registro es amarillo, de ancho completo. El aviso es lavanda con borde amarillo y no recorta texto. Se corrigió el selector del botón nativo `primaryFormSubmit`.

El formulario público conserva los catorce campos del formulario de solicitud: empresa, contacto, RUT, cargo, correo, teléfono, servicio, temática, participantes, horas, modalidad, lugar, fecha y detalle. Empresa puede quedar vacía si se consulta a título personal: se utiliza el nombre del contacto. La selección ofrece las mismas opciones reales de servicio, temática y modalidad del proyecto. Consentimiento obligatorio y honeypot se comprueban también en el servidor. El código anterior todavía enviaba el enlace público al login y no tenía honeypot; se agregó esa protección sin modificar el formulario interno.

**Límite de Community Cloud comprobado en la publicación:** el menú, encabezado y pie internos de Streamlit están ocultos en el formulario. Sin embargo, el contenedor externo del alojamiento muestra sus propios controles en una esquina. El CSS de la aplicación no los elimina. Se probó también `embed=true`: quita controles de la app, pero el contenedor del alojamiento puede mostrar “Built with Streamlit” y pantalla completa. Por tanto, no se garantiza una página completamente sin marca del proveedor en Community Cloud. [Documentación oficial del modo de incrustación](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app/embed-your-app). No se añadieron modificaciones frágiles al marco externo ni se ocultó la administración del alojamiento.

Paso 1: empresa y contacto. Paso 2: tarjetas de servicio/temática, pastillas de modalidad, participantes y horas. Paso 3: lugar, fecha, mensaje, resumen completo y consentimiento. Atrás conserva lo escrito. En celular la barra de acciones queda fuera del contenedor animado para que su posición fija sea respecto de la pantalla. `visualViewport` ajusta el espacio ante teclados que superponen la página; `safe-area-inset-bottom` contempla el borde inferior de iOS. Los campos indican email/teléfono/número al navegador y mantienen los callbacks y validaciones nativos.

## Guardado y seguridad

- La nueva RPC pública crea una solicitud y devuelve únicamente su código. No concede lectura o escritura directa de tablas ni cambia el rol de nadie.
- No se vincula automáticamente una cuenta a partir de un correo escrito por un visitante. Una solicitud sin cuenta tiene `creado_por = NULL` y `cliente_id = NULL`, con origen y consentimiento explícitos. La dueña puede gestionarla desde su flujo habitual.
- El reintento utiliza UUID y token aleatorio por borrador. El servidor guarda hashes privados y solo confirma el mismo envío si coinciden token y contenido. No crea duplicados por repetir el mismo envío tras una caída de red.
- Hay un honeypot y límites de 3 envíos por correo cada 15 minutos y 60 envíos públicos por hora. Son protecciones básicas: **no equivalen a un CAPTCHA** ni garantizan evitar ataques. No se envían correos ni se cambian estados automáticamente.
- El borrador se guarda en `st.session_state` y `sessionStorage`, por pestaña y hasta 24 horas, incluyendo texto antes de perder foco. No guarda contraseñas, tokens Auth ni consentimiento. Al confirmar el envío se elimina del navegador. Los datos de contacto y el RUT permanecen en ese almacenamiento durante el borrador: cierra la pestaña al terminar en un dispositivo compartido.
- Si el navegador bloquea almacenamiento o se cierra/destruye la pestaña de Instagram, no puede garantizarse recuperar el borrador. La app no afirma que el envío esté guardado hasta recibir el código de Supabase. Si el proyecto está pausado o la app dormida, este diseño tampoco elimina el tiempo de reactivación del proveedor.

## Pruebas y resultado esperado

| Prueba | Qué debería verse |
|---|---|
| Login a 1440 px | Panel de marca a la izquierda y tarjeta blanca con dos pestañas a la derecha; botón amarillo y aviso completo. |
| Login a 768 y 375 px | Panel compacto arriba y tarjeta debajo; sin desplazamiento horizontal. |
| Abrir `?vista=solicitud` sin sesión | Encabezado con logo y enlaces configurados, paso 1 de 3 y ningún menú privado ni barra/pie de Streamlit. |
| Abrirlo con una sesión administrativa | El mismo formulario público; no usa la sesión administrativa para leer datos o guardar. Volver al enlace privado conserva el flujo de la dueña. |
| Paso 1 con RUT `12.345.678-9` | Mensaje junto al RUT; Siguiente no avanza. Con `12.345.678-5` sí puede avanzar. |
| Teléfonos `912345678`, `+56912345678`, `9 1234 5678` | Al salir del campo, los tres quedan `+56 9 1234 5678`. |
| Servicio y temática | Tarjetas seleccionables con icono, borde y estado seleccionado explícito; modalidad en pastillas. Las opciones son las mismas del formulario interno. |
| Atrás y Siguiente | Se mantienen todos los valores y cambia el progreso; se lleva la vista al nuevo paso. |
| Recargar a medio escribir, sin salir del campo | En la misma pestaña se recuperan el texto, selecciones y paso. Consentimiento se debe marcar nuevamente. |
| Enviar sin consentimiento | Mensaje claro junto al control; no se llama al guardado. |
| Desconectar durante envío y reintentar | Se conserva el borrador y aparece un aviso amable. Un envío confirmado repetido con el mismo contenido genera un solo caso. |
| Envío correcto | Check, confeti breve en la paleta, código y “Te contactaremos dentro de las próximas 48 horas hábiles”. No se muestra listado de solicitudes. |
| Visitante consulta tablas con la clave pública | Error de permisos o cero filas; solo están permitidas las dos RPC públicas acotadas. |
| Dueña abre Casos/Hoy/Dashboard | Conserva permisos y registros anteriores; recibe también las nuevas solicitudes públicas por los ciclos de actualización existentes. |
| Movimiento reducido | Sin animaciones; funciones y confirmación permanecen. |

**Dispositivos reales pendientes:** abrir el enlace desde Instagram y Facebook en Android/iOS, Chrome de Android y Safari de iOS. Con el teclado abierto verificar que Siguiente/Atrás queden visibles, se pueda llegar a cada campo sin scroll horizontal, el correo tenga teclado adecuado y la recarga conserve el borrador. En iOS comprobar además la zona del indicador inferior y el zoom. Si el navegador interno elimina su almacenamiento al salir, usar “Abrir en navegador”. La emulación de pantalla o de user-agent en Edge no sustituye estas pruebas.

Se ejecutaron pruebas Python de UI/validación y regresión, pruebas JS del borrador/teclado y PostgreSQL efímero de envío, límites, RLS y reversión, únicamente con datos ficticios. Las capturas corresponden a una vista local aislada sin conexión a la base real.

```powershell
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_publico_borrador.mjs
node tests/test_publico_sql.mjs
```

El último comando usa el PGlite de pruebas ya preparado en `tmp/db-test/node_modules`. En otra máquina, instalar temporalmente `@electric-sql/pglite` bajo `tmp/db-test`; no es una dependencia de producción.

## Reversión

Desplegar primero el código anterior y ejecutar [rollback del canal público](../supabase/rollback/202610230002_formulario_publico.sql). Se revocan las funciones de entrada pública, **sin eliminar solicitudes**. Si ya existen solicitudes sin cuenta, se conserva su autoría nula y su restricción de consentimiento; no se inventa un usuario ni se borran registros para restaurar NOT NULL. Los recibos privados se conservan. El SQL de migración se ejecuta una vez; una reactivación tras rollback requiere revisar los objetos preservados, no repetirlo sin ajustes.
