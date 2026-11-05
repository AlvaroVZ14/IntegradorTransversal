"""Sistema de diseño único: variables, CSS y componentes de presentación.

Los adaptadores utils.estilos/componentes mantienen las importaciones existentes.
No conoce repositorios, roles, importes de negocio ni documentos imprimibles.
"""
import re

AZUL='#3D6FE0'
AZUL_CLARO='#6699FF'
MORADO='#9966FF'
AMARILLO='#FFCC00'
LAVANDA='#CCCCFF'
TEXTO='#0B2545'
SECUNDARIO='#5B6B82'
PALETA=[AZUL,AZUL_CLARO,MORADO,'#B794FF',AMARILLO,LAVANDA]
TEMA_BARRA_LATERAL='oscuro'
from ui.estados import CATALOGO,color_estado,clase_estado,chip_estado
# Adaptador para consumidores anteriores; no define colores propios.
ESTADOS_COLORES={e['etiqueta']:(e['solido'],e['fondo'],e['texto']) for e in CATALOGO['caso'].values()}

# Selectores internos de Streamlit 1.65: stHeader/TopNav, stMain,
# stVerticalBlock/Column, stForm/WidgetLabel, stMetric y stPopover.
# Todos los st-key-mfy_* y las clases mfy-* pertenecen a la aplicación.
CSS_PORTAL=r'''
:root{
 --mfy-blue:#3D6FE0;--mfy-blue-light:#6699FF;--mfy-purple:#9966FF;--mfy-yellow:#FFCC00;--mfy-lavender:#CCCCFF;
 --mfy-text:#0B2545;--mfy-muted:#5B6B82;--mfy-bg:#F4F7FF;--mfy-white:#FFF;--mfy-border:#E3E8F4;
 --mfy-blue-soft:#EAF1FF;--mfy-lavender-soft:#F1ECFF;--mfy-yellow-soft:#FFF6D1;
 --mfy-s1:4px;--mfy-s2:8px;--mfy-s3:12px;--mfy-s4:16px;--mfy-s6:24px;--mfy-s8:32px;--mfy-s12:48px;
 --mfy-r1:10px;--mfy-r2:16px;--mfy-r3:24px;--mfy-card-radius:16px;--mfy-button-radius:10px;--mfy-hero-radius:24px;
 --mfy-shadow:0 4px 18px #0B25450A;--mfy-shadow-hover:0 8px 26px #3D6FE018;
 --mfy-title:clamp(24px,3vw,36px);--mfy-section:20px;--mfy-body:16px;--mfy-small:13px;
 --mfy-gradient:linear-gradient(135deg,#315BBC,#6D38B6);--mfy-nav-background:linear-gradient(135deg,#0B2545,#1B2F6B);
 --mfy-nav-text:#FFF;--mfy-nav-muted:#D8E2F7;--mfy-nav-icon:#D8E2F7;--mfy-nav-border:#FFFFFF35;--mfy-nav-hover:#FFFFFF18;
 --mfy-nav-active:var(--mfy-gradient);--mfy-nav-active-text:#FFF;--mfy-nav-active-icon:#FFCC00;--mfy-nav-indicator:#FFCC00;--mfy-nav-focus:#FFCC00;
}
*{box-sizing:border-box}::selection{background:#CCCCFF;color:#0B2545}
.stApp{font-family:Inter,system-ui,sans-serif;color:var(--mfy-text);background:radial-gradient(ellipse at 4% 0%,#6699FF15,transparent 45%),radial-gradient(ellipse at 96% 68%,#9966FF12,transparent 44%),radial-gradient(ellipse at 15% 95%,#FFCC0010,transparent 30%),linear-gradient(160deg,#F4F7FF,#FFF);background-attachment:fixed;}
.stApp:before{content:'';position:fixed;inset:0;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='26' height='26'%3E%3Ccircle cx='2' cy='2' r='1' fill='%239966FF' opacity='.07'/%3E%3C/svg%3E");}
.block-container{max-width:1200px;padding:24px 24px 40px;}
h1,h2,h3{font-family:Poppins,Inter,system-ui,sans-serif!important;letter-spacing:-.025em;color:var(--mfy-text)}
h1{font-size:var(--mfy-title)!important}h2{font-size:24px!important}h3{font-size:var(--mfy-section)!important}
p{line-height:1.5}input,textarea,button,[role=combobox]{font-family:inherit;font-size:16px!important}
input,textarea,[role=combobox]{scroll-margin:88px 0 110px;}
button,a,summary{touch-action:manipulation}button,summary,[role=combobox],[data-testid=stPageLink-NavLink]{min-height:44px}
button:focus-visible,a:focus-visible,[tabindex]:focus-visible{outline:3px solid #315BBC!important;outline-offset:3px}
[data-baseweb=base-input]:focus-within,[data-baseweb=select]:focus-within{outline:2px solid #3D6FE0;outline-offset:2px;border-radius:10px}
[data-testid=stMain] :is([data-testid=stVerticalBlock],[data-testid=stColumn],[data-testid=stElementContainer]){min-width:0}
[data-testid=stElementContainer]:has(style),[data-testid=stElementContainer]:has(.mfy-top-nav-marker,.mfy-public-nav-marker){display:none}
#MainMenu,[data-testid=stMainMenu],[data-testid=stToolbarActions],[data-testid=stAppDeployButton],footer{display:none!important}
.mfy-sr-only{position:absolute!important;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
[data-testid=stHeader]{background:transparent}
.stApp:has(.mfy-top-nav-marker,.mfy-public-nav-marker) [data-testid=stHeader]{display:flex!important;position:fixed;height:64px;min-height:64px;background:var(--mfy-nav-background);color:white;z-index:990;padding-right:150px}
.stApp:has(.mfy-top-nav-marker,.mfy-public-nav-marker) .block-container{padding-top:80px}
[data-testid=stHeaderLogo]{width:154px!important;max-width:154px!important;height:48px!important;object-fit:contain;background:transparent!important;padding:0!important;margin-left:16px;border-radius:0!important}
[data-testid=stLogoLink]{flex-shrink:0}
[data-testid=stToolbar], [data-testid=stToolbar]>div{width:100%}
[data-testid=stToolbar] .rc-overflow{margin-left:auto;justify-content:flex-end}
[data-testid=stTopNavLink],[data-testid=stTopNavSection]{min-height:44px;border-radius:10px;color:white!important}
[data-testid=stTopNavLink] :is(p,span),[data-testid=stTopNavSection] :is(p,span){color:inherit!important;font-size:14px!important}
[data-testid=stTopNavLink][aria-current=page]{background:#FFFFFF20!important;border-bottom:3px solid #FFCC00}
[data-testid=stTopNavLink]:hover{background:#FFFFFF18}
[data-testid=stTopNavLink][href$=nueva-solicitud]{background:var(--mfy-gradient);border:1px solid #FFFFFF60}
[data-testid=stTopNavDropdownLink]{min-height:44px}
.st-key-mfy_top_account,.st-key-mfy_top_mobile{position:fixed!important;top:10px;right:16px;width:126px!important;z-index:1000}
.st-key-mfy_top_mobile{display:none}
:is(.st-key-mfy_top_account,.st-key-mfy_top_mobile) [data-testid=stPopoverButton]{min-height:44px;border:1px solid #FFFFFF55;background:transparent;color:#FFF;box-shadow:none}
:is(.st-key-mfy_top_account,.st-key-mfy_top_mobile) [data-testid=stPopoverButton] p{color:inherit}
[data-testid=stPageLink-NavLink]{border-radius:10px;padding:10px 12px}
[class*=st-key-mfy_mobile_active_] [data-testid=stPageLink-NavLink]{background:#F1ECFF;border-left:3px solid #7138B3}
.mfy-identity{display:flex;gap:12px;align-items:center;padding:12px 0}.mfy-identity strong{display:block;font-size:14px}.mfy-identity small{color:var(--mfy-muted)}
.mfy-avatar{display:grid;place-items:center;flex-shrink:0;width:42px;height:42px;border-radius:14px;background:var(--mfy-gradient);color:white;font-weight:700}
:is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_login_brand,.st-key-mfy_public_header){position:relative;isolation:isolate;overflow:hidden;min-height:120px;padding:20px 24px;border-radius:24px;margin-bottom:12px;color:white;background:radial-gradient(ellipse at 95% 0,#CCCCFF33,transparent 50%),var(--mfy-gradient);box-shadow:var(--mfy-shadow)}
.st-key-mfy_page_header:has(.mfy-eyebrow[data-vista=HOY]){min-height:190px;padding:28px 32px}
.mfy-hero-copy{position:relative;z-index:1;padding-right:90px}.mfy-eyebrow{display:block;font-size:11px;letter-spacing:.1em;font-weight:700;color:white}
.mfy-hero-copy h1{font-size:clamp(24px,3vw,34px)!important;line-height:1.2;color:white!important;margin:6px 0}
.mfy-hero-copy p{margin:4px 0;font-size:14px;color:white;overflow-wrap:anywhere}
.mfy-hero-orbit{position:absolute;right:20px;top:50%;transform:translateY(-50%);width:76px;opacity:.25;pointer-events:none}
.mfy-bulb{width:100%;height:auto;display:block}.mfy-ilustracion{max-width:220px;width:100%;margin:0 auto}.mfy-ilustracion svg{display:block;width:100%;height:auto}
.mfy-hero-principal{position:absolute;right:12px;bottom:0;width:230px;opacity:.85;pointer-events:none}.mfy-hero-principal svg{width:100%;height:auto}
.st-key-mfy_page_header:has(.mfy-hero-principal) .mfy-hero-copy{padding-right:225px}
:is([class*=st-key-mfy_form_],[class*=st-key-mfy_kpi_],[class*=st-key-mfy_chart_],.st-key-dashboard_filters,.st-key-mfy_login,[data-testid=stForm],.mfy-card,.mfy-highlight){position:relative;border:1px solid var(--mfy-border);border-top:3px solid #6699FF;border-radius:16px;background:#FFF;box-shadow:var(--mfy-shadow);padding:20px;transition:transform 160ms,box-shadow 160ms}
:is([class*=st-key-mfy_kpi_],[class*=st-key-mfy_chart_],.mfy-card):hover{transform:translateY(-2px);box-shadow:var(--mfy-shadow-hover)}
.st-key-mfy_request [data-testid=stForm],.st-key-mfy_login [data-testid=stForm]{border:0;padding:0;box-shadow:none}
.mfy-section-title{display:flex;align-items:center;gap:12px;margin:0 0 14px}.mfy-section-title>span{display:grid;place-items:center;flex-shrink:0;width:36px;height:36px;border-radius:12px;background:var(--mfy-gradient);color:white;font-weight:700}.mfy-section-title h2{font-size:16px!important;margin:0}.mfy-section-title i{flex:1;height:1px;background:var(--mfy-border)}
button[kind=primary],button[data-testid=stBaseButton-primary]{background:var(--mfy-gradient)!important;border:0;color:white!important;box-shadow:0 4px 12px #3D6FE025;border-radius:10px;transition:transform 160ms}
button[kind=primary] :is(p,span){color:white!important}
button[kind=secondary]{border:1px solid #315BBC;border-radius:10px;color:#244FAF;background:white}
button[kind=secondary]:hover{background:#F1ECFF}button[kind=primary]:hover{transform:translateY(-1px)}
.st-key-mfy_danger button{background:#FCECEE!important;border-color:#963D47!important;color:#963D47!important}
[data-testid=stTabs] [data-baseweb=tab-list]{gap:8px;max-width:100%;overflow-x:auto}
[data-testid=stTabs] [data-baseweb=tab]{min-height:44px;flex-shrink:0;border-radius:10px 10px 0 0}
[data-baseweb=tab-highlight]{background:var(--mfy-gradient)}
[data-testid=stAlert]{border-radius:12px;line-height:1.5;overflow-wrap:anywhere}
.mfy-notice{border:1px solid var(--mfy-border);border-left:4px solid #3D6FE0;padding:12px 16px;border-radius:12px;background:#EAF1FF;color:#0B2545}
.mfy-notice.atencion{background:#FFF6D1;border-left-color:#C69A00}.mfy-notice.error{background:#FCECEE;border-left-color:#963D47}.mfy-notice.exito{background:#E7F5ED;border-left-color:#216342}
.mfy-empty,.mfy-all-done{display:flex;align-items:center;gap:16px;padding:22px;border-radius:16px;background:linear-gradient(135deg,#EAF1FF,#F1ECFF);border:1px solid var(--mfy-border);color:#0B2545}
.mfy-empty>span,.mfy-all-done>.mfy-bulb{max-width:80px;flex-shrink:0}.mfy-empty .mfy-ilustracion{width:100px;margin:0}.mfy-empty p{margin:4px 0}
.mfy-chips,.mfy-state-key{display:flex;flex-wrap:wrap;gap:8px}.mfy-chips span,.mfy-badge{display:inline-flex;align-items:center;min-height:28px;padding:5px 10px;border-radius:999px;font-size:12px;max-width:100%;overflow-wrap:anywhere}.mfy-chips span{background:#F1ECFF;color:#6533A8;border:1px solid #CCCCFF}
.mfy-table-wrap{width:100%;overflow-x:auto;border:1px solid var(--mfy-border);border-radius:16px;background:white}
.mfy-table{border-collapse:collapse;width:100%;font-size:14px}.mfy-table caption{text-align:left;padding:14px;color:#5B6B82}.mfy-table th{background:#F1ECFF;color:#0B2545;padding:12px;text-align:left}.mfy-table td{padding:12px;border-bottom:1px solid #E3E8F4;overflow-wrap:anywhere}.mfy-table tbody tr:hover{background:#EAF1FF}
[data-testid=stDataFrame]{max-width:100%;overflow-x:auto}
[data-testid=stCode],pre{max-width:100%;overflow-x:auto}code{overflow-wrap:anywhere}
.st-key-mfy_form_compartir_descargas img{max-width:100%;height:auto;object-fit:contain}
.mfy-kpi-icon{display:grid;place-items:center;width:36px;height:36px;border-radius:12px;background:#EAF1FF;color:#244FAF;font-size:22px;margin-bottom:8px}
.mfy-tone-morado{background:#F1ECFF;color:#6533A8}.mfy-tone-amarillo{background:#FFF6D1;color:#705800}
[class*=st-key-mfy_kpi_] [data-testid=stMetric]{padding:0;background:transparent;border:0;box-shadow:none}
[class*=st-key-mfy_kpi_] [data-testid=stMetricValue]{font-size:26px;color:#0B2545}
.mfy-sparkline{display:block;width:100%;max-height:44px}.mfy-sparkline polyline{stroke:#3D6FE0;stroke-width:2;fill:none}.mfy-sparkline circle{fill:#3D6FE0}.mfy-spark-top{stop-color:#6699FF;stop-opacity:.2}.mfy-spark-bottom{stop-color:#6699FF;stop-opacity:0}
[class*=st-key-mfy_hoy_accion_] button{width:100%;min-height:138px;justify-content:flex-start;text-align:left;padding:20px;border:1px solid #E3E8F4;border-top:4px solid #9966FF;border-radius:16px;background:white;box-shadow:var(--mfy-shadow)}
[class*=st-key-mfy_hoy_accion_] button strong{display:block;font-size:30px;color:#0B2545}[class*=st-key-mfy_hoy_accion_] button p{font-size:15px;color:#0B2545}
.st-key-mfy_form_compartir_hoy{padding:12px 16px}.st-key-hoy_solicitudes_todas button{border:0;text-decoration:underline;background:transparent;color:#244FAF}
.st-key-casos_chips_estados button{min-height:44px;white-space:normal}
.st-key-mfy_dashboard_kpis [class*=st-key-mfy_kpi_]{min-height:150px;padding:16px}
.st-key-mfy_dashboard_kpis .mfy-kpi-icon{width:30px;height:30px;font-size:18px}

.st-key-mfy_login_layout{padding:16px 0}.st-key-mfy_login_brand{min-height:440px;padding:32px}.mfy-login-steps{display:grid;gap:18px;margin-top:24px}.mfy-login-steps span{display:flex;gap:12px;align-items:center;color:white}.mfy-login-steps b{display:grid;place-items:center;border:1px solid #FFFFFF80;border-radius:12px;width:36px;height:36px}.st-key-mfy_login img{max-width:240px;margin:auto}.mfy-login-subtitle{color:#5B6B82}
.mfy-login-information{background:#F1ECFF;border-left:4px solid #FFCC00;border-radius:12px;padding:14px;color:#0B2545;white-space:normal}
.mfy-public-progress{display:flex;justify-content:space-between;gap:8px;font-size:13px;color:#5B6B82}.mfy-public-progress .active{color:#244FAF;font-weight:700}.mfy-progress-track{height:6px;border-radius:6px;background:#E3E8F4;overflow:hidden}.mfy-progress-track i{display:block;height:100%;background:var(--mfy-gradient);transition:transform 180ms}


.mfy-public-links{display:flex;flex-wrap:wrap;gap:14px;align-items:center}.mfy-public-links a{color:white;min-height:44px;display:inline-flex;align-items:center;gap:6px}.mfy-public-links svg{width:22px;height:22px}
.st-key-mfy_form_publico{max-width:720px;margin:auto}.st-key-mfy_form_publico .mfy-section-title h2{font-size:16px!important}
[data-testid=stTextInput]:has(input[aria-label="Deja este campo vacío"]),[data-testid=stTextInput]:has(input[aria-label="Sitio web de confirmación"]){position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.mfy-success{padding:24px;border-radius:24px;border:1px solid #CCCCFF;background:#F1ECFF;text-align:center}.mfy-success .mfy-ilustracion{max-width:180px}
.mfy-timeline{border-left:2px solid #CCCCFF;padding-left:20px}.mfy-timeline article{position:relative;margin:0 0 16px}.mfy-timeline article:before{content:'';position:absolute;left:-27px;top:7px;width:12px;height:12px;border-radius:50%;background:#9966FF}
.mfy-skeleton-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.mfy-skeleton{height:120px;border-radius:16px;background:linear-gradient(110deg,#EAF1FF,#F1ECFF,#EAF1FF)}
.st-key-mfy_generate,.st-key-mfy_quote_ready,.st-key-mfy_quote_downloads,.st-key-mfy_undo{position:fixed;bottom:20px;right:24px;z-index:900;max-width:calc(100vw - 32px);padding:14px;border-radius:16px;background:white;box-shadow:var(--mfy-shadow-hover);border:1px solid #E3E8F4}.st-key-mfy_quote_ready,.st-key-mfy_quote_downloads{bottom:85px;max-height:60vh;overflow-y:auto}
.mfy-confetti{display:none}.footer{font-size:13px;color:#5B6B82;text-align:center;padding:24px 0;border-top:1px solid #E3E8F4;margin-top:24px}
.mfy-public-success>svg{width:64px;height:64px}.mfy-public-success{text-align:center}.mfy-public-summary dd{margin:0;overflow-wrap:anywhere}.mfy-progress-1 i{width:33.33%}.mfy-progress-2 i{width:66.66%}.mfy-progress-3 i{width:100%}.mfy-public-progress{display:block}.mfy-progress-labels{display:flex;gap:12px;margin-bottom:8px}.mfy-progress-labels span{flex:1}
@media(max-width:1023px){.block-container{padding-inline:20px}.st-key-mfy_login_layout>[data-testid=stHorizontalBlock]{flex-wrap:wrap}.st-key-mfy_login_layout>[data-testid=stHorizontalBlock]>[data-testid=stColumn]{flex:1 1 100%;width:100%}.st-key-mfy_login_brand{min-height:240px}}
@media(max-width:767px){
 .block-container{padding:20px 16px 100px}.stApp:has(.mfy-top-nav-marker,.mfy-public-nav-marker) .block-container{padding-top:80px}
 .stApp{background:radial-gradient(ellipse at 0 0,#6699FF13,transparent 60%),linear-gradient(160deg,#F4F7FF,#FFF);background-attachment:scroll}
 .st-key-mfy_top_mobile{display:block;right:16px;width:60px!important}.st-key-mfy_top_account{right:86px;width:112px!important}
 .stApp:has(.mfy-top-nav-marker) [data-testid=stHeader]{padding-right:206px}
 .stApp:has(.mfy-top-nav-marker) [data-testid=stHeader] .rc-overflow{display:none!important}
 [data-testid=stHeaderLogo]{width:125px!important;max-width:125px!important;margin-left:12px}
 .st-key-mfy_top_mobile [data-testid=stPopoverButton] p{font-size:0}.st-key-mfy_top_mobile [data-testid=stIconMaterial]{font-size:24px}
 :is(.st-key-mfy_page_header,.mfy-hero,.st-key-mfy_public_header){min-height:112px;padding:16px;border-radius:16px}
 .st-key-mfy_page_header:has(.mfy-eyebrow[data-vista=HOY]){min-height:170px;padding:20px}
 .mfy-hero-copy{padding-right:38px}.mfy-hero-copy h1{font-size:25px!important}.mfy-hero-orbit{right:12px;width:38px;opacity:.2}
 .mfy-hero-principal{width:135px;opacity:.3}.st-key-mfy_page_header:has(.mfy-hero-principal) .mfy-hero-copy{padding-right:35px}
 :is([class*=st-key-mfy_form_],[class*=st-key-mfy_chart_],[data-testid=stForm],.st-key-mfy_login){padding:16px}
 [data-testid=stMain] :is(.stButton,.stDownloadButton,.stLinkButton,.stFormSubmitButton)>:is(button,a){width:100%;min-height:44px;white-space:normal}
 [data-testid=stMain] :is(input,textarea,[role=combobox]){font-size:16px!important;min-width:0;max-width:100%}
 [data-testid=stMain] [data-testid=stWidgetLabel] p{white-space:normal;overflow-wrap:anywhere}
 [data-testid=stMain] [data-testid=stWidgetLabel] button{min-width:44px;min-height:44px}
 .mfy-table,.mfy-table tbody,.mfy-table tr{display:block;width:100%}.mfy-table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.mfy-table tr{padding:10px;border-bottom:1px solid #E3E8F4}.mfy-table td{display:grid;grid-template-columns:minmax(70px,30%) minmax(0,1fr);gap:8px;border:0;padding:8px 0}.mfy-table td:before{content:attr(data-label);color:#5B6B82;font-size:13px}
 .st-key-mfy_dashboard_kpis [data-testid=stHorizontalBlock]{flex-wrap:wrap;gap:8px}.st-key-mfy_dashboard_kpis [data-testid=stHorizontalBlock]>[data-testid=stColumn]{width:calc(50% - 4px)!important;flex:0 0 calc(50% - 4px)!important;min-width:0!important}.st-key-mfy_dashboard_kpis [class*=st-key-mfy_kpi_]{min-height:138px;padding:12px}.st-key-mfy_dashboard_kpis [data-testid=stMetricValue]{font-size:18px}
 .mfy-skeleton-grid{grid-template-columns:1fr}
 .st-key-mfy_public_actions{position:sticky;bottom:0;padding:8px 0 calc(8px + env(safe-area-inset-bottom));background:#F4F7FF;z-index:20}
 .st-key-mfy_generate{left:16px;right:16px;bottom:calc(12px + env(safe-area-inset-bottom))}
 [data-testid=stImage] img{max-width:100%;height:auto} [data-testid=stDialog] [role=dialog]{max-width:calc(100vw - 24px);max-height:calc(100dvh - 24px);overflow-y:auto}
}
@media(prefers-reduced-motion:reduce),(prefers-reduced-data:reduce){.stApp{background:linear-gradient(160deg,#F4F7FF,#FFF)}.stApp:before,.mfy-hero-orbit,.mfy-hero-principal,.mfy-ilustracion{display:none!important}*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
html[data-mfy-light=true] .stApp{background:linear-gradient(160deg,#F4F7FF,#FFF)}
html[data-mfy-light=true] :is(.stApp:before,.mfy-hero-orbit,.mfy-hero-principal,.mfy-ilustracion){display:none!important}
html[data-mfy-light=true] *,html[data-mfy-light=true] *:before,html[data-mfy-light=true] *:after{animation:none!important;transition:none!important}
'''


