"""Sistema visual compartido. Todo el CSS de la interfaz vive en este archivo."""
AZUL = "#3D6FE0"
AZUL_CLARO = "#6699FF"
MORADO = "#9966FF"
AMARILLO = "#FFCC00"
LAVANDA = "#CCCCFF"
TEXTO = "#0B2545"
SECUNDARIO = "#5B6B82"
PALETA = [AZUL, AZUL_CLARO, MORADO, "#B794FF", AMARILLO, LAVANDA]
TEMA_BARRA_LATERAL = "oscuro"  # Cambiar a "claro"; ambas paletas están en :root.

# Color de gráfico, fondo y texto accesible: una fuente para todos los estados.
ESTADOS_COLORES = {
    "Solicitud": (AZUL, "#EAF0FF", "#244FAF"),
    "Cotizada": (MORADO, "#F1EAFF", "#6533A8"),
    "Aceptada": ("#32956B", "#E7F5ED", "#216342"),
    "En seguimiento": (AMARILLO, "#FFF6CC", "#705800"),
    "Cerrada": ("#8793A5", "#EDF0F4", "#4D5C71"),
    "Rechazada": ("#E99A9F", "#FCECEE", "#963D47"),
}

ESTILOS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
:root{
 --mfy-blue:#3D6FE0;--mfy-blue-light:#6699FF;--mfy-purple:#9966FF;
 --mfy-yellow:#FFCC00;--mfy-lavender:#CCCCFF;--mfy-text:#0B2545;
 --mfy-muted:#5B6B82;--mfy-bg:#F6F8FC;--mfy-white:#FFF;--mfy-border:#E4E9F2;
 --mfy-lavender-soft:color-mix(in srgb,var(--mfy-lavender) 22%,white);
 --mfy-gradient:linear-gradient(135deg,var(--mfy-blue),var(--mfy-purple));
 --mfy-shadow:0 6px 24px #0B254507;--mfy-shadow-hover:0 12px 32px #3D6FE015;
 --mfy-card-radius:16px;--mfy-button-radius:12px;--mfy-hero-radius:20px;
 --mfy-entry:300ms;--mfy-entry-delay:0ms;
 /* Dos paletas de navegación; los alias --mfy-nav-* se generan al final. */
 --mfy-nav-dark-background:radial-gradient(ellipse at 45% 100%,#9966FF20,transparent 55%),linear-gradient(160deg,#0B2545,#1B2F6B);
 --mfy-nav-dark-text:#FFF;--mfy-nav-dark-muted:#C5D2ED;--mfy-nav-dark-icon:#D8E2F7;
 --mfy-nav-dark-hover:#FFFFFF12;--mfy-nav-dark-active:linear-gradient(#0B254533,#0B254533),var(--mfy-gradient);
 --mfy-nav-dark-active-text:#FFF;--mfy-nav-dark-active-icon:var(--mfy-yellow);
 --mfy-nav-dark-indicator:var(--mfy-yellow);--mfy-nav-dark-border:#FFFFFF26;
 --mfy-nav-dark-card:#FFFFFF0D;--mfy-nav-dark-focus:var(--mfy-yellow);
 --mfy-nav-light-background:var(--mfy-white);--mfy-nav-light-text:var(--mfy-text);
 --mfy-nav-light-muted:var(--mfy-muted);--mfy-nav-light-icon:var(--mfy-blue);
 --mfy-nav-light-hover:var(--mfy-lavender-soft);--mfy-nav-light-active:var(--mfy-lavender-soft);
 --mfy-nav-light-active-text:var(--mfy-text);--mfy-nav-light-active-icon:var(--mfy-purple);
 --mfy-nav-light-indicator:var(--mfy-purple);--mfy-nav-light-border:var(--mfy-border);
 --mfy-nav-light-card:var(--mfy-bg);--mfy-nav-light-focus:var(--mfy-blue);
}
/* Streamlit: stApp y block-container son el lienzo y el ancho del contenido. */
.stApp{background:radial-gradient(ellipse at 0 0,#6699FF0c,transparent 42%),radial-gradient(ellipse at 100% 100%,#9966FF0a,transparent 44%),var(--mfy-bg);color:var(--mfy-text);font-family:Inter,sans-serif;}
.block-container{max-width:1440px;padding:2.3rem 2rem 3rem;}
input,textarea,button,[data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"]{font-family:Inter,sans-serif;}
h1,h2,h3{font-family:Poppins,sans-serif!important;letter-spacing:-.035em;color:var(--mfy-text);}
h1{font-size:2.2rem!important;font-weight:700!important;}h2{font-size:1.5rem!important;}h3{font-size:1.12rem!important;}
summary{min-height:44px;}p{line-height:1.65;}
.mfy-sr-only{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0;}
.st-key-mfy_undo{position:fixed;right:24px;bottom:24px;z-index:9999;width:300px;max-width:calc(100vw - 32px);padding:18px;background:var(--mfy-white);border:1px solid var(--mfy-border);border-left:4px solid var(--mfy-purple);border-radius:16px;box-shadow:0 10px 32px #0B254526;}
/* Controles internos: oculta acciones/menu/pie nativos; NO el encabezado,
   el botón de navegación móvil ni el estado de ejecución. Cloud Manage app es externo. */
#MainMenu,[data-testid="stMainMenu"],[data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],footer{display:none!important;}
[data-testid="stHeader"]{background:transparent;}
/* Navegación nativa: selectores internos verificados en Streamlit 1.65.
   aria-current identifica el enlace activo sin depender solo del color.
   El enlace único usa st.page_link porque Streamlit oculta menús de una página. */
[data-testid="stSidebar"]{background:var(--mfy-nav-background);color:var(--mfy-nav-text);border-right:1px solid var(--mfy-nav-border);}
[data-testid="stSidebarContent"]{display:flex;flex-direction:column;min-height:100%;padding-top:16px;}
[data-testid="stSidebarHeader"]{height:auto;min-height:118px;flex-shrink:0;gap:12px;margin-bottom:18px;}
[data-testid="stSidebarLogo"]{background:white;padding:10px;border-radius:16px;width:100%;max-width:230px;height:auto!important;max-height:135px;box-sizing:border-box;object-fit:contain;box-shadow:0 6px 24px #00000012;}
[data-testid="stSidebarHeader"]:has([data-testid="stSidebarLogo"])>:first-child{min-width:0;flex:1;}
[data-testid="stSidebarCollapseButton"]{visibility:visible!important;opacity:1!important;flex-shrink:0;}
[data-testid="stSidebarCollapseButton"] button{min-width:44px;min-height:44px;color:var(--mfy-nav-text);}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]{color:var(--mfy-nav-text)!important;}
[data-testid="stSidebarNav"]{flex-shrink:0;padding-bottom:12px;}
[data-testid="stSidebarNavItems"]{padding:0;}
[data-testid="stSidebarNavLinkContainer"]{margin:6px 0;}
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]){position:relative;display:flex;align-items:center;gap:12px;min-height:48px;padding:12px 16px;border-radius:12px;border:1px solid transparent;box-sizing:border-box;color:var(--mfy-nav-text)!important;text-decoration:none;font-size:.9rem;font-weight:500;transition:transform 200ms ease,background 200ms ease,box-shadow 200ms ease;}
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]) p{font-size:.9rem;line-height:1.5;color:var(--mfy-nav-text)!important;white-space:normal;}
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]) [data-testid="stIconMaterial"]{font-size:24px!important;width:24px;height:24px;line-height:1;flex-shrink:0;color:var(--mfy-nav-icon)!important;}
:is([data-testid="stSidebarNavLink"][aria-current="page"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]){background:var(--mfy-nav-active)!important;color:var(--mfy-nav-active-text)!important;font-weight:700;box-shadow:0 6px 20px #00000016;}
:is([data-testid="stSidebarNavLink"][aria-current="page"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]) p{color:var(--mfy-nav-active-text)!important;font-weight:700;}
:is([data-testid="stSidebarNavLink"][aria-current="page"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"])::before{content:'';position:absolute;left:0;top:10px;bottom:10px;width:4px;border-radius:4px;background:var(--mfy-nav-indicator);}
:is([data-testid="stSidebarNavLink"][aria-current="page"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]) [data-testid="stIconMaterial"]{color:var(--mfy-nav-active-icon)!important;}
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]):focus-visible{outline:3px solid var(--mfy-nav-focus)!important;outline-offset:3px;}
:is([data-testid="stNavSectionHeader"],.mfy-nav-group){color:var(--mfy-nav-muted);font-size:.66rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;padding:10px 12px 4px;margin:8px 0 4px;}
[data-testid="stNavSectionHeader"] p{color:var(--mfy-nav-muted);font-size:.66rem;letter-spacing:.15em;}
[data-testid="stNavSectionHeader"] [data-testid="stIconMaterial"]{color:var(--mfy-nav-muted)!important;}
[data-testid="stSidebarNavSeparator"]{border-color:var(--mfy-nav-border);}
[data-testid="stSidebarUserContent"]{flex:1;display:flex;flex-direction:column;padding-top:12px;padding-bottom:20px;}
[data-testid="stSidebarUserContent"]>div{flex:1;}
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"]:has(.st-key-mfy_sidebar){flex:1;}
.st-key-mfy_sidebar{display:flex;flex-direction:column;min-height:100%;flex:1;gap:18px;}
.st-key-mfy_sidebar_bottom{margin-top:auto;padding-top:24px;}
.mfy-identity{display:flex;align-items:center;gap:12px;padding:16px 12px;margin-bottom:10px;min-width:0;border:1px solid var(--mfy-nav-border);border-radius:16px;background:var(--mfy-nav-card);}
.mfy-avatar{width:44px;height:44px;flex-shrink:0;border-radius:14px;background:linear-gradient(#0B254533,#0B254533),var(--mfy-gradient);color:white;display:grid;place-items:center;font-weight:700;font-size:.85rem;}
.mfy-identity strong{display:block;overflow-wrap:anywhere;color:var(--mfy-nav-text);font-size:.85rem;line-height:1.5;}.mfy-identity small{color:var(--mfy-nav-muted);font-size:.75rem;}
[data-testid="stSidebar"] .st-key-mfy_sidebar_bottom .stButton button{background:transparent;border:1px solid transparent;color:var(--mfy-nav-muted);box-shadow:none;justify-content:flex-start;padding:12px;min-height:44px;font-weight:500;}
[data-testid="stSidebar"] .st-key-mfy_sidebar_bottom .stButton button:hover{background:var(--mfy-nav-hover);color:var(--mfy-nav-text);transform:none;}
[data-testid="stSidebar"] .stButton button:focus-visible{outline-color:var(--mfy-nav-focus)!important;}
@media(hover:hover) and (pointer:fine){
 :is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]):hover{background:var(--mfy-nav-hover);transform:translateX(3px);}
}
/* Encabezado único: tres luces radiales suaves sobre la base azul/morado.
   La capa oscura de contraste y el brillo no requieren imágenes ni JavaScript. */
:is(.st-key-mfy_page_header,.mfy-hero){position:relative;isolation:isolate;overflow:hidden;min-height:224px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;padding:28px 32px;border-radius:var(--mfy-hero-radius);color:white;margin:0 0 18px;box-shadow:0 10px 30px #3D6FE01a;background:radial-gradient(ellipse at 96% 8%,#FFCC0024,transparent 40%),radial-gradient(ellipse at 70% 120%,#CCCCFF45,transparent 43%),radial-gradient(ellipse at 0 0,#6699FF55,transparent 48%),var(--mfy-gradient);animation:mfy-enter var(--mfy-entry) ease both;}
:is(.st-key-mfy_page_header,.mfy-hero)::before{content:'';position:absolute;inset:0;z-index:-1;pointer-events:none;background:linear-gradient(110deg,#0B25453d,#0B25452e 70%,#0B25451a);}
:is(.st-key-mfy_page_header,.mfy-hero)::after{content:'';position:absolute;inset:0;z-index:-1;pointer-events:none;background:linear-gradient(115deg,transparent 45%,#FFFFFF0b 55%,transparent 75%);}
.mfy-hero-copy{position:relative;z-index:1;padding-right:65px;}
.mfy-hero-copy h1{color:white;font-size:2rem!important;margin:8px 0 10px!important;line-height:1.25;}
.mfy-hero-copy p{margin:0;color:white;font-size:.93rem;line-height:1.6;max-width:760px;}
.mfy-eyebrow{font-size:.68rem;letter-spacing:.13em;font-weight:700;color:white;}
.mfy-hero-orbit{position:absolute;right:22px;top:22px;font-size:92px;color:#FFFFFF26;pointer-events:none;line-height:1;}
/* stHorizontalBlock es la fila nativa de las acciones, no un botón HTML. */
.st-key-mfy_page_header [data-testid="stHorizontalBlock"]{align-items:center;}
.st-key-mfy_header_actions{position:relative;z-index:2;}
/* Una sola regla para tarjetas. Los prefijos st-key son claves nuestras;
   stForm/stMetric son selectores internos de Streamlit y deben revisarse al actualizarlo. */
:is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight){position:relative;box-sizing:border-box;border:1px solid transparent;border-radius:var(--mfy-card-radius);background:linear-gradient(var(--mfy-white),var(--mfy-white)) padding-box,linear-gradient(var(--mfy-border),var(--mfy-border)) border-box;box-shadow:var(--mfy-shadow);padding:24px;transition:transform .18s ease,box-shadow .18s ease;animation:mfy-enter var(--mfy-entry) ease var(--mfy-entry-delay) both;}
:is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight)::before{content:'';position:absolute;left:16px;right:16px;top:0;height:2px;border-radius:999px;background:var(--mfy-gradient);pointer-events:none;}
[class*="st-key-mfy_form_section_s2_"]{--mfy-entry-delay:50ms;}[class*="st-key-mfy_form_section_s3_"]{--mfy-entry-delay:100ms;}
[data-testid="stColumn"]:nth-of-type(2) :is([class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"]){--mfy-entry-delay:50ms;}
[data-testid="stColumn"]:nth-of-type(3) [class*="st-key-mfy_kpi_"]{--mfy-entry-delay:100ms;}
[class*="st-key-mfy_kpi_"]{min-height:185px;}
[data-testid="stMetric"]{background:var(--mfy-white);border:1px solid var(--mfy-border);border-radius:var(--mfy-card-radius);padding:20px;}
[class*="st-key-mfy_kpi_"] [data-testid="stMetric"]{background:transparent;border:0;box-shadow:none;padding:0;}
[data-testid="stMetricLabel"]{color:var(--mfy-muted);font-size:.8rem;}[data-testid="stMetricValue"]{color:var(--mfy-text);font-size:1.7rem;font-weight:700;}
.mfy-kpi-icon{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;font-size:20px;font-weight:600;margin-bottom:4px;}
.mfy-tone-azul{background:#EAF0FF;color:var(--mfy-blue);}.mfy-tone-morado{background:#F1EAFF;color:#8050DF;}.mfy-tone-amarillo{background:#FFF7D1;color:#927200;}
[class*="st-key-mfy_chart_"]{padding:22px 22px 8px;margin:8px 0 14px;}
[class*="st-key-mfy_chart_"] h3{font-size:1rem!important;}[class*="st-key-mfy_chart_"] [data-testid="stCaptionContainer"]{color:var(--mfy-muted);}
.st-key-dashboard_filters{padding:14px 18px;margin-bottom:10px;}
[class*="st-key-mfy_form_section_"]{margin-bottom:16px;}
/* Un único st.form sigue envolviendo la solicitud completa. Estas dos envolturas
   no son tarjetas extra: las secciones interiores y el login ya tienen su tarjeta. */
:is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]{border:0;background:transparent;box-shadow:none;padding:0;transform:none;animation:none;}
:is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]::before{display:none;}
.mfy-section-title{display:flex;align-items:center;gap:12px;margin-bottom:12px;}
.mfy-section-title>span{display:grid;place-items:center;flex-shrink:0;width:36px;height:36px;background:var(--mfy-gradient);color:white;border-radius:50%;font-size:.74rem;font-weight:700;box-shadow:0 3px 10px #9966FF22;}
.mfy-section-title h2{font-family:Inter,sans-serif!important;font-size:.74rem!important;letter-spacing:.08em;margin:0!important;line-height:1.6;}
.mfy-section-title i{height:1px;flex:1;min-width:12px;background:var(--mfy-border);}
/* BaseWeb input/select y stTextArea son controles nativos: foco azul visible,
   sin alterar eventos, validación, contenido ni el estado disabled. */
[data-baseweb="input"],[data-baseweb="select"]>div,textarea{border-radius:10px!important;}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within,.stTextArea textarea:focus{border-color:var(--mfy-blue)!important;box-shadow:0 0 0 3px #3D6FE01f!important;}
/* Botones nativos: conserva navegación de teclado, estados disabled y callbacks. */
:is(.stButton,.stDownloadButton,.stFormSubmitButton) button{position:relative;overflow:hidden;border-radius:var(--mfy-button-radius);font-weight:600;min-height:44px;border:1px solid var(--mfy-blue);color:var(--mfy-blue);background:var(--mfy-white);transition:transform .18s,box-shadow .18s,background .18s;}
:is(.stButton,.stFormSubmitButton) button[kind="primary"]{background:var(--mfy-yellow);border-color:var(--mfy-yellow);color:var(--mfy-text);box-shadow:0 5px 16px #FFCC0033;}
button[kind="primary"]::after{content:'';position:absolute;inset:-30% auto -30% -70%;width:45%;background:linear-gradient(100deg,transparent,#FFFFFF80,transparent);transform:skewX(-18deg);pointer-events:none;}
button:disabled{opacity:.55;box-shadow:none!important;}
button:focus-visible,a:focus-visible,.mfy-table-wrap:focus-visible{outline:3px solid var(--mfy-purple)!important;outline-offset:3px;}
/* stTabs/BaseWeb: mismo fondo y barra de selección de marca en todas las vistas. */
.stTabs [data-baseweb="tab-list"]{gap:8px;background:var(--mfy-white);border-radius:12px;border:1px solid var(--mfy-border);padding:4px 8px;overflow-x:auto;}
.stTabs [data-baseweb="tab"]{min-height:44px;border-radius:9px;padding:0 12px;color:var(--mfy-muted);}
.stTabs [data-baseweb="tab"][aria-selected="true"]{color:var(--mfy-blue);background:var(--mfy-lavender-soft);font-weight:600;}
.stTabs [data-baseweb="tab-highlight"]{height:3px;background:var(--mfy-gradient);border-radius:3px;}
.stTabs [data-baseweb="tab-border"]{background:transparent;}
/* Alertas internas: se conservan sus colores semánticos y texto nativos. */
[data-testid="stAlert"]{border-radius:12px;border:1px solid var(--mfy-border);box-shadow:0 3px 12px #0B254505;}
.mfy-chips,.mfy-state-key{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 18px;}
.mfy-chips span{border:1px solid #CCCCFF;background:var(--mfy-lavender-soft);color:#6042A5;border-radius:999px;padding:5px 11px;font-size:.74rem;}
.mfy-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:6px 10px;font-size:.74rem;font-weight:600;white-space:nowrap;line-height:1.3;}
.mfy-badge::before{content:'';width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0;}
.mfy-table-wrap{width:100%;overflow-x:auto;padding:0;margin:12px 0 18px;}
.mfy-table{border-collapse:collapse;width:100%;font-size:.84rem;text-align:left;}
.mfy-table caption{text-align:left;padding:16px 18px;color:var(--mfy-muted);font-size:.78rem;}
.mfy-table th{background:var(--mfy-lavender-soft);color:var(--mfy-text);font-weight:600;white-space:nowrap;}
.mfy-table th,.mfy-table td{padding:14px 16px;border-bottom:1px solid var(--mfy-border);overflow-wrap:anywhere;}
.mfy-table tr:last-child td{border-bottom:0;}
.mfy-table tbody tr:hover{background:var(--mfy-lavender-soft);}
.mfy-highlight{padding:24px 28px;margin:20px 0;background:linear-gradient(135deg,#EAF0FF,#F0EAFF) padding-box,linear-gradient(var(--mfy-border),var(--mfy-border)) border-box;}
.mfy-highlight>span{font-size:.65rem;letter-spacing:.16em;font-weight:700;color:#7251B4;}.mfy-highlight p{font-family:Poppins,sans-serif;font-weight:500;font-size:1.12rem;margin:8px 0 0;}
.note{padding:16px 18px;border-radius:12px;background:#FFF9DF;border-left:3px solid var(--mfy-yellow);color:#78672C;font-size:.88rem;line-height:1.65;}
.footer{color:var(--mfy-muted);font-size:.75rem;text-align:center;margin-top:36px;padding:18px 0;border-top:1px solid var(--mfy-border);}
/* Login comparte tarjeta, línea de marca, foco y botones con las páginas privadas. */
.stApp:has(.st-key-mfy_login){background:radial-gradient(ellipse at 0 0,#6699FF1a,transparent 65%),radial-gradient(ellipse at 100% 100%,#9966FF14,transparent 65%),var(--mfy-bg);}
.st-key-mfy_login{max-width:510px;width:100%;margin:16px auto 0;padding:32px;box-shadow:0 16px 60px #3D6FE011;}
.st-key-mfy_login [data-testid="stImage"]{max-width:260px;margin:0 auto 8px;}
.st-key-mfy_login h1{font-size:1.5rem!important;text-align:center;line-height:1.4;}
.st-key-mfy_login .note{font-size:.8rem;padding:14px 16px;}
.mfy-login-subtitle{text-align:center;color:var(--mfy-muted);font-size:.88rem;margin-bottom:16px;}
.mfy-login-steps{max-width:510px;margin:22px auto 0;color:var(--mfy-muted);font-size:.76rem;line-height:1.7;display:grid;gap:8px;animation:mfy-enter var(--mfy-entry) ease 100ms both;}
.mfy-login-steps b{color:#7650BB;margin-right:10px;}
.mfy-empty{min-height:250px;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;color:var(--mfy-muted);padding:22px;}
.mfy-empty>span{font-size:55px;color:var(--mfy-lavender);line-height:1.5;}.mfy-empty p{max-width:310px;font-size:.88rem;line-height:1.65;}
.mfy-skeleton-grid{position:relative;display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;}
.mfy-skeleton{height:150px;border-radius:var(--mfy-card-radius);background:linear-gradient(100deg,#EDF0F8 30%,#F9FAFF 50%,#EDF0F8 70%);background-size:200% 100%;animation:mfy-shimmer 1.4s linear infinite;}
.mfy-preview-shell{max-width:1300px;margin:30px auto;padding:16px;}.mfy-preview-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;}
@media(hover:hover) and (pointer:fine){
 :is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight):hover{transform:translateY(-3px);box-shadow:var(--mfy-shadow-hover);background:linear-gradient(var(--mfy-white),var(--mfy-white)) padding-box,var(--mfy-gradient) border-box;}
 :is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]:hover{background:transparent;box-shadow:none;transform:none;}
 :is(.stButton,.stDownloadButton,.stFormSubmitButton) button:not(:disabled):hover{background:var(--mfy-lavender-soft);color:var(--mfy-blue);transform:translateY(-2px);}
 :is(.stButton,.stFormSubmitButton) button[kind="primary"]:not(:disabled):hover{background:var(--mfy-yellow);color:var(--mfy-text);box-shadow:0 8px 20px #FFCC004d;}
 button[kind="primary"]:not(:disabled):hover::after{animation:mfy-button-shine 400ms ease 1;}
}
@keyframes mfy-enter{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes mfy-shimmer{to{background-position:-200% 0}}
@keyframes mfy-button-shine{from{left:-70%}to{left:140%}}
/* Responsive: stHorizontalBlock/stColumn son las columnas internas de Streamlit.
   Bajo 768 px se apilan; los filtros usan además el expander existente. */
@media(max-width:767px){
 .block-container{padding:1.2rem;}
 [data-testid="stMain"] [data-testid="stHorizontalBlock"]{flex-direction:column!important;gap:1rem!important;}
 [data-testid="stMain"] [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:1 1 100%!important;}
 :is(.st-key-mfy_page_header,.mfy-hero){min-height:264px;padding:22px;margin-bottom:16px;}
 .mfy-hero-copy{padding-right:16px;}.mfy-hero-copy h1{font-size:1.6rem!important;}.mfy-hero-copy p{font-size:.88rem;}
 .mfy-hero-orbit{font-size:70px;right:14px;top:15px;}
 .st-key-mfy_header_actions{width:100%;}
 :is([class*="st-key-mfy_form_"],[data-testid="stForm"]){padding:18px;}
 :is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]{padding:0;}
 [class*="st-key-mfy_chart_"]{padding:18px 12px 5px;}[class*="st-key-mfy_kpi_"]{min-height:155px;padding:18px;}
 .mfy-highlight{padding:20px;}
 [data-testid="stSidebar"][aria-expanded="true"]{width:calc(100vw - 20px)!important;max-width:420px;min-width:0;}
 .mfy-table-wrap{border:0;background:transparent;overflow:visible;box-shadow:none;transform:none!important;}
 .mfy-table-wrap::before{display:none;}.mfy-table,.mfy-table tbody,.mfy-table tr{display:block;width:100%;}
 .mfy-table caption{display:block;padding:0 0 12px;}.mfy-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);}
 .mfy-table tr{background:var(--mfy-white);border:1px solid var(--mfy-border);border-top:2px solid var(--mfy-blue);border-radius:var(--mfy-card-radius);padding:6px 14px;margin-bottom:12px;box-sizing:border-box;}
 .mfy-table td{display:grid;grid-template-columns:80px minmax(0,1fr);gap:10px;padding:10px 0;align-items:start;}
 .mfy-table td::before{content:attr(data-label);color:var(--mfy-muted);font-size:.74rem;padding-top:2px;}.mfy-table td>span{justify-self:start;}
 .mfy-preview-grid{grid-template-columns:minmax(0,1fr);}.mfy-preview-shell{margin:0;}
}
@media(max-width:480px){
 .block-container{padding:1rem;}[data-testid="stMarkdownContainer"]{overflow-wrap:anywhere;}
 .st-key-mfy_login{margin-top:8px;padding:22px 18px;}.st-key-mfy_login [data-testid="stImage"]{max-width:220px;}
 .st-key-mfy_login h1{font-size:1.3rem!important;}
 .stTabs [data-baseweb="tab"]{font-size:.8rem;padding:0 10px;}.mfy-login-steps{padding:0 4px;}
 .mfy-section-title{gap:10px;}.mfy-section-title h2{font-size:.7rem!important;letter-spacing:.05em;}
}
@media(prefers-reduced-motion:reduce){
 *,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important;}
 :is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight,button):hover{transform:none!important;}
 button[kind="primary"]::after{display:none;}
 [data-testid="stSidebarNavLink"]:hover,.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]:hover{transform:none!important;}
}
.st-key-mfy_generate{position:fixed;right:24px;bottom:20px;width:240px;z-index:90;}
.st-key-mfy_quote_downloads,.st-key-mfy_quote_ready{position:fixed;right:24px;bottom:84px;z-index:95;width:360px;max-width:calc(100vw - 32px);background:white;border:1px solid var(--mfy-border);border-radius:16px;box-shadow:var(--mfy-shadow-hover);padding:16px;}
.st-key-mfy_form_quote{margin-bottom:90px;}
@media(max-width:480px){.st-key-mfy_generate{right:16px;bottom:12px;width:220px;}.st-key-mfy_quote_downloads,.st-key-mfy_quote_ready{right:16px;bottom:74px;}}
"""

# st.page_link reemplaza el menú nativo; estos data-testid son de Streamlit 1.65.
ESTILOS_BASE += """
.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]{position:relative;display:flex;align-items:center;gap:12px;min-height:48px;padding:12px 16px;border-radius:12px;color:var(--mfy-nav-text)!important;text-decoration:none;transition:transform 200ms,background 200ms;}
.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"] p{color:inherit!important;font-size:.9rem;}
.st-key-mfy_custom_nav [data-testid="stIconMaterial"]{font-size:24px;color:var(--mfy-nav-icon);}
.st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stPageLink-NavLink"]{background:var(--mfy-nav-active);color:var(--mfy-nav-active-text)!important;font-weight:700;}
.st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stIconMaterial"]{color:var(--mfy-nav-active-icon);}
.st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stPageLink-NavLink"]::before{content:'';position:absolute;left:0;top:10px;bottom:10px;width:4px;border-radius:4px;background:var(--mfy-nav-indicator);}
.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]:focus-visible{outline:3px solid var(--mfy-nav-focus);outline-offset:3px;}
@media(hover:hover){.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]:hover{background:var(--mfy-nav-hover);transform:translateX(3px);}}
@media(prefers-reduced-motion:reduce){.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]{transition:none!important;transform:none!important;}}
"""
_paleta_nav = {"oscuro": "dark", "claro": "light"}[TEMA_BARRA_LATERAL]
ESTILOS_BASE += ":root{" + "".join(
    f"--mfy-nav-{token}:var(--mfy-nav-{_paleta_nav}-{token});"
    for token in ("background","text","muted","icon","hover","active","active-text",
                  "active-icon","indicator","border","card","focus")
) + "}"
ESTILOS_BASE += "".join(
    f'.mfy-state-{i}{{background:{bg};color:{fg};}}'
    for i, (_, bg, fg) in enumerate(ESTADOS_COLORES.values())
) + "</style>"

# Los componentes v2 tienen raíz propia; estos estilos siguen centralizados aquí.
CSS_COPIAR = 'button{min-height:44px;border-radius:12px;padding:10px 18px;border:1px solid #3D6FE0;background:white;color:#0B2545;cursor:pointer}button:focus-visible{outline:3px solid #FFCC00;outline-offset:3px}'
CSS_EN_VIVO = """
.live{display:inline-flex;align-items:center;gap:8px;border-radius:22px;padding:9px 12px;
background:#fff;color:#0B2545;font:500 12px Inter,sans-serif;min-height:26px;line-height:1.5}
.live::before{content:'';width:8px;height:8px;flex-shrink:0;border-radius:50%;background:#198754;
animation:mfy-live-pulse 2s ease-in-out infinite}
.live.offline{background:#fff7d6}.live.offline::before{background:#b77900;animation:none}
@keyframes mfy-live-pulse{50%{box-shadow:0 0 0 4px #19875420}}
@media(prefers-reduced-motion:reduce){.live::before{animation:none}}
"""
