import streamlit as st
import pandas as pd
from supabase import create_client

supabase = create_client(
    st.secrets["https://noldlxbmfjegljktzqxb.supabase.co"],
    st.secrets["sb_publishable_1Miox6QfQDzfCCTUtEUvEA_7CVPMgeL"]
)

response = supabase.table("casos").select("*").execute()
casos = pd.DataFrame(response.data)

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Mente y Futuro",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# ESTILOS
# =========================================================

st.markdown("""
<style>

    /* Fondo general */
    .stApp {
        background-color: #f5f7fb;
    }

    /* Títulos */
    h1 {
        color: #123b6d;
        font-weight: 700;
    }

    h2, h3 {
        color: #174f8a;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #123b6d;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    /* Tarjetas */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    .card-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 5px;
    }

    .card-value {
        font-size: 27px;
        font-weight: 700;
        color: #123b6d;
    }

    /* Etiquetas */
    .status {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 13px;
        font-weight: 600;
        background-color: #e8f1fb;
        color: #174f8a;
    }

    /* Separador */
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 25px 0;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATOS DE PRUEBA
# =========================================================

casos = pd.DataFrame({
    "Caso": [
        "2026-014",
        "2026-013",
        "2026-012",
        "2026-011"
    ],
    "Cliente": [
        "Empresa ABC",
        "Empresa XYZ",
        "Empresa Norte",
        "Empresa Sur"
    ],
    "Temática": [
        "Capacitación empresarial",
        "Liderazgo",
        "Trabajo en equipo",
        "Comunicación"
    ],
    "Participantes": [
        20,
        15,
        30,
        25
    ],
    "Horas": [
        8,
        6,
        10,
        6
    ],
    "Estado": [
        "Solicitud",
        "Vendido",
        "Vendido",
        "En seguimiento"
    ],
    "Tarifa": [
        "$480.000",
        "$360.000",
        "$600.000",
        "$420.000"
    ]
})

ventas = pd.DataFrame({
    "Mes": [
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre"
    ],
    "Ventas": [
        650000,
        900000,
        1200000,
        480000
    ]
})


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 0 25px 0;
        ">
            <div style="
                font-size:42px;
            ">
                📊
            </div>

            <div style="
                font-size:24px;
                font-weight:700;
            ">
                Mente y Futuro
            </div>

            <div style="
                font-size:13px;
                opacity:0.8;
            ">
                Gestión de casos y ventas
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Navegación")

    pagina = st.radio(
        "",
        [
            "Nueva solicitud",
            "Casos y cotizaciones",
            "Dashboard"
        ]
    )

    st.markdown("---")

    st.caption("Prototipo")
    st.caption("Datos de prueba")


# =========================================================
# PANTALLA 1 — NUEVA SOLICITUD
# =========================================================

if pagina == "Nueva solicitud":

    st.title("Nueva solicitud")

    st.write(
        "Registra los datos principales de un nuevo servicio."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Información del cliente")

        cliente = st.text_input(
            "Cliente",
            placeholder="Ej. Empresa ABC"
        )

        tematica = st.selectbox(
            "Temática",
            [
                "Capacitación empresarial",
                "Liderazgo",
                "Trabajo en equipo",
                "Comunicación"
            ]
        )

    with col2:

        st.subheader("Características del servicio")

        participantes = st.number_input(
            "Número de participantes",
            min_value=1,
            value=20
        )

        horas = st.number_input(
            "Horas de trabajo",
            min_value=1,
            value=8
        )

    st.markdown("---")

    st.subheader("Resumen")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Cliente</div>
                <div class="card-value">Empresa ABC</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Participantes</div>
                <div class="card-value">20</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Horas</div>
                <div class="card-value">8</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "Crear solicitud",
        type="primary",
        use_container_width=True
    ):

        st.success(
            "Solicitud creada correctamente. "
            "Caso asignado: 2026-015"
        )


# =========================================================
# PANTALLA 2 — CASOS Y COTIZACIONES
# =========================================================

elif pagina == "Casos y cotizaciones":

    st.title("Casos y cotizaciones")

    st.write(
        "Consulta y gestiona las solicitudes registradas."
    )

    st.markdown("---")

    # Tabla
    st.subheader("Registro de casos")

    st.dataframe(
        casos,
        width="stretch",
        hide_index=True,
        column_config={
            "Caso": st.column_config.TextColumn(
                "Caso"
            ),
            "Cliente": st.column_config.TextColumn(
                "Cliente"
            ),
            "Temática": st.column_config.TextColumn(
                "Temática"
            ),
            "Participantes": st.column_config.NumberColumn(
                "Participantes"
            ),
            "Horas": st.column_config.NumberColumn(
                "Horas"
            ),
            "Estado": st.column_config.TextColumn(
                "Estado"
            ),
            "Tarifa": st.column_config.TextColumn(
                "Tarifa"
            )
        }
    )

    st.markdown("---")

    st.subheader("Detalle del caso")

    col1, col2 = st.columns([2, 1])

    with col1:

        st.markdown(
            """
            <div class="card">

            <div style="
                font-size:13px;
                color:#64748b;
            ">
                CASO
            </div>

            <div style="
                font-size:28px;
                font-weight:700;
                color:#123b6d;
                margin-bottom:15px;
            ">
                #2026-014
            </div>

            <b>Cliente:</b> Empresa ABC<br>
            <b>Temática:</b> Capacitación empresarial<br>
            <b>Participantes:</b> 20<br>
            <b>Duración:</b> 8 horas

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="card">

            <div class="card-title">
                TARIFA SUGERIDA
            </div>

            <div class="card-value">
                $480.000
            </div>

            <br>

            <span class="status">
                Solicitud
            </span>

            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button(
        "Generar cotización",
        type="primary"
    ):

        st.success(
            "Cotización generada correctamente."
        )

    st.info(
        "La tarifa sugerida se obtiene considerando "
        "la temática, las horas y el número de participantes."
    )


# =========================================================
# PANTALLA 3 — DASHBOARD
# =========================================================

else:

    st.title("Dashboard")

    st.write(
        "Resumen de la actividad comercial de Mente y Futuro."
    )

    st.markdown("---")

    # Indicadores
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    Ventas acumuladas
                </div>
                <div class="card-value">
                    $3.230.000
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    Casos vendidos
                </div>
                <div class="card-value">
                    2
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    Casos registrados
                </div>
                <div class="card-value">
                    4
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    Ticket promedio
                </div>
                <div class="card-value">
                    $807.500
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Gráfico
    col1, col2 = st.columns([2, 1])

    with col1:

        st.subheader("Ventas por mes")

        st.bar_chart(
            ventas.set_index("Mes"),
            width="stretch"
        )

    with col2:

        st.subheader("Temáticas")

        tematicas = pd.DataFrame({
            "Solicitudes": [
                8,
                6,
                5,
                3
            ]
        }, index=[
            "Capacitación",
            "Liderazgo",
            "Trabajo en equipo",
            "Comunicación"
        ])

        st.bar_chart(
            tematicas,
            width="stretch"
        )

    st.markdown("---")

    st.subheader("Últimos casos")

    st.dataframe(
        casos,
        width="stretch",
        hide_index=True
    )

    st.caption(
        "Datos utilizados exclusivamente para demostración del prototipo."
    )
