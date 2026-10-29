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

CSS_VIDRIO = """
.mfy-glass-chips{display:flex;gap:10px;flex-wrap:wrap;margin:5px 0 0;padding:2px 0;font-family:Inter,sans-serif}
.mfy-glass-chip{display:flex;flex-direction:column;gap:4px;min-width:110px;max-width:100%;box-sizing:border-box;
background:var(--mfy-glass,#0B254566);border:1px solid var(--mfy-glass-border,#FFFFFF50);border-radius:12px;padding:10px 14px;color:white;
backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.mfy-glass-chip small{font-size:11px;line-height:1.5;color:white}.mfy-glass-chip strong{font-size:17px;line-height:1.4;color:white;overflow-wrap:anywhere}
.mfy-glass-chips[hidden],.live[hidden]{display:none!important}
@media(max-width:767px){.mfy-glass-chip{min-width:100px;flex:1;padding:9px 11px;backdrop-filter:none;-webkit-backdrop-filter:none}.mfy-glass-chip strong{font-size:16px}}

"""

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
 --mfy-entry:240ms;--mfy-entry-delay:0ms;--mfy-stagger:60ms;
 --mfy-aurora-opacity:.08;--mfy-aurora-blur:38px;--mfy-drift-duration:36s;
 --mfy-hero-light-duration:38s;--mfy-glass:#0B254566;--mfy-glass-border:#FFFFFF50;
 --mfy-number-gradient:linear-gradient(115deg,var(--mfy-text),var(--mfy-blue));
 /* Dos paletas de navegación; los alias --mfy-nav-* se generan al final. */
 --mfy-nav-dark-background:radial-gradient(ellipse at 45% 100%,#9966FF20,transparent 55%),linear-gradient(160deg,#0B2545,#1B2F6B);
 --mfy-nav-dark-text:#FFF;--mfy-nav-dark-muted:#C5D2ED;--mfy-nav-dark-icon:#D8E2F7;
 --mfy-nav-dark-hover:#FFFFFF12;--mfy-nav-dark-active:linear-gradient(#0B254533,#0B254533),var(--mfy-gradient);
 --mfy-nav-dark-active-text:#FFF;--mfy-nav-dark-active-icon:var(--mfy-yellow);
 --mfy-nav-dark-indicator:var(--mfy-yellow);--mfy-nav-dark-border:#FFFFFF26;
 --mfy-nav-dark-card:#FFFFFF0D;--mfy-nav-dark-card-solid:#162E58;--mfy-nav-dark-focus:var(--mfy-yellow);
 --mfy-nav-light-background:var(--mfy-white);--mfy-nav-light-text:var(--mfy-text);
 --mfy-nav-light-muted:var(--mfy-muted);--mfy-nav-light-icon:var(--mfy-blue);
 --mfy-nav-light-hover:var(--mfy-lavender-soft);--mfy-nav-light-active:var(--mfy-lavender-soft);
 --mfy-nav-light-active-text:var(--mfy-text);--mfy-nav-light-active-icon:var(--mfy-purple);
 --mfy-nav-light-indicator:var(--mfy-purple);--mfy-nav-light-border:var(--mfy-border);
 --mfy-nav-light-card:var(--mfy-bg);--mfy-nav-light-card-solid:var(--mfy-bg);--mfy-nav-light-focus:var(--mfy-blue);
}
/* Streamlit: stApp y block-container son el lienzo y el ancho del contenido. */
.stApp{isolation:isolate;background:var(--mfy-bg);color:var(--mfy-text);font-family:Inter,sans-serif;}
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
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]){position:relative;display:flex;align-items:center;gap:12px;min-height:48px;padding:12px 16px;border-radius:12px;border:1px solid transparent;box-sizing:border-box;color:var(--mfy-nav-text)!important;text-decoration:none;font-size:.9rem;font-weight:500;transition:transform 200ms ease,opacity 200ms ease;}
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]) p{font-size:.9rem;line-height:1.5;color:var(--mfy-nav-text)!important;white-space:normal;}
:is([data-testid="stSidebarNavLink"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]) [data-testid="stIconMaterial"]{font-size:24px!important;width:24px;height:24px;line-height:1;flex-shrink:0;color:var(--mfy-nav-icon)!important;}
:is([data-testid="stSidebarNavLink"][aria-current="page"],.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]){background:var(--mfy-nav-active)!important;color:var(--mfy-nav-active-text)!important;font-weight:700;box-shadow:0 0 24px #9966FF35,0 6px 20px #00000016;}
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
.mfy-identity{display:flex;align-items:center;gap:12px;padding:16px 12px;margin-bottom:10px;min-width:0;border:1px solid transparent;border-radius:16px;background:linear-gradient(var(--mfy-nav-card-solid),var(--mfy-nav-card-solid)) padding-box,linear-gradient(135deg,#6699FF80,#9966FF77,#FFCC0030) border-box;}
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
:is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header){position:relative;isolation:isolate;overflow:hidden;min-height:288px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;padding:28px 32px;border-radius:var(--mfy-hero-radius);color:white;margin:0 0 18px;box-shadow:0 14px 36px #3D6FE027,0 8px 24px #9966FF15;background:radial-gradient(ellipse at 96% 8%,#FFCC0024,transparent 40%),radial-gradient(ellipse at 70% 120%,#CCCCFF45,transparent 43%),radial-gradient(ellipse at 0 0,#6699FF55,transparent 48%),var(--mfy-gradient);animation:mfy-enter var(--mfy-entry) ease both;}
:is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header)::before{content:'';position:absolute;inset:0;z-index:-1;pointer-events:none;background:linear-gradient(110deg,#0B25456b,#0B25456b);}
:is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header)::after{content:'';position:absolute;inset:-40%;z-index:-1;pointer-events:none;background:radial-gradient(ellipse at 75% 20%,#FFFFFF20,transparent 45%);animation:mfy-hero-light var(--mfy-hero-light-duration) ease-in-out infinite alternate;}
.mfy-hero-copy{position:relative;z-index:1;padding-right:110px;}
.mfy-hero-copy h1{color:white;font-size:clamp(36px,3.3vw,44px)!important;margin:8px 0 10px!important;line-height:1.25;}
.mfy-hero-copy p{margin:0;color:white;font-size:.93rem;line-height:1.6;max-width:760px;}
.mfy-eyebrow{font-size:.68rem;letter-spacing:.13em;font-weight:700;color:white;}
.mfy-hero-orbit{position:absolute;right:12px;top:4px;width:106px;pointer-events:none;line-height:1;opacity:.9;}
/* stHorizontalBlock es la fila nativa de las acciones, no un botón HTML. */
.st-key-mfy_page_header [data-testid="stHorizontalBlock"]{align-items:center;}
.st-key-mfy_header_actions{position:relative;z-index:2;}
/* Una sola regla para tarjetas. Los prefijos st-key son claves nuestras;
   stForm/stMetric son selectores internos de Streamlit y deben revisarse al actualizarlo. */
:is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight){position:relative;box-sizing:border-box;border:1px solid transparent;border-radius:var(--mfy-card-radius);background:linear-gradient(var(--mfy-white),var(--mfy-white)) padding-box,linear-gradient(var(--mfy-border),var(--mfy-border)) border-box;box-shadow:var(--mfy-shadow);padding:24px;transition:transform 200ms ease,opacity 200ms ease;animation:mfy-enter var(--mfy-entry) ease var(--mfy-entry-delay) both;}
:is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight)::before{content:'';position:absolute;left:16px;right:16px;top:0;height:2px;border-radius:999px;background:var(--mfy-gradient);pointer-events:none;}
[class*="st-key-mfy_form_section_s2_"]{--mfy-entry-delay:60ms;}[class*="st-key-mfy_form_section_s3_"]{--mfy-entry-delay:120ms;}
[data-testid="stColumn"]:nth-of-type(2) :is([class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"]){--mfy-entry-delay:60ms;}
[data-testid="stColumn"]:nth-of-type(3) [class*="st-key-mfy_kpi_"]{--mfy-entry-delay:120ms;}
[class*="st-key-mfy_kpi_"]{min-height:230px;}
[data-testid="stMetric"]{background:var(--mfy-white);border:1px solid var(--mfy-border);border-radius:var(--mfy-card-radius);padding:20px;}
[class*="st-key-mfy_kpi_"] [data-testid="stMetric"]{background:transparent;border:0;box-shadow:none;padding:0;}
[data-testid="stMetricLabel"]{color:var(--mfy-muted);font-size:.8rem;}[data-testid="stMetricValue"]{color:var(--mfy-text);font-size:clamp(1.8rem,2.6vw,2.35rem);font-weight:700;letter-spacing:-.045em;animation:mfy-number-reveal 360ms ease both;}
.mfy-kpi-icon{display:grid;place-items:center;width:40px;height:40px;border-radius:14px;font-size:22px;font-weight:700;margin-bottom:6px;border:1px solid #FFFFFF80;box-shadow:inset 0 1px 1px #FFFFFFB0,0 4px 12px #6699FF18;}
.mfy-tone-azul{background:linear-gradient(135deg,#EAF0FF,#CCCCFF);color:var(--mfy-blue);}.mfy-tone-morado{background:linear-gradient(135deg,#F1EAFF,#CCCCFF);color:#6533A8;}.mfy-tone-amarillo{background:linear-gradient(135deg,#FFF7D1,var(--mfy-yellow));color:var(--mfy-text);}
[class*="st-key-mfy_chart_"]{padding:22px 22px 8px;margin:8px 0 14px;}
[class*="st-key-mfy_chart_"] h3{font-size:1rem!important;}[class*="st-key-mfy_chart_"] [data-testid="stCaptionContainer"]{color:var(--mfy-muted);}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] p{color:var(--mfy-muted)!important;opacity:1;}
.st-key-dashboard_filters{padding:14px 18px;margin-bottom:10px;}
[class*="st-key-mfy_form_section_"]{margin-bottom:16px;}
/* Un único st.form sigue envolviendo la solicitud completa. Estas dos envolturas
   no son tarjetas extra: las secciones interiores y el login ya tienen su tarjeta. */
:is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]{border:0;background:transparent;box-shadow:none;padding:0;transform:none;animation:none;}
:is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]::before{display:none;}
.mfy-section-title{display:flex;align-items:center;gap:12px;margin-bottom:12px;}
.mfy-section-title>span{display:grid;place-items:center;flex-shrink:0;width:36px;height:36px;background:linear-gradient(#0B254555,#0B254555),var(--mfy-gradient);color:white;border-radius:50%;font-size:.74rem;font-weight:700;box-shadow:0 3px 10px #9966FF22;}
.mfy-section-title h2{font-family:Inter,sans-serif!important;font-size:.74rem!important;letter-spacing:.08em;margin:0!important;line-height:1.6;}
.mfy-section-title i{height:1px;flex:1;min-width:12px;background:var(--mfy-border);}
/* BaseWeb input/select y stTextArea son controles nativos: foco azul visible,
   sin alterar eventos, validación, contenido ni el estado disabled. */
[data-baseweb="input"],[data-baseweb="select"]>div,textarea{border-radius:10px!important;}
[data-baseweb="input"],[data-baseweb="select"]>div{min-height:44px;}
[data-testid="stNumberInput"] button{min-width:44px;min-height:44px;}
[data-testid="stCheckbox"] label,.stLinkButton a{min-height:44px;}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within,.stTextArea textarea:focus{border-color:var(--mfy-blue)!important;box-shadow:0 0 0 3px #3D6FE01f!important;}
/* Botones nativos: conserva navegación de teclado, estados disabled y callbacks. */
:is(.stButton,.stDownloadButton,.stFormSubmitButton) button{position:relative;overflow:hidden;border-radius:var(--mfy-button-radius);font-weight:600;min-height:44px;border:1px solid var(--mfy-blue);color:var(--mfy-blue);background:var(--mfy-white);transition:transform 200ms ease,opacity 200ms ease;}
:is(.stButton,.stFormSubmitButton) button[kind^="primary"]{background:var(--mfy-yellow);border-color:var(--mfy-yellow);color:var(--mfy-text);box-shadow:0 5px 16px #FFCC0033;}
button[kind^="primary"]::after{content:'';position:absolute;inset:-30% auto -30% 0;width:45%;background:linear-gradient(100deg,transparent,#FFFFFF80,transparent);transform:translateX(-240%) skewX(-18deg);pointer-events:none;}
button:disabled{opacity:.55;box-shadow:none!important;}
button:focus-visible,a:focus-visible,.mfy-table-wrap:focus-visible{outline:3px solid var(--mfy-blue)!important;outline-offset:3px;}
/* stTabs/BaseWeb: mismo fondo y barra de selección de marca en todas las vistas. */
.stTabs [data-baseweb="tab-list"]{gap:8px;background:var(--mfy-white);border-radius:12px;border:1px solid var(--mfy-border);padding:4px 8px;overflow-x:auto;}
.stTabs [data-baseweb="tab"]{min-height:44px;border-radius:9px;padding:0 12px;color:var(--mfy-muted);}
.stTabs [data-baseweb="tab"][aria-selected="true"]{color:var(--mfy-text);background:var(--mfy-lavender-soft);font-weight:600;}
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
.stApp:has(.st-key-mfy_login){background:var(--mfy-bg);}
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
.mfy-skeleton{height:150px;border-radius:var(--mfy-card-radius);background:#EDF0F8;}
.mfy-skeleton-grid::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(100deg,transparent,#FFFFFFA0,transparent);animation:mfy-shimmer 1.3s ease 3 both;}
.mfy-preview-shell{max-width:1300px;margin:30px auto;padding:16px;}.mfy-preview-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;}
@media(hover:hover) and (pointer:fine){
 :is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight):hover{transform:translateY(-3px);box-shadow:var(--mfy-shadow-hover);background:linear-gradient(var(--mfy-white),var(--mfy-white)) padding-box,var(--mfy-gradient) border-box;}
 :is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]:hover{background:transparent;box-shadow:none;transform:none;}
 :is(.stButton,.stDownloadButton,.stFormSubmitButton) button:not(:disabled):hover{background:var(--mfy-lavender-soft);color:var(--mfy-text);transform:translateY(-2px);}
 :is(.stButton,.stFormSubmitButton) button[kind^="primary"]:not(:disabled):hover{background:var(--mfy-yellow);color:var(--mfy-text);box-shadow:0 8px 20px #FFCC004d;}
 button[kind^="primary"]:not(:disabled):hover::after{animation:mfy-button-shine 400ms ease 1;}
}
/* Aurora: una única capa para las tres manchas, sin filtros animados. */
.stApp::before{content:'';position:fixed;inset:-10%;z-index:-1;pointer-events:none;
 background:radial-gradient(ellipse at 8% 8%,var(--mfy-blue) 0,transparent 46%),radial-gradient(ellipse at 94% 80%,var(--mfy-purple) 0,transparent 45%),radial-gradient(ellipse at 75% 5%,var(--mfy-yellow) 0,transparent 30%);
 opacity:var(--mfy-aurora-opacity);filter:blur(var(--mfy-aurora-blur));animation:mfy-aurora var(--mfy-drift-duration) ease-in-out infinite alternate;}
.stApp:has(.mfy-skeleton-grid)::before,.stApp:has(.mfy-skeleton-grid) :is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header)::after{animation-play-state:paused;}
::selection{background:var(--mfy-lavender);color:var(--mfy-text);}
.mfy-bulb{display:block;width:100%;height:auto;overflow:visible;}
.mfy-bulb-rays{animation:mfy-rays 700ms ease-in-out 3 alternate;}
.mfy-sparkline{display:block;width:100%;height:42px;margin-top:10px;overflow:visible;color:var(--mfy-blue);}
.mfy-sparkline polyline{fill:none;stroke:currentColor;stroke-width:2.3;stroke-linecap:round;stroke-linejoin:round;}
.mfy-sparkline circle{fill:currentColor;stroke:white;stroke-width:1.5;}
.mfy-spark-top{stop-color:var(--mfy-blue);stop-opacity:.16;}.mfy-spark-bottom{stop-color:var(--mfy-blue);stop-opacity:0;}
[class*="st-key-mfy_kpi_"] [data-testid="stMetricValue"]>div{color:var(--mfy-text);}
@supports (background-clip:text) or (-webkit-background-clip:text){
 [class*="st-key-mfy_kpi_"] [data-testid="stMetricValue"]>div{background:var(--mfy-number-gradient);background-clip:text;-webkit-background-clip:text;color:transparent!important;-webkit-text-fill-color:transparent;}
}
[class*="st-key-mfy_kpi_"] [data-testid="stCaptionContainer"]{font-size:.74rem;line-height:1.5;}
.mfy-skeleton-grid{overflow:hidden;}
.mfy-all-done{display:flex;gap:24px;align-items:center;padding:24px;border:1px solid var(--mfy-border);border-radius:var(--mfy-card-radius);background:linear-gradient(135deg,#FFF9DF,#FFFFFF);color:var(--mfy-text);}
.mfy-all-done .mfy-bulb{width:82px;flex-shrink:0;filter:drop-shadow(0 0 12px #FFCC0033);}
.mfy-all-done strong{font:600 1.1rem Poppins,sans-serif;}.mfy-all-done p{margin:8px 0 0;color:var(--mfy-muted);font-size:.88rem;}
/* Gráficos SVG de Plotly: halo fijo; solo transform se interpola en hover. */
.js-plotly-plot .scatterlayer .js-line{filter:drop-shadow(0 2px 3px #3D6FE02A);}
.js-plotly-plot .slicetext,.js-plotly-plot text.bartext{fill:var(--mfy-text)!important;paint-order:stroke;stroke:white;stroke-width:3px;stroke-linejoin:round;}
@media(hover:hover) and (pointer:fine){.js-plotly-plot .slice path.surface{transform-box:fill-box;transform-origin:center;transition:transform 200ms ease;}.js-plotly-plot .slice path.surface:hover{transform:scale(1.035);}}
[data-testid="stSidebar"] ::-webkit-scrollbar{width:5px;height:5px;}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb{background:var(--mfy-gradient);border-radius:8px;}
[data-testid="stSidebar"] *{scrollbar-width:thin;scrollbar-color:#9966FF #0B2545;}
/* El confeti es un portal efímero propio, no reemplaza ningún nodo de Streamlit. */
.mfy-celebration{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:99999;}
.mfy-confetti-piece{position:absolute;top:-20px;left:5%;width:8px;height:14px;border-radius:2px;background:var(--mfy-blue);animation:mfy-confetti 1900ms ease-out both;}
.mfy-confetti-piece:nth-child(3n+2){background:var(--mfy-purple);}.mfy-confetti-piece:nth-child(3n){background:var(--mfy-yellow);}
.mfy-confetti-piece:nth-child(2n){--mfy-confetti-drift:55px;}.mfy-confetti-piece:nth-child(2n+1){--mfy-confetti-drift:-45px;}
@keyframes mfy-confetti{from{opacity:0;transform:translate3d(0,-30px,0) rotate(0)}12%{opacity:1}to{opacity:0;transform:translate3d(var(--mfy-confetti-drift),90vh,0) rotate(280deg)}}
@keyframes mfy-aurora{from{transform:translate3d(-1%,0,0)}to{transform:translate3d(2%,2%,0)}}
@keyframes mfy-hero-light{from{transform:translate3d(-4%,0,0);opacity:.5}to{transform:translate3d(4%,2%,0);opacity:1}}
@keyframes mfy-rays{from{opacity:.4}to{opacity:1}}
@keyframes mfy-number-reveal{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@keyframes mfy-enter{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes mfy-shimmer{from{transform:translateX(-100%);opacity:0}50%{opacity:.8}to{transform:translateX(100%);opacity:0}}
@keyframes mfy-button-shine{from{transform:translateX(-240%) skewX(-18deg);opacity:0}40%{opacity:1}to{transform:translateX(400%) skewX(-18deg);opacity:0}}
/* Responsive: stHorizontalBlock/stColumn son las columnas internas de Streamlit.
   Bajo 768 px se apilan; los filtros usan además el expander existente. */
@media(max-width:767px){
 .stApp::before{--mfy-aurora-blur:16px;animation:none;}
 :is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header)::after,.mfy-bulb-rays{animation:none;}
 .js-plotly-plot .scatterlayer .js-line{filter:none;}
 .mfy-confetti-piece:nth-child(n+9){display:none;}
 .block-container{padding:1.2rem;}
 [data-testid="stMain"] [data-testid="stHorizontalBlock"]{flex-direction:column!important;gap:1rem!important;}
 [data-testid="stMain"] [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:1 1 100%!important;}
 :is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header){min-height:264px;padding:22px;margin-bottom:16px;}
 .mfy-hero-copy{padding-right:55px;}.mfy-hero-copy h1{font-size:36px!important;}.mfy-hero-copy p{font-size:.88rem;}
 .mfy-hero-orbit{width:58px;right:0;top:8px;opacity:.6;}
 .st-key-mfy_header_actions{width:100%;}
 :is([class*="st-key-mfy_form_"],[data-testid="stForm"]){padding:18px;}
 :is(.st-key-mfy_request,.st-key-mfy_login) [data-testid="stForm"]{padding:0;}
 [class*="st-key-mfy_chart_"]{padding:18px 12px 5px;}[class*="st-key-mfy_kpi_"]{min-height:220px;padding:20px;}
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
@media(min-width:768px) and (max-width:1023px){
 [data-testid="stHorizontalBlock"]:has([class*="st-key-mfy_kpi_"]){flex-wrap:wrap;}
 [data-testid="stHorizontalBlock"]:has([class*="st-key-mfy_kpi_"])>[data-testid="stColumn"]{flex:1 1 calc(50% - 1rem);min-width:0;}
 [class*="st-key-mfy_kpi_"] [data-testid="stMetricValue"]{font-size:1.7rem;}
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
 .mfy-celebration{display:none!important;}
 .js-plotly-plot .slice path.surface{transform:none!important;transition:none!important;}
 :is(.st-key-mfy_login,.st-key-dashboard_filters,[class*="st-key-mfy_kpi_"],[class*="st-key-mfy_chart_"],[class*="st-key-mfy_form_"],[data-testid="stForm"],.mfy-table-wrap,.mfy-highlight,button):hover{transform:none!important;}
 button[kind^="primary"]::after{display:none;}
 [data-testid="stSidebarNavLink"]:hover,.st-key-mfy_single_page [data-testid="stPageLink-NavLink"]:hover{transform:none!important;}
}
.st-key-mfy_generate{position:fixed;right:24px;bottom:20px;width:240px;z-index:90;}
.st-key-mfy_quote_downloads,.st-key-mfy_quote_ready{position:fixed;right:24px;bottom:84px;z-index:95;width:360px;max-width:calc(100vw - 32px);background:white;border:1px solid var(--mfy-border);border-radius:16px;box-shadow:var(--mfy-shadow-hover);padding:16px;}
.st-key-mfy_form_quote{margin-bottom:90px;}
@media(max-width:480px){.st-key-mfy_generate{right:16px;bottom:12px;width:220px;}.st-key-mfy_quote_downloads,.st-key-mfy_quote_ready{right:16px;bottom:74px;}}
"""

# st.page_link reemplaza el menú nativo; estos data-testid son de Streamlit 1.65.
ESTILOS_BASE += """
.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]{position:relative;display:flex;align-items:center;gap:12px;min-height:48px;padding:12px 16px;border-radius:12px;color:var(--mfy-nav-text)!important;text-decoration:none;transition:transform 200ms ease,opacity 200ms ease;}
.stApp [data-testid="stSidebar"] .st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"] p{color:var(--mfy-nav-text)!important;font-size:.9rem;}
.stApp [data-testid="stSidebar"] .st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stPageLink-NavLink"] p{color:var(--mfy-nav-active-text)!important;}
.st-key-mfy_custom_nav [data-testid="stIconMaterial"]{font-size:24px;color:var(--mfy-nav-icon);}
.st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stPageLink-NavLink"]{background:var(--mfy-nav-active);color:var(--mfy-nav-active-text)!important;font-weight:700;box-shadow:0 0 24px #9966FF40,inset 0 1px 0 #FFFFFF20;}
.st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stIconMaterial"]{color:var(--mfy-nav-active-icon);}
.st-key-mfy_custom_nav [class*="st-key-mfy_nav_active_"] [data-testid="stPageLink-NavLink"]::before{content:'';position:absolute;left:0;top:10px;bottom:10px;width:4px;border-radius:4px;background:var(--mfy-nav-indicator);}
.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]:focus-visible{outline:3px solid var(--mfy-nav-focus);outline-offset:3px;}
@media(hover:hover){.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]:hover{background:var(--mfy-nav-hover);transform:translateX(3px);}}
@media(prefers-reduced-motion:reduce){.st-key-mfy_custom_nav [data-testid="stPageLink-NavLink"]{transition:none!important;transform:none!important;}}
"""
# Login y canal público. Claves propias; los data-testid/pills son internos de
# Streamlit 1.65. No se oculta el encabezado privado ni su menú móvil.
ESTILOS_BASE += """
:root{--mfy-public-width:720px;--mfy-keyboard-bottom:0px;}
.stApp:has(:is(.st-key-mfy_login_layout,.st-key-mfy_public)){--mfy-aurora-opacity:.10;background:radial-gradient(ellipse at 0 0,#6699FF15,transparent 55%),radial-gradient(ellipse at 100% 100%,#9966FF18,transparent 55%),var(--mfy-bg);}
.st-key-mfy_login_layout{max-width:1160px;margin:18px auto;}
.st-key-mfy_login_layout [data-testid="stHorizontalBlock"]{align-items:stretch;gap:32px;}
.st-key-mfy_login{margin:0 auto;padding:28px;}
.st-key-mfy_login_brand{min-height:610px;height:100%;margin:0;padding:40px;}
.st-key-mfy_login_brand .mfy-hero-copy{padding-right:0;padding-top:140px;}
.st-key-mfy_login_brand .mfy-hero-copy h1{font-size:clamp(30px,3.1vw,42px)!important;}
.st-key-mfy_login_brand .mfy-hero-orbit{top:0;left:0;right:auto;width:100px;}
.st-key-mfy_login_brand .mfy-login-steps{color:white;margin:28px 0 0;font-size:.9rem;gap:18px;}
.st-key-mfy_login_brand .mfy-login-steps span{display:flex;align-items:center;}
.st-key-mfy_login_brand .mfy-login-steps b{display:inline-flex;align-items:center;justify-content:center;min-width:34px;height:34px;border:1px solid #FFFFFF55;border-radius:50%;background:#0B25454D;color:var(--mfy-yellow);}
.st-key-mfy_login .note{background:var(--mfy-lavender-soft);border:1px solid var(--mfy-yellow);border-left:4px solid var(--mfy-yellow);color:var(--mfy-text);font-size:.86rem;line-height:1.65;padding:16px;border-radius:12px;white-space:normal;overflow:visible;overflow-wrap:anywhere;max-height:none;}
.st-key-mfy_login :is(.stFormSubmitButton,.stButton) button{width:100%;}
.stApp:has(.st-key-mfy_public) :is([data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stStatusWidget"],.mfy-footer){display:none!important;}
.stApp:has(.st-key-mfy_public) .block-container{max-width:960px;padding-top:24px;}
.st-key-mfy_public{min-width:0;max-width:100%;}
.st-key-mfy_formulario_interno{max-width:960px;margin:0 auto;}
.st-key-mfy_client_bar{max-width:720px;margin:0 auto 12px;}
.st-key-mfy_client_bar [data-testid="stHorizontalBlock"]{align-items:center;}
.mfy-form-heading{position:relative;min-width:0;}
.st-key-mfy_steps [role="radiogroup"]{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;}
.st-key-mfy_steps button{width:100%;min-height:44px;white-space:normal;}
.st-key-mfy_public :is(.st-key-request_contacto,.st-key-request_email) input:disabled{color:var(--mfy-muted);-webkit-text-fill-color:var(--mfy-muted);opacity:1;}
.st-key-mfy_public :is(.st-key-request_contacto,.st-key-request_email) label p{color:var(--mfy-text);}
.st-key-mfy_public_header{min-height:270px;padding:24px 32px;}
.st-key-mfy_public_logo{width:max-content!important;max-width:100%;background:white;padding:10px 14px;border-radius:14px;box-shadow:0 5px 20px #0B25451A;}
.mfy-public-heading{display:flex;align-items:center;gap:18px;}
.mfy-public-heading h1{color:white;font-size:clamp(26px,3.5vw,36px)!important;line-height:1.25;max-width:590px;margin:10px 0;}
.mfy-public-heading p{color:white;margin:0;}
.mfy-public-heading .mfy-bulb{width:86px;flex-shrink:0;}
.mfy-public-links{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.mfy-public-links a{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;box-sizing:border-box;border-radius:10px;padding:6px 10px;border:1px solid #FFFFFF55;background:#0B25454D;color:white!important;text-decoration:none;font-size:.8rem;overflow-wrap:anywhere;}
.mfy-public-links svg{width:22px;height:22px;}
.st-key-mfy_public_top [data-testid="stHorizontalBlock"]{align-items:center;flex-direction:row!important;flex-wrap:nowrap!important;gap:16px;}
.st-key-mfy_public_top [data-testid="stColumn"]{min-width:0!important;}
.mfy-public-contact{font-size:.85rem;color:var(--mfy-muted);text-align:center;overflow-wrap:anywhere;margin:16px 0;}
.mfy-public-contact a{color:#244FAF;}
.mfy-public-links a:focus-visible{outline:3px solid var(--mfy-yellow);outline-offset:3px;}
:is(.st-key-mfy_form_publico,.st-key-mfy_form_publico_success){max-width:var(--mfy-public-width);width:100%;margin:0 auto;padding:28px;transform:none!important;}
.mfy-public-progress{margin:0 0 24px;}
.mfy-progress-labels{display:flex;justify-content:space-between;gap:8px;font-size:.8rem;font-weight:600;color:var(--mfy-muted);margin-bottom:12px;}
.mfy-progress-track{height:5px;border-radius:999px;background:var(--mfy-lavender-soft);overflow:hidden;}
.mfy-progress-track i{display:block;width:100%;height:100%;background:var(--mfy-gradient);transform-origin:left;transition:transform 200ms ease;}
.mfy-progress-1 i{transform:scaleX(.3333);}.mfy-progress-2 i{transform:scaleX(.6667);}.mfy-progress-3 i{transform:scaleX(1);}
.mfy-progress-1 .mfy-progress-labels span:nth-child(1),.mfy-progress-2 .mfy-progress-labels span:nth-child(2),.mfy-progress-3 .mfy-progress-labels span:nth-child(3){color:var(--mfy-text);}
.mfy-field-error{font-size:.82rem;color:#963D47;margin:-8px 0 8px;line-height:1.45;}
/* stButtonGroup es el control nativo de st.pills; selección explícita y foco. */
:is(.st-key-mfy_public,.st-key-mfy_formulario_interno) [data-testid="stButtonGroup"]{gap:8px;flex-wrap:wrap;}
:is(.st-key-mfy_public,.st-key-mfy_formulario_interno) [data-testid="stButtonGroup"] button{min-height:48px;border:1px solid var(--mfy-border);background:var(--mfy-white);color:var(--mfy-text);border-radius:12px;padding:12px 16px;white-space:normal;max-width:100%;}
:is(.st-key-mfy_public,.st-key-mfy_formulario_interno) [data-testid="stButtonGroup"] button:is([aria-checked="true"],[aria-pressed="true"],[data-selected="true"]){background:var(--mfy-lavender-soft);border:2px solid var(--mfy-purple);color:var(--mfy-text);box-shadow:0 0 0 1px #9966FF20;}
:is(.st-key-mfy_public_servicio,.st-key-mfy_public_tematica) [data-testid="stButtonGroup"] :is([role="radiogroup"],[role="group"]){display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;}
:is(.st-key-mfy_public_servicio,.st-key-mfy_public_tematica) [data-testid="stButtonGroup"] button{width:100%;justify-content:flex-start;text-align:left;min-height:66px;}
.mfy-public-summary{border:1px solid var(--mfy-border);border-radius:14px;padding:18px;background:var(--mfy-bg);}
.mfy-public-summary dl{margin:0;display:grid;gap:10px;}
.mfy-public-summary dl>div{display:grid;grid-template-columns:1fr 1.4fr;gap:12px;border-bottom:1px solid var(--mfy-border);padding:0 0 8px;}
.mfy-public-summary dt{font-size:.77rem;color:var(--mfy-muted);}.mfy-public-summary dd{margin:0;font-size:.84rem;overflow-wrap:anywhere;white-space:pre-wrap;}
:is(.st-key-publico_sitio_confirmacion,.st-key-request_sitio_confirmacion,.st-key-signup_sitio_confirmacion){position:absolute!important;left:-9999px;top:0;width:1px!important;height:1px;overflow:hidden;pointer-events:none;}
.st-key-signup_sitio_confirmacion{visibility:hidden;}
.st-key-mfy_public .st-key-mfy_public_actions{max-width:var(--mfy-public-width);margin:0 auto;padding:16px 24px;background:var(--mfy-white);border-radius:12px;}
.st-key-mfy_public_actions [data-testid="stHorizontalBlock"]{flex-direction:row!important;flex-wrap:nowrap!important;gap:12px;}
.st-key-mfy_public_actions [data-testid="stColumn"]{min-width:0!important;}
.mfy-public-success{text-align:center;padding:24px 0;}
.mfy-public-success svg{width:76px;height:76px;animation:mfy-enter 300ms ease both;}
.mfy-public-success h2{margin:18px 0 12px;}
@media(max-width:1023px){
 .st-key-mfy_login_layout [data-testid="stHorizontalBlock"]{flex-direction:column;gap:20px;}
 .st-key-mfy_login_layout [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{width:100%;flex:1 1 auto;}
 .st-key-mfy_login_brand{min-height:0;height:auto;padding:26px;}
 .st-key-mfy_login_brand .mfy-hero-copy{padding:0 90px 0 0;}
 .st-key-mfy_login_brand .mfy-hero-orbit{left:auto;right:0;width:76px;}
 .st-key-mfy_login_brand .mfy-login-steps{margin-top:16px;font-size:.8rem;gap:8px;}
 .st-key-mfy_login_brand .mfy-hero-copy h1{font-size:28px!important;}
}
@media(max-width:767px){
 .stApp:has(.st-key-mfy_public) .block-container{padding:12px 12px 110px;}
 .st-key-mfy_public_header{min-height:0;padding:20px;}
 .st-key-mfy_public_logo{padding:7px 9px;}.st-key-mfy_public_logo [data-testid="stImage"]{max-width:125px;}
 .st-key-mfy_public_logo img{max-width:125px!important;}
 /* Excepción al apilado general: marca/enlaces y Atrás/Siguiente comparten fila. */
 [data-testid="stMain"] :is(.st-key-mfy_public_top,.st-key-mfy_public_actions) [data-testid="stColumn"]{flex:1 1 0%!important;width:0!important;}
 [data-testid="stMain"] .st-key-mfy_client_bar [data-testid="stHorizontalBlock"]{flex-direction:row!important;gap:8px!important;}
 [data-testid="stMain"] .st-key-mfy_client_bar [data-testid="stColumn"]{flex:1 1 0%!important;width:0!important;}
 .st-key-mfy_client_bar button{padding:8px;}
 .st-key-mfy_client_bar button p{font-size:.8rem!important;}
 .st-key-mfy_public_actions [data-testid="stColumn"]:not(:has(button)){display:none;}
 .mfy-public-links{justify-content:flex-end;gap:5px;}.mfy-public-links a{font-size:.72rem;padding:5px 8px;}
 .mfy-public-heading{gap:8px;}.mfy-public-heading .mfy-bulb{width:54px;}
 .mfy-public-heading h1{font-size:26px!important;}.mfy-public-heading p{font-size:.86rem;}
 :is(.st-key-mfy_form_publico,.st-key-mfy_form_publico_success){padding:22px 18px;}
 .st-key-mfy_form_publico{padding-bottom:110px;}
 .st-key-mfy_public .st-key-mfy_public_actions{max-width:none;border-radius:0;position:fixed;bottom:var(--mfy-keyboard-bottom);left:0;right:0;z-index:1000;padding:12px 18px max(12px,env(safe-area-inset-bottom));border-top:1px solid var(--mfy-border);box-shadow:0 -4px 20px #0B25450A;}
 .st-key-mfy_public :is(input,textarea){font-size:16px!important;min-height:44px;}
 .mfy-progress-labels{font-size:.75rem;}
 .mfy-public-summary dl>div{grid-template-columns:1fr;gap:3px;}
 .st-key-mfy_login_layout{margin-top:0;}.st-key-mfy_login_brand{padding:22px;}
 .st-key-mfy_login_brand .mfy-hero-copy{padding-right:60px;}
 .st-key-mfy_login_brand .mfy-hero-orbit{width:50px;}
 .st-key-mfy_login_brand .mfy-hero-copy h1{font-size:26px!important;}
}
@media(prefers-reduced-motion:reduce){.mfy-progress-track i{transition:none!important;}}
"""
# Barra superior: selectores internos de Streamlit 1.65 (stHeader,
# stHeaderLogo, stTopNavLink/Section/Popover). Los st-key son propios.
ESTILOS_BASE += """
.stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) [data-testid="stHeader"]{display:flex!important;position:fixed;height:64px;min-height:64px;background:var(--mfy-nav-background);border-bottom:1px solid var(--mfy-nav-border);color:var(--mfy-nav-text);z-index:990;}
.stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) .block-container{padding-top:88px;}
.stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) [data-testid="stHeaderLogo"]{display:block;max-width:154px!important;height:48px!important;max-height:48px!important;object-fit:contain;background:var(--mfy-white);padding:4px 8px;border-radius:10px;margin-left:16px;box-sizing:border-box;}
.stApp:has(.mfy-top-nav-marker) [data-testid="stHeader"]{padding-right:150px;}
.stApp:has(.mfy-top-nav-marker) [data-testid="stToolbar"]{width:100%;}
.stApp:has(.mfy-top-nav-marker) [data-testid="stToolbar"]>div{width:100%;justify-content:space-between;}
.stApp:has(.mfy-top-nav-marker) [data-testid="stToolbar"] .rc-overflow{margin-left:auto;flex:1!important;justify-content:flex-end!important;}
.stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) [data-testid="stLogoLink"]{max-width:none!important;flex-shrink:0;}
.stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) [data-testid="stHeaderLogo"]{width:154px!important;object-position:center;}
[data-testid="stTopNavLink"],[data-testid="stTopNavSection"]{min-height:44px!important;box-sizing:border-box;border-radius:12px;color:var(--mfy-nav-text)!important;font-family:Inter,sans-serif;}
[data-testid="stTopNavLink"] p,[data-testid="stTopNavSection"] p{color:inherit!important;font-size:.85rem!important;}
[data-testid="stTopNavLink"] span,[data-testid="stTopNavLink"] p,[data-testid="stTopNavSection"] span,[data-testid="stTopNavSection"] p{color:var(--mfy-nav-text)!important;}
[data-testid="stTopNavLink"] [data-testid="stIconMaterial"]{color:var(--mfy-nav-icon)!important;}
[data-testid="stTopNavLink"][aria-current="page"]{background:var(--mfy-nav-active)!important;border-bottom:3px solid var(--mfy-nav-indicator);font-weight:700;}
[data-testid="stTopNavLink"][aria-current="page"] [data-testid="stIconMaterial"]{color:var(--mfy-nav-active-icon)!important;}
[data-testid="stTopNavLink"]:hover,[data-testid="stTopNavSection"]:hover{background:var(--mfy-nav-hover);}
[data-testid="stTopNavLink"]:focus-visible,[data-testid="stTopNavSection"]:focus-visible{outline:3px solid var(--mfy-nav-focus);outline-offset:2px;}
[data-testid="stTopNavDropdownLink"]{min-height:44px;}
.st-key-mfy_top_account,.st-key-mfy_top_mobile,.st-key-mfy_top_single{position:fixed!important;top:10px;right:16px;width:126px!important;z-index:1000;}
.st-key-mfy_top_mobile{display:none;}
.st-key-mfy_top_single{right:164px;width:175px!important;}
.st-key-mfy_top_single [data-testid="stPageLink-NavLink"]{min-height:44px;color:var(--mfy-nav-text)!important;background:var(--mfy-nav-active);border-bottom:3px solid var(--mfy-nav-indicator);border-radius:12px;}
.st-key-mfy_top_single [data-testid="stPageLink-NavLink"] :is(span,p){color:var(--mfy-nav-text)!important;}
:is(.st-key-mfy_top_account,.st-key-mfy_top_mobile) [data-testid="stPopoverButton"]{min-height:44px;background:transparent;color:var(--mfy-nav-text);border:1px solid var(--mfy-nav-border);box-shadow:none;white-space:nowrap;}
:is(.st-key-mfy_top_account,.st-key-mfy_top_mobile) [data-testid="stPopoverButton"] p{color:inherit!important;}
:is(.st-key-mfy_top_account,.st-key-mfy_top_mobile) button:focus-visible{outline:3px solid var(--mfy-nav-focus)!important;outline-offset:2px;}
.st-key-mfy_mobile_links [data-testid="stPageLink-NavLink"]{display:flex;align-items:center;min-height:48px;padding:10px 12px;border-radius:12px;color:var(--mfy-text);}
.st-key-mfy_mobile_links [class*="st-key-mfy_mobile_active_"] [data-testid="stPageLink-NavLink"]{background:var(--mfy-lavender-soft);border-left:4px solid var(--mfy-purple);font-weight:700;}
.st-key-mfy_mobile_links button{min-height:44px;}
.stApp:has(.mfy-top-nav-marker) :is([data-testid="stSidebar"],[data-testid="stExpandSidebarButton"]){display:none!important;}
/* La barra pública solo contiene la marca; los enlaces configurados se
   conservan en la cabecera del formulario. */
.stApp:has(.mfy-public-nav-marker) [data-testid="stHeader"] [data-testid="stToolbarActions"]{display:none;}
@media(max-width:767px){
 .stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) [data-testid="stHeaderLogo"]{max-width:124px!important;height:44px!important;max-height:44px!important;margin-left:12px;}
 .st-key-mfy_top_account,.st-key-mfy_top_single{display:none!important;}
 .st-key-mfy_top_mobile{display:block;right:12px;width:108px!important;}
 .stApp:has(.mfy-top-nav-marker) [data-testid="stHeader"] :is([data-testid="stTopNavLinkContainer"],[data-testid="stTopNavSection"]){display:none!important;}
 .stApp:has(:is(.mfy-top-nav-marker,.mfy-public-nav-marker)) .block-container{padding-top:80px!important;}
 [data-testid="stPopoverBody"]:has(.st-key-mfy_mobile_links){max-width:calc(100vw - 24px)!important;max-height:calc(100dvh - 80px);overflow-y:auto;}
}
"""
# Ajustes responsive compartidos. stMain/Column/ElementContainer, stImage,
# stDataFrame y los selectores BaseWeb son internos de Streamlit 1.65.
# No ocultar overflow globalmente: tablas, pestañas y código tienen su propio scroll.
ESTILOS_BASE += """
[data-testid="stMain"]{scroll-padding-top:80px;scroll-padding-bottom:110px;}
[data-testid="stMain"] :is([data-testid="stVerticalBlock"],[data-testid="stColumn"],[data-testid="stElementContainer"]){min-width:0;}
[data-testid="stMain"] :is([data-testid="stElementContainer"],[data-testid="stDataFrame"],.mfy-table-wrap,.stTabs){max-width:100%;box-sizing:border-box;}
[data-testid="stMain"] :is(input,textarea,[role="combobox"],button,.mfy-public-progress){scroll-margin-top:80px;scroll-margin-bottom:110px;}
[data-testid="stMain"] :is(input:not([type="checkbox"]):not([type="radio"]),textarea,[role="combobox"]){font-size:16px!important;}
[data-baseweb="select"]>div{font-size:16px;}
[data-testid="stMain"] :is([data-testid="stImage"],[data-testid="stImage"] img){max-width:100%;}
.st-key-mfy_form_compartir_descargas [data-testid="stImage"]{margin-inline:auto;}
.st-key-mfy_form_compartir_descargas img{height:auto;object-fit:contain;}
.st-key-mfy_form_compartir_descargas button{min-width:44px;min-height:44px;}
[class*="st-key-mfy_form_compartir_"] :is(pre,code){max-width:100%;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;}
[data-testid="stCode"]{max-width:100%;overflow-x:auto;}
.mfy-chips span,.mfy-state-key>span{max-width:100%;overflow-wrap:anywhere;}
.mfy-table td>span{min-width:0;max-width:100%;overflow-wrap:anywhere;}
@media(max-width:1023px){
 [data-testid="stMain"] [data-testid="stWidgetLabel"] p{white-space:normal;overflow-wrap:anywhere;line-height:1.5;}
 /* Evitar el reloj comprimido junto a títulos y métricas en la tableta. */
 .st-key-mfy_page_header [data-testid="stHorizontalBlock"]{flex-direction:column!important;}
 .st-key-mfy_page_header [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex:1 1 100%!important;width:100%!important;min-width:0;}
 .st-key-mfy_header_actions{width:100%;}
 [data-testid="stDialog"] [role="dialog"]{max-width:calc(100vw - 24px);max-height:calc(100dvh - 24px);overflow-y:auto;}
}
@media(min-width:768px) and (max-width:1023px){
 .block-container{padding-inline:24px;}
 .mfy-table{min-width:680px;}
 /* Formularios densos: dos columnas solo cuando cada campo tiene espacio. */
 [data-testid="stMain"] :is([data-testid="stForm"],.st-key-mfy_form_quote) [data-testid="stHorizontalBlock"]{flex-wrap:wrap;}
 [data-testid="stMain"] :is([data-testid="stForm"],.st-key-mfy_form_quote) [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex:1 1 260px;min-width:0;}
 [data-testid="stHorizontalBlock"]:has(>[data-testid="stColumn"] [class*="st-key-mfy_chart_"]){flex-wrap:wrap;}
 [data-testid="stHorizontalBlock"]:has(>[data-testid="stColumn"] [class*="st-key-mfy_chart_"])>[data-testid="stColumn"]{flex:1 1 340px;min-width:0;}
}
@media(max-width:767px){
 .block-container{padding-inline:16px!important;padding-bottom:calc(100px + env(safe-area-inset-bottom));}
 [data-testid="stMain"] :is(.stButton,.stDownloadButton,.stLinkButton,.stFormSubmitButton){width:100%;max-width:100%;}
 [data-testid="stMain"] :is(.stButton,.stDownloadButton,.stLinkButton,.stFormSubmitButton)>:is(button,a){width:100%;min-height:44px;white-space:normal;box-sizing:border-box;}
 [data-testid="stMain"] :is(button,a) p{white-space:normal;overflow-wrap:anywhere;}
 /* Los botones de ayuda pertenecen a la etiqueta, no a las tarjetas de opción. */
 [data-testid="stMain"] [data-testid="stWidgetLabel"] button{width:44px!important;min-width:44px;max-width:44px;min-height:44px!important;height:44px!important;padding:4px!important;}
 [data-testid="stMain"] :is([data-testid="stTextInput"],[data-testid="stNumberInput"],[data-testid="stSelectbox"],[data-testid="stTextArea"],[data-testid="stDateInput"]){width:100%;min-width:0;}
 .mfy-hero-copy{padding-right:0;min-width:0;}
 .mfy-hero-copy .mfy-eyebrow{display:block;min-height:40px;padding-right:46px;box-sizing:border-box;}
 .mfy-hero-copy h1{font-size:clamp(28px,7.5vw,34px)!important;overflow-wrap:anywhere;}
 .mfy-hero-orbit{width:44px;top:0;}
 .st-key-mfy_login_brand .mfy-hero-copy{padding-right:0;}
 .st-key-mfy_login_brand .mfy-hero-orbit{width:44px;}
 .mfy-all-done{padding:18px;gap:14px;align-items:flex-start;}
 .mfy-all-done .mfy-bulb{width:48px;}
 .stTabs [data-baseweb="tab-list"]{max-width:100%;overscroll-behavior-x:contain;}
 .stTabs [data-baseweb="tab"]{flex-shrink:0;}
 .st-key-mfy_steps button{height:auto!important;min-height:68px!important;padding:10px 8px;}
 .st-key-mfy_steps button p{white-space:normal!important;line-height:1.35;}
 .st-key-mfy_login [data-testid="stImage"]{max-width:200px;margin-inline:auto;}
 .mfy-table,.mfy-table tbody,.mfy-table tr{min-width:0;max-width:100%;}
 .mfy-table td{grid-template-columns:minmax(65px,28%) minmax(0,1fr);}
 [data-testid="stDataFrame"]{overflow-x:auto;overscroll-behavior-x:contain;}
 /* Las acciones flotantes quedan fuera de las tarjetas animadas. Se deja
    espacio al pie y se reutiliza el desplazamiento del teclado del formulario. */
 .st-key-mfy_formulario_interno{padding-bottom:86px;}
 .st-key-mfy_formulario_interno .st-key-ff_guardar{position:fixed;left:16px;right:16px;bottom:calc(12px + env(safe-area-inset-bottom) + var(--mfy-keyboard-bottom));width:auto!important;z-index:980;}
 .st-key-mfy_login{padding-bottom:90px;transform:none!important;animation:none;}
 .st-key-mfy_login [data-testid="stFormSubmitButton"]{position:fixed;left:16px;right:16px;bottom:calc(12px + env(safe-area-inset-bottom));width:auto!important;z-index:980;}
 .st-key-mfy_generate{left:16px;right:16px;width:auto;bottom:calc(12px + env(safe-area-inset-bottom));}
 .st-key-mfy_quote_downloads,.st-key-mfy_quote_ready{left:16px;right:16px;width:auto;max-width:calc(100vw - 32px);max-height:calc(100dvh - 165px);overflow-y:auto;box-sizing:border-box;}
 [data-testid="stDialog"] [data-testid="stHorizontalBlock"]{flex-direction:column!important;}
 [data-testid="stDialog"] [data-testid="stColumn"]{width:100%!important;flex:1 1 100%!important;min-width:0!important;}
}
"""
# Posiciones estáticas; las únicas propiedades animadas del confeti son transform y opacity.
ESTILOS_BASE += "".join(
    f'.mfy-confetti-piece:nth-child({i+1}){{left:{5+i*5}%;animation-delay:{(i%4)*25}ms;}}'
    for i in range(18)
)
_paleta_nav = {"oscuro": "dark", "claro": "light"}[TEMA_BARRA_LATERAL]
ESTILOS_BASE += ":root{" + "".join(
    f"--mfy-nav-{token}:var(--mfy-nav-{_paleta_nav}-{token});"
    for token in ("background","text","muted","icon","hover","active","active-text",
                  "active-icon","indicator","border","card","card-solid","focus")
) + "}"
ESTILOS_BASE += "".join(
    f'.mfy-state-{i}{{background:{bg};color:{fg};}}'
    for i, (_, bg, fg) in enumerate(ESTADOS_COLORES.values())
) + CSS_VIDRIO + "</style>"

# Los componentes v2 tienen raíz propia; estos estilos siguen centralizados aquí.
CSS_COPIAR = 'button{box-sizing:border-box;width:100%;max-width:100%;min-height:44px;border-radius:12px;padding:10px 18px;border:1px solid #3D6FE0;background:white;color:#0B2545;cursor:pointer;white-space:normal;overflow-wrap:anywhere}button:focus-visible{outline:3px solid #FFCC00;outline-offset:3px}'
CSS_EN_VIVO = """
.live{display:inline-flex;align-items:center;gap:8px;border-radius:22px;padding:9px 12px;
background:#fff;color:#0B2545;font:500 12px Inter,sans-serif;min-height:26px;line-height:1.5}
.live::before{content:'';width:8px;height:8px;flex-shrink:0;border-radius:50%;background:#198754;
animation:none}
.live.offline{background:#fff7d6}.live.offline::before{background:#b77900;animation:none}

@media(prefers-reduced-motion:reduce){.live::before{animation:none}}

"""

CSS_EN_VIVO += CSS_VIDRIO
