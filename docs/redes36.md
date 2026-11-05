# Prompt 36: redes de la consultora en el formulario

## Qué se reutilizó

El formulario ya tiene una sola implementación para público, cuenta de cliente
y Administración. Ya había dos enlaces básicos en su encabezado, obtenidos
de la configuración pública. Se sustituyó ese punto por un componente común;
no se añadieron formularios ni se alteraron campos, permisos, consentimiento,
honeypot, borradores, canales de captación o guardado.

Este prompt cambia expresamente la fuente de la identidad pública del
formulario: nombre, sitio, correo y redes salen de `servicios/marca.py`.
No se repiten sus URLs en otros archivos. La política de privacidad sigue
leyéndose de la configuración existente. Los datos antiguos de configuración
no se borran ni se migran; sus campos de contacto/redes ya no determinan los
enlaces de marca del formulario. Otras funciones que usan esa configuración
conservan su comportamiento.

## Qué debe verse

| Modo o pantalla | Encabezado | Bloque final | Confirmación |
|---|---|---|---|
| Formulario público | Íconos y Volver al sitio | Conoce a Mente y Futuro | Mientras tanto, conócenos |
| Solicitar servicio, cuenta cliente | Los mismos enlaces | El mismo bloque | Los mismos enlaces |
| Nueva solicitud, Administración | Sin redes en el encabezado | Solo el bloque final | Sin bloque adicional de redes |

El bloque final incluye «Charlas, talleres, capacitaciones y coaching».
Las redes de la empresa **del cliente** siguen siendo campos opcionales
independientes (Prompt 27), sin cambios.

## Enlaces pendientes

Los únicos valores públicos están en `servicios/marca.py`:

- Sitio y correo: los indicados en el prompt.
- Instagram: URL construida a partir del usuario entregado, con conexión
  segura y sin parámetros de seguimiento.
- Facebook: enlace confirmado por el usuario; se quitaron los parámetros de
  redirección y el fragmento vacío. El destino canónico vive solo en marca.py.
- **YouTube: falta la URL oficial.** Marcador TODO y valor vacío.
- **LinkedIn: falta la URL oficial.** Marcador TODO y valor vacío.

Se confirmó Facebook después de la entrega inicial; no se adivinaron perfiles.
YouTube y LinkedIn permanecen ocultos. Para completarlos basta
actualizar las entradas correspondientes en ese archivo y publicar el cambio.

Comprobación externa: la herramienta web pudo consultar el sitio indicado;
Instagram devolvió «Failed to fetch / Cache miss», así que **no se da por
verificada la disponibilidad ni la titularidad del perfil**. Facebook fue
confirmado por el usuario; YouTube y LinkedIn no se probaron contra sitios
reales porque faltan sus direcciones.
El correo se conserva como contacto; no se enviaron mensajes de prueba.

## Diseño, accesibilidad y privacidad

SVG en línea, sin paquetes, fuentes, imágenes ni scripts de terceros.
Íconos monocromos azules sobre fondo circular suave; hover morado y
desplazamiento de 2 px. Los objetivos táctiles miden 44×44 px, con foco visible,
etiqueta accesible, tooltip, pestaña nueva y `rel="noopener noreferrer"`.
Se desactiva el movimiento con `prefers-reduced-motion` y con el modo ligero
existente. Las cuatro redes ocupan 200 px en total: la fila de íconos no se
divide, mientras el enlace al sitio puede pasar a otra línea.

El código no visita las redes para construir la pantalla. Los enlaces no
cargan widgets, contenido embebido ni rastreadores. Permanecen las conexiones
de la aplicación que ya existían con Supabase y los recursos propios del portal;
«sin peticiones externas» se refiere a no añadir peticiones a redes sociales.

Todo el CSS está en `ui/tema.py`, en un bloque que se carga solo con el
formulario; usa clases propias, sin sobrescribir selectores internos nuevos.
Los destinos vacíos, inseguros o con credenciales/parámetros quedan ocultos.

## Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| Cuatro redes ficticias, cada ubicación | Correcto: mismos cuatro destinos y SVG locales |
| URL vacía o esquema peligroso | Correcto: ícono omitido, sin enlace roto |
| Accesibilidad y enlaces | Correcto: etiqueta, tooltip, pestaña nueva y rel seguro |
| Público: formulario → envío simulado → confirmación | Correcto: tres ubicaciones, sin crear sesión y con mensaje de 48 horas |
| Administración | Correcto: solo bloque final; campos de redes del cliente intactos |
| Cliente con cuenta | Correcto: encabezado y pie con los mismos destinos |
| Regresión del formulario | 15 pruebas existentes correctas: validaciones, consentimiento, honeypot, identidad y flujo |

`tests/test_marca36.py`: **4/4 correctas**, usando datos ficticios.
`python -m unittest discover -s tests -p 'test_formulario*.py'`: **15/15 correctas**.
Sin correos, cuentas ni escrituras reales.

### Revisión visual pendiente

El navegador automatizado no estuvo disponible: «The browser access host is
unavailable». No se tomaron capturas ni se presentan como aprobadas las
pruebas visuales de 375, 768 y 1280 px.

1. Abre el formulario público en esos anchos. Deben verse Instagram y Facebook
   en el encabezado y en el pie; YouTube y LinkedIn siguen ocultos.
2. Toca el ícono: debe abrir otra pestaña y conservar lo escrito en la app.
   Vuelve y comprueba también el tooltip con mouse y el foco con Tab.
3. Envía una solicitud ficticia con consentimiento. Debe aparecer el mismo
   ícono bajo «Mientras tanto, conócenos», conservando número y mensaje de éxito.
4. Como Administración, abre Nueva solicitud. Las redes deben aparecer solo
   al final; los campos donde el cliente registra sus redes no cambian.
5. Con las herramientas de red del navegador, filtra por dominios de redes:
   al cargar no deben aparecer peticiones a ellos; solo al pulsar el enlace.

## Archivos completos y activación

- `servicios/marca.py`: única fuente y validación de destinos públicos.
- `ui/tema.py`: componente común, cuatro SVG y estilos del formulario.
- `paginas/formulario.py`: integración según modo y pantalla.
- `tests/test_marca36.py`: pruebas de enlaces, omisión y recorridos.
- Este informe.

**Sin SQL, cambios de base de datos ni dependencias nuevas.** No necesitas
ejecutar nada en Supabase. Tras publicar, recarga el formulario para verlo.