def _compactar(css):
    css=re.sub(r'\s+',' ',re.sub(r'/\*.*?\*/','',css,flags=re.S)).strip()
    css=re.sub(r'\s*([{};,])\s*',r'\1',css).replace(';}', '}')
    # Alias de clase equivalentes, verificados en el frontend de Streamlit 1.65.
    for nombre in ('stHorizontalBlock','stVerticalBlock','stColumn','stElementContainer'):
        css=css.replace('[data-testid='+nombre+']','.'+nombre)
    # Solo el CSS emitido se compacta. Las variables legibles permanecen arriba.
    variables={n:'--v'+str(i) for i,n in enumerate(dict.fromkeys(re.findall(r'--mfy-[\w-]+',css)))}
    return re.sub(r'--mfy-[\w-]+',lambda m:variables[m[0]],css)


# Exclusivo de la previsualización estática de desarrollo, no de las páginas.
CSS_PREVIEW='<style>'+'.mfy-preview-shell{max-width:1200px;margin:24px auto;padding:16px}.mfy-preview-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.mfy-preview-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}@media(max-width:767px){.mfy-preview-grid{grid-template-columns:minmax(0,1fr)}.mfy-preview-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}'+'</style>'

CSS_VIDRIO='.mfy-glass-chips{display:flex;flex-wrap:wrap;gap:8px}.mfy-glass-chip{display:grid;gap:4px;padding:8px 12px;border:1px solid #FFFFFF70;border-radius:12px;color:white;background:#0B254540}.mfy-glass-chip small{font-size:12px}'
CSS_COPIAR='button{font:inherit;box-sizing:border-box;width:100%;min-height:44px;border:1px solid #315BBC;border-radius:10px;padding:10px;background:white;color:#244FAF;cursor:pointer}button:focus-visible{outline:3px solid #315BBC;outline-offset:2px}'
# Streamlit distingue CSS literal de una ruta por los saltos de línea.
CSS_COPIAR+='\n'
CSS_EN_VIVO='.live[hidden]{display:none!important}\n'+CSS_VIDRIO
def _css_estados():
    grupos={}
    for tipo,estados in CATALOGO.items():
        for e in estados.values():
            colores=tuple(e[k] for k in ('fondo','texto','borde','solido'))
            grupos.setdefault(colores,set()).add('.'+clase_estado(e['clave'],tipo))
    css=''.join(','.join(selectores)+'{'+''.join(f'--s-{k}:{v};' for k,v in zip(('bg','fg','b','s'),colores))+'}' for colores,selectores in grupos.items())
    css+='[class*=mfy-estado-]{color:var(--s-fg);background:var(--s-bg);border:1px solid var(--s-b)}.mfy-badge{gap:5px}.mfy-table tr[class*=mfy-estado-]{border-left:4px solid var(--s-s);background:white;color:inherit}.mfy-case-band{padding:12px 16px;border-left:6px solid var(--s-s);border-radius:12px}.mfy-timeline article[class*=mfy-estado-]{border:0;border-left:3px solid var(--s-s);padding:8px}.mfy-timeline article[class*=mfy-estado-]:before{background:var(--s-s)}'
    # Orden de las opciones nativas; conserva la subetapa En revisión.
    for n,estado in enumerate(('Solicitud','En revisión','Cotizado','Vendido','En ejecución','Finalizado','Cancelado'),2):
        e=color_estado(estado)
        css+=f'.st-key-casos_chips_estados button:nth-child({n})'+'{'+f'background:{e["fondo"]};color:{e["texto"]};border-color:{e["borde"]}'+'}'
    css+='.st-key-casos_chips_estados button[data-selected]{outline:3px solid currentColor;outline-offset:2px;font-weight:700}'
    return css

