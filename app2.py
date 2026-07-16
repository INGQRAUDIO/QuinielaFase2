import streamlit as st
import streamlit.components.v1 as components
import math
import base64
import os
import json
import requests
import urllib.parse
from collections import defaultdict
from PIL import Image
from datetime import datetime
import pytz

# ── Ícono de pestaña (Iconos/DOCopa.png en el repositorio) ──────────
# Se convierte a un canvas cuadrado con fondo transparente antes de
# pasarlo a Streamlit, para que no se deforme al mostrarse en la pestaña.
def _cargar_icono(ruta, tam=64):
    """Abre la imagen y la centra en un canvas cuadrado transparente."""
    img = Image.open(ruta).convert("RGBA")
    w, h = img.size
    lado = max(w, h)
    canvas = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    offset_x = (lado - w) // 2
    offset_y = (lado - h) // 2
    canvas.paste(img, (offset_x, offset_y), img)
    canvas = canvas.resize((tam, tam), Image.LANCZOS)
    return canvas

_ICON_PATH = os.path.join(os.path.dirname(__file__), "Iconos", "DOCopa.png")
_PAGE_ICON = _cargar_icono(_ICON_PATH) if os.path.exists(_ICON_PATH) else "🏆"


# ─── Supabase ────────────────────────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_data(ttl=0)
def obtener_participantes():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    all_names = []
    limit = 1000
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/Quiniela_Fase2?select=nombre&limit={limit}&offset={offset}"
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            all_names.extend(row["nombre"] for row in batch if row.get("nombre"))
            offset += limit
        except Exception as e:
            st.error(f"Error al conectar con Supabase: {e}")
            return []
    return list(dict.fromkeys(all_names))


def obtener_datos_participante(nombre):
    """Devuelve todas las filas de la tabla Quiniela_Fase2 para un nombre dado."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    all_rows = []
    limit = 1000
    offset = 0
    nombre_limpio = nombre.strip()
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/Quiniela_Fase2?"
            f"select=*&nombre=ilike.{urllib.parse.quote(nombre_limpio)}"
            f"&limit={limit}&offset={offset}"
        )
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            all_rows.extend(batch)
            offset += limit
        except Exception as e:
            st.error(f"Error al obtener datos del participante: {e}")
            return []
    return all_rows


@st.cache_data(ttl=0)
def obtener_todos_los_registros():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/Quiniela_Fase2?select=*&limit={limit}&offset={offset}"
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            all_rows.extend(batch)
            offset += limit
        except Exception as e:
            st.error(f"Error al obtener todos los registros: {e}")
            return []
    return all_rows


def calcular_aciertos_por_participante(rows):
    participantes_rows = defaultdict(list)
    for row in rows:
        nombre = row.get("nombre", "").strip()
        if nombre:
            participantes_rows[nombre].append(row)

    aciertos_dict = {}
    claves_r16_set = set(r16_key_map.values())
    claves_r32_set = set(mapeo_circulo_a_indice.values())
    claves_qf_set  = set(qf_key_map.values())
    claves_sf_set  = set(sf_key_map.values())
    claves_fin_set = set(final_key_map.values())

    for nombre, rows_participante in participantes_rows.items():
        total = 0
        for row in rows_participante:
            celda = (row.get("celda") or "").strip()

            # ── "¿Quién pasa?" (país) ──────────────────────────────────
            # Aplica a las celdas de Octavos ("Quién pasa a Octavos?"),
            # Cuartos ("Quién pasa a Cuartos?"), Semifinales
            # ("Quién pasa a Semifinales?") y Finales ("Quién pasa a Finales?")
            if (celda in claves_r16_set or celda in claves_qf_set
                    or celda in claves_sf_set or celda in claves_fin_set):
                pais_hijo = (row.get("pais") or "").strip()
                pais_madre = resultados_madre_por_celda.get(celda)
                if pais_madre and pais_hijo == pais_madre:
                    total += 1

            # ── Goles Dieciseisavos ─────────────────────────────────────
            # Los equipos de esta ronda ya son fijos (herencia_fija),
            # así que solo se compara el número de goles.
            if celda in claves_r32_set:
                goles_hijo = row.get("goles")
                if goles_hijo is None:
                    goles_hijo = ""
                else:
                    goles_hijo = str(goles_hijo).strip()
                goles_madre = goles_madre_por_celda.get(celda)
                if goles_madre is not None and goles_madre != "":
                    try:
                        if int(goles_hijo) == int(goles_madre):
                            total += 1
                    except (ValueError, TypeError):
                        pass

            # ── Goles Octavos ───────────────────────────────────────────
            # Aquí el equipo de la celda depende de quién ganó Dieciseisavos,
            # así que el acierto solo cuenta si, ADEMÁS de coincidir los
            # goles, el país predicho es realmente el que avanzó según
            # madre_r16_flags (si no, aunque los goles coincidan por
            # casualidad, no se otorga el punto).
            if celda in claves_r16_set:
                goles_hijo = row.get("goles")
                if goles_hijo is None:
                    goles_hijo = ""
                else:
                    goles_hijo = str(goles_hijo).strip()
                goles_madre = goles_madre_por_celda.get(celda)
                if goles_madre is not None and goles_madre != "":
                    pais_real_info = madre_r16_flags.get(celda)
                    pais_real = pais_real_info[1] if pais_real_info else None
                    pais_hijo = (row.get("pais") or "").strip()
                    try:
                        if (pais_real and pais_hijo == pais_real
                                and int(goles_hijo) == int(goles_madre)):
                            total += 1
                    except (ValueError, TypeError):
                        pass

            # ── Goles Cuartos ────────────────────────────────────────────
            # Igual criterio que "Goles Octavos": el equipo de la celda
            # depende de quién ganó Octavos, así que el acierto solo
            # cuenta si, ADEMÁS de coincidir los goles, el país predicho
            # es realmente el que avanzó según madre_qf_flags.
            if celda in claves_qf_set:
                goles_hijo = row.get("goles")
                if goles_hijo is None:
                    goles_hijo = ""
                else:
                    goles_hijo = str(goles_hijo).strip()
                goles_madre = goles_madre_por_celda.get(celda)
                if goles_madre is not None and goles_madre != "":
                    pais_real_info = madre_qf_flags.get(celda)
                    pais_real = pais_real_info[1] if pais_real_info else None
                    pais_hijo = (row.get("pais") or "").strip()
                    try:
                        if (pais_real and pais_hijo == pais_real
                                and int(goles_hijo) == int(goles_madre)):
                            total += 1
                    except (ValueError, TypeError):
                        pass

            # ── Goles Semifinales ────────────────────────────────────────
            # Igual criterio que "Goles Cuartos": el equipo de la celda
            # depende de quién ganó Cuartos, así que el acierto solo
            # cuenta si, ADEMÁS de coincidir los goles, el país predicho
            # es realmente el que avanzó según madre_sf_flags.
            if celda in claves_sf_set:
                goles_hijo = row.get("goles")
                if goles_hijo is None:
                    goles_hijo = ""
                else:
                    goles_hijo = str(goles_hijo).strip()
                goles_madre = goles_madre_por_celda.get(celda)
                if goles_madre is not None and goles_madre != "":
                    pais_real_info = madre_sf_flags.get(celda)
                    pais_real = pais_real_info[1] if pais_real_info else None
                    pais_hijo = (row.get("pais") or "").strip()
                    try:
                        if (pais_real and pais_hijo == pais_real
                                and int(goles_hijo) == int(goles_madre)):
                            total += 1
                    except (ValueError, TypeError):
                        pass

        aciertos_dict[nombre] = total
    return aciertos_dict


# ════════════════════════════════════════════════════════════════════
#  PUNTOS EXTRA DE BONUS
# ════════════════════════════════════════════════════════════════════
# Cada bonus está ligado a un cruce de 2 equipos (tabla BonusCheck).
# Ese cruce puede ocurrir en DOS niveles distintos del bracket, y el
# nivel se DETECTA AUTOMÁTICAMENTE a partir de dónde se enfrentan
# realmente esos 2 equipos entre sí (ver _celdas_bonus_desde_equipos):
#
#   • Nivel "r32" (rivales de Dieciseisavos, ej. Bonus 1: Argelia vs Suiza)
#     Se usan SOLO estas tablas:
#       1) "¿Quién pasa a Octavos?"   → celda de Octavos del cruce (r16_key_map)
#       2) "Goles Dieciseisavos" eq.1 → celda fija de Dieciseisavos (herencia_fija)
#       3) "Goles Dieciseisavos" eq.2 → celda fija de Dieciseisavos (herencia_fija)
#
#   • Nivel "r16" (rivales de Octavos, ej. Bonus 2: Argentina vs Egipto)
#     Se usan SOLO estas tablas:
#       1) "¿Quién pasa a Cuartos?" → celda de Cuartos del cruce (qf_key_map)
#       2) "Goles Octavos" eq.1     → celda de Octavos del eq.1 (r16_key_map)
#       3) "Goles Octavos" eq.2     → celda de Octavos del eq.2 (r16_key_map)
#
# Un participante registrado en ese bonus (tabla BonusCheck) gana
# PUNTOS_POR_ACIERTO_BONUS por cada acierto CORRECTO, de forma
# independiente, en esas 3 predicciones. Si acierta las 3, gana
# 3 × PUNTOS_POR_ACIERTO_BONUS puntos extra.
# Estos puntos se basan en lo que el participante puso ORIGINALMENTE en
# su quiniela (Quiniela_Fase2), no en la selección hecha dentro del
# panel de bonus (esa selección solo sirve para registrar quién participa).
#
# IMPORTANTE: nunca se mezclan tablas de ambos niveles para un mismo
# bonus — cada cruce usa EXCLUSIVAMENTE las 3 tablas de su propio nivel,
# detectado según en qué ronda se enfrentan realmente esos 2 equipos.
# ─────────────────────────────────────────────────────────────────────
PUNTOS_POR_ACIERTO_BONUS = 3


@st.cache_data(ttl=0)
def obtener_registros_bonus():
    """Devuelve todas las filas de la tabla BonusCheck (quién se registró en cada bonus)."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    all_rows = []
    limit = 1000
    offset = 0
    while True:
        url = f"{SUPABASE_URL}/rest/v1/BonusCheck?select=*&limit={limit}&offset={offset}"
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            all_rows.extend(batch)
            offset += limit
        except Exception as e:
            st.error(f"Error al obtener registros de bonus: {e}")
            return []
    return all_rows


