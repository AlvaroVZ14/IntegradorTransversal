# Estado del proyecto · 25/10/2026

Actualización del 26/10/2026: la raíz ahora muestra login o recupera la sesión; `?vista=solicitud` es una entrada pública independiente, incluso con cuenta abierta. La persistencia de sesión incluye Administración y Cliente. [Informe vigente, archivos y pruebas](entradas_y_sesion.md). Lo que sigue registra la entrega anterior.

## Última entrega funcional

Commit `fa14018`: Compartir con enlaces por canal, QR y atribución de solicitudes. Publicado en `origin/main`.

- Formulario único público, cliente e interno, con tres pasos y borradores.
- Entrada pública sin cuenta; acceso de cuentas mediante `?vista=acceso`.
- Administración: Hoy, Nueva solicitud, Casos y cotizaciones, Compartir y Dashboard. Cliente: solo el formulario.
- Sesión recordada de Administración y navegación con rutas registradas de forma estable.
- Compartir: seis canales, textos editables, QR PNG/SVG, acceso desde Hoy y campo `canal_captacion`.
- Chip de canal en el caso y gráfico de solicitudes por canal, usando los filtros existentes.

## Comprobaciones realizadas

Regresión de 164 pruebas aprobada, seguida de 9 pruebas finales específicas de Compartir. Pruebas SQL de canales, permisos, reintentos, lectura en vivo y rollback aprobadas. Lectura independiente de los seis QR originales y a tamaño de vista previa aprobada. Revisión visual local en 375, 768 y 1440 px, sin desbordamiento horizontal ni excepciones visibles.

Las pruebas utilizan datos ficticios y una base efímera; no son una comprobación de envíos reales ni de la configuración actual de producción.

## Configuraciones que se deben confirmar

- La última captura compartida por el usuario mostraba Compartir funcionando en una dirección local, con `url_publica` sin configurar. Confirmar que se haya guardado la dirección publicada en Casos y cotizaciones → Configuración → Formulario: contacto, redes y privacidad. La dirección debe permanecer en Supabase, no fijarse en el código.
- Confirmar aplicación de las migraciones en el entorno que se esté utilizando. No repetir migraciones ya ejecutadas. La guía de Compartir indica dependencias y orden.
- SMTP de confirmación y avisos a la dueña requieren configuración del proveedor y secretos en sus paneles. No se ha verificado su activación real ni se guardan credenciales en este registro.
- Pendiente validación con celular físico, incluido el escaneo QR y navegadores internos de redes sociales.

## Archivos para retomar

- [Formulario unificado y configuración de correo](formulario_unificado.md).
- [Compartir: activación, pruebas y resultados esperados](compartir.md).
- [SQL de Compartir](../supabase/migrations/202610240002_compartir_canales.sql).
- [Rollback de Compartir](../supabase/rollback/202610240002_compartir_canales.sql).
- Archivo completo con capturas generado localmente: `output/mente-futuro-compartir-canales.zip` (excluido del repositorio).

No guardar contraseñas ni tokens en documentación, código, capturas o respaldos públicos.
