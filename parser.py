import re
from datetime import datetime
import pandas as pd


def limpiar_texto(texto):
    if texto is None:
        return ""
    return texto.replace("\u202f", " ")


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


def filtrar_por_fecha(texto, fecha_ini, fecha_fin):
    bloques = re.split(r"\n(?=\d{1,2}/\d{1,2}/\d{4},)", texto)
    resultado = []

    for bloque in bloques:
        match = re.search(
            r"TURNO\s+(?:DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})",
            bloque,
            re.IGNORECASE
        )
        if match:
            fecha_turno = datetime.strptime(match.group(1), "%d/%m/%Y")

            if fecha_ini <= fecha_turno <= fecha_fin:
                resultado.append(bloque)

    return "\n".join(resultado)


# -------------------------
# EXTRAER NÚMEROS
# -------------------------
def extraer_numero(texto, campo):
    match = re.search(fr"{campo}[:\s]*([\d\.,]+)", texto, re.IGNORECASE)

    if match and match.group(1):
        valor = match.group(1).replace(",", ".")
        try:
            return float(valor)
        except:
            return None

    return None


# -------------------------
# EXTRAER TEXTO DE UNA LÍNEA
# -------------------------
def extraer_linea(texto, campo):
    match = re.search(fr"{campo}[:\s]*(.*)", texto)
    if match:
        return match.group(1).split("\n")[0].strip()
    return None


# -------------------------
# PROCESAMIENTO PRINCIPAL
# -------------------------
def procesar(texto):

    registros = []

    bloques = re.split(r"\n(?=\d{1,2}/\d{1,2}/\d{4},)", texto)

    for bloque in bloques:

        proyecto_match = re.search(r"PROYECTO\s+(.+)", bloque)
        proyecto = proyecto_match.group(1).strip() if proyecto_match else None

        turno_match = re.search(
            r"TURNO\s+(DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})",
            bloque,
            re.IGNORECASE
        )

        if not turno_match:
            continue

        turno = turno_match.group(1).upper()
        fecha = turno_match.group(2)

        sondas = re.split(r"\n(?=SONDA)", bloque)

        for s in sondas:

            if "SONDA" not in s:
                continue

            sonda = extraer_linea(s, "SONDA")

            # 🟢 POZO
            pozo = extraer_linea(s, "Pozo")

            # NUMÉRICOS
            fondo_inicial = extraer_numero(s, "Fondo Inicial")
            fondo_final = extraer_numero(s, "Fondo Final")
            programado = extraer_numero(s, "Programado")

            perforado = extraer_numero(s, "Perforado")
            if perforado is None:
                perforado = extraer_numero(s, "Avance")

            # 🟢 RECOMENDACIÓN (SOLUCIÓN CLAVE)
            recomendacion = None
            match_rec = re.search(r"Recomendación[:\s]*(.*)", s)

            if match_rec:
                linea = match_rec.group(1).split("\n")[0].strip()

                # 🚫 si la línea es otro campo → ignorar
                if not re.match(
                    r"(Pozo|Fondo|Programado|Perforado|Azimuth|Inclinación|Diámetro|Recuperación)",
                    linea,
                    re.IGNORECASE
                ):
                    if linea != "":
                        recomendacion = linea

            # CAMPOS SIMPLES
            azimuth = extraer_linea(s, "Azimuth")
            inclinacion = extraer_linea(s, "Inclinación")
            diametro = extraer_linea(s, "Diámetro")
            recuperacion = extraer_linea(s, "Recuperación")

            # OBSERVACIONES
            observaciones_match = re.search(r"Observaciones:\s*(.*)", s, re.DOTALL)
            observaciones = observaciones_match.group(1).strip() if observaciones_match else None

            registros.append({
                "Fecha": fecha,
                "Proyecto": proyecto,
                "Turno": turno,
                "Sonda": sonda,
                "Pozo": pozo,
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