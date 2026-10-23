# Mente y Futuro · Portal de gestión

Aplicación Streamlit para solicitudes, casos, tarifas, cotizaciones y ventas, con Supabase Auth y PostgreSQL. Usa el logo original y los colores celeste, violeta y amarillo. No incluye marketing ni captación de clientes.

## Las tres secciones

| Sección | Cliente | Dueña |
|---|---|---|
| Nueva solicitud | Registra una solicitud en su propia cuenta | Registra solicitudes y las vincula a una cuenta de cliente, si existe |
| Casos y cotizaciones | Sin acceso | Gestiona casos, emite cotizaciones, registra ventas y administra el tarifario |
| Dashboard | Sin acceso | Ventas por período, ticket promedio, demanda por temática, estados, conversión y exportaciones CSV |

El tarifario está dentro de **Casos y cotizaciones → Tarifas y servicios**. Las cuentas se crean como clientes; el rol de dueña se asigna únicamente desde Supabase. Los permisos se validan en la base de datos, además de en la interfaz.

## Activar Supabase (una vez)

La aplicación necesita estas tablas y funciones antes de utilizar cuentas o guardar registros. La clave publicable no permite crear el esquema.

1. En el proyecto de Supabase correspondiente a `SUPABASE_URL`, abre **SQL Editor → New query**.
2. Copia y ejecuta **todo** el archivo [migración inicial](supabase/migrations/202610150001_gestion_mente_futuro.sql). Es una transacción: si algo falla, no queda una configuración parcial. Ejecutarlo una sola vez; para comprobar si ya se aplicó, busca la tabla `mf_perfiles`.
3. En **Authentication → Providers**, mantén habilitado Email. Configura **Authentication → URL Configuration → Site URL** con la URL del Streamlit desplegado (o `http://localhost:8501` para desarrollo). Los correos de confirmación llevan al sitio para iniciar sesión; la app no usa un callback propio.
4. La dueña debe crear y confirmar su cuenta desde el portal. También puede usar una cuenta de Auth ya existente; la migración crea su perfil como cliente.
5. En **Authentication → Users**, identifica la cuenta de la dueña y copia su UUID. En SQL Editor ejecuta, reemplazando el marcador:

   ```sql
   update public.mf_perfiles
   set rol = 'admin'
   where id = 'UUID-DE-LA-CUENTA-DE-LA-DUENA'::uuid
   returning id, nombre, email, rol;
   ```

   Verifica que el resultado corresponde a la persona correcta. Nunca asignes el rol basándote en datos de registro elegidos por el cliente. La dueña puede actualizar la página para ver sus permisos.

6. Verifica con dos cuentas de cliente que cada una vea únicamente sus solicitudes. La dueña debe ver ambas y el dashboard.

**Datos anteriores:** las tablas nuevas usan el prefijo `mf_` para preservar la tabla `casos` del prototipo sin adivinar su estructura. Los registros anteriores no se importan automáticamente. Antes de publicar, revisa esa tabla en SQL Editor y restringe su acceso anónimo si contiene datos reales. La aplicación nueva no la consulta. Para trasladar registros existentes, primero se necesita conocer sus columnas y vincular cada caso a su cliente correcto.

## Configuración y ejecución

Python 3.11 o superior:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La configuración local existente se conserva. Para una instalación nueva, copia `.streamlit/secrets.example.toml` como `.streamlit/secrets.toml` y completa:

```toml
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_KEY = "TU-CLAVE-PUBLICABLE"
```

Usa la clave `sb_publishable_...` o la clave `anon`. La aplicación rechaza claves `service_role` y `sb_secret_...` para no saltarse las políticas de acceso. También acepta estas dos variables de entorno. En Streamlit Community Cloud, configura los mismos valores en **Settings → Secrets**. Nunca subas `secrets.toml` al repositorio.

## Cómo se utiliza