def _celdas_bonus_desde_equipos(codigo_eq1, codigo_eq2):
    """A partir de los códigos de bandera de los 2 equipos de un cruce de
    bonus, DETECTA AUTOMÁTICAMENTE en qué ronda se enfrentan entre sí y
    devuelve las celdas correspondientes para calificarlo.

    Devuelve (nivel, celda_eq1, celda_eq2, celda_avance):

      • nivel == "r32"  → son rivales de DIECISEISAVOS (su cruce original
        de grupo es uno contra el otro, ej. Argelia vs Suiza).
          celda_eq1/celda_eq2 → celdas fijas de Dieciseisavos (herencia_fija),
                                 usadas para "Goles Dieciseisavos"
          celda_avance        → celda de Octavos (r16_key_map), usada para
                                 "¿Quién pasa a Octavos?"

      • nivel == "r16"  → son rivales de OCTAVOS (cada uno avanzó por su
        lado desde Dieciseisavos y se enfrentan en Octavos, ej. Argentina
        vs Egipto).
          celda_eq1/celda_eq2 → celdas de Octavos (madre_r16_flags), usadas
                                 para "Goles Octavos"
          celda_avance        → celda de Cuartos (qf_key_map), usada para
                                 "¿Quién pasa a Cuartos?"

      • nivel is None   → no se pudo determinar que esos 2 equipos se
        enfrenten entre sí en ninguno de los dos niveles conocidos.
    """
    # ── Intento 1: ¿son rivales de Dieciseisavos? ──────────────────────
    celda_eq1_r32 = next(
        (c for c, archivo in herencia_fija.items() if archivo == f"{codigo_eq1}.svg"), None
    )
    celda_eq2_r32 = next(
        (c for c, archivo in herencia_fija.items() if archivo == f"{codigo_eq2}.svg"), None
    )
    _index_r32 = {v: k for k, v in mapeo_circulo_a_indice.items()}
    if celda_eq1_r32 in _index_r32 and celda_eq2_r32 in _index_r32:
        idx1, idx2 = _index_r32[celda_eq1_r32], _index_r32[celda_eq2_r32]
        if idx1 // 2 == idx2 // 2:
            celda_r16 = r16_key_map.get(idx1 // 2)
            return "r32", celda_eq1_r32, celda_eq2_r32, celda_r16

    # ── Intento 2: ¿son rivales de Octavos? ─────────────────────────────
    celda_eq1_r16 = next(
        (c for c, (archivo, _p) in madre_r16_flags.items() if archivo == f"{codigo_eq1}.svg"),
        None,
    )
    celda_eq2_r16 = next(
        (c for c, (archivo, _p) in madre_r16_flags.items() if archivo == f"{codigo_eq2}.svg"),
        None,
    )
    _index_r16 = {v: k for k, v in r16_key_map.items()}
    if celda_eq1_r16 in _index_r16 and celda_eq2_r16 in _index_r16:
        idx1, idx2 = _index_r16[celda_eq1_r16], _index_r16[celda_eq2_r16]
        if idx1 // 2 == idx2 // 2:
            celda_qf = qf_key_map.get(idx1 // 2)
            return "r16", celda_eq1_r16, celda_eq2_r16, celda_qf

    return None, None, None, None


def calcular_puntos_bonus_todos(registros_bonus, todos_los_registros):
    """
    Calcula, para TODOS los bonus ya registrados en Supabase (tabla
    BonusCheck), los puntos extra ganados por cada participante inscrito.

    Devuelve:
      puntos_totales      → {nombre: puntos_bonus_acumulados_de_todos_los_bonus}
      detalle_por_persona → {nombre: [ {bonus_number, equipo1, equipo2, puntos}, ... ]}
    """
    # Índice de predicciones originales: (nombre, celda) -> fila
    prediccion = {}
    for row in todos_los_registros:
        nombre = (row.get("nombre") or "").strip()
        celda  = (row.get("celda") or "").strip()
        if nombre and celda:
            prediccion[(nombre, celda)] = row

    # Agrupar los registros de bonus por cruce (bonus_number, equipo1, equipo2)
    bonus_grupos = defaultdict(list)
    for reg in registros_bonus:
        clave = (reg.get("bonus_number"), reg.get("equipo1"), reg.get("equipo2"))
        nombre = (reg.get("nombre") or "").strip()
        if nombre:
            bonus_grupos[clave].append(nombre)

    puntos_totales = defaultdict(int)
    detalle_por_persona = defaultdict(list)

    for (bonus_number, pais1, pais2), nombres in bonus_grupos.items():
        codigo_eq1 = country_to_flag.get(pais1)
        codigo_eq2 = country_to_flag.get(pais2)
        nivel = celda_eq1 = celda_eq2 = celda_avance = None
        if codigo_eq1 and codigo_eq2:
            nivel, celda_eq1, celda_eq2, celda_avance = _celdas_bonus_desde_equipos(codigo_eq1, codigo_eq2)

        # "¿Quién pasa a Octavos/Cuartos?" — solo cuenta si ya hay
        # resultado real cargado en esa celda de avance.
        pais_real_avance = resultados_madre_por_celda.get(celda_avance) if celda_avance else None

        goles_real_eq1 = goles_madre_por_celda.get(celda_eq1) if celda_eq1 else None
        goles_real_eq2 = goles_madre_por_celda.get(celda_eq2) if celda_eq2 else None

        # Solo en nivel "r16" (Goles Octavos) el equipo de la celda depende
        # de quién ganó Dieciseisavos, así que el acierto de goles exige
        # ADEMÁS que el país predicho sea el que realmente llegó ahí
        # (igual criterio que calcular_aciertos_por_participante). En
        # nivel "r32" (Goles Dieciseisavos) el equipo ya es fijo y este
        # requisito extra no aplica.
        pais_real_eq1 = pais_real_eq2 = None
        if nivel == "r16":
            _info_real_eq1 = madre_r16_flags.get(celda_eq1) if celda_eq1 else None
            _info_real_eq2 = madre_r16_flags.get(celda_eq2) if celda_eq2 else None
            pais_real_eq1 = _info_real_eq1[1] if _info_real_eq1 else None
            pais_real_eq2 = _info_real_eq2[1] if _info_real_eq2 else None

        for nombre in nombres:
            puntos = 0

            # 1) ¿Quién pasa a Octavos? (r32) / ¿Quién pasa a Cuartos? (r16)
            if pais_real_avance and celda_avance:
                fila = prediccion.get((nombre, celda_avance))
                if fila and (fila.get("pais") or "").strip() == pais_real_avance:
                    puntos += PUNTOS_POR_ACIERTO_BONUS

            # 2) Goles equipo 1 (Dieciseisavos si r32 / Octavos si r16)
            if goles_real_eq1 is not None and celda_eq1:
                fila = prediccion.get((nombre, celda_eq1))
                if fila:
                    try:
                        goles_ok = int(fila.get("goles")) == int(goles_real_eq1)
                        if nivel == "r16":
                            pais_hijo = (fila.get("pais") or "").strip()
                            goles_ok = goles_ok and bool(pais_real_eq1) and pais_hijo == pais_real_eq1
                        if goles_ok:
                            puntos += PUNTOS_POR_ACIERTO_BONUS
                    except (ValueError, TypeError):
                        pass

            # 3) Goles equipo 2 (Dieciseisavos si r32 / Octavos si r16)
            if goles_real_eq2 is not None and celda_eq2:
                fila = prediccion.get((nombre, celda_eq2))
                if fila:
                    try:
                        goles_ok = int(fila.get("goles")) == int(goles_real_eq2)
                        if nivel == "r16":
                            pais_hijo = (fila.get("pais") or "").strip()
                            goles_ok = goles_ok and bool(pais_real_eq2) and pais_hijo == pais_real_eq2
                        if goles_ok:
                            puntos += PUNTOS_POR_ACIERTO_BONUS
                    except (ValueError, TypeError):
                        pass

            puntos_totales[nombre] += puntos
            detalle_por_persona[nombre].append({
                "bonus_number": bonus_number,
                "equipo1": pais1,
                "equipo2": pais2,
                "puntos": puntos,
            })

    return dict(puntos_totales), dict(detalle_por_persona)


# ════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GEOMÉTRICA DEL BRACKET (compartida por madre e hijas)
# ════════════════════════════════════════════════════════════════════
SIZE = 900
Y_OFFSET = 100
SVG_HEIGHT = SIZE + Y_OFFSET + 80

TEAM_R   = 420
R16_R    = 330
R8_R     = 255
R4_R     = 190
R2_R     = 135
RF_OUT   =  88
RF_IN    =  55
RC       =  28

TEAM_NODE_R = 20
DOT_R       =  5

NUM_TEAMS   = 32
NUM_MATCHES = 16
DEG_STEP    = 360 / NUM_TEAMS
PAIR_STEP   = 360 / NUM_MATCHES
PAIR_OFFSET = DEG_STEP / 2

C = {
    "gold":   "#c8a84b",
    "gold2":  "#a07030",
    "gold3":  "#7a5520",
    "gold4":  "#5a3d10",
    "gold5":  "#3a2508",
    "conn":   "#4a3818",
    "dot":    "#b8922a",
    "glow":   "#d4a843",
}

mapeo_circulo_a_indice = {
    0: "B5", 1: "B1", 2: "B6", 3: "B2",
    4: "B7", 5: "B3", 6: "B8", 7: "B4",
    8: "D1", 9: "D5", 10: "D2", 11: "D6",
    12: "D3", 13: "D7", 14: "D4", 15: "D8",
    16: "C8", 17: "C4", 18: "C7", 19: "C3",
    20: "C6", 21: "C2", 22: "C5", 23: "C1",
    24: "A8", 25: "A4", 26: "A7", 27: "A3",
    28: "A6", 29: "A2", 30: "A5", 31: "A1"
}

r16_key_map = {
    0:  "B9", 1:  "B10", 2:  "B11", 3:  "B12",
    4:  "D9", 5:  "D10", 6:  "D11", 7:  "D12",
    8:  "C12", 9:  "C11", 10: "C10", 11: "C9",
    12: "A12", 13: "A11", 14: "A10", 15: "A9"
}
qf_key_map = {
    0: "B13", 1: "B14", 2: "D13", 3: "D14",
    4: "C14", 5: "C13", 6: "A14", 7: "A13"
}
sf_key_map = {0: "B15", 1: "D15", 2: "C15", 3: "A15"}
final_key_map = {0: "S2", 1: "S1"}
champion_key_map = {0: "W1"}

# ── Resultados reales del torneo (RUEDA MADRE) ──────────────────────
herencia_fija = {
    # Grupo A
    "A1": "de.svg", "A5": "py.svg",
    "A2": "fr.svg", "A6": "se.svg",
    "A3": "za.svg", "A7": "ca.svg",
    "A4": "nl.svg", "A8": "ma.svg",
    # Grupo B
    "B5": "br.svg", "B1": "jp.svg",
    "B6": "ci.svg", "B2": "no.svg",
    "B7": "mx.svg", "B3": "ec.svg",
    "B8": "gb-eng.svg", "B4": "cd.svg",
    # Grupo C
    "C1": "hr.svg", "C5": "pt.svg",
    "C2": "es.svg", "C6": "at.svg",
    "C3": "us.svg", "C7": "ba.svg",
    "C4": "be.svg", "C8": "sn.svg",
    # Grupo D
    "D1": "ar.svg", "D5": "cv.svg",
    "D2": "au.svg", "D6": "eg.svg",
    "D3": "ch.svg", "D7": "dz.svg",
    "D4": "gh.svg", "D8": "co.svg"
}

madre_r16_flags = {
    "B9": ("br.svg", "Brasil"),
    "A11": ("ca.svg", "Canadá"),
    "A12": ("ma.svg", "Marruecos"),
    "A9": ("py.svg", "Paraguay"),
    "B10": ("no.svg", "Noruega"),
    "A10": ("fr.svg", "Francia"),
    "B11": ("mx.svg", "México"),
    "B12": ("gb-eng.svg", "Inglaterra"),
    "C12": ("be.svg", "Bélgica"),
    "C11": ("us.svg", "Estados Unidos"),
    "C10": ("es.svg", "España"),
    "C9": ("pt.svg", "Portugal"),
    "D11": ("ch.svg", "Suiza"),
    "D10": ("eg.svg", "Egipto"),
    "D9": ("ar.svg", "Argentina"),
    "D12": ("co.svg", "Colombia")
}
madre_qf_flags = {
    "A13": ("fr.svg", "Francia"),
    "A14": ("ma.svg", "Marruecos"),
    "B13": ("no.svg", "Noruega"),
    "B14": ("gb-eng.svg", "Inglaterra"),
    "C13": ("es.svg", "España"),
    "C14": ("be.svg", "Bélgica"),
    "D13": ("ar.svg", "Argentina"),
    "D14": ("ch.svg", "Suiza")
}
madre_sf_flags = {
    "A15": ("fr.svg", "Francia"),
    "B15": ("gb-eng.svg", "Inglaterra"),
    "C15": ("es.svg", "España"),
    "D15": ("ar.svg", "Argentina")
}
madre_final_flags = {
    "S1": ("es.svg", "España"),
    "S2": ("ar.svg", "Argentina")
}
madre_champion_flags = {}

# ── Goles de la rueda madre ─────────────────────────────────────────
goles_madre_r32 = {
    "A3": 0, "A7": 1,
    "B5": 2, "B1": 1,
    "A1": 4, "A5": 5,
    "A4": 3, "A8": 4,
    "B6": 1, "B2": 2,
    "A2": 3, "A6": 0,
    "B7": 2, "B3": 0,
    "B8": 2, "B4": 1,
    "C4": 3, "C8": 2,
    "C3": 2, "C7": 0,
    "C2": 3, "C6": 0,
    "C1": 1, "C5": 2,
    "D3": 2, "D7": 0,
    "D2": 3, "D6": 5,
    "D1": 3, "D5": 2,
    "D4": 0, "D8": 1,
}
goles_madre_r16 = {
    
    "A11": 0, "A12": 3,
    "A9": 0, "A10": 1,
    "B9": 1, "B10": 2, 
    "B11": 2, "B12": 3,
    "C9": 0, "C10": 1,
    "C11": 1, "C12": 4,
    "D9": 3, "D10": 2,
    "D11": 4, "D12": 3
}
goles_madre_qf = {
    "A13": 2, "A14": 0,
    "B13": 1, "B14": 2,
    "C13": 2, "C14": 1,
    "D13": 3, "D14": 1
}
goles_madre_sf = {
    "A15": 0, "C15": 2,
    "B15": 1, "D15": 2
}
goles_madre_final = {
    #"S1": 2, "S2": 1
}
goles_madre_champion = {}

def _construir_goles_madre():
    goles = {}
    for ronda_dict in (
        goles_madre_r32, goles_madre_r16, goles_madre_qf,
        goles_madre_sf, goles_madre_final, goles_madre_champion,
    ):
        for clave, valor in ronda_dict.items():
            goles[clave] = valor
    return goles

goles_madre_por_celda = _construir_goles_madre()

flag_to_country = {
    "de": "Alemania", "py": "Paraguay",
    "fr": "Francia", "se": "Suecia",
    "za": "Sudáfrica", "ca": "Canadá",
    "nl": "Países Bajos", "ma": "Marruecos",
    "br": "Brasil", "jp": "Japón",
    "ci": "Costa de Marfil", "no": "Noruega",
    "mx": "México", "ec": "Ecuador",
    "gb-eng": "Inglaterra", "cd": "RD Congo",
    "hr": "Croacia", "pt": "Portugal",
    "es": "España", "at": "Austria",
    "us": "Estados Unidos", "ba": "Bosnia y Herzegovina",
    "be": "Bélgica", "sn": "Senegal",
    "ar": "Argentina", "cv": "Cabo Verde",
    "au": "Australia", "eg": "Egipto",
    "ch": "Suiza", "dz": "Argelia",
    "gh": "Ghana", "co": "Colombia"
}
country_to_flag = {v: k for k, v in flag_to_country.items()}

def _construir_resultados_madre():
    resultados = {}
    for celda, archivo in herencia_fija.items():
        codigo = archivo.replace(".svg", "")
        pais = flag_to_country.get(codigo)
        if pais:
            resultados[celda] = pais
    for ronda_dict in (
        madre_r16_flags, madre_qf_flags, madre_sf_flags,
        madre_final_flags, madre_champion_flags,
    ):
        for clave, (archivo, pais) in ronda_dict.items():
            resultados[clave] = pais
    return resultados

resultados_madre_por_celda = _construir_resultados_madre()


@st.cache_data(ttl=3600)
def _fetch_trophy_b64():
    """Descarga la imagen del trofeo FIFA y la devuelve en base64.
    Se cachea 1 hora para no hacer requests repetidos en cada re-render."""
    url = "https://static.wikia.nocookie.net/logopedia/images/9/90/FIFA_World_Cup_trophy.png/revision/latest?cb=20260701115015"
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        b64 = base64.b64encode(resp.content).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def d2r(deg): return deg * math.pi / 180


def construir_bracket_html(
    team_flags, r16_flags, qf_flags, sf_flags, final_flags, champion_flags,
    titulo="COPA DEL MUNDO 2026",
    resultados_madre=None,
    solo_madre=False,
    goles_madre=None,
):
    CX = SIZE // 2
    CY = (SIZE // 2) + Y_OFFSET

    def pt(r, deg):
        a = d2r(deg - 90)
        return CX + r * math.cos(a), CY + r * math.sin(a)

    bg_els, conn_els, node_els = [], [], []

    def line(x1, y1, x2, y2, col="#7a6030", w=1.3):
        conn_els.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{col}" stroke-width="{w}"/>'
        )

    def arc(r, a0, a1, col="#7a6030", w=1.3):
        if abs(a1 - a0) < 0.01: return
        lf = 1 if abs(a1 - a0) > 180 else 0
        sw = 1 if (a1 - a0) > 0 else 0
        x0, y0 = pt(r, a0)
        x1, y1 = pt(r, a1)
        conn_els.append(
            f'<path d="M{x0:.2f},{y0:.2f} A{r},{r} 0 {lf},{sw} {x1:.2f},{y1:.2f}" '
            f'fill="none" stroke="{col}" stroke-width="{w}"/>'
        )

    def circle_ring(x, y, r, fill="#111", stroke="#c8a84b", sw=2.0, cls="", data_attrs=""):
        node_els.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" class="{cls}" {data_attrs}/>'
        )

    def dot(x, y, r=DOT_R, fill="#b8972a"):
        node_els.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}"/>')

    goles_madre = goles_madre or {}

    def gol_label(x, y, valor):
        if valor is None or valor == "":
            return
        node_els.append(
            f'<text x="{x:.2f}" y="{(y + 3):.2f}" text-anchor="middle" '
            f'fill="#0a0a0a" font-size="9" font-family="monospace" font-weight="bold" '
            f'paint-order="stroke" stroke="#f0d060" stroke-width="2.2" '
            f'style="pointer-events:none;">{valor}</text>'
        )

    bg_els.append('''
    <defs>
      <filter id="grayscale_filter">
        <feColorMatrix type="saturate" values="0"/>
        <feComponentTransfer>
          <feFuncR type="linear" slope="0.55" intercept="0.05"/>
          <feFuncG type="linear" slope="0.55" intercept="0.05"/>
          <feFuncB type="linear" slope="0.55" intercept="0.05"/>
        </feComponentTransfer>
      </filter>
    </defs>
    ''')

    GLOBAL_ROT = DEG_STEP / 2
    team_angles = [GLOBAL_ROT + k * DEG_STEP for k in range(NUM_TEAMS)]

    country_names = []
    flags_dict = {}
    for idx, celda in mapeo_circulo_a_indice.items():
        celda_visible = (not solo_madre) or (resultados_madre and celda in resultados_madre)
        archivo = team_flags.get(celda) if celda_visible else None
        flags_dict[idx] = f"Banderas/{archivo}" if archivo else None
        codigo = archivo.replace(".svg", "") if archivo else None
        country_names.append(flag_to_country.get(codigo, "Por definir"))

    equipos_eliminados = set()

    loaded_flags = []
    diameter = TEAM_NODE_R * 2
    for idx, path in flags_dict.items():
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                b64_data = f"data:image/svg+xml;base64,{b64}"
                bg_els.append(f'''
                <defs>
                  <pattern id="flag_{idx}" width="1" height="1" viewBox="0 0 {diameter} {diameter}">
                    <image href="{b64_data}" x="0" y="0" width="{diameter}" height="{diameter}" preserveAspectRatio="none"/>
                  </pattern>
                </defs>
                ''')
                loaded_flags.append(idx)

    def cargar_ronda(key_map, flags_map, node_radius, prefix):
        loaded, names = {}, {}
        diam = node_radius * 2
        for idx_nodo, clave in key_map.items():
            if clave not in flags_map:
                continue
            if solo_madre and not (resultados_madre and clave in resultados_madre):
                continue
            archivo, nombre_pais = flags_map[clave]
            ruta = f"Banderas/{archivo}"
            if os.path.exists(ruta):
                with open(ruta, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    b64_data = f"data:image/svg+xml;base64,{b64}"
                    bg_els.append(f'''
                    <defs>
                      <pattern id="flag_{prefix}_{idx_nodo}" width="1" height="1" viewBox="0 0 {diam} {diam}">
                        <image href="{b64_data}" x="0" y="0" width="{diam}" height="{diam}" preserveAspectRatio="none"/>
                      </pattern>
                    </defs>
                    ''')
                    loaded[idx_nodo] = True
                    names[idx_nodo] = nombre_pais
        return loaded, names

    R16_NODE_R   = DOT_R + 14
    QF_NODE_R    = DOT_R + 14
    SF_NODE_R    = DOT_R + 16
    FINAL_NODE_R = DOT_R + 19
    CHAMP_NODE_R = RC

    r16_loaded, r16_names   = cargar_ronda(r16_key_map, r16_flags, R16_NODE_R, "r16")
    qf_loaded, qf_names     = cargar_ronda(qf_key_map, qf_flags, QF_NODE_R, "qf")
    sf_loaded, sf_names     = cargar_ronda(sf_key_map, sf_flags, SF_NODE_R, "sf")
    final_loaded, final_names = cargar_ronda(final_key_map, final_flags, FINAL_NODE_R, "final")
    champion_loaded, champion_names = cargar_ronda(champion_key_map, champion_flags, CHAMP_NODE_R, "champion")

    def calcular_aciertos(key_map_ronda, flags_ronda, es_team_flags=False):
        resultado = {}
        if not resultados_madre:
            return resultado
        for idx_nodo, clave in key_map_ronda.items():
            if es_team_flags:
                archivo_hijo = flags_ronda.get(clave)
                pais_hijo = flag_to_country.get(
                    archivo_hijo.replace(".svg", "")
                ) if archivo_hijo else None
            else:
                entrada = flags_ronda.get(clave)
                pais_hijo = entrada[1] if entrada else None

            pais_madre = resultados_madre.get(clave)
            if pais_hijo is None or pais_madre is None:
                continue
            if pais_hijo == pais_madre:
                resultado[idx_nodo] = "#3ddc6e"
            else:
                resultado[idx_nodo] = "#e0473e"
        return resultado

    aciertos_r16_stroke  = calcular_aciertos(r16_key_map, r16_flags)
    aciertos_qf_stroke   = calcular_aciertos(qf_key_map, qf_flags)
    aciertos_sf_stroke   = calcular_aciertos(sf_key_map, sf_flags)
    aciertos_final_stroke = calcular_aciertos(final_key_map, final_flags)

    anchors_r16, anchors_qf, anchors_sf = [], [], []

    for i in range(NUM_MATCHES):
        ang_a = team_angles[i * 2]
        ang_b = team_angles[i * 2 + 1]
        pair_ang = (ang_a + ang_b) / 2

        xa, ya = pt(TEAM_R, ang_a)
        xb, yb = pt(TEAM_R, ang_b)
        xn, yn = pt(R16_R, pair_ang)

        R_meet = R16_R + (TEAM_R - R16_R) * 0.38
        xma, yma = pt(R_meet, ang_a)
        xmb, ymb = pt(R_meet, ang_b)
        xmc, ymc = pt(R_meet, pair_ang)

        line(xa, ya, xma, yma, col=C["gold2"], w=1.3)
        line(xb, yb, xmb, ymb, col=C["gold2"], w=1.3)
        line(xma, yma, xmb, ymb, col=C["gold2"], w=1.3)
        line(xmc, ymc, xn, yn, col=C["gold3"], w=1.2)

        team_a_idx, team_b_idx = i * 2, i * 2 + 1
        fill_a = f"url(#flag_{team_a_idx})" if team_a_idx in loaded_flags else "#111"
        fill_b = f"url(#flag_{team_b_idx})" if team_b_idx in loaded_flags else "#111"

        stroke_a, sw_a = C["gold"], 2.0
        stroke_b, sw_b = C["gold"], 2.0

        filtro_a = ''
        filtro_b = ''

        circle_ring(xa, ya, TEAM_NODE_R, fill=fill_a, stroke=stroke_a, sw=sw_a, cls="team-node", data_attrs=filtro_a)
        circle_ring(xb, yb, TEAM_NODE_R, fill=fill_b, stroke=stroke_b, sw=sw_b, cls="team-node", data_attrs=filtro_b)

        celda_a = mapeo_circulo_a_indice.get(team_a_idx)
        celda_b = mapeo_circulo_a_indice.get(team_b_idx)
        gol_label(xa, ya, goles_madre.get(celda_a))
        gol_label(xb, yb, goles_madre.get(celda_b))

        if i in r16_loaded:
            stroke_r16 = aciertos_r16_stroke.get(i, C["gold"])
            sw_r16 = 3.0 if i in aciertos_r16_stroke else 2.0
            circle_ring(xn, yn, R16_NODE_R, fill=f"url(#flag_r16_{i})",
                        stroke=stroke_r16, sw=sw_r16, cls="r16-node",
                        data_attrs=f'data-node-idx="{i}"')
            gol_label(xn, yn, goles_madre.get(r16_key_map.get(i)))
        else:
            dot(xn, yn, DOT_R, fill=C["dot"])

        anchors_r16.append((xn, yn, pair_ang))

    # ── R16 → QF ──
    for i in range(8):
        x0, y0, a0 = anchors_r16[i * 2]
        x1, y1, a1 = anchors_r16[i * 2 + 1]
        match_ang = (a0 + a1) / 2
        xn, yn = pt(R8_R, match_ang)

        aa, ab = min(a0, a1), max(a0, a1)
        arc(R16_R, aa, ab, col=C["gold3"], w=1.2)

        R_mid = R8_R + (R16_R - R8_R) * 0.45
        xma, yma = pt(R_mid, a0)
        xmb, ymb = pt(R_mid, a1)
        xmc, ymc = pt(R_mid, match_ang)

        line(x0, y0, xma, yma, col=C["gold3"], w=1.1)
        line(x1, y1, xmb, ymb, col=C["gold3"], w=1.1)
        line(xma, yma, xmb, ymb, col=C["gold3"], w=1.1)
        line(xmc, ymc, xn, yn,   col=C["gold4"], w=1.1)

        if i in qf_loaded:
            stroke_qf = aciertos_qf_stroke.get(i, C["gold"])
            sw_qf = 3.0 if i in aciertos_qf_stroke else 2.0
            circle_ring(xn, yn, QF_NODE_R, fill=f"url(#flag_qf_{i})",
                        stroke=stroke_qf, sw=sw_qf, cls="qf-node",
                        data_attrs=f'data-node-idx="{i}"')
            gol_label(xn, yn, goles_madre.get(qf_key_map.get(i)))
        else:
            dot(xn, yn, DOT_R, fill=C["dot"])

        anchors_qf.append((xn, yn, match_ang))

    # ── QF → SF ──
    for i in range(4):
        x0, y0, a0 = anchors_qf[i * 2]
        x1, y1, a1 = anchors_qf[i * 2 + 1]
        match_ang = (a0 + a1) / 2
        xn, yn = pt(R4_R, match_ang)

        aa, ab = min(a0, a1), max(a0, a1)
        arc(R8_R, aa, ab, col=C["gold4"], w=1.1)

        R_mid = R4_R + (R8_R - R4_R) * 0.45
        xma, yma = pt(R_mid, a0)
        xmb, ymb = pt(R_mid, a1)
        xmc, ymc = pt(R_mid, match_ang)

        line(x0, y0, xma, yma, col=C["gold4"], w=1.0)
        line(x1, y1, xmb, ymb, col=C["gold4"], w=1.0)
        line(xma, yma, xmb, ymb, col=C["gold4"], w=1.0)
        line(xmc, ymc, xn, yn,   col=C["gold5"], w=1.0)

        if i in sf_loaded:
            stroke_sf = aciertos_sf_stroke.get(i, C["gold"])
            sw_sf = 3.0 if i in aciertos_sf_stroke else 2.0
            circle_ring(xn, yn, SF_NODE_R, fill=f"url(#flag_sf_{i})",
                        stroke=stroke_sf, sw=sw_sf, cls="sf-node",
                        data_attrs=f'data-node-idx="{i}"')
            gol_label(xn, yn, goles_madre.get(sf_key_map.get(i)))
        else:
            dot(xn, yn, DOT_R, fill=C["dot"])

        anchors_sf.append((xn, yn, match_ang))

    # ── SF → Final ──
    anchors_final = []
    for i in range(2):
        x0, y0, a0 = anchors_sf[i * 2]
        x1, y1, a1 = anchors_sf[i * 2 + 1]
        match_ang = (a0 + a1) / 2
        xn, yn = pt(R2_R, match_ang)

        aa, ab = min(a0, a1), max(a0, a1)
        arc(R4_R, aa, ab, col=C["gold5"], w=1.0)

        R_mid = R2_R + (R4_R - R2_R) * 0.45
        xma, yma = pt(R_mid, a0)
        xmb, ymb = pt(R_mid, a1)
        xmc, ymc = pt(R_mid, match_ang)

        line(x0, y0, xma, yma, col=C["gold5"], w=1.0)
        line(x1, y1, xmb, ymb, col=C["gold5"], w=1.0)
        line(xma, yma, xmb, ymb, col=C["gold5"], w=1.0)
        line(xmc, ymc, xn, yn,   col=C["gold"],  w=1.0)

        if i in final_loaded:
            stroke_final = aciertos_final_stroke.get(i, C["gold"])
            sw_final = 3.2 if i in aciertos_final_stroke else 2.2
            circle_ring(xn, yn, FINAL_NODE_R, fill=f"url(#flag_final_{i})",
                        stroke=stroke_final, sw=sw_final, cls="final-node",
                        data_attrs=f'data-node-idx="{i}"')
            gol_label(xn, yn, goles_madre.get(final_key_map.get(i)))
        else:
            dot(xn, yn, DOT_R + 1, fill=C["dot"])

        anchors_final.append((xn, yn, match_ang))

    # ── Final → Campeón ──
    for r_ring, col, w in [(RF_OUT, C["gold"], 1.5), (RF_IN, C["gold"], 1.2)]:
        conn_els.append(
            f'<circle cx="{CX}" cy="{CY}" r="{r_ring}" '
            f'fill="none" stroke="{col}" stroke-width="{w}"/>'
        )

    for xf, yf, af in anchors_final:
        xo, yo = pt(RF_OUT, af)
        xi, yi = pt(RF_IN,  af)
        line(xf, yf, xo, yo, col=C["gold"],  w=1.2)
        line(xo, yo, xi, yi, col=C["gold"],  w=1.2)
        line(xi, yi, CX, CY, col=C["gold"],  w=1.0)

    bg_els.append(f"""
    <defs>
      <radialGradient id="glow_grad" cx="50%" cy="50%" r="50%">
        <stop offset="0%"   stop-color="#d4a843" stop-opacity="0.55"/>
        <stop offset="45%"  stop-color="#8a6020" stop-opacity="0.20"/>
        <stop offset="100%" stop-color="#0a0a0a" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <circle cx="{CX}" cy="{CY}" r="260" fill="url(#glow_grad)"/>
    """)

    node_els.append(f"""
    <defs>
      <clipPath id="champ_clip">
        <circle cx="{CX}" cy="{CY}" r="{RC + 22}"/>
      </clipPath>
    </defs>
    """)

    if 0 in champion_loaded:
        # Si hay bandera de campeón definida, la mostramos en el círculo central
        node_els.append(
            f'<circle cx="{CX}" cy="{CY}" r="{CHAMP_NODE_R}" '
            f'fill="url(#flag_champion_0)" stroke="{C["glow"]}" stroke-width="2.5" '
            f'class="champion-node" data-node-idx="0"/>'
        )
        gol_label(CX, CY, goles_madre.get(champion_key_map.get(0)))
    else:
        # Sin campeón definido: mostramos la imagen real del trofeo FIFA.
        # La descargamos en tiempo de ejecución y la embebemos en base64 para
        # evitar bloqueos CORS cuando el SVG se renderiza dentro del iframe de
        # components.html.
        trophy_size = (RC + 22) * 2
        trophy_x   = CX - (RC + 22)
        trophy_y   = CY - (RC + 22)

        try:
            trophy_href = _fetch_trophy_b64()
        except Exception:
            trophy_href = None

        if trophy_href:
            node_els.append(
                f'<image href="{trophy_href}" '
                f'x="{trophy_x:.1f}" y="{trophy_y:.1f}" '
                f'width="{trophy_size}" height="{trophy_size}" '
                f'clip-path="url(#champ_clip)" '
                f'preserveAspectRatio="xMidYMid meet"/>'
            )
        else:
            node_els.append(
                f'<text x="{CX}" y="{CY + 9}" text-anchor="middle" '
                f'font-size="26" font-family="serif">🏆</text>'
            )

    node_els.append(
        f'<text x="{CX}" y="26" text-anchor="middle" fill="{C["gold"]}" '
        f'font-size="24" font-family="serif" letter-spacing="5">{titulo}</text>'
    )

    for r_l, txt, col in [
        (R16_R,  "R32",   C["gold3"]),
        (R8_R,   "R16",   C["gold3"]),
        (R4_R,   "QF",    C["gold3"]),
        (R2_R,   "SF",    C["gold3"]),
        (RF_OUT, "Final", C["gold"]),
    ]:
        xl = CX - r_l - 6
        node_els.append(
            f'<text x="{xl:.1f}" y="{CY + 4}" text-anchor="end" '
            f'fill="{col}" font-size="8" font-family="monospace" opacity="0.6">{txt}</text>'
        )

    svg_body = "\n".join(bg_els) + "\n" + "\n".join(conn_els) + "\n" + "\n".join(node_els)

    country_names_json = json.dumps(country_names, ensure_ascii=False)
    r16_names_json = json.dumps({str(k): v for k, v in r16_names.items()}, ensure_ascii=False)
    qf_names_json = json.dumps({str(k): v for k, v in qf_names.items()}, ensure_ascii=False)
    sf_names_json = json.dumps({str(k): v for k, v in sf_names.items()}, ensure_ascii=False)
    final_names_json = json.dumps({str(k): v for k, v in final_names.items()}, ensure_ascii=False)
    champion_names_json = json.dumps({str(k): v for k, v in champion_names.items()}, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: #0a0a0a;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding-top: 50px;
    overflow-y: hidden;
  }}
  .team-node, .r16-node, .qf-node, .sf-node, .final-node, .champion-node {{
    cursor:pointer;
    transition: stroke-width .15s, stroke .15s;
  }}
  .team-node:hover, .r16-node:hover, .qf-node:hover, .sf-node:hover, .final-node:hover {{
    stroke:#f0d060 !important;
    stroke-width:3.5 !important;
  }}
  .champion-node:hover {{
    stroke:#f0e090 !important;
    stroke-width:4 !important;
  }}
  #tip {{
    position:fixed;
    background:rgba(20,12,0,.93);
    border:1px solid #b8972a;
    color:#e8d080;
    font:12px monospace;
    padding:5px 10px;
    border-radius:6px;
    pointer-events:none;
    display:none;
    z-index:99;
  }}
