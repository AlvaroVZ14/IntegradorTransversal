# Navegación superior

Cambio limitado al marco de navegación y a la ubicación de la marca. Se mantienen los colores, tipografías, campos, consultas, funciones y comprobaciones de autorización existentes.

## Implementación

Streamlit instalado: **1.65.0**, compatible con `st.navigation(position="top")` y `st.Page(visibility=...)`. Se utiliza el menú nativo en escritorio. Todas las URLs conocidas siguen registradas; solo son visibles las secciones del rol verificado. Inicio y Estado mantienen su carácter oculto. La página elegida continúa pasando por `guard_route`, y cada página conserva su propia protección.

La navegación se registra después de verificar la cuenta y antes de resolver/ejecutar su destino. Durante una restauración fallida o una pantalla de acceso se registra sin enlaces visibles. No se modifica cómo se guardan o restauran las sesiones.

La administración mantiene Hoy, Nueva solicitud, Casos y cotizaciones, Compartir y Dashboard. Si se añaden más de cinco secciones, las primeras cuatro quedan visibles y el resto se agrupa en **Más**. Streamlit también agrupa automáticamente los enlaces que no caben; un componente v2 existente en la plataforma traduce ese control a Más.

En celulares se combina la marca nativa con una hamburguesa hecha con `st.popover` y `st.page_link`: el control nativo utiliza otro comportamiento móvil, por lo que este complemento garantiza una lista vertical en español, objetivos de 48 px y cierre al elegir una página. La barra mide 64 px. No se agrega ninguna dependencia.

Mi cuenta reúne la identidad y el cierre de sesión existentes. Cliente solo recibe Nueva solicitud y las acciones de su cuenta. La URL pública conserva únicamente la marca en la barra; los enlaces sociales configurados, el contenido y las acciones del formulario se conservan en su cabecera/cuerpo.

## Archivos

- `app.py`: integra el menú superior tras verificar la cuenta; elimina el montaje lateral, manteniendo las guardias y la ejecución de páginas.
- `utils/navegacion.py`: registro con visibilidad por rol, barra de cuenta, marca pública, hamburguesa y ajustes de accesibilidad/cierre.
- `utils/estilos.py`: estilos centrales de la barra fija, enlace activo, foco, marca y adaptación móvil; reutiliza las variables de color existentes. Se documentan los selectores internos de Streamlit sobrescritos.
- `paginas/formulario.py`: evita duplicar la marca y la barra de cuenta que ahora están en el marco superior; conserva campos y envío.
- `tests/test_app.py` y `tests/test_recarga.py`: adaptan las expectativas del menú lateral al nuevo menú por rol.
- `tests/test_navegacion_superior.py`: verifica URLs estables, visibilidad por rol, navegación nativa y agrupación Más.

## Cómo probar

Ejecutar desde la carpeta del proyecto:

```powershell
python -m streamlit run app.py
```

1. Ingresar con Administración: logo a la izquierda, cinco secciones a la derecha, página activa resaltada y Mi cuenta con nombre, rol y Cerrar sesión. Abrir las cinco secciones y recargar: deben mantener sus rutas sin mostrar Page not found.
2. Usar las herramientas de desarrollo del navegador en 360, 375 y 430 px: la barra mide como máximo 64 px; Menú abre los enlaces en vertical, cada uno de al menos 44 px. Elegir una sección cierra el desplegable. No debe aparecer desplazamiento horizontal. Revisar también 768 px y escritorio: si no caben los enlaces, aparece Más.
3. Ingresar con Cliente: solo Nueva solicitud y las acciones de su cuenta. Nombre y correo siguen precargados y bloqueados. Abrir `/dashboard`, `/casos` o `/compartir`: vuelve a Nueva solicitud sin cargar datos administrativos.
4. Abrir `?vista=solicitud` sin sesión y con ambas cuentas: solo la marca en la barra, sin menú administrativo, y el formulario habitual. Los canales y el consentimiento siguen funcionando.
5. Usar Cerrar sesión desde Mi cuenta o desde la hamburguesa: debe aparecer el ingreso; una recarga no debe recuperar esa sesión.
6. Recorrer los enlaces con Tab y abrir los menús con el teclado: el foco debe ser visible y la página actual debe distinguirse también por su indicador/borde.

## Validación y límites

Las pruebas de datos y acceso usan cuentas y repositorios ficticios; no modifican Supabase ni crean solicitudes reales. La revisión visual usa Edge con tamaños de pantalla simulados, no teléfonos físicos. Al actualizar Streamlit, revisar los selectores `stHeader`, `stHeaderLogo`, `stTopNav*` y el comportamiento de sus popovers. No requiere migración SQL ni secretos nuevos.

Se ejecutaron las 174 pruebas existentes: 173 pasaron en la primera ejecución y una expectativa del menú necesitó excluir el enlace de contenido «Ir a Compartir». Corregido el ayudante de prueba, ese caso y las dos pruebas nuevas pasaron. Las comprobaciones en navegador cubrieron Administración, Cliente, URL administrativa denegada, formulario público, cierre del menú al navegar y ausencia de Page not found. La barra midió 64 px y los enlaces móviles 48 px; no se detectó desborde horizontal en los anchos revisados.

Documentación oficial: https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation
