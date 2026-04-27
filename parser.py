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
# FILTRO POR FECHA TURNO
# -------------------------
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
# EXTRAER NÚMERO
# -------------------------
def extraer_numero(texto, campo):
    match = re.search(fr"{campo}[:\s]*([\d\.,]+)", texto, re.IGNORECASE)
    if match:
        valor = match.group(1).replace(",", ".")
        try:
            return float(valor)
        except:
            return None
    return None


# -------------------------
# PROCESAMIENTO PRINCIPAL
# -------------------------
def procesar(texto):

    registros = []

    bloques = re.split(r"\n(?=\d{1,2}/\d{1,2}/\d{4},)", texto)

    for bloque in bloques:

        # PROYECTO
        proyecto_match = re.search(r"PROYECTO\s+(.+)", bloque)
        proyecto = proyecto_match.group(1).strip() if proyecto_match else None

        # TURNO + FECHA
        turno_match = re.search(
            r"TURNO\s+(DIA|NOCHE)\s+(\d{1,2}/\d{1,2}/\d{4})",
            bloque,
            re.IGNORECASE
        )

        if not turno_match:
            continue

        turno = turno_match.group(1).upper()
        fecha = turno_match.group(2)

        # DIVIDIR POR SONDAS
        sondas = re.split(r"\n(?=SONDA)", bloque)

        for s in sondas:

            if "SONDA" not in s:
                continue

            # SONDA
            sonda_match = re.search(r"SONDA\s+([A-Za-z0-9\-]+)", s)
            sonda = sonda_match.group(1) if sonda_match else None

            # 🟢 POZO
            pozo_match = re.search(r"Pozo[:\s]*([A-Za-z0-9\-]+)", s, re.IGNORECASE)
            pozo = pozo_match.group(1) if pozo_match else None

            # NUMÉRICOS
            fondo_inicial = extraer_numero(s, "Fondo Inicial")
            fondo_final = extraer_numero(s, "Fondo Final")
            programado = extraer_numero(s, "Programado")
            perforado = extraer_numero(s, "Perforado|Avance")

            # 🟢 RECOMENDACIÓN (CORREGIDO)
            recomendacion_match = re.search(r"Recomendación[:\s]*(.*)", s)

            if recomendacion_match:
                recomendacion = recomendacion_match.group(1).strip()
                recomendacion = recomendacion.split("\n")[0].strip()

                if recomendacion == "":
                    recomendacion = None
            else:
                recomendacion = None

            # OTROS CAMPOS
            azimuth_match = re.search(r"Azimuth[:\s]*(.*)", s)
            azimuth = azimuth_match.group(1).split("\n")[0].strip() if azimuth_match else None

            inclinacion_match = re.search(r"Inclinación[:\s]*(.*)", s)
            inclinacion = inclinacion_match.group(1).split("\n")[0].strip() if inclinacion_match else None

            diametro_match = re.search(r"Diámetro[:\s]*(.*)", s)
            diametro = diametro_match.group(1).split("\n")[0].strip() if diametro_match else None

            recuperacion_match = re.search(r"Recuperación[:\s]*(.*)", s)
            recuperacion = recuperacion_match.group(1).split("\n")[0].strip() if recuperacion_match else None

            # OBSERVACIONES (puede ser multilínea)
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