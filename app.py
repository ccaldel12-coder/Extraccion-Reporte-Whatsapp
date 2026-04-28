import streamlit as st
from datetime import datetime
from io import BytesIO
import pandas as pd

from parser import (
    limpiar_texto,
    filtrar_por_fecha,
    procesar,
    obtener_rango_fechas,
    filtrar_por_fecha_envio
)

from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="Perforación", layout="wide")

# -------------------------
# ESTILO
# -------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #0b1f3a; color: white; }
    html, body, [class*="css"] { color: white !important; }
    label { color: white !important; }

    div[data-testid="stFileUploader"],
    div[data-testid="stSelectbox"],
    div[data-testid="stDateInput"] {
        background-color: white !important;
        border-radius: 8px;
        padding: 5px;
    }

    div[data-testid="stFileUploader"] *,
    div[data-testid="stSelectbox"] *,
    div[data-testid="stDateInput"] * {
        color: #0b1f3a !important;
    }

    div.stButton > button,
    div[data-testid="stDownloadButton"] button {
        background-color: white !important;
        color: #0b1f3a !important;
        font-weight: bold;
        border-radius: 8px;
    }

    div[data-testid="metric-container"] {
        background-color: transparent !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# HEADER
# -------------------------
st.image("encabezado.jpg", width=900)
st.title("📊 Reportes de Perforación")

archivo = st.file_uploader("Suba archivo WhatsApp (.txt)", type=["txt"])

if "df" not in st.session_state:
    st.session_state.df = None

# -------------------------
# PROCESO
# -------------------------
if archivo:

    texto = archivo.read().decode("utf-8")
    texto = limpiar_texto(texto)

    fecha_minima = datetime(2026, 4, 20)
    texto = filtrar_por_fecha_envio(texto, fecha_minima)

    if not texto.strip():
        st.error("❌ No hay mensajes válidos")
        st.stop()

    min_fecha, max_fecha = obtener_rango_fechas(texto)

    col1, col2 = st.columns(2)

    with col1:
        fecha_ini = st.date_input("Fecha inicio", min_fecha)

    with col2:
        fecha_fin = st.date_input("Fecha fin", max_fecha)

    if st.button("🚀 Procesar datos"):

        texto_filtrado = filtrar_por_fecha(
            texto,
            datetime.combine(fecha_ini, datetime.min.time()),
            datetime.combine(fecha_fin, datetime.max.time())
        )

        df = procesar(texto_filtrado)

        df["Perforado"] = pd.to_numeric(df["Perforado"], errors="coerce").fillna(0)
        df["Programado"] = pd.to_numeric(df["Programado"], errors="coerce").fillna(0)

        # 🚦 SEMÁFORO
        def semaforo(row):
            if row["Perforado"] == 0:
                return "🔴 Detenido"
            elif row["Perforado"] < row["Programado"]:
                return "🟡 Bajo"
            else:
                return "🟢 Cumple"

        df["Estado"] = df.apply(semaforo, axis=1)

        st.session_state.df = df

# -------------------------
# RESULTADOS
# -------------------------
if st.session_state.df is not None:

    df = st.session_state.df

    st.subheader("📊 Resultados")

    col1, col2 = st.columns(2)

    with col1:
        proyectos = ["Todos"] + sorted(df["Proyecto"].dropna().unique())
        proyecto_sel = st.selectbox("Proyecto", proyectos)

    with col2:
        turnos = ["Todos"] + sorted(df["Turno"].dropna().unique())
        turno_sel = st.selectbox("Turno", turnos)

    df_filtrado = df.copy()

    if proyecto_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Proyecto"] == proyecto_sel]

    if turno_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Turno"] == turno_sel]

    # TABLA
    st.dataframe(df_filtrado, use_container_width=True)

    # KPI
    total = df_filtrado["Perforado"].sum()

    st.markdown(
        f"<h3 style='color:white;'>Total metros perforados: {total:,.2f}</h3>",
        unsafe_allow_html=True
    )

    # RESUMEN SEMÁFORO
    st.subheader("🚦 Resumen Operacional")
    st.write(df_filtrado["Estado"].value_counts())

    # -------------------------
    # EXPORTAR EXCEL
    # -------------------------
    buffer = BytesIO()

    columnas_orden = [
        "Fecha",
        "Proyecto",
        "Turno",
        "Sonda",
        "Pozo",
        "Estado",
        "Programado",
        "Fondo Inicial",   # 👈 NUEVO ORDEN
        "Fondo Final",     # 👈 NUEVO ORDEN
        "Perforado",
        "Azimuth",
        "Inclinación",
        "Diámetro",
        "Recuperación (%)",
        "Recomendación",
        "Observaciones"
    ]

    columnas_orden = [c for c in columnas_orden if c in df_filtrado.columns]

    df_export = df_filtrado[columnas_orden].copy()

    wb = Workbook()
    ws = wb.active

    for r in dataframe_to_rows(df_export, index=False, header=True):
        ws.append(r)

    wb.save(buffer)

    st.download_button("📥 Descargar Excel", buffer.getvalue(), "reporte.xlsx")