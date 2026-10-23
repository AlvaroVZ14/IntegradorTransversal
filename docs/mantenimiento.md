# Mantenimiento y respaldo

Implementación del 22/10/2026. La presencia de estos archivos no demuestra que
exista un respaldo correcto: comprueba la última ejecución en Actions y /estado.

Publicación realizada en `AlvaroVZ14/IntegradorTransversal`; workflows copiados al
repositorio privado `AlvaroVZ14/mente-futuro-mantenimiento`. Se configuraron
`SUPABASE_URL`, `APP_URL`, `BACKUP_ENCRYPTION_KEY` y `MAINTENANCE_ENABLED=true`.
La tabla y la RPC de respaldo existen en el proyecto conectado y bloquean acceso
anónimo. **Pendiente: agregar `SUPABASE_SERVER_KEY` al repositorio privado y
comprobar el primer respaldo.** No hay una copia automática confirmada por esta
configuración todavía. La clave de recuperación queda también en el archivo
local `.streamlit/secrets.toml`, excluido de Git; conservarla en un gestor privado.

## Límites reales del plan gratuito

- Streamlit Community Cloud duerme apps después de **12 horas sin tráfico**.
  Cualquier visitante autorizado puede pulsar **Yes, get this app back up!**.
  El workflow revisa HTML y `/_stcore/health` cada dos días; esa frecuencia no evita
  una suspensión a las 12 horas. Un HTTP 200 puede ser una página de hibernación:
  se detectan sus mensajes conocidos, redirecciones y respuestas de salud inválidas.
  Incluso pasar ambos controles **no demuestra** que Auth, WebSocket y el envío
  del formulario funcionen. No hay una garantía documentada de que pings HTTP
  mantengan la app despierta; aumentar su frecuencia no permite prometerlo.
- Supabase Free puede pausar por **baja actividad durante 7 días**, no únicamente
  por ausencia absoluta de consultas. La documentación dice que unas pocas
  consultas de usuario al día suelen bastar. Una consulta cada dos días ayuda a
  detectar disponibilidad, **no garantiza** evitar pausas. Si se pausa, entrar al
  panel y usar **Resume project**. Actualmente la ventana de reanudación es de un año.
- GitHub Actions puede retrasar o descartar ejecuciones programadas. Solo ejecuta
  cron desde la rama predeterminada. En repositorios públicos los cron se desactivan
  tras 60 días sin actividad. Usamos un repositorio privado, pero sus cuotas,
  incidencias, deshabilitación manual y vencimiento de artefactos siguen aplicando.
- No se crean commits artificiales, sesiones falsas ni cambios de planes.

