# Datos para el pago en las cotizaciones

Prompt 22. Datos de transferencia exclusivamente en el documento y en su editor administrativo. No hay nuevas dependencias ni SQL que ejecutar.

## Comportamiento

En Tu propuesta a medida → Condiciones aparece Datos para el pago, con Incluir datos de pago activado inicialmente y siete campos editables: titular, RUT, banco, tipo de cuenta, número de cuenta, correo del titular y correo para comprobantes.

Se leen los valores de `[pago]` en `st.secrets` al preparar un borrador que aún no tiene ese bloque. Se copian a ese borrador; las ediciones no alteran secretos ni otras cotizaciones. Reabrir un borrador conserva lo editado. Si el borrador se preparó antes de agregar los secretos y quedó vacío, se pueden completar sus campos a mano; los casos nuevos toman los secretos nuevos.

Los siete campos deben estar completos para imprimir el bloque. Si falta alguno, el editor avisa y PDF/Word omiten la sección sin bloquear la generación. No se imprime información bancaria parcial. El interruptor apagado también la omite, conservando los campos para poder volver a activarlo. Se normalizan espacios; datos de tipos inesperados o excesivamente largos se consideran incompletos, sin truncar números de cuenta silenciosamente.

PDF: sección final después de Condiciones generales, título azul con línea cálida, tabla de dos columnas y seis filas, bordes finos. Debajo se indican el correo para comprobantes y “Indicar el N° de cotización en el asunto”. Si no hay espacio, título, tabla e instrucciones pasan juntos a la página siguiente con KeepTogether, sin dividir filas.

Word: mismo contenido y estilos. Las filas tienen `cantSplit`; el título, párrafos de las celdas e instrucciones se encadenan con `keep_with_next` para mantener el bloque unido. No se usa Word ni LibreOffice al generar.

La vista previa usa el mismo generador PDF. Todo el bloque (`pago` e `incluir_pago`) queda en `mf_cotizaciones.documento`, JSONB existente, al generar la versión. Los generadores usan solo ese snapshot, sin consultar secretos. Cambiar secretos o editar otro borrador no altera una versión emitida. No se añaden datos de pago a versiones históricas que no los guardaron.

No se encontraron bloques bancarios que quitar en el formulario público, confirmación, registro de cliente o cuenta de cliente. Las pantallas y permisos permanecen iguales. Se conserva la edición administrativa de estado de pago de una venta: esa función no es un bloque bancario del cliente.

## Cargar los datos reales en Community Cloud

El archivo `secrets.toml.example` contiene **solo datos ficticios**. No sirve para recibir pagos y no se carga automáticamente.

1. Iniciar sesión en Streamlit Community Cloud con la cuenta que administra la app.
2. Desde el espacio de aplicaciones, abrir el menú ⋮ junto a esta aplicación y elegir **Settings → Secrets**. También se puede entrar desde **Manage app → ⋮ → Settings**.
3. Conservar los secretos existentes, como las claves de Supabase, y agregar al final la sección `[pago]` del ejemplo. Reemplazar sus siete valores por los datos reales. No duplicar `[pago]` si ya existe: editar la sección existente.
4. Mantener todos los valores entre comillas, especialmente RUT y número de cuenta, para conservar guiones y ceros iniciales.
5. Pulsar **Save**. Abrir un caso nuevo y revisar Condiciones; los campos deben aparecer completos. Generar una cotización de prueba y comprobar el bloque antes de enviarla.

Procedimiento verificado en la [documentación oficial de ajustes de Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings) y en [gestión de secretos](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

Para desarrollo local, copiar solo `[pago]` con los valores reales a `.streamlit/secrets.toml`, junto a los secretos existentes. Ese archivo está excluido de Git; también se excluye cualquier archivo llamado `secrets.toml`. No editar el ejemplo con valores reales ni subirlo así a GitHub. Los reales no se cargaron ni se mostraron durante esta tarea.

## Verificación

Resultado: **207 pruebas Python aprobadas**, incluidas las cuatro pruebas nuevas del bloque de pago. Las verificaciones usan datos ficticios y no consultan los datos bancarios reales ni escriben cotizaciones en producción.

Pruebas en `tests/test_pago_cotizacion.py` con valores del ejemplo ficticio:

| Prueba | Resultado esperado |
|---|---|
| Datos completos | Tabla e instrucciones presentes en PDF y Word, después de condiciones. |
| Sin datos o incompletos | Documento generado normalmente sin sección ni información parcial. |
| Interruptor apagado | Sección ausente; los valores siguen disponibles en el borrador. |
| Número distinto en una cotización | Solo esa versión tiene la cuenta alternativa; otra cotización toma la cuenta inicial. |
| Reabrir borrador | Mantiene la edición particular, sin recargarla desde secretos. |
| Cambiar datos después de emitir | La versión anterior conserva su snapshot y su documento. |
| Poco espacio | Título, seis filas e instrucciones se encuentran completos en la página siguiente. |
| Cliente o enlace público | No hay campos ni bloques bancarios; sigue disponible el formulario habitual. |

Se generaron cinco muestras ficticias en `output/pago-cotizacion/` (fuera de Git). Se renderizaron e inspeccionaron el PDF normal con pago y la sección trasladada completa a una tercera página, comparando colores, tipografía y tablas con el documento del Prompt 19. Word se verificó por contenido y propiedades OOXML para mantener las filas juntas. La revisión visual de Word sigue pendiente: LibreOffice no está instalado y la prueba anterior con Word instalado se bloqueó; no se repitió esa automatización ni se afirma haber comprobado su paginación visual.

```powershell
python -m unittest discover -s tests -p 'test_pago_cotizacion.py' -q
python -m unittest discover -s tests -p 'test_*.py' -q
```

Para generar nuevamente las muestras ficticias desde la raíz, usando PowerShell:

```powershell
$env:PYTHONPATH=(Get-Location).Path
python tests/test_pago_cotizacion.py
```

## Archivos completos

`.gitignore`, `secrets.toml.example`, `servicios/pago_cotizacion.py`, `servicios/propuesta_documento.py`, `servicios/documentos_propuesta.py`, `paginas/cotizador.py`, `utils/cotizacion_borrador.py`, `tests/test_app.py`, `tests/test_pago_cotizacion.py` y este documento.
