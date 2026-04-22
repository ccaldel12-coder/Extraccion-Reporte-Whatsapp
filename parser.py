import re
import pandas as pd
from datetime import datetime

# -------------------------
# LIMPIEZA
# -------------------------
def limpiar_texto(texto):
    return texto.replace("\xa0", " ")

# -------------------------
# LIMPIAR NÚMEROS
# -------------------------
def limpiar_numero(valor):
    if not valor:
        return None
    valor = valor.replace("mts", "").replace("mt", "")
    valor = valor.replace(".", "").replace(",", ".")
    valor = valor.strip()
    try:
        return float(valor)
    except:
        return None

# -------------------------
# 🔥 DIVIDIR MENSAJES WHATSAPP
# -------------------------
def dividir_mensajes(texto):
    patron = r"\d{1,2}/\d{1,2}/\d{4},"
    indices = [m.start() for m in re.finditer(patron, texto)]

    bloques = []

    for i in range(len(indices)):
        inicio = indices[i]
        fin = indices[i+1] if i+1 < len(indices) else len(texto)
        bloques.append(texto[inicio:fin])

    return bloques

# -------------------------
# 🔥 FILTRO POR FECHA ENVÍO
# -------------------------
def filtrar_por_fecha_envio(texto, fecha_minima):

    mensajes = dividir_mensajes(texto)
    resultado = ""

    for msg in mensajes:

        match = re.match(r"(\d{1,2}/\d{1,2}/\d{4}),", msg)

        if not match:
            continue

        fecha = datetime.strptime(match.group(1), "%d/%m/%Y")

        if fecha >= fecha_minima:
            resultado += msg + "\n"

    return resultado

# -------------------------
# RANGO FECHAS (TURNO)
# -------------------------
def obtener_rango_fechas(texto):
    fechas = re.findall(
        r"TURNO\s+(?:DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})",
        texto,
        re.IGNORECASE
    )

    if not fechas:
        return None, None

    fechas_dt = [datetime.strptime(f, "%d/%m/%Y") for f in fechas]
    return min(fechas_dt), max(fechas_dt)

# -------------------------
# FILTRO POR TURNO
# -------------------------
def filtrar_por_fecha(texto, fecha_ini, fecha_fin):

    mensajes = dividir_mensajes(texto)
    resultado = ""

    for msg in mensajes:

        match = re.search(
            r"TURNO\s+(?:DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})",
            msg,
            re.IGNORECASE
        )

        if not match:
            continue

        fecha = datetime.strptime(match.group(1), "%d/%m/%Y")

        if fecha_ini <= fecha <= fecha_fin:
            resultado += msg + "\n"

    return resultado

# -------------------------
# DIVIDIR SONDAS
# -------------------------
def dividir_sondas(texto):
    bloques = re.split(r"(SONDA\s+[^\n]+)", texto)
    pares = []

    for i in range(1, len(bloques), 2):
        header = bloques[i]
        body = bloques[i+1] if i+1 < len(bloques) else ""
        pares.append((header, body))

    return pares

# -------------------------
# EXTRAER DATOS SONDA
# -------------------------
def extraer_sonda(header, bloque):

    def buscar(pat):
        m = re.search(pat, bloque, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else None

    sonda = header.replace("SONDA", "").strip()

    return {
        "Sonda": sonda,
        "Recomendación": buscar(r"Recomendación:\s*(.*)"),
        "Programado": limpiar_numero(buscar(r"Programado:\s*([^\n]*)")),
        "Fondo Inicial": limpiar_numero(buscar(r"Fondo Inicial:\s*([^\n]*)")),
        "Fondo Final": limpiar_numero(buscar(r"Fondo Final:\s*([^\n]*)")),
        "Perforado": limpiar_numero(buscar(r"(?:Perforado|Avance):\s*([^\n]*)")),
        "Azimuth": limpiar_numero(buscar(r"(?:Azimuth|Azimut):\s*([^\n]*)")),
        "Inclinación": limpiar_numero(buscar(r"Inclinación:\s*([^\n]*)")),
        "Diámetro": buscar(r"Diámetro:\s*([^\n]*)"),
        "Recuperación (%)": limpiar_numero(buscar(r"(?:Recuperación|Retorno):\s*([^\n]*)")),
        "Observaciones": buscar(r"Observaciones:(.*?)(?:SONDA|OBSERVACIONES GENERALES|$)")
    }

# -------------------------
# PROCESAR
# -------------------------
def procesar(texto):

    mensajes = dividir_mensajes(texto)

    filas = []

    for msg in mensajes:

        proyecto_match = re.search(r"PROYECTO\s+([^\n]+)", msg, re.IGNORECASE)
        proyecto = proyecto_match.group(1).strip() if proyecto_match else "No identificado"

        turno_match = re.search(r"TURNO\s+(DIA|NOCHE)", msg, re.IGNORECASE)
        turno = turno_match.group(1).upper() if turno_match else "No identificado"

        fecha_match = re.search(
            r"TURNO\s+(?:DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})",
            msg,
            re.IGNORECASE
        )
        fecha = fecha_match.group(1) if fecha_match else None

        sondas = dividir_sondas(msg)

        for h, b in sondas:
            data = extraer_sonda(h, b)

            data["Proyecto"] = proyecto
            data["Turno"] = turno
            data["Fecha"] = fecha

            filas.append(data)

    df = pd.DataFrame(filas)
    return df