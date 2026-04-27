import re
from datetime import datetime
import pandas as pd


# -------------------------
# LIMPIEZA TEXTO
# -------------------------
def limpiar_texto(texto):
    texto = texto.replace("\u202f", " ")
    return texto


# -------------------------
# FILTRO POR FECHA ENVÍO
# -------------------------
def filtrar_por_fecha_envio(texto, fecha_minima):
    bloques = re.split(r"\n(?=\d{1,2}/\d{1,2}/\d{4},)", texto)
    resultado = []

    for bloque in bloques:
        match = re.match(r"(\d{1,2}/\d{1,2}/\d{4})", bloque)
        if match:
            fecha_envio = datetime.strptime(match.group(1), "%d/%m/%Y")
            if fecha_envio >= fecha_minima:
                resultado.append(bloque)

    return "\n".join(resultado)


# -------------------------
# RANGO FECHAS TURNO
# -------------------------
def obtener_rango_fechas(texto):
    fechas = re.findall(r"TURNO\s+(?:DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})", texto, re.IGNORECASE)

    if not fechas:
        return None, None

    fechas_dt = [datetime.strptime(f, "%d/%m/%Y") for f in fechas]

    return min(fechas_dt), max(fechas_dt)


# -------------------------
# FILTRO POR FECHA TURNO
# -------------------------
def filtrar_por_fecha(texto, fecha_ini, fecha_fin):
    bloques = re.split(r"\n(?=\d{1,2}/\d{1,2}/\d{4},)", texto)
    resultado = []

    for bloque in bloques:
        match = re.search(r"TURNO\s+(?:DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})", bloque, re.IGNORECASE)
        if match:
            fecha_turno = datetime.strptime(match.group(1), "%d/%m/%Y")

            if fecha_ini <= fecha_turno <= fecha_fin:
                resultado.append(bloque)

    return "\n".join(resultado)


# -------------------------
# FUNCIÓN PRINCIPAL
# -------------------------
def procesar(texto):

    registros = []

    bloques = re.split(r"\n(?=\d{1,2}/\d{1,2}/\d{4},)", texto)

    for bloque in bloques:

        # PROYECTO
        proyecto_match = re.search(r"PROYECTO\s+(.+)", bloque)
        proyecto = proyecto_match.group(1).strip() if proyecto_match else None

        # TURNO Y FECHA
        turno_match = re.search(r"TURNO\s+(DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})", bloque, re.IGNORECASE)

        if not turno_match:
            continue

        turno = turno_match.group(1).upper()
        fecha = turno_match.group(2)

        # SEPARAR POR SONDAS
        sondas = re.split(r"\n(?=SONDA)", bloque)

        for s in sondas:

            if "SONDA" not in s:
                continue

            # SONDA
            sonda_match = re.search(r"SONDA\s+([A-Za-z0-9\-]+)", s)
            sonda = sonda_match.group(1) if sonda_match else None

            # 🟢 POZO (NUEVO CAMPO)
            pozo = None
            pozo_match = re.search(r"(?:ID\s*)?Pozo[:\s]*([A-Za-z0-9\-]+)", s, re.IGNORECASE)
            if pozo_match:
                pozo = pozo_match.group(1)

            # CAMPOS NUMÉRICOS
            def extraer_numero(campo):
                match = re.search(fr"{campo}[:\s]*([\d\.,]+)", s, re.IGNORECASE)
                if match:
                    return float(match.group(1).replace(",", "."))
                return None

            fondo_inicial = extraer_numero("Fondo Inicial")
            fondo_final = extraer_numero("Fondo Final")
            programado = extraer_numero("Programado")
            perforado = extraer_numero("Perforado|Avance")

            # OTROS CAMPOS
            recomendacion = re.search(r"Recomendación[:\s]*(.*)", s)
            recomendacion = recomendacion.group(1).strip() if recomendacion else None

            azimuth = re.search(r"Azimuth[:\s]*(.*)", s)
            azimuth = azimuth.group(1).strip() if azimuth else None

            inclinacion = re.search(r"Inclinación[:\s]*(.*)", s)
            inclinacion = inclinacion.group(1).strip() if inclinacion else None

            diametro = re.search(r"Diámetro[:\s]*(.*)", s)
            diametro = diametro.group(1).strip() if diametro else None

            recuperacion = re.search(r"Recuperación[:\s]*(.*)", s)
            recuperacion = recuperacion.group(1).strip() if recuperacion else None

            observaciones = re.search(r"Observaciones:\s*(.*)", s, re.DOTALL)
            observaciones = observaciones.group(1).strip() if observaciones else None

            registros.append({
                "Fecha": fecha,
                "Proyecto": proyecto,
                "Turno": turno,
                "Sonda": sonda,
                "Pozo": pozo,  # 👈 NUEVO
                "Recomendación": recomendacion,
                "Programado": programado,
                "Fondo Inicial": fondo_inicial,
                "Fondo Final": fondo_final,
                "Perforado": perforado,
                "Azimuth": azimuth,
                "Inclinación": inclinacion,
                "Diámetro": diametro,
                "Recuperación (%)": recuperacion,
                "Observaciones": observaciones
            })

    return pd.DataFrame(registros)