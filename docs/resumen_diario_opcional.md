# Resumen diario opcional pendiente de implementar

Esta entrega no crea tareas programadas ni envíos diarios. Hoy funciona mientras se usa la app, sin un servidor de programación adicional. Se eligió la alternativa documentada para no mezclar el nuevo apoyo diario con una automatización externa que requiere credenciales, cuotas y manejo de fallos propios.

Para una fase posterior:

1. Crear un script aislado que lea Supabase desde GitHub Actions, reutilice `servicios.hoy.pendientes` y prepare un resumen para la administradora únicamente si hay tareas. No debe cambiar estados, marcar contactos ni ejecutar cierres.
2. Guardar URL y clave de servidor de Supabase, credenciales SMTP y destinatario solo en GitHub Secrets. La clave de servidor no corresponde a la app web ni debe publicarse en código, ZIP, logs o navegador. El cliente público actual rechaza esas claves por diseño.
3. Incorporar una opción de configuración de resumen diario, inicialmente desactivada. Cada ejecución debe leerla y terminar sin enviar si está apagada, aunque siga activo el cron.
4. Añadir un registro de avisos diarios independiente del de cotizaciones: fecha de Chile como clave única, intento, estado y error reducido, sin credenciales. La tabla actual de envíos exige una cotización y no debe llenarse con cotizaciones ficticias para representar un resumen.
5. Reservar el aviso de esa fecha antes de contactar SMTP y no reenviar automáticamente un resultado incierto. Guardar el fallo permitirá mostrarlo en Hoy cuando esa integración exista.
6. Configurar cron en la rama predeterminada y un disparador manual para probar primero con un destinatario ficticio/sistema de correo de pruebas. Una propuesta es 09:15 en America/Santiago, considerando el cambio estacional de hora. GitHub documenta horarios UTC por defecto y la opción de zona IANA; también posibles retrasos y desactivación de programaciones de repositorios públicos tras 60 días sin actividad. [Programación de workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
7. Antes de activarlo, comprobar las cuotas y políticas del repositorio concreto; esta entrega no promete ejecución gratuita ilimitada ni puntualidad de un cron externo.

Se desactivaría mediante la futura opción de configuración y, además, deshabilitando el workflow en Actions. No basta con cerrar Streamlit para detener una tarea de GitHub. Ninguno de estos pasos está habilitado actualmente.