**Alternativa gratuita para no perder el primer contacto:** mantener un formulario
alternativo de Google Forms con almacenamiento de respuestas y compartir también
su enlace directo como puerta de entrada. Requiere
configurar ese formulario y revisar/importar las respuestas; no se ha añadido ni
publicado uno en esta entrega. Un monitor externo tampoco garantiza que Streamlit
permanezca activo. Con estos dos planes gratuitos no podemos prometer disponibilidad
continua y reanudación automática sin intervención. Para una garantía más fuerte
hay que evaluar un alojamiento que no hiberne y el plan apropiado de la base.
La alternativa conserva respuestas fuera de Streamlit; consulta las funciones de
[Google Forms](https://developers.google.com/workspace/forms/api/guides).

Fuentes oficiales consultadas:
[Streamlit: administración e hibernación](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app),
[Supabase: pausas](https://supabase.com/docs/guides/platform/free-project-pausing),
[Supabase: respaldos](https://supabase.com/docs/guides/platform/backups),
[GitHub: cron](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[GitHub: acceso y caducidad de artefactos](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).

## Activación, una sola vez

1. Aplica en SQL Editor **completo** `supabase/migrations/202610220005_mantenimiento.sql`
   después de las migraciones 001–004 del 22/10 y las anteriores del proyecto.
   No pegues la clave de servidor en SQL. No cambia estados ni permisos comerciales.
   Si ya se aplicó correctamente, no ejecutarla de nuevo. Reversión:
   `supabase/rollback/202610220005_mantenimiento.sql`; retira también la nueva UI
   si quieres desactivar la función por completo. Los CSV de GitHub no se eliminan.
2. Publica los archivos actualizados de la app en su repositorio habitual.
   En **Configuración**, después de las opciones actuales, aparece Respaldo;
   `/estado` es una ruta registrada únicamente para Administración y oculta del menú.
   Cliente no recibe esta página ni permisos de descarga en SQL.
3. Crea un repositorio **privado** de mantenimiento, por ejemplo
   `mente-futuro-mantenimiento`, con Issues y Actions habilitados. Copia allí:
   `.github/workflows/mantenimiento.yml`, `.github/workflows/respaldo-semanal.yml`,
   `scripts/mantenimiento.py`, `servicios/respaldos.py`,
   `requirements-mantenimiento.txt` y esta guía. Conserva las mismas carpetas.
   No copies `secrets.toml`, `.env`, archivos de clientes o ZIP descargados.
   Estos scripts solo usan biblioteca estándar y cryptography: no requieren
   Streamlit ni desplegar otra app. Mantén esas copias actualizadas al cambiar
   el esquema de la aplicación.
4. En ese repositorio privado: **Settings → Secrets and variables → Actions →
   Repository secrets → New repository secret**:

   | Secreto | Contenido |
   | --- | --- |
   | `SUPABASE_URL` | URL HTTPS del proyecto, `https://REFERENCIA.supabase.co`, sin `/rest/v1` |
   | `SUPABASE_SERVER_KEY` | Clave secreta `sb_secret_…` o `service_role` del proyecto. Nunca la anon/publicable |
   | `APP_URL` | URL pública HTTPS de la aplicación, terminada en `.streamlit.app/` |
   | `BACKUP_ENCRYPTION_KEY` | 32 bytes aleatorios codificados en Base64; ver generación abajo |

   En **Variables**, crea `MAINTENANCE_ENABLED` con valor `true`. Cambiar a `false`
   desactiva ambos cron; **Run workflow** sigue permitiendo una prueba manual.
   No hace falta PAT, contraseña SMTP ni contraseña de la usuaria: `github.token`
   existe automáticamente y solo necesita `contents: read` e `issues: write`.
   Si una política de la organización bloquea Issues, corrígela antes de activar.
5. Genera la clave localmente, con Python, y copia el resultado al secreto:

   ```powershell
   python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
   ```

   Guarda también la clave en el gestor de contraseñas de la dueña, fuera de
   GitHub: GitHub no vuelve a mostrar el valor. Si se pierde, los respaldos no se
   pueden descifrar. Al rotarla, conserva las anteriores para copias antiguas.
   La clave de servidor puede leer toda la base: solo debe estar en los secretos
   de este repositorio privado con acceso limitado. **No sustituye `SUPABASE_KEY`
   publicable de Streamlit**; la app sigue usando Auth y RLS con la sesión real.
6. En **Actions**, ejecuta primero **Respaldo semanal cifrado → Run workflow**.
   Revisa que termina en verde y que existe el artefacto. Luego ejecuta
   **Comprobar disponibilidad**. Si la app está dormida, la revisión puede fallar
   aunque Supabase esté disponible. `/estado` muestra la fecha confirmada después
   de recargar. La revisión inicial sin respaldos falla a propósito.
7. Activa **Watch → All activity** en el repositorio privado y las notificaciones
   por correo de GitHub para la persona responsable. Cada fallo abre/actualiza
   una issue sin datos de clientes; la siguiente ejecución correcta la cierra.
   Las notificaciones dependen de la configuración de GitHub, no de SMTP de la app.
   Si GitHub no llega a iniciar un workflow, este no puede crear una issue: mira
   también el aviso de respaldo antiguo en Configuración.

Ambos workflows se **omiten en repositorios públicos**, incluso al ejecutarlos a
mano. No basta con copiarlos al repositorio público de la app. Para esta cuenta
ya se creó el repositorio privado y la programación está habilitada, pero aún
necesita el secreto administrativo pendiente para poder generar respaldos.

## Qué se respalda y dónde

Cada lunes 09:43 UTC se genera un ZIP de CSV desde una única llamada SQL STABLE
(misma instantánea entre tablas). El monitor corre a las 10:17 UTC cada dos días,
con posibles intervalos de tres días entre meses. No inicia sesión como cliente,
no registra casos ficticios y no envía correos comerciales.

Nombres **reales** del esquema:

| Categoría | Tabla |
| --- | --- |
| Cuentas/clientes | `mf_perfiles`; los contactos y empresas están también en `mf_casos` |
| Casos y solicitudes | `mf_casos` |
| Cotizaciones y ventas | `mf_cotizaciones`, `mf_ventas` |
| Tarifas y programas | `mf_tarifas`, `mf_plantillas_programa` |
| Historial y correos | `mf_eventos_caso`, `mf_envios_cotizacion` |
| Configuración y borradores | `mf_configuracion`, `mf_borradores_cotizacion` |
| Mantenimiento | `mf_mantenimiento` |

Tablas vacías conservan cabeceras. JSON anidado se conserva como JSON. El
`manifest.json` registra fecha de instantánea, columnas y tipos, columnas generadas
e identity, cantidades, SHA-256 por CSV y posiciones de celdas nulas (para distinguir
NULL de cadena vacía). No se altera contenido que parezca fórmula: importa CSV
como **texto**, sin ejecutar fórmulas en Excel. No se eliminan filas anuladas ni
versiones antiguas: esto es respaldo, no un reporte de ventas.

El ZIP semanal existe solo en memoria del runner, se cifra con **AES-256-GCM**, se
verifica su descifrado y se sube exclusivamente `respaldo.mfy` como artefacto del
repositorio privado. No se comitea, no usa Storage del mismo Supabase y no queda
en logs. Solo después de confirmar la subida se registra el éxito en
`mf_mantenimiento` (ID de artefacto, SHA-256 del cifrado y enlace de ejecución).
Si la base no permite registrar el éxito, puede existir un artefacto válido pero
la fecha no avanzará: consulta Actions. Una copia manual no cambia esa fecha.

Retención: **28 días**, unas cuatro copias semanales; no es archivo permanente.
Vigila la cuota gratuita de Actions y de artefactos. Si cambia la retención de
GitHub, se borra un artefacto a mano o se elimina el repositorio, la fecha de éxito
histórica no demuestra que esa copia siga existiendo. La descarga manual ZIP de
Configuración es directa, con un clic, y **no está cifrada**: mantenerla privada.
No añade dependencias al runtime de Streamlit; solo el job y pruebas usan
`requirements-mantenimiento.txt` (`cryptography>=46,<51`).

La exportación falla explícitamente si supera **100.000 filas por tabla o 50 MiB
de JSON total**, o si falta cualquier tabla/columna. Nunca presenta una copia
parcial como completa. Para volúmenes mayores usa `supabase db dump`/`pg_dump`.
Puede fallar antes por límites de memoria o timeout del plan; se avisa como fallo.

**Alcance:** todos los datos comerciales de estas 11 tablas. No es una imagen
completa de PostgreSQL: no incluye `auth.users`, contraseñas, sesiones, objetos
Storage, funciones, políticas, secuencias ni claves. Conserva las migraciones de
este proyecto para el esquema. Para recuperar un proyecto perdido por completo
se necesita además un dump de PostgreSQL/Auth y respaldo de Storage; Supabase
recomienda exportaciones externas para Free. No prometemos recrear cuentas desde
estos CSV.

## Recuperar y verificar una copia

1. GitHub privado → Actions → ejecución correcta de Respaldo → Artifacts.
   Descarga y extrae el contenedor de GitHub: dentro está `respaldo.mfy`.
2. En un equipo privado instala `python -m pip install -r requirements-mantenimiento.txt`.
   Introduce la clave sin dejarla en el historial de PowerShell:

   ```powershell
   $claveRespaldo = Read-Host 'Clave de respaldo (Base64)' -AsSecureString
   $env:BACKUP_ENCRYPTION_KEY = [System.Net.NetworkCredential]::new('', $claveRespaldo).Password
   python scripts/mantenimiento.py decrypt --input respaldo.mfy --output respaldo-recuperado.zip
   Remove-Item Env:BACKUP_ENCRYPTION_KEY
   ```

   Clave incorrecta o manipulación del cifrado producen error y **ningún ZIP**.
   Un archivo de salida existente no se sobrescribe. Comprueba el SHA-256 del
   cifrado contra el registro y el de los CSV contra el manifiesto.
3. Antes de restaurar, entrega el ZIP al responsable técnico. Prueba primero en
  una base aislada: aplica el esquema, conserva/reconcilia UUID de Auth, respeta
   FK, omite columnas generadas y ajusta las secuencias identity al máximo final.
   No importes estos CSV directamente sobre producción desde una planilla.
   No hay restauración automática/destructiva en la app.

## Pruebas sin datos reales

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p 'test_*.py' -q
node tests/test_mantenimiento.mjs
```

La prueba SQL usa el PostgreSQL efímero PGlite de `tmp/db-test` ya utilizado por
las otras pruebas; si falta, instala `npm install --prefix tmp/db-test --no-audit
--no-fund @electric-sql/pglite`. No usa el proyecto vivo.

| Prueba | Qué debería verse |
| --- | --- |
| Administración abre `/estado` | Conexión, última copia automática, último código/fecha de caso y conteo de correos; no muestra claves |
| Cliente intenta `/estado` o `?pagina=Estado` | Ruta no registrada para su cuenta / retorno a Nueva solicitud; RPC de respaldo devuelve permiso denegado |
| Cliente consulta `mf_mantenimiento` | Cero filas; no puede insertar ni actualizar metadatos |
| Configuración → Descargar respaldo | Un ZIP con 11 CSV y manifiesto; tablas vacías tienen cabeceras; fecha automática no cambia |
| Más de 1.000 casos ficticios | Se exportan todos: la RPC no usa paginación REST ni límite predeterminado de 1.000 |
| Supabase caído / clave inválida | Job falla y abre issue si GitHub funciona; no se registra éxito ni se borra la última fecha correcta |
| Streamlit dormido con HTTP 200 o redirección | Monitor falla; no declara que el formulario está disponible |
| Respaldo semanal | Artefacto privado cifrado, descarga/descifrado verificables y fecha actualizada después de la subida |
| Clave incorrecta/cifrado alterado | Descifrado rechazado sin crear ZIP |
| Repositorio público / variable false | Jobs omitidos; configurar el repositorio privado o activar la variable, respectivamente |
| Sin respaldo o más de 9 días | Monitor alerta; Configuración avisa de antigüedad cuando hay fecha anterior |

Las pruebas locales cubren formato, más de 1.000 filas, tablas vacías, nulos,
JSON, cifrado, alteración, respuestas HTTP falsas y permisos SQL. La ejecución
real en GitHub y la revisión visual del artefacto quedan para después de configurar
los secretos; no se han utilizado datos reales ni provocado una caída de producción.

Verificación local: 113 pruebas Python aprobadas y prueba SQL de mantenimiento
aprobada, incluida exportación de 1.001 casos ficticios. Los dos YAML se analizaron
con un lector YAML temporal; no se ha ejecutado GitHub Actions con secretos reales.