</style>
</head>
<body>
<div id="tip"></div>
<svg width="{SIZE}" height="{SVG_HEIGHT}" viewBox="0 0 {SIZE} {SVG_HEIGHT}"
     xmlns="http://www.w3.org/2000/svg" style="will-change: transform; contain: paint;">
  <rect width="{SIZE}" height="{SVG_HEIGHT}" fill="#0a0a0a"/>
  {svg_body}
</svg>
<script>
const tip = document.getElementById('tip');
let countryNames = {country_names_json};
let r16Names = {r16_names_json};
let qfNames = {qf_names_json};
let sfNames = {sf_names_json};
let finalNames = {final_names_json};
let championNames = {champion_names_json};

function wireTooltip(selector, namesObj, byIndexAttr) {{
  document.querySelectorAll(selector).forEach((el, i) => {{
    const key = byIndexAttr ? el.getAttribute('data-node-idx') : i;
    el.addEventListener('mouseenter', e => {{
      tip.style.display = 'block';
      tip.textContent = namesObj[key] || 'Por definir';
    }});
    el.addEventListener('mousemove', e => {{
      tip.style.left = (e.clientX + 14) + 'px';
      tip.style.top  = (e.clientY - 6) + 'px';
    }});
    el.addEventListener('mouseleave', () => tip.style.display = 'none');
  }});
}}