1. El cliente inicia sesión y envía una solicitud. Solo se confirma el guardado después de recibir respuesta de Supabase.
2. La dueña abre el caso, revisa sus datos y, si lo registró manualmente, puede vincularlo a una cuenta existente. El correo de contacto por sí solo no otorga acceso.
3. En **Cotizaciones**, elige una tarifa o un valor personalizado, revisa alcance, descuento, IVA, vigencia y condiciones. El total se calcula antes de emitir.
4. Al emitir se guarda una copia del contenido y los valores. Las propuestas se descargan en HTML con el logo; pueden imprimirse o guardarse como PDF desde el navegador. La descarga no envía un correo ni acepta la propuesta.
5. En **Venta**, la dueña confirma la aceptación, registra su fecha y el estado del pago. Se admite una venta por caso, asociada a una cotización de ese mismo caso. La fecha debe estar dentro de la vigencia y no ser futura. El monto proviene de la cotización, sin volver a consultar la tarifa.
6. La dueña puede actualizar el estado del pago o anular la venta. El dashboard excluye las ventas anuladas. El seguimiento del caso se administra por separado de su estado de pago.

## Tarifas de los documentos

La migración incluye 11 referencias: 3 planes individuales, 3 planes dúo por separado, 3 planes dúo en conjunto, taller de escape room y charla de liderazgo. Todos los montos están en CLP y representan el total del plan, no una tarifa por hora.

- Individual: 4 / 6 / 8 sesiones por $420.000 / $580.000 / $740.000.
- Dúo separado: totales de $714.000 / $986.000 / $1.258.000 para dos personas. Las horas de atención suman las sesiones de ambas personas.
- Dúo conjunto: totales de $546.000 / $754.000 / $962.000 para dos personas.
- Escape room: referencia de $4.580.000 para 56 participantes y 8 horas.
- Charla: referencia de $2.650.000 para hasta 300 personas y 1 hora.

Las dos cotizaciones corporativas señalan exención de IVA; los planes de coaching quedan con **IVA por confirmar**, porque el documento no define ese tratamiento. La dueña debe elegirlo antes de emitir. Los descuentos históricos de aniversario del 15% no se aplican automáticamente. Las condiciones comerciales iniciales son editables y deben revisarse para cada servicio.

## Dashboard por períodos

La interfaz está en `paginas/dashboard.py` y la lógica en `servicios/dashboard.py`. Incluye cinco agrupaciones, filtros superiores, rangos rápidos y comparación con el bloque anterior. Consulta [cómo funciona y cómo probarlo](docs/dashboard_periodos.md).

La [presentación visual posterior](docs/dashboard_visual.md) incorpora Plotly, estilos centralizados, seis KPI y ocho gráficos. Agrega `plotly>=6.1,<7`, sin modificar los cálculos ni las consultas. Incluye una muestra HTML con datos ficticios y no requiere SQL adicional.

## Indicadores

- **Ventas del período:** suma de ventas no anuladas por fecha de aceptación, con los impuestos de cada propuesta. No equivale a dinero cobrado.
- **Ticket promedio:** monto vendido / número de ventas del período.
- **Demanda:** solicitudes según fecha de creación en `America/Santiago`.
- **Conversión:** porcentaje de solicitudes creadas en el período con venta no anulada hasta la fecha final seleccionada.
- **Ventas con pago pendiente:** valor completo de ventas no pagadas totalmente, incluidas las que tienen abonos. No es un saldo exacto por cobrar; esta versión no lleva un libro de pagos parciales.
- Las solicitudes conservan su estado actual; el dashboard no reconstruye el estado histórico en cada fecha. El filtro por servicio utiliza la clasificación actual del caso.

## Validación

Pruebas de cálculo, seguridad de exportación y recorrido de Streamlit con repositorio aislado:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Prueba del SQL en PostgreSQL efímero (PGlite), sin tocar Supabase:

```powershell
npm install --prefix tmp/db-test --no-audit --no-fund @electric-sql/pglite
node tests/test_database.mjs
```

La suite SQL verifica permisos de lectura y escritura, aislamiento entre clientes, promoción de roles bloqueada, cotizaciones inmutables, cálculos, concurrencia, duplicados y relación entre cotización y venta. Estas pruebas no sustituyen la prueba final con cuentas en el proyecto real después de aplicar la migración.

## Cambio de permisos del 21/10/2026

Consulta [la guía de activación, pruebas manuales y reversión](docs/cliente_solo_solicitud.md). El código de permisos requiere la migración de ese día antes de publicarse. Esa entrega no agrega dependencias; la mejora visual posterior requiere Plotly.