ESTILOS_BASE='<style>'+_compactar(CSS_PORTAL+_css_estados())+CSS_VIDRIO+'</style>'


from contextlib import contextmanager
from html import escape
from datetime import date, datetime
from math import isfinite
from re import sub

import streamlit as st

from utils.estados import estado_visual



def ampolleta_svg():
    from servicios.imagenes import leer_icono
    return leer_icono()


def ilustracion(nombre, clase='mfy-ilustracion'):
    from servicios.imagenes import leer_svg
    return '<div class="'+escape(clase,quote=True)+'" aria-hidden="true">'+leer_svg(nombre)+'</div>'


def html_chips_vidrio(metricas):
    return '<div class="mfy-glass-chips">'+''.join(
        f'<span class="mfy-glass-chip"><small>{escape(str(label))}</small><strong>{escape(str(valor))}</strong></span>'
        for label,valor in metricas)+'</div>'


def sparkline_svg(valores, etiquetas=None, key='serie', formato='entero'):
    """Hasta seis valores reales. Los None son huecos, nunca ceros inventados."""
    valores=list(valores)[-6:]
    etiquetas=list(etiquetas or [])[-len(valores):]
    numeros=[float(v) if v is not None and isfinite(float(v)) else None for v in valores]
    validos=[v for v in numeros if v is not None]
    if not validos:return ''
    inferior,superior=min(0,min(validos)),max(validos)
    amplitud=superior-inferior or 1
    segmentos=[];actual=[];puntos=[]
    for i,v in enumerate(numeros):
        if v is None:
            if actual:segmentos.append(actual);actual=[]
            continue
        x=4+i*192/max(1,len(numeros)-1);y=35-(v-inferior)/amplitud*28
        actual.append(f'{x:.2f},{y:.2f}');puntos.append((x,y))
    if actual:segmentos.append(actual)
    def numero(v):
        if formato=='moneda':return '$'+f'{v:,.0f}'.replace(',','.')
        if formato=='porcentaje':return f'{v:.1f}'.replace('.',',')+'%'
        return f'{v:,.0f}'.replace(',','.')
    descripcion=' · '.join(f'{etiquetas[i] if i<len(etiquetas) else i+1}: {numero(v)}' for i,v in enumerate(numeros) if v is not None)
    ident='spark-'+sub(r'[^a-zA-Z0-9_-]','',str(key))
    return (f'<svg class="mfy-sparkline" viewBox="0 0 200 42" role="img" aria-label="{escape(descripcion,quote=True)}">'
        f'<title>{escape(descripcion)}</title><defs><linearGradient id="{ident}" x2="0" y2="1">'
        '<stop class="mfy-spark-top"/><stop offset="1" class="mfy-spark-bottom"/></linearGradient></defs>'
        +''.join(f'<polygon points="{s[0].split(",")[0]},39 {" ".join(s)} {s[-1].split(",")[0]},39" fill="url(#{ident})"/>'
                  f'<polyline points="{" ".join(s)}"/>' for s in segmentos)
        +''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.4"/>' for x,y in puntos)+'</svg>')


def identidad_usuario(nombre, es_admin):
    nombre = str(nombre or "Mi cuenta")
    rol = "Administración" if es_admin else "Cliente"
    partes = nombre.split()
    iniciales = ''.join(p[:1] for p in (partes[:1] + partes[-1:] if len(partes)>1 else partes)).upper()
    st.markdown(f'<div class="mfy-identity"><span class="mfy-avatar" aria-hidden="true">{escape(iniciales)}</span>'
                f'<div><strong>{escape(nombre)}</strong><small>{rol}</small></div></div>', unsafe_allow_html=True)


def badge_estado(estado, cantidad=None):
    return chip_estado(estado,cantidad=cantidad)


def leyenda_estados():
    with st.expander('¿Qué significa cada color?'):
        for e in CATALOGO['caso'].values():
            st.markdown(chip_estado(e['clave'])+' '+escape(e['ayuda']),unsafe_allow_html=True)


def html_tabla_registros(frame, titulo="Registro de casos"):
    """Tabla accesible que se convierte en fichas en celular. Escapa todos los datos."""
    encabezados = ''.join(f'<th scope="col">{escape(str(c))}</th>' for c in frame.columns)
    filas = []
    for registro in frame.to_dict("records"):
        celdas = []
        for columna, valor in registro.items():
            if columna == "Estado":
                contenido = badge_estado(valor)
            else:
                if isinstance(valor, (date, datetime)):
                    valor = valor.strftime("%d/%m/%Y")
                contenido = f'<span>{escape(str(valor if valor is not None else "—"))}</span>'
            celdas.append(f'<td data-label="{escape(str(columna), quote=True)}">{contenido}</td>')
        clase=' class="'+clase_estado(registro['Estado'])+'"' if 'Estado' in registro else ''
        filas.append('<tr'+clase+'>'+''.join(celdas)+'</tr>')
    return ('<div class="mfy-table-wrap" tabindex="0"><table class="mfy-table">'
            f'<caption>{escape(titulo)} · {len(frame)} registros</caption><thead><tr>{encabezados}</tr></thead>'
            '<tbody>'+''.join(filas)+'</tbody></table></div>')


def tabla_registros(frame, titulo="Registro de casos"):
    st.markdown(html_tabla_registros(frame, titulo), unsafe_allow_html=True)


def pie_portal():
    st.markdown('<div class="footer">Mente y Futuro · Sistema de gestión</div>', unsafe_allow_html=True)


def html_contenido_encabezado(titulo, subtitulo, etiqueta, icono):
    """Solo texto escapado: no permite introducir HTML a través de los datos."""
    etiqueta=str(etiqueta).upper().removeprefix('MENTE Y FUTURO · ')
    return (f'<div class="mfy-hero-copy"><span class="mfy-eyebrow" data-vista="{escape(str(etiqueta).upper(),quote=True)}">MENTE Y FUTURO · {escape(str(etiqueta).upper())}</span>'
            f'<h1>{escape(str(titulo))}</h1><p>{escape(str(subtitulo))}</p></div>'
            '<span class="mfy-hero-orbit" aria-hidden="true">'+ampolleta_svg()+'</span>')


def encabezado_pagina(titulo, subtitulo, etiqueta, icono, acciones=None, mostrar_metricas=True):
    """Un encabezado por página. acciones es una función que dibuja widgets nativos.

    Los botones conservan callbacks, foco y permisos de Streamlit. No se acepta
    HTML de acciones ni JavaScript; en móvil las acciones se sitúan bajo el título.
    """
    vista={'HOY':'hoy','DASHBOARD':'dashboard','SEGUIMIENTO':'casos'}.get(str(etiqueta).upper())
    def contenido():
        st.markdown(html_contenido_encabezado(titulo, subtitulo, etiqueta, icono), unsafe_allow_html=True)
        if vista=='hoy':
            st.markdown(ilustracion('equipo','mfy-hero-principal'),unsafe_allow_html=True)
        elif titulo=='Mis documentos':
            st.markdown(ilustracion('documentos','mfy-hero-principal'),unsafe_allow_html=True)
        if vista and mostrar_metricas:
            from utils.en_vivo import metricas_cabecera
            metricas_cabecera(vista)
        elif str(etiqueta).upper()=='SOLICITUDES':
            st.markdown(html_chips_vidrio([('01','Datos de contacto'),('02','Servicio y objetivos')]),unsafe_allow_html=True)
    with st.container(key="mfy_page_header"):
        if acciones is None:
            contenido()
        else:
            texto, botones = st.columns([3, 1], gap="large")
            with texto:
                contenido()
            with botones, st.container(key="mfy_header_actions"):
                acciones()


def panel_marca_login():
    with st.container(key='mfy_login_brand'):
        st.markdown(html_contenido_encabezado('Tu próximo paso, en un solo lugar.',
            'Conversemos sobre lo que necesita tu equipo.','BIENVENIDA',''),unsafe_allow_html=True)
        st.markdown(ilustracion('bienvenida'),unsafe_allow_html=True)
        st.markdown('''<div class="mfy-login-steps"><span><b>01</b> Cuéntanos qué necesitas</span>
        <span><b>02</b> Revisamos tu solicitud</span>
        <span><b>03</b> Te enviamos una propuesta a tu medida</span></div>''',unsafe_allow_html=True)


def html_encabezado(agrupacion, desde, hasta):
    """Compatibilidad para la vista HTML del dashboard: usa el mismo contenido."""
    return '<section class="mfy-hero">'+html_contenido_encabezado(
        "Una mirada a tu negocio", f"{agrupacion} · {desde:%d/%m/%Y} – {hasta:%d/%m/%Y}", "DASHBOARD", "✦")+'</section>'


def titulo_seccion(numero, titulo):
    st.markdown(f'<div class="mfy-section-title"><span aria-hidden="true">{int(numero):02d}</span>'
                f'<h2><span class="mfy-sr-only">{int(numero):02d} / </span>{escape(str(titulo).upper())}</h2>'
                '<i aria-hidden="true"></i></div>', unsafe_allow_html=True)


@contextmanager
def seccion_formulario(numero, titulo, key):
    # Tres pasos de animación como máximo: 300 ms + 0/50/100 ms.
    with st.container(key=f"mfy_form_section_s{min(int(numero), 3)}_{key}"):
        titulo_seccion(numero, titulo)
        yield


@contextmanager
def cargando_datos(mensaje="Preparando la información…", cantidad=3):
    marcador = st.empty()
    marcador.markdown(esqueletos(cantidad), unsafe_allow_html=True)
    try:
        with st.spinner(mensaje):
            yield
    finally:
        marcador.empty()


def chips_activos(valores):
    st.markdown('<div class="mfy-chips">'+''.join(f'<span>{escape(str(v))}</span>' for v in valores)+'</div>', unsafe_allow_html=True)


def tarjeta_kpi(label, value, *, icon="↗", tone="azul", delta=None, help=None, caption=None, inverse=False, key,
                serie=None, etiquetas=None, contexto_serie=None, formato_serie='entero'):
    with st.container(key=f"mfy_kpi_{key}"):
        st.markdown(f'<div class="mfy-kpi-icon mfy-tone-{escape(tone)}" aria-hidden="true">{escape(icon)}</div>', unsafe_allow_html=True)
        st.metric(label, value, delta=delta, help=help, delta_color="inverse" if inverse else "normal")
        if caption:
            st.caption(caption)
        if serie is not None:
            st.markdown(sparkline_svg(serie,etiquetas,key,formato_serie),unsafe_allow_html=True)
            if contexto_serie:st.caption(contexto_serie)


def tarjeta_accion(titulo, cantidad, *, key, icono, ayuda, on_click, args=()):
    """Toda la tarjeta es un botón nativo: teclado, foco y callback protegidos."""
    with st.container(key='mfy_hoy_accion_'+key):
        st.button(f'**{cantidad}**\n\n{titulo}', icon=icono, help=ayuda,
                  key='hoy_tarjeta_'+key, width='stretch', on_click=on_click, args=args)


def todo_al_dia():
    st.markdown('<div class="mfy-all-done">'+ampolleta_svg()+
                '<div><strong>Todo al día. Buen trabajo</strong><p>Hoy tienes espacio para nuevas ideas.</p></div></div>',unsafe_allow_html=True)


def preparar_celebracion(identificador, mensaje):
    """Solo se llama después de una escritura confirmada. No ejecuta escrituras."""
    st.session_state['mfy_celebracion']=dict(id=str(identificador),mensaje=mensaje)


def mostrar_celebracion():
    from pathlib import Path
    from streamlit.components.v2 import component
    evento=st.session_state.pop('mfy_celebracion',None)
    if not evento or st.session_state.get('mfy_celebracion_vista')==evento['id']:return
    st.session_state['mfy_celebracion_vista']=evento['id']
    st.toast(evento['mensaje'],icon=':material/celebration:')
    componente=component('mfy_celebracion',html='<span aria-hidden="true"></span>',
        js=(Path(__file__).resolve().parent.parent/'utils'/'celebracion.js').read_text(encoding='utf-8'))
    componente(data={'id':evento['id']},key='mfy_celebracion',height=0)


@contextmanager
def tarjeta_grafico(titulo, subtitulo, key, help=None):
    with st.container(key=f"mfy_chart_{key}"):
        st.subheader(titulo)
        st.caption(subtitulo,help=help)
        yield


def estado_vacio(mensaje="Aún no hay datos en este período. Prueba con un rango más amplio.", icon="◌"):
    st.markdown('<div class="mfy-empty" role="status">'+ilustracion('vacio')+f'<p>{escape(mensaje)}</p></div>', unsafe_allow_html=True)


def dato_destacado(texto):
    st.markdown(f'<aside class="mfy-highlight"><span>DATO DESTACADO</span><p>{escape(texto)}</p></aside>', unsafe_allow_html=True)


def esqueletos(cantidad=4):
    return ('<div class="mfy-skeleton-grid" role="status" aria-live="polite">'
            '<span class="mfy-sr-only">Cargando información</span>'
            + ''.join('<div class="mfy-skeleton" aria-hidden="true"></div>' for _ in range(cantidad))+'</div>')


def enlaces_publicos(config):
    enlaces=[]
    # Solo destinos validados y provenientes de mf_configuracion.datos.
    iconos={
        'facebook':'<path d="M14 8h3V4h-3c-4 0-5 2-5 5v3H6v4h3v8h4v-8h3l1-4h-4V9c0-1 0-1 1-1Z"/>',
        'instagram':'<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1"/>'}
    for red in ('facebook','instagram'):
        url=config['redes'].get(red)
        if url:enlaces.append(f'<a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="{red.capitalize()}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">{iconos[red]}</svg></a>')
    if config.get('sitio_web'):
        enlaces.append(f'<a href="{escape(config["sitio_web"],quote=True)}" target="_blank" rel="noopener noreferrer">Volver al sitio ↗</a>')
    return '<nav class="mfy-public-links" aria-label="Contacto y redes">'+''.join(enlaces)+'</nav>' if enlaces else ''


@contextmanager
def tarjeta(titulo=None, *, key='tarjeta'):
    with st.container(key='mfy_form_'+key):
        if titulo:st.subheader(titulo)
        yield


def tarjeta_lista(titulo, detalle='', *, accion=None, key='lista'):
    with tarjeta(key=key):
        st.markdown('**'+escape(str(titulo))+'**')
        if detalle:st.write(detalle)
        if accion:accion()


def chip(texto):
    chips_activos([texto])


def insignia(estado):
    st.markdown(badge_estado(estado),unsafe_allow_html=True)


def boton_principal(texto, **kwargs):
    kwargs.setdefault('type','primary')
    return st.button(texto,**kwargs)


def boton_secundario(texto, **kwargs):
    kwargs.setdefault('type','secondary')
    return st.button(texto,**kwargs)


def boton_peligro(texto, **kwargs):
    with st.container(key='mfy_danger'):
        return st.button(texto,**kwargs)


def aviso(mensaje, tipo='info'):
    clases={'exito':'exito','info':'info','atencion':'atencion','error':'error'}
    clase=clases.get(tipo,'info')
    st.markdown(f'<div class="mfy-notice {clase}" role="status">{escape(str(mensaje))}</div>',unsafe_allow_html=True)


def tabla(frame, titulo='Registro'):
    tabla_registros(frame,titulo)


def linea_de_tiempo(eventos):
    st.markdown('<section class="mfy-timeline">'+''.join(
        '<article'+(' class="'+clase_estado(e['estado'])+'"' if e.get('estado') else '')+'><small>'+escape(str(e.get('fecha','')))+ '</small><strong>'+escape(str(e.get('titulo','')))+
        '</strong><p>'+escape(str(e.get('detalle','')))+ '</p></article>' for e in eventos)+'</section>',unsafe_allow_html=True)


def avatar(nombre):
    partes=str(nombre or 'Mi cuenta').split()
    letras=''.join(p[0] for p in (partes[:1]+partes[-1:] if len(partes)>1 else partes)).upper()
    return '<span class="mfy-avatar" aria-hidden="true">'+escape(letras)+'</span>'


def esqueleto_carga(cantidad=3):
    st.markdown(esqueletos(cantidad),unsafe_allow_html=True)