wireTooltip('.team-node', countryNames, false);
wireTooltip('.r16-node', r16Names, true);
wireTooltip('.qf-node', qfNames, true);
wireTooltip('.sf-node', sfNames, true);
wireTooltip('.final-node', finalNames, true);
wireTooltip('.champion-node', championNames, true);
</script>
</body>
</html>"""

    return html


# ════════════════════════════════════════════════════════════════════
#  FUNCIÓN REUTILIZABLE: tabla de resultados con el diseño estándar
# ════════════════════════════════════════════════════════════════════

def construir_tabla_acordeon_html(titulo, subtitulo, tabla_bloque, ocultar_columnas=None):
    """Igual que construir_tabla_detalle_html pero con toggle de acordeón.
    La tabla arranca colapsada; al hacer clic en el título se expande/colapsa."""
    ocultar_columnas = ocultar_columnas or []
    ocultar_css = "\n".join(
        f"      th.{clase}, td.{clase} {{ display: none !important; }}"
        for clase in ocultar_columnas
    )
    return f"""<!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{
        background: #0a0a0a;
        font-family: 'Georgia', serif;
        display: flex;
        justify-content: center;
        padding: 10px 20px 20px 20px;
      }}
      .page-wrap {{
        position: relative;
        width: 100%;
        max-width: 760px;
      }}
      /* ── Cabecera acordeón ── */
      .acordeon-header {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        cursor: pointer;
        user-select: none;
        padding: 14px 20px;
        background: linear-gradient(180deg, #1a1508 0%, #110d04 100%);
        border: 1px solid #3a2e10;
        border-radius: 10px;
        transition: border-color 0.2s;
      }}
      .acordeon-header:hover {{ border-color: #c8a84b; }}
      .acordeon-header h2 {{
        text-align: center;
        color: #d4a843;
        font-family: 'Georgia', serif;
        font-weight: normal;
        letter-spacing: 4px;
        font-size: 16px;
        text-transform: uppercase;
        margin: 0;
      }}
      .acordeon-arrow {{
        color: #7a6535;
        font-size: 14px;
        transition: transform 0.25s;
        flex-shrink: 0;
      }}
      .acordeon-arrow.open {{ transform: rotate(180deg); }}
      /* ── Contenido colapsable ── */
      .acordeon-body {{
        overflow: hidden;
        max-height: 0;
        transition: max-height 0.35s ease;
      }}
      .acordeon-body.open {{ max-height: 9999px; }}
      .subtitle {{
        text-align: center;
        color: #7a6535;
        font-family: monospace;
        font-size: 10px;
        letter-spacing: 2px;
        margin: 10px 0 14px 0;
        text-transform: uppercase;
      }}
      .divider {{
        width: 100px;
        height: 1px;
        background: linear-gradient(90deg, transparent, #c8a84b, transparent);
        margin: 0 auto 18px auto;
      }}
      /* ── Tabla ── */
      .quiniela-table {{
        width: 100%;
        border-collapse: collapse;
        background: rgba(20,15,5,.5);
        border: 1px solid #3a2e10;
        border-radius: 10px;
        overflow: hidden;
      }}
      .quiniela-table thead th {{
        background: linear-gradient(180deg, #1a1508, #110d04);
        color: #e8d080;
        font-family: monospace;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 14px 10px;
        border-bottom: 1px solid #c8a84b;
        text-align: center;
        font-weight: normal;
      }}
      .quiniela-row td {{
        padding: 11px 10px;
        text-align: center;
        color: #d8cba8;
        font-family: monospace;
        font-size: 13px;
        border-bottom: 1px solid #221a0a;
        transition: background .15s;
      }}
      .quiniela-row:hover td {{ background: rgba(200,168,75,.08); color: #f0d060; }}
      .quiniela-row:last-child td {{ border-bottom: none; }}
      .quiniela-footer td {{
        padding: 10px;
        font-family: monospace;
        font-size: 12px;
        background: linear-gradient(180deg, #1a1508, #110d04);
        border-top: 1px solid #c8a84b;
      }}
      .footer-label {{ color: #7a6535; text-align: right !important; letter-spacing: 1px; }}
      .footer-valor  {{ color: #d4a843; font-weight: bold; font-size: 14px; }}
      .col-num       {{ color: #7a6535; width: 6%; }}
      .col-celda     {{ width: 12%; }}
      .col-pais      {{ width: 38%; text-align: left !important; padding-left: 18px !important; }}
      .col-goles     {{ color: #c8a84b; font-weight: bold; width: 12%; }}
      .col-goles-madre {{ color: #d4a843; width: 12%; }}
      .col-comparacion {{ width: 18%; }}
      .col-estado    {{ width: 18%; }}
      .madre-ref     {{ color: #6a5528; font-size: 11px; }}
      .badge-ok      {{ color:#3ddc6e; border:1px solid #2a8a4a; background:rgba(61,220,110,.08); border-radius:6px; padding:2px 8px; font-size:11px; }}
      .badge-fail    {{ color:#e0473e; border:1px solid #8a2a24; background:rgba(224,71,62,.08);  border-radius:6px; padding:2px 8px; font-size:11px; }}
      .empty-state   {{ text-align:center; color:#7a6535; font-family:monospace; font-size:13px; padding:50px 20px; border:1px dashed #3a2e10; border-radius:10px; }}
      {ocultar_css}
    </style>
    </head>
    <body>
      <div class="page-wrap">
        <div class="acordeon-header" onclick="toggleAcordeon()">
          <span class="acordeon-arrow" id="arrow">▼</span>
          <h2>{titulo}</h2>
          <span class="acordeon-arrow" id="arrow2">▼</span>
        </div>
        <div class="acordeon-body" id="body">
          <div class="subtitle" style="margin-top:14px;">{subtitulo}</div>
          <div class="divider"></div>
          {tabla_bloque}
        </div>
      </div>
      <script>
        function toggleAcordeon() {{
          const body  = document.getElementById('body');
          const arr1  = document.getElementById('arrow');
          const arr2  = document.getElementById('arrow2');
          const open  = body.classList.toggle('open');
          arr1.classList.toggle('open', open);
          arr2.classList.toggle('open', open);
        }}
      </script>
    </body>
    </html>"""


def construir_tabla_detalle_html(titulo, subtitulo, tabla_bloque, ocultar_columnas=None):
    ocultar_columnas = ocultar_columnas or []
    ocultar_css = "\n".join(
        f"      th.{clase}, td.{clase} {{ display: none !important; }}"
        for clase in ocultar_columnas
    )
    return f"""<!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{
        background: #0a0a0a;
        font-family: 'Georgia', serif;
        display: flex;
        justify-content: center;
        padding: 10px 20px 50px 20px;
      }}
      .page-wrap {{
        position: relative;
        width: 100%;
        max-width: 760px;
      }}
      h2.title {{
        text-align: center;
        color: #d4a843;
        font-family: 'Georgia', serif;
        font-weight: normal;
        letter-spacing: 4px;
        font-size: 18px;
        margin: 0 0 4px 0;
        text-transform: uppercase;
      }}
      .subtitle {{
        text-align: center;
        color: #7a6535;
        font-family: monospace;
        font-size: 10px;
        letter-spacing: 2px;
        margin-bottom: 22px;
        text-transform: uppercase;
      }}
      .divider {{
        width: 100px;
        height: 1px;
        background: linear-gradient(90deg, transparent, #c8a84b, transparent);
        margin: 0 auto 26px auto;
      }}
      .table-scroll {{
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        width: 100%;
        border-radius: 10px;
      }}
      .quiniela-table {{
        table-layout: fixed;   /* el ancho total = suma de los anchos de columna de abajo, nada más que ajustar aquí */
        margin: 0 auto;
        border-collapse: collapse;
        background: rgba(20, 15, 5, 0.5);
        border: 1px solid #3a2e10;
        border-radius: 10px;
        overflow: hidden;
      }}
      .quiniela-table thead th {{
        background: linear-gradient(180deg, #1a1508, #110d04);
        color: #e8d080;
        font-family: monospace;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 14px 10px;
        border-bottom: 1px solid #c8a84b;
        text-align: center;
        font-weight: normal;
        white-space: nowrap;
      }}
      .quiniela-row td {{
        padding: 11px 10px;
        text-align: center;
        color: #d8cba8;
        font-family: monospace;
        font-size: 13px;
        border-bottom: 1px solid #221a0a;
        transition: background 0.15s;
        white-space: nowrap;
      }}
      .quiniela-row:hover td {{
        background: rgba(200, 168, 75, 0.08);
        color: #f0d060;
      }}
      .quiniela-row:last-child td {{ border-bottom: none; }}
      .col-num {{ color: #7a6535; width: 40px; }}
      .col-celda {{ width: 60px; }}
      .col-pais {{ width: 100px; text-align: left !important; padding-left: 12px !important; }}
      .col-goles {{ color: #c8a84b; font-weight: bold; width: 80px; }}
      .col-goles-madre {{ color: #e8d080; width: 90px; }}
      .col-estado {{ width: 130px; }}
      .col-comparacion {{ width: 160px; }}
      .madre-ref {{ color: #6a5528; font-size: 11px; }}
      .badge-ok {{
        color: #3ddc6e;
        border: 1px solid #2a8a4a;
        background: rgba(61,220,110,0.08);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
      }}
      .badge-fail {{
        color: #e0473e;
        border: 1px solid #8a2a24;
        background: rgba(224,71,62,0.08);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
      }}
      .quiniela-footer td {{
        padding: 12px 10px;
        font-family: monospace;
        border-top: 1px solid #c8a84b;
        background: linear-gradient(180deg, #1a1508, #110d04);
      }}
      .footer-label {{
        text-align: right !important;
        color: #7a6535;
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
      }}
      .footer-valor {{
        text-align: center;
        color: #f0d060;
        font-size: 14px;
        font-weight: bold;
      }}
      .empty-state {{
        text-align: center;
        color: #7a6535;
        font-family: monospace;
        font-size: 13px;
        padding: 50px 20px;
        border: 1px dashed #3a2e10;
        border-radius: 10px;
      }}
      /* ============ SOLO PARA MÓVILES (≤640px) ============ */
      @media (max-width: 640px) {{
        body {{ padding: 10px 6px 40px 6px; }}
        h2.title {{ font-size: 15px; letter-spacing: 3px; }}
        .subtitle {{ font-size: 9px; }}
        .quiniela-table thead th {{ font-size: 9px; padding: 10px 6px; }}
        .quiniela-row td {{ font-size: 11px; padding: 8px 6px; }}
        .badge-ok, .badge-fail {{ font-size: 9px; padding: 2px 6px; }}
        .madre-ref {{ font-size: 9px; }}
      }}
      {ocultar_css}
    </style>
    </head>
    <body>
      <div class="page-wrap">
        <h2 class="title">{titulo}</h2>
        <div class="subtitle">{subtitulo}</div>
        <div class="divider"></div>
        <div class="table-scroll">
          {tabla_bloque}
        </div>
      </div>
    </body>
    </html>"""


# ════════════════════════════════════════════════════════════════════
#  DETECCIÓN DE PÁGINA DE PARTICIPANTE (rueda hija)
# ════════════════════════════════════════════════════════════════════
query_params = st.query_params
participante_seleccionado = query_params.get("participant", None)

if participante_seleccionado:
    st.set_page_config(
        page_title=f"Quiniela de {participante_seleccionado}",
        page_icon=_PAGE_ICON,
        layout="wide",
    )
    st.markdown("""
        <style>
            .stApp { background-color: #0a0a0a; }
            header, footer { display: none !important; }
            .block-container { padding: 0 !important; max-width: 100% !important; }
        </style>
    """, unsafe_allow_html=True)

    datos = obtener_datos_participante(participante_seleccionado)

    hijo_team_flags    = {}
    hijo_r16_flags     = {}
    hijo_qf_flags      = {}
    hijo_sf_flags      = {}
    hijo_final_flags   = {}
    hijo_champion_flags = {}

    claves_r32  = set(mapeo_circulo_a_indice.values())
    claves_r16  = set(r16_key_map.values())
    claves_qf   = set(qf_key_map.values())
    claves_sf   = set(sf_key_map.values())
    claves_fin  = set(final_key_map.values())
    claves_camp = set(champion_key_map.values())

    for row in datos:
        celda = (row.get("celda") or "").strip()
        pais  = (row.get("pais") or "").strip()
        if not celda or not pais:
            continue
        codigo = country_to_flag.get(pais)
        if not codigo:
            continue
        archivo = f"{codigo}.svg"

        if celda in claves_r32:
            hijo_team_flags[celda] = archivo
        elif celda in claves_r16:
            hijo_r16_flags[celda] = (archivo, pais)
        elif celda in claves_qf:
            hijo_qf_flags[celda] = (archivo, pais)
        elif celda in claves_sf:
            hijo_sf_flags[celda] = (archivo, pais)
        elif celda in claves_fin:
            hijo_final_flags[celda] = (archivo, pais)
        elif celda in claves_camp:
            hijo_champion_flags[celda] = (archivo, pais)

    st.markdown("""
        <style>
            div[data-testid="stRadio"] > label {
                display: none;
            }
            div[data-testid="stRadio"] div[role="radiogroup"] {
                display: flex;
                justify-content: center;
                gap: 2px;
                background: linear-gradient(180deg, #1a1508, #110d04);
                border: 1px solid #5a4520;
                border-radius: 999px;
                padding: 4px;
                width: fit-content;
                margin: 0 auto 4px auto;
                box-shadow: inset 0 0 12px rgba(0,0,0,0.4);
            }
            div[data-testid="stRadio"] div[role="radiogroup"] label {
                margin: 0 !important;
                padding: 8px 22px !important;
                border-radius: 999px !important;
                color: #7a6535 !important;
                font-family: monospace !important;
                font-size: 11px !important;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                cursor: pointer;
                border: 1px solid transparent;
                transition: all .18s;
            }
            div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
                color: #d8cba8 !important;
            }
            div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
                display: none !important;
            }
            div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
                background: linear-gradient(180deg, #3a2d10, #221a08);
                color: #f0d060 !important;
                border: 1px solid #c8a84b;
                box-shadow: 0 0 10px rgba(212,168,67,0.30);
            }
        </style>
    """, unsafe_allow_html=True)



    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        modo_vista = st.radio(
            "Vista del bracket",
            options=["Predicción completa", "Resultado en tiempo real"],
            horizontal=True,
            label_visibility="collapsed",
        )

    usar_solo_madre = (modo_vista == "Resultado en tiempo real")
    titulo_bracket = (
        f"TIEMPO REAL · {participante_seleccionado.upper()}"
        if usar_solo_madre else
        f"QUINIELA · {participante_seleccionado.upper()}"
    )

    bracket_html = construir_bracket_html(
        team_flags=hijo_team_flags,
        r16_flags=hijo_r16_flags,
        qf_flags=hijo_qf_flags,
        sf_flags=hijo_sf_flags,
        final_flags=hijo_final_flags,
        champion_flags=hijo_champion_flags,
        titulo=titulo_bracket,
        resultados_madre=resultados_madre_por_celda,
        solo_madre=usar_solo_madre,
    )

    components.html(bracket_html, height=SVG_HEIGHT + 60, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  ORDEN DE TABLAS EN STATS DE PARTICIPANTE:
    #  1. Rueda (ya renderizada arriba)
    #  2. QUIEN PASA A SEMIFINALES?  ← nueva
    #  3. GOLES CUARTOS              ← nueva
    #  4. QUIEN PASA A CUARTOS?      ← existente
    #  5. GOLES OCTAVOS              ← existente
    #  6. QUIEN PASA A OCTAVOS?      ← existente (con acordeón)
    #  7. GOLES DIECISEISAVOS        ← existente (con acordeón)
    #  8. INSIGNIAS
    #  9. Botón volver
    # ════════════════════════════════════════════════════════════════

    # ── Helper reutilizable de comparar goles ────────────────────────
    def comparar_goles(goles_p, goles_r, pais_p=None, pais_real=None):
        """
        Compara la predicción de goles contra el resultado real.
        Si se pasan pais_p/pais_real (validación extra, usada en "Goles
        Octavos"), el acierto solo se otorga si, ADEMÁS de coincidir los
        goles, el país predicho es el que realmente avanzó. Si no,
        simplemente se marca como Falló (sin ningún detalle adicional).
        """
        if goles_r is None or goles_r == "":
            return '<span class="madre-ref">Pendiente</span>', False, False
        try:
            p_val = int(str(goles_p).strip())
            r_val = int(str(goles_r).strip())
        except (TypeError, ValueError):
            return '<span class="madre-ref">—</span>', False, False

        goles_ok = (p_val == r_val)

        if pais_real is not None:
            if goles_ok and (pais_p or "").strip() == (pais_real or "").strip():
                return '<span class="badge-ok">✓ Acierto!</span>', True, True
            return '<span class="badge-fail">✗ Falló</span>', True, False

        if goles_ok:
            return '<span class="badge-ok">✓ Acierto!</span>', True, True
        return '<span class="badge-fail">✗ Falló</span>', True, False

    # ── Helper que construye una tabla de aciertos de PAÍS ───────────
    def _tabla_pais(filas_data, clave_set, titulo_tabla, subtitulo_tabla,
                    resultados_ref, altura_base=280, acordeon=False):
        """
        filas_data     : lista completa de rows del participante
        clave_set      : conjunto de celdas que se filtran (ej claves_qf)
        resultados_ref : dict {celda: pais_real} para la comparación
        acordeon       : si True devuelve HTML con toggle estilo acordeón
        """
        if filas_data:
            filtradas = sorted(
                [r for r in filas_data
                 if (r.get("celda", "") or "").strip() in clave_set],
                key=lambda x: x["celda"],
            )
            filas_html = ""
            total_ac, total_con = 0, 0
            for i, row in enumerate(filtradas, start=1):
                celda = row.get("celda", "")
                pais  = row.get("pais", "")
                pais_madre = resultados_ref.get(celda)
                if pais_madre:
                    total_con += 1
                    if pais.strip() == pais_madre.strip():
                        est = '<span class="badge-ok">✓ Acierto</span>'
                        total_ac += 1
                    else:
                        est = '<span class="badge-fail">✗ Falló</span>'
                    p_html = f'{pais} <span class="madre-ref">(real: {pais_madre})</span>'
                else:
                    est, p_html = "", pais
                filas_html += f"""
                <tr class="quiniela-row">
                    <td class="col-num">{i}</td>
                    <td class="col-celda">{celda}</td>
                    <td class="col-pais">{p_html}</td>
                    <td class="col-estado">{est}</td>
                </tr>"""
            n = len(filtradas)
            footer = (
                f'<tfoot><tr class="quiniela-footer">'
                f'<td colspan="3" class="footer-label">Total de aciertos</td>'
                f'<td class="footer-valor">{total_ac}/{total_con}</td>'
                f'</tr></tfoot>'
            ) if n > 0 else ""
            tabla_bloque = f"""
            <table class="quiniela-table">
                <thead><tr>
                    <th>#</th><th class="col-celda">Celda</th>
                    <th>País</th><th>Estado</th>
                </tr></thead>
                <tbody>{filas_html}</tbody>
                {footer}
            </table>"""
            altura = altura_base + n * 44
        else:
            tabla_bloque = '<div class="empty-state">Sin datos.</div>'
            altura = 260

        if acordeon:
            html = construir_tabla_acordeon_html(titulo_tabla, subtitulo_tabla, tabla_bloque)
        else:
            html = construir_tabla_detalle_html(titulo_tabla, subtitulo_tabla, tabla_bloque)
        return html, altura

    # ── Helper que construye una tabla de aciertos de GOLES ──────────
    def _tabla_goles(filas_data, clave_set, goles_ref,
                     titulo_tabla, subtitulo_tabla,
                     altura_base=280, acordeon=False, validar_pais=None):
        """
        validar_pais : dict opcional {celda: pais_real}. Cuando se pasa
        (usado en "Goles Octavos"), el acierto de goles solo se otorga
        si el país predicho para esa celda coincide con el país real,
        evitando falsos aciertos cuando el equipo predicho ni siquiera
        avanzó realmente a esa ronda.
        """
        if filas_data:
            filtradas = sorted(
                [r for r in filas_data
                 if (r.get("celda", "") or "").strip() in clave_set],
                key=lambda x: x["celda"],
            )
            filas_html = ""
            total_ac, total_con = 0, 0
            for i, row in enumerate(filtradas, start=1):
                celda   = row.get("celda", "")
                pais    = row.get("pais", "")
                goles_p = row.get("goles", "0")
                goles_r = goles_ref.get(celda)
                goles_r_html = (
                    goles_r if goles_r is not None and goles_r != ""
                    else '<span class="madre-ref">—</span>'
                )
                if validar_pais is not None:
                    comp_html, cuenta, acerto = comparar_goles(
                        goles_p, goles_r,
                        pais_p=pais, pais_real=validar_pais.get(celda),
                    )
                else:
                    comp_html, cuenta, acerto = comparar_goles(goles_p, goles_r)
                if cuenta:
                    total_con += 1
                    if acerto:
                        total_ac += 1
                filas_html += f"""
                <tr class="quiniela-row">
                    <td class="col-num">{i}</td>
                    <td class="col-celda">{celda}</td>
                    <td class="col-pais">{pais}</td>
                    <td class="col-goles">{goles_p}</td>
                    <td class="col-goles-madre">{goles_r_html}</td>
                    <td class="col-comparacion">{comp_html}</td>
                </tr>"""
            n = len(filtradas)
            footer = (
                f'<tfoot><tr class="quiniela-footer">'
                f'<td colspan="4" class="footer-label">Total de aciertos</td>'
                f'<td class="footer-valor">{total_ac}/{total_con}</td>'
                f'</tr></tfoot>'
            ) if n > 0 else ""
            tabla_bloque = f"""
            <table class="quiniela-table">
                <thead><tr>
                    <th>#</th><th class="col-celda">Celda</th>
                    <th>País</th><th>Goles P</th><th>Goles R</th>
                    <th>Comparación</th>
                </tr></thead>
                <tbody>{filas_html}</tbody>
                {footer}
            </table>"""
            altura = altura_base + n * 44
        else:
            tabla_bloque = '<div class="empty-state">Sin datos.</div>'
            altura = 260

        if acordeon:
            html = construir_tabla_acordeon_html(titulo_tabla, subtitulo_tabla, tabla_bloque,
                                                  ocultar_columnas=["col-celda"])
        else:
            html = construir_tabla_detalle_html(titulo_tabla, subtitulo_tabla, tabla_bloque,
                                                ocultar_columnas=["col-celda"])
        return html, altura

    # ════════════════════════════════════════════════════════════════
    #  TABLA "QUIEN PASA A FINALES?" — clon de "Quién pasa a Semifinales"
    # ════════════════════════════════════════════════════════════════
    html_finales, alt_finales = _tabla_pais(
        filas_data=datos,
        clave_set=claves_fin,                  # ← compara con resultados de claves_fin
        titulo_tabla="¿QUIÉN PASA A LA GRAN FINAL?",
        subtitulo_tabla="Verde = acierto vs. resultado real &middot; Rojo = no coincide",
        resultados_ref=resultados_madre_por_celda,
        acordeon=False,
    )
    st.components.v1.html(html_finales, height=alt_finales, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "GOLES SEMIFINALES" — clon de "Goles Cuartos"
    # ════════════════════════════════════════════════════════════════
    html_goles_semis, alt_goles_semis = _tabla_goles(
        filas_data=datos,
        clave_set=claves_sf,                  # ← celdas SF (B15, D15…)
        goles_ref=goles_madre_sf,             # ← compara con goles_madre_sf
        titulo_tabla="GOLES SEMIFINALES",
        subtitulo_tabla="Verde = goles exactos &middot; Rojo = no coincide",
        acordeon=False,
        validar_pais={celda: info[1] for celda, info in madre_sf_flags.items()},
    )
    st.components.v1.html(html_goles_semis, height=alt_goles_semis, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "QUIEN PASA A SEMIFINALES?"
    # ════════════════════════════════════════════════════════════════
    html_semis, alt_semis = _tabla_pais(
        filas_data=datos,
        clave_set=claves_sf,                   # ← compara con resultados de claves_sf
        titulo_tabla="¿QUIÉN PASA A SEMIFINALES?",
        subtitulo_tabla="Verde = acierto vs. resultado real &middot; Rojo = no coincide",
        resultados_ref=resultados_madre_por_celda,
        acordeon=False,
    )
    st.components.v1.html(html_semis, height=alt_semis, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "GOLES CUARTOS"
    # ════════════════════════════════════════════════════════════════
    html_goles_cuartos, alt_goles_cuartos = _tabla_goles(
        filas_data=datos,
        clave_set=claves_qf,                  # ← celdas QF (D13, D14…)
        goles_ref=goles_madre_qf,             # ← compara con goles_madre_qf
        titulo_tabla="GOLES CUARTOS",
        subtitulo_tabla="Verde = goles exactos &middot; Rojo = no coincide",
        acordeon=False,
        validar_pais={celda: info[1] for celda, info in madre_qf_flags.items()},
    )
    st.components.v1.html(html_goles_cuartos, height=alt_goles_cuartos, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "QUIEN PASA A CUARTOS?" — AQUI ESTA LA TABLA DE QUIEN PASA A CUARTOS
    # ════════════════════════════════════════════════════════════════
    html_cuartos, alt_cuartos = _tabla_pais(
        filas_data=datos,
        clave_set=claves_qf,                  # ← compara con madre_qf_flags
        titulo_tabla="¿QUIÉN PASA A CUARTOS?",
        subtitulo_tabla="Verde = acierto vs. resultado real &middot; Rojo = no coincide",
        resultados_ref=resultados_madre_por_celda,
        acordeon=False,
    )
    st.components.v1.html(html_cuartos, height=alt_cuartos, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "GOLES OCTAVOS"
    # ════════════════════════════════════════════════════════════════
    html_goles_octavos, alt_goles_octavos = _tabla_goles(
        filas_data=datos,
        clave_set=claves_r16,                 # ← celdas R16 (B9, B10…)
        goles_ref=goles_madre_r16,            # ← compara con goles_madre_r16
        titulo_tabla="GOLES OCTAVOS",
        subtitulo_tabla="Verde = goles exactos &middot; Rojo = no coincide",
        acordeon=False,
        validar_pais={celda: info[1] for celda, info in madre_r16_flags.items()},
    )
    st.components.v1.html(html_goles_octavos, height=alt_goles_octavos, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "QUIEN PASA A OCTAVOS?" — con acordeón (colapsada por defecto)
    # ════════════════════════════════════════════════════════════════
    html_octavos, alt_octavos = _tabla_pais(
        filas_data=datos,
        clave_set=claves_r16,                 # ← compara con madre_r16_flags
        titulo_tabla="¿QUIÉN PASA A OCTAVOS?",
        subtitulo_tabla="Verde = acierto vs. resultado real &middot; Rojo = no coincide",
        resultados_ref=resultados_madre_por_celda,
        acordeon=False,                        # ← toggle acordeón
    )
    st.components.v1.html(html_octavos, height=alt_octavos + 60, scrolling=False)

    # ════════════════════════════════════════════════════════════════
    #  TABLA "GOLES DIECISEISAVOS" — con acordeón (colapsada por defecto)
    # ════════════════════════════════════════════════════════════════
    html_goles_16, alt_goles_16 = _tabla_goles(
        filas_data=datos,
        clave_set=claves_r32,                 # ← celdas R32
        goles_ref={k: v for d in [goles_madre_r32] for k, v in d.items()},
        titulo_tabla="GOLES DIECISEISAVOS",
        subtitulo_tabla="Verde = goles exactos &middot; Rojo = no coincide",
        acordeon=False,                        # ← toggle acordeón
    )
    st.components.v1.html(html_goles_16, height=alt_goles_16 + 60, scrolling=False)

    # ── TABLA "INSIGNIAS" (bonus en los que participó) ─────────────────
    _registros_bonus_todos = obtener_registros_bonus()
    _, _detalle_bonus_todos = calcular_puntos_bonus_todos(_registros_bonus_todos, datos)
    insignias_participante = sorted(
        _detalle_bonus_todos.get(participante_seleccionado, []),
        key=lambda b: b["bonus_number"],
    )

    if insignias_participante:
        filas_insignias = ""
        for i, ins in enumerate(insignias_participante, start=1):
            puntos = ins["puntos"]
            badge_puntos = (
                f'<span class="badge-ok">+{puntos} pts</span>' if puntos > 0
                else '<span class="badge-fail">0 pts</span>'
            )
            filas_insignias += f"""
            <tr class="quiniela-row">
                <td class="col-num">{i}</td>
                <td class="col-pais" style="text-align:center !important;">Bonus {ins['bonus_number']}</td>
                <td class="col-pais">{ins['equipo1']} vs {ins['equipo2']}</td>
                <td class="col-estado">{badge_puntos}</td>
            </tr>
            """
        total_puntos_insignias = sum(b["puntos"] for b in insignias_participante)
        footer_insignias = f"""
        <tfoot>
            <tr class="quiniela-footer">
                <td colspan="3" class="footer-label">Total puntos de bonus</td>
                <td class="footer-valor">{total_puntos_insignias}</td>
            </tr>
        </tfoot>
        """
        tabla_insignias = f"""
        <table class="quiniela-table">
            <thead>
                <tr>
                    <th>#</th><th>Bonus</th><th>Cruce</th><th>Puntos</th>
                </tr>
            </thead>
            <tbody>
                {filas_insignias}
            </tbody>
            {footer_insignias}
        </table>
        """
        altura_insignias = 280 + len(insignias_participante) * 44
    else:
        tabla_insignias = '<div class="empty-state">Este participante aún no se ha registrado en ningún bonus.</div>'
        altura_insignias = 260

    insignias_html = construir_tabla_detalle_html(
        titulo="Insignias",
        subtitulo="Bonus en los que participaste &middot; Puntos extra ganados",
        tabla_bloque=tabla_insignias,
        ocultar_columnas=["col-celda"],
    )
    st.components.v1.html(insignias_html, height=altura_insignias, scrolling=False)

    # ── Botón de regreso ──────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Volver al bracket", use_container_width=True):
            st.query_params.clear()
            st.rerun()

    st.markdown("""
        <style>
            div[data-testid="stButton"] button {
                background: linear-gradient(180deg, #1a1508, #110d04);
                color: #d4a843;
                border: 1px solid #5a4520;
                border-radius: 8px;
                font-family: monospace;
                letter-spacing: 1px;
                padding: 8px 16px;
                transition: all 0.15s;
            }
            div[data-testid="stButton"] button:hover {
                border-color: #c8a84b;
                color: #f0d060;
                background: linear-gradient(180deg, #221a08, #160f04);
            }
        </style>
    """, unsafe_allow_html=True)

    st.stop()


# ════════════════════════════════════════════════════════════════════
#  RUEDA MADRE (página principal)
# ════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Quiniela Fase 2 909",
    page_icon=_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header, footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

bracket_html = construir_bracket_html(
    team_flags=herencia_fija,
    r16_flags=madre_r16_flags,
    qf_flags=madre_qf_flags,
    sf_flags=madre_sf_flags,
    final_flags=madre_final_flags,
    champion_flags=madre_champion_flags,
    titulo="COPA DEL MUNDO 2026",
    goles_madre=goles_madre_por_celda,
)

components.html(bracket_html, height=SVG_HEIGHT + 60, scrolling=False)

# ════════════════════════════════════════════════════════════════════
#  PANEL BONUS
# ════════════════════════════════════════════════════════════════════
# CÓMO REUTILIZAR ESTE PANEL PARA FUTUROS BONUS:
# ─────────────────────────────────────────────────────────────────────
# Cambia estas variables manualmente para cada nuevo bonus:
#   BONUS_NUMBER        → número identificador (1, 2, 3…)
#   BONUS_EQUIPO1/2     → código de bandera ("dz"=Argelia, "ch"=Suiza…)
#   bonus_visible       → True = visible para usuarios / False = oculto
#   BONUS_FECHA         → fecha de activación "DD/MM/YYYY"
#   BONUS_HORA_INICIO   → hora de apertura "HH:MM" (CDMX)
#   BONUS_HORA_FIN      → hora de cierre   "HH:MM" (CDMX)
# ─────────────────────────────────────────────────────────────────────

BONUS_NUMBER      = 2           # ← identificador del bonus
BONUS_EQUIPO1     = "ar"        # ← equipo 1 (Argentina)
BONUS_EQUIPO2     = "eg"        # ← equipo 2 (Bélgica)

# ════════════════════════════════════════════════════════════════════
#  CELDAS DEL BONUS — definen dónde se hace el UPDATE en Quiniela_Fase2
# ════════════════════════════════════════════════════════════════════
# Cambia estas dos celdas manualmente para cada nuevo bonus.
# Son las posiciones del bracket donde se actualizará pais + goles
# del participante cuando envíe su pronóstico.
BONUS_CELDA1 = "D10"   # ← celda del equipo 1
BONUS_CELDA2 = "D9"   # ← celda del equipo 2

# ── Control de inputs de goles ───────────────────────────────────────
# True  → aparecen los inputs de goles + hace UPDATE en Quiniela_Fase2
# False → solo registra en BonusCheck (sin actualizar goles ni país)
bonus_goles_activo = True

# ── Visibilidad manual ───────────────────────────────────────────────
# True  → el bonus se muestra (sujeto además a la ventana de tiempo)
# False → el bonus está oculto sin importar fecha/hora
bonus_visible = False

# ── Ventana de tiempo de activación (hora CDMX = America/Mexico_City) ─
# Formato fecha: "DD/MM/YYYY"    Formato hora: "HH:MM" en 24h
BONUS_FECHA       = "07/07/2026"
BONUS_HORA_INICIO = "09:00"
BONUS_HORA_FIN    = "09:55"

# ── Cálculo de estado temporal ───────────────────────────────────────
_TZ_CDMX = pytz.timezone("America/Mexico_City")
_ahora   = datetime.now(_TZ_CDMX)

def _parse_ventana():
    """Devuelve (dt_inicio, dt_fin) localizados en CDMX."""
    dia, mes, anio = BONUS_FECHA.split("/")
    h_ini, m_ini  = BONUS_HORA_INICIO.split(":")
    h_fin, m_fin  = BONUS_HORA_FIN.split(":")
    inicio = _TZ_CDMX.localize(datetime(int(anio), int(mes), int(dia),
                                         int(h_ini), int(m_ini), 0))
    fin    = _TZ_CDMX.localize(datetime(int(anio), int(mes), int(dia),
                                         int(h_fin), int(m_fin), 0))
    return inicio, fin

_bonus_inicio, _bonus_fin = _parse_ventana()
_bonus_activo   = bonus_visible and (_bonus_inicio <= _ahora <= _bonus_fin)
_bonus_pendiente = bonus_visible and (_ahora < _bonus_inicio)
_bonus_cerrado  = bonus_visible and (_ahora > _bonus_fin)

# ── Datos de los equipos ─────────────────────────────────────────────
_nombre_eq1 = flag_to_country.get(BONUS_EQUIPO1, BONUS_EQUIPO1)
_nombre_eq2 = flag_to_country.get(BONUS_EQUIPO2, BONUS_EQUIPO2)

def _bandera_b64(codigo):
    ruta = f"Banderas/{codigo}.svg"
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()
    return ""

_b64_eq1 = _bandera_b64(BONUS_EQUIPO1)
_b64_eq2 = _bandera_b64(BONUS_EQUIPO2)

def _enviar_bonus(nombre_participante):
    """Inserta un registro en la tabla BonusCheck de Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "nombre":       nombre_participante,
        "bonus_number": BONUS_NUMBER,
        "equipo1":      _nombre_eq1,
        "equipo2":      _nombre_eq2,
    }
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/BonusCheck",
            headers=headers,
            json=payload,
            timeout=8,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def _actualizar_goles_bonus(nombre_participante, goles1, goles2):
    """
    Hace dos PATCH en Quiniela_Fase2 para actualizar país y goles:
      WHERE nombre = nombre_participante AND celda = BONUS_CELDA1
        → SET pais = _nombre_eq1, goles = goles1
      WHERE nombre = nombre_participante AND celda = BONUS_CELDA2
        → SET pais = _nombre_eq2, goles = goles2
    Retorna (ok1, ok2, debug1, debug2).
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",   # ← devuelve la fila actualizada
    }

    def _patch(celda, pais_val, goles_val):
        # safe='' → codifica espacios como %20 pero respeta caracteres
        # especiales del nombre. Supabase acepta %20 en filtros eq.
        nombre_enc = urllib.parse.quote(nombre_participante, safe="")
        celda_enc  = urllib.parse.quote(celda, safe="")
        url = (
            f"{SUPABASE_URL}/rest/v1/Quiniela_Fase2"
            f"?nombre=eq.{nombre_enc}"
            f"&celda=eq.{celda_enc}"
        )
        payload = {"pais": pais_val, "goles": int(goles_val)}
        try:
            r = requests.patch(url, headers=headers, json=payload, timeout=10)
        except Exception as exc:
            return False, {"url": url, "error": str(exc)}

        # Con "Prefer: return=representation", PostgREST responde 200 y
        # devuelve un array con las filas que SÍ se modificaron. Si ese
        # array viene vacío ([]), la petición "tuvo éxito" a nivel HTTP
        # pero CERO filas cumplieron el WHERE (nombre+celda) — típicamente
        # porque RLS (Row Level Security) las está ocultando para el rol
        # anon/publishable. Un status 200/204 por sí solo NO significa
        # que algo se haya actualizado de verdad.
        filas_afectadas = []
        if r.text:
            try:
                filas_afectadas = r.json()
            except ValueError:
                filas_afectadas = []

        ok = r.status_code == 200 and len(filas_afectadas) > 0
        debug = {
            "url":             url,
            "status":          r.status_code,
            "body":            r.text[:300] if r.text else "(vacío)",
            "filas_afectadas": len(filas_afectadas),
        }
        return ok, debug

    ok1, dbg1 = _patch(BONUS_CELDA1, _nombre_eq1, goles1)
    ok2, dbg2 = _patch(BONUS_CELDA2, _nombre_eq2, goles2)
    return ok1, ok2, dbg1, dbg2

# ── Estado de sesión ─────────────────────────────────────────────────
if "bonus_abierto"   not in st.session_state: st.session_state.bonus_abierto   = False
if "bonus_enviado"   not in st.session_state: st.session_state.bonus_enviado   = False
if "bonus_seleccion" not in st.session_state: st.session_state.bonus_seleccion = None
if "bonus_goles1"    not in st.session_state: st.session_state.bonus_goles1    = 0
if "bonus_goles2"    not in st.session_state: st.session_state.bonus_goles2    = 0

_lista_bonus = obtener_participantes() or []

# ── Solo renderizamos el panel si bonus_visible = True ───────────────
if bonus_visible:

    _, col_bonus, _ = st.columns([1, 2, 1])

    with col_bonus:

        # ── CSS del panel ────────────────────────────────────────────
        st.markdown("""
        <style>
        .bonus-panel {
            background: linear-gradient(180deg, #110d04 0%, #0a0a0a 100%);
            border: 1px solid #3a2e10;
            border-radius: 12px;
            padding: 22px 20px 24px 20px;
        }
        .bonus-title {
            text-align: center;
            color: #d4a843;
            font-family: 'Georgia', serif;
            font-size: 14px;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .bonus-subtitle {
            text-align: center;
            color: #7a6535;
            font-family: monospace;
            font-size: 10px;
            white-space: pre-wrap;
            letter-spacing: 2px;
            margin-bottom: 14px;
        }
        .bonus-divider {
            width: 80px;
            height: 1px;
            background: linear-gradient(90deg, transparent, #c8a84b, transparent);
            margin: 0 auto 18px auto;
        }
        /* Banderas lado a lado con nombre debajo de cada una */
        .bonus-matchup {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            gap: 18px;
            margin-bottom: 18px;
        }
        .bonus-team {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .bonus-team img {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 2px solid #c8a84b;
            object-fit: cover;
        }
        .bonus-team-name {
            color: #d8cba8;
            font-family: monospace;
            font-size: 11px;
            text-align: center;
            letter-spacing: 1px;
        }
        .bonus-vs-label {
            color: #7a6535;
            font-family: monospace;
            font-size: 13px;
            letter-spacing: 2px;
            margin-top: 18px;
        }
        /* Contador de tiempo */
        .bonus-countdown {
            text-align: center;
            font-family: monospace;
            font-size: 11px;
            color: #d4a843;
            background: rgba(212,168,67,0.07);
            border: 1px solid #3a2e10;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 14px;
            letter-spacing: 1px;
        }
        .bonus-countdown-num {
            font-size: 20px;
            font-weight: bold;
            color: #f0d060;
            letter-spacing: 3px;
            display: block;
            margin-top: 4px;
        }
        .bonus-cerrado {
            text-align: center;
            color: #e0473e;
            font-family: monospace;
            font-size: 11px;
            padding: 10px;
            border: 1px solid #8a2a24;
            border-radius: 8px;
            background: rgba(224,71,62,0.07);
            letter-spacing: 1px;
        }
        .bonus-ok {
            text-align: center;
            color: #3ddc6e;
            font-family: monospace;
            font-size: 11px;
            margin-top: 8px;
            padding: 8px;
            border: 1px solid #2a8a4a;
            border-radius: 6px;
            background: rgba(61,220,110,0.07);
        }
        .bonus-err {
            text-align: center;
            color: #e0473e;
            font-family: monospace;
            font-size: 11px;
            margin-top: 8px;
            padding: 6px;
            border: 1px solid #8a2a24;
            border-radius: 6px;
            background: rgba(224,71,62,0.07);
        }
        /* Botones centrados */
        div[data-testid="stButton"],
        .stButton {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }
        div[data-testid="element-container"]:has(div[data-testid="stButton"]) {
            display: flex !important;
            justify-content: center !important;
        }
        div[data-testid="stButton"] > button,
        .stButton > button {
            background: linear-gradient(180deg, #1e1608, #110d04) !important;
            color: #d4a843 !important;
            border: 1px solid #5a4520 !important;
            border-radius: 8px !important;
            font-family: monospace !important;
            letter-spacing: 2px !important;
            font-size: 12px !important;
            width: auto !important;
            min-width: 180px !important;
            padding: 10px 20px !important;
            transition: all 0.15s !important;
            margin: 0 auto !important;
        }
        div[data-testid="stButton"] > button:hover,
        .stButton > button:hover {
            border-color: #c8a84b !important;
            color: #f0d060 !important;
            background: linear-gradient(180deg, #2a1e08, #160f04) !important;
        }
        div[data-testid="stSelectbox"] > div > div {
            background: #110d04 !important;
            border: 1px solid #3a2e10 !important;
            color: #d8cba8 !important;
            font-family: monospace !important;
            border-radius: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Cuerpo del panel ─────────────────────────────────────────
        st.markdown('<div class="bonus-panel">', unsafe_allow_html=True)
        st.markdown('<div class="bonus-title">⚡ Bonus</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="bonus-subtitle">'
            f'{BONUS_FECHA} · {BONUS_HORA_INICIO} – {BONUS_HORA_FIN} CDMX\n'
            f'Este bonus vale 3 puntos extra, Aplica para goles y pase de país a siguiete ronda\n'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="bonus-divider"></div>', unsafe_allow_html=True)

        # Banderas con nombre debajo de cada una
        flag1_html = f'<img src="{_b64_eq1}"/>' if _b64_eq1 else "🏳"
        flag2_html = f'<img src="{_b64_eq2}"/>' if _b64_eq2 else "🏳"
        st.markdown(f"""
        <div class="bonus-matchup">
            <div class="bonus-team">
                {flag1_html}
                <span class="bonus-team-name">{_nombre_eq1}</span>
            </div>
            <span class="bonus-vs-label">VS</span>
            <div class="bonus-team">
                {flag2_html}
                <span class="bonus-team-name">{_nombre_eq2}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Contador JavaScript en tiempo real ───────────────────────
        # Se recalcula cada segundo en el navegador usando la hora del
        # servidor (CDMX) que se inyecta en el HTML como timestamp Unix.
        _ts_inicio = int(_bonus_inicio.timestamp())
        _ts_fin    = int(_bonus_fin.timestamp())
        _ts_ahora  = int(_ahora.timestamp())

        _countdown_html = f"""
        <div id="bonus-cd" class="bonus-countdown">
            <span id="cd-label">Cargando…</span>
            <span class="bonus-countdown-num" id="cd-time">--:--:--</span>
        </div>
        <script>
        (function() {{
            const tsInicio = {_ts_inicio};
            const tsFin    = {_ts_fin};
            const offset   = {_ts_ahora} - Math.floor(Date.now() / 1000);

            function fmt(s) {{
                const h = String(Math.floor(s/3600)).padStart(2,'0');
                const m = String(Math.floor((s%3600)/60)).padStart(2,'0');
                const ss = String(s%60).padStart(2,'0');
                return h+':'+m+':'+ss;
            }}

            function tick() {{
                const now = Math.floor(Date.now()/1000) + offset;
                const lbl = document.getElementById('cd-label');
                const tim = document.getElementById('cd-time');
                if (!lbl || !tim) return;

                if (now < tsInicio) {{
                    lbl.textContent = '⏳ Abre en';
                    lbl.style.color = '#d4a843';
                    tim.style.color = '#f0d060';
                    tim.textContent = fmt(tsInicio - now);
                }} else if (now <= tsFin) {{
                    lbl.textContent = '🟢 Cierra en';
                    lbl.style.color = '#3ddc6e';
                    tim.style.color = '#3ddc6e';
                    tim.textContent = fmt(tsFin - now);
                }} else {{
                    lbl.textContent = '🔴 Bonus cerrado';
                    lbl.style.color = '#e0473e';
                    tim.style.color = '#e0473e';
                    tim.textContent = '00:00:00';
                    clearInterval(timer);
                }}
            }}

            tick();
            const timer = setInterval(tick, 1000);
        }})();
        </script>
        """
        components.html(_countdown_html, height=80)

        # ── Lógica de interacción según estado temporal ───────────────
        if _bonus_activo:
            if not st.session_state.bonus_enviado:

                # ── PASO 1: ACEPTAR BONUS ─────────────────────────────
                if not st.session_state.bonus_abierto:
                    _bl1, _bm1, _br1 = st.columns([1, 2, 1])
                    with _bm1:
                        if st.button(
                            "⚡ ACEPTAR BONUS",
                            key="btn_bonus_toggle",
                            use_container_width=True,
                        ):
                            st.session_state.bonus_abierto   = True
                            st.session_state.bonus_seleccion = None
                            st.session_state.bonus_goles1    = 0
                            st.session_state.bonus_goles2    = 0
                            st.rerun()

                # ── PASO 2: SELECCIONAR PARTICIPANTE ──────────────────
                if st.session_state.bonus_abierto and _lista_bonus:
                    seleccion = st.selectbox(
                        "Selecciona tu nombre",
                        options=["— elige —"] + _lista_bonus,
                        key="bonus_select",
                        label_visibility="collapsed",
                    )
                    if seleccion != "— elige —":
                        st.session_state.bonus_seleccion = seleccion

                    # ── PASO 3: INPUTS DE GOLES ───────────────────────
                    if st.session_state.bonus_seleccion:

                        if bonus_goles_activo:
                            st.markdown(
                                '<div style="text-align:center; color:#7a6535; '
                                'font-family:monospace; font-size:11px; '
                                'letter-spacing:2px; margin:14px 0 6px 0;">'
                                'PRONÓSTICO DE GOLES</div>',
                                unsafe_allow_html=True,
                            )
                            _gc1, _gv, _gc2 = st.columns([2, 1, 2])

                            with _gc1:
                                st.markdown(
                                    f'<div style="text-align:center; color:#d8cba8; '
                                    f'font-family:monospace; font-size:11px; '
                                    f'margin-bottom:4px;">{_nombre_eq1}</div>',
                                    unsafe_allow_html=True,
                                )
                                goles1 = st.number_input(
                                    label=_nombre_eq1,
                                    min_value=0, max_value=30,
                                    value=st.session_state.bonus_goles1,
                                    step=1, key="input_goles1",
                                    label_visibility="collapsed",
                                )
                                st.session_state.bonus_goles1 = goles1

                            with _gv:
                                st.markdown(
                                    '<div style="text-align:center; color:#7a6535; '
                                    'font-family:monospace; font-size:16px; '
                                    'padding-top:28px;">VS</div>',
                                    unsafe_allow_html=True,
                                )

                            with _gc2:
                                st.markdown(
                                    f'<div style="text-align:center; color:#d8cba8; '
                                    f'font-family:monospace; font-size:11px; '
                                    f'margin-bottom:4px;">{_nombre_eq2}</div>',
                                    unsafe_allow_html=True,
                                )
                                goles2 = st.number_input(
                                    label=_nombre_eq2,
                                    min_value=0, max_value=30,
                                    value=st.session_state.bonus_goles2,
                                    step=1, key="input_goles2",
                                    label_visibility="collapsed",
                                )
                                st.session_state.bonus_goles2 = goles2

                            st.markdown(
                                f'<div style="text-align:center; color:#c8a84b; '
                                f'font-family:monospace; font-size:13px; '
                                f'letter-spacing:2px; margin:10px 0 4px 0;">'
                                f'{int(st.session_state.bonus_goles1)} '
                                f'— '
                                f'{int(st.session_state.bonus_goles2)}</div>',
                                unsafe_allow_html=True,
                            )

                        # ── PASO 4: ENVIAR ────────────────────────────
                        _bl2, _bm2, _br2 = st.columns([1, 2, 1])
                        with _bm2:
                            if st.button(
                                "✓ ENVIAR",
                                key="btn_bonus_enviar",
                                use_container_width=True,
                            ):
                                nombre_sel = st.session_state.bonus_seleccion
                                errores = []

                                # INSERT en BonusCheck
                                if not _enviar_bonus(nombre_sel):
                                    errores.append("Error al registrar en BonusCheck.")

                                # UPDATE en Quiniela_Fase2 (solo si activo)
                                if bonus_goles_activo:
                                    ok1, ok2, dbg1, dbg2 = _actualizar_goles_bonus(
                                        nombre_sel,
                                        st.session_state.bonus_goles1,
                                        st.session_state.bonus_goles2,
                                    )
                                    def _nota_rls(dbg):
                                        if dbg.get("filas_afectadas") == 0:
                                            return (" → 0 filas coincidieron. Revisa la "
                                                     "policy de UPDATE (RLS) en Supabase, o "
                                                     "que nombre/celda existan tal cual.")
                                        return ""

                                    if not ok1:
                                        errores.append(
                                            f"Error {BONUS_CELDA1} "
                                            f"[{dbg1.get('status','?')}]: "
                                            f"{dbg1.get('body', dbg1.get('error',''))}"
                                            f"{_nota_rls(dbg1)}"
                                        )
                                    if not ok2:
                                        errores.append(
                                            f"Error {BONUS_CELDA2} "
                                            f"[{dbg2.get('status','?')}]: "
                                            f"{dbg2.get('body', dbg2.get('error',''))}"
                                            f"{_nota_rls(dbg2)}"
                                        )

                                if not errores:
                                    st.session_state.bonus_enviado = True
                                    st.session_state.bonus_abierto = False
                                    st.rerun()
                                else:
                                    for e in errores:
                                        st.markdown(
                                            f'<div class="bonus-err">{e}</div>',
                                            unsafe_allow_html=True,
                                        )
            else:
                resumen = (
                    f" · {int(st.session_state.bonus_goles1)}–"
                    f"{int(st.session_state.bonus_goles2)}"
                    if bonus_goles_activo else ""
                )
                st.markdown(
                    f'<div class="bonus-ok">✓ Bonus registrado<br/>'
                    f'<span style="opacity:.7">'
                    f'{st.session_state.bonus_seleccion}{resumen}'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )

        elif _bonus_pendiente:
            pass

        elif _bonus_cerrado:
            st.markdown(
                '<div class="bonus-cerrado">🔴 El tiempo de este bonus ha cerrado. '
                'Se abrirán más bonuses en el futuro. ¡Atentos!</div>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)  # cierra .bonus-panel

# ════════════════════════════════════════════════════════════════════
#  TABLA DE PARTICIPANTES (con aciertos y ordenación)
# ════════════════════════════════════════════════════════════════════
participantes = obtener_participantes()

if participantes:
    todos_registros = obtener_todos_los_registros()
    registros_bonus = obtener_registros_bonus()
    aciertos_por_participante = calcular_aciertos_por_participante(todos_registros)
    puntos_bonus_por_participante, _detalle_bonus_por_participante = calcular_puntos_bonus_todos(
        registros_bonus, todos_registros
    )

    # Los puntos de bonus se suman al total de aciertos de cada participante
    for _nombre_bonus, _pts_bonus in puntos_bonus_por_participante.items():
        aciertos_por_participante[_nombre_bonus] = (
            aciertos_por_participante.get(_nombre_bonus, 0) + _pts_bonus
        )

    participantes_ordenados = sorted(
        participantes,
        key=lambda n: (-aciertos_por_participante.get(n, 0), n)
    )

    filas_html = ""
    for i, nombre in enumerate(participantes_ordenados, start=1):
        url_participante = f"?participant={urllib.parse.quote(nombre)}"
        total_aci = aciertos_por_participante.get(nombre, 0)
        filas_html += f"""
        <tr class="part-row" onclick="window.open('{url_participante}', '_blank')">
            <td class="p-num">{i:02d}</td>
            <td class="p-name">{nombre}</td>
            <td class="p-aciertos">{total_aci}</td>
            <td class="p-arrow">→</td>
        </tr>
        """
    num_filas = len(participantes_ordenados)
    tabla_bloque = f"""
    <table class="part-table">
        <thead>
            <tr><th>#</th><th>Participante</th><th>Aciertos</th><th></th></tr>
        </thead>
        <tbody>
            {filas_html}
        </tbody>
    </table>
    """
    altura_tabla_section = 220 + num_filas * 46
else:
    tabla_bloque = '<div class="empty-state">No se encontraron participantes en la base de datos.</div>'
    altura_tabla_section = 260

participants_html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: #0a0a0a;
    font-family: 'Georgia', serif;
    display: flex;
    justify-content: center;
    padding: 30px 20px 50px 20px;
  }}
  .page-wrap {{
    position: relative;
    width: 100%;
    max-width: 640px;
  }}
  .glow-bg {{
    position: absolute;
    top: -80px;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(212,168,67,0.14) 0%, rgba(138,96,32,0.05) 45%, rgba(10,10,10,0) 75%);
    pointer-events: none;
    z-index: 0;
  }}
  .content {{ position: relative; z-index: 1; }}
  h2.title {{
    text-align: center;
    color: #d4a843;
    font-family: 'Georgia', serif;
    font-weight: normal;
    letter-spacing: 5px;
    font-size: 20px;
    margin: 0 0 4px 0;
    text-transform: uppercase;
  }}
  .subtitle {{
    text-align: center;
    color: #7a6535;
    font-family: monospace;
    font-size: 10px;
    letter-spacing: 2px;
    margin-bottom: 22px;
    text-transform: uppercase;
  }}
  .divider {{
    width: 100px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #c8a84b, transparent);
    margin: 0 auto 26px auto;
  }}
  .table-scroll {{
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    width: 100%;
    border-radius: 10px;
  }}
  .part-table {{
    table-layout: fixed;   /* el ancho total = suma de los anchos de columna de abajo, nada más que ajustar aquí */
    margin: 0 auto;
    border-collapse: collapse;
    background: rgba(20, 15, 5, 0.5);
    border: 1px solid #3a2e10;
    border-radius: 10px;
    overflow: hidden;
  }}
  .part-table thead th {{
    background: linear-gradient(180deg, #1a1508, #110d04);
    color: #e8d080;
    font-family: monospace;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 12px 16px;
    border-bottom: 1px solid #c8a84b;
    text-align: left;
    font-weight: normal;
    white-space: nowrap;
  }}
  .part-row {{
    cursor: pointer;
    transition: background 0.15s;
  }}
  .part-row td {{
    padding: 12px 16px;
    color: #d8cba8;
    font-family: monospace;
    font-size: 13px;
    border-bottom: 1px solid #221a0a;
    white-space: nowrap;
  }}
  .part-row:hover td {{
    background: rgba(200, 168, 75, 0.08);
    color: #f0d060;
  }}
  .part-row:last-child td {{ border-bottom: none; }}
  .p-num {{ color: #7a6535; width: 40px; }}
  .p-name {{ width: 210px; }}
  .p-aciertos {{
    width: 100px;
    text-align: center;
    color: #c8a84b;
    font-weight: bold;
  }}
  .p-arrow {{
    width: 70px;
    text-align: right;
    color: #5a4520;
    transition: color 0.15s, transform 0.15s;
  }}
  .part-row:hover .p-arrow {{
    color: #d4a843;
    transform: translateX(3px);
  }}
  .empty-state {{
    text-align: center;
    color: #7a6535;
    font-family: monospace;
    font-size: 13px;
    padding: 50px 20px;
    border: 1px dashed #3a2e10;
    border-radius: 10px;
  }}
  /* ============ SOLO PARA MÓVILES (≤640px) ============ */
  @media (max-width: 640px) {{
    body {{ padding: 15px 5px 30px 5px; }}
    h2.title {{ font-size: 16px; letter-spacing: 3px; }}
    .subtitle {{ font-size: 9px; }}
    .part-table thead th {{ font-size: 9px; padding: 8px 6px; }}
    .part-row td {{ font-size: 11px; padding: 8px 6px; }}
  }}
</style>
</head>
<body>
  <div class="page-wrap">
    <div class="glow-bg"></div>
    <div class="content">
      <h2 class="title">Participantes</h2>
      <div class="subtitle">Quiniela &middot; World Cup</div>
      <div class="divider"></div>
      <div class="table-scroll">
        {tabla_bloque}
      </div>
    </div>
  </div>
</body>
</html>"""

st.components.v1.html(participants_html, height=altura_tabla_section, scrolling=False)