## Estructura

La actualización de presentación del portal, archivos completos y matriz de revisión a 375 px, 768 px y escritorio están en [Portal como producto](docs/portal_producto.md).

La unificación más reciente de encabezados, tarjetas y formularios está en [Lenguaje visual común](docs/lenguaje_visual.md), con la entrega completa y sus pruebas.

El reemplazo del radio por navegación nativa, permisos por rol y paletas de la barra lateral está en [Navegación lateral](docs/navegacion_lateral.md).

El autoguardado de casos, reintentos, Deshacer, caché y evaluación de sesión están en [Autoguardado](docs/autoguardado.md), con sus límites y pruebas manuales.

La vinculación por correo, búsqueda de empresas, RUT, teléfono, sugerencias, duplicados y recuperación del formulario están en [Solicitud rápida](docs/solicitud_rapida.md). Requiere ejecutar la migración SQL indicada en esa guía para almacenar RUT y cargo.

El editor prellenado de cotizaciones, borrador persistente, Word/PDF, correo confirmado y aceptación/venta están en [Cotizador asistido](docs/cotizador_asistido.md). Incluye SQL de activación, configuración del emisor y SMTP, y pruebas con datos ficticios.

El inicio administrativo Hoy, las tareas accionables, los mensajes preparados y el cierre con Deshacer están en [Hoy](docs/hoy.md). El resumen diario por GitHub Actions queda documentado como ampliación opcional, sin activar envíos automáticos.

## Si el formulario está dormido o falla

1. Si aparece “Zzzz / This app has gone to sleep”, pulsa **Yes, get this app back up!** y espera. Cualquier visitante autorizado puede hacerlo. Si aparece un error, avisa a la persona responsable del repositorio y adjunta la hora y captura, sin claves ni datos del cliente.
2. Si sigue fallando, la administradora revisa Supabase: si está pausado, pulsa **Resume project**. No borres el proyecto ni vuelvas a ejecutar todas las migraciones para intentar arreglarlo. Revisa también las issues privadas de mantenimiento y los logs de Streamlit.
3. Al recuperar el acceso, entra con Administración a **`/estado`** y a **Casos y cotizaciones**: comprueba el último código/fecha y busca el correo de la solicitud esperada. Solo una pantalla de éxito con código confirma el registro del formulario. Un intento mientras estaba caído podría no haberse guardado; un respaldo tampoco recupera solicitudes nunca recibidas. Si falta, contacta al cliente por el canal habitual y verifica antes de registrarla otra vez.
4. En **Casos y cotizaciones → Configuración**, descarga un ZIP si necesitas una copia inmediata. La tarjeta muestra la última copia automática confirmada, no la última copia manual.

La [guía de mantenimiento](docs/mantenimiento.md) contiene los dos workflows, SQL nuevo, secretos del repositorio privado, recuperación y pruebas. **Streamlit puede dormir a las 12 horas y Supabase pausar por baja actividad en 7 días**: estas comprobaciones no garantizan disponibilidad continua gratuita. Los workflows requieren activación y guardan únicamente respaldos cifrados en un repositorio privado; no subas CSV a uno público.

La [guía de recarga y sesión](docs/recarga_y_sesion.md) explica el registro estable
de rutas, la recuperación administrativa durante siete días, su riesgo de cookie
sin HttpOnly y las pruebas. No requiere nuevas claves ni SQL. También documenta
la diferencia encontrada con el supuesto formulario anónimo `?vista=solicitud`.

```text
app.py                     Entrada, sesión y navegación
mente_futuro/
  domain.py                Validaciones, montos e indicadores
  repository.py            Acceso autenticado a Supabase
  pages.py                 Las tres vistas
  ui.py                    Acceso y componentes comunes
  presentation.py          Estilos y cotización imprimible
assets/                    Logo original
supabase/migrations/       Esquema, permisos y tarifas iniciales
tests/                     Pruebas de aplicación y PostgreSQL
```

Referencias de implementación: [Supabase Auth para Python](https://supabase.com/docs/reference/python/auth-signinwithpassword), [permisos RLS](https://supabase.com/docs/guides/database/postgres/row-level-security) y [pruebas de Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
