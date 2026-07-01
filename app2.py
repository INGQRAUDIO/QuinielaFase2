import streamlit as st
import streamlit.components.v1 as components
import math
import base64
import os
import json
import requests
import urllib.parse
from collections import defaultdict


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

    for nombre, rows_participante in participantes_rows.items():
        aciertos_octavos = 0
        aciertos_goles = 0
        for row in rows_participante:
            celda = (row.get("celda") or "").strip()
            if celda in claves_r16_set:
                pais_hijo = row.get("pais", "").strip()
                pais_madre = resultados_madre_por_celda.get(celda)
                if pais_madre and pais_hijo == pais_madre:
                    aciertos_octavos += 1
            elif celda in claves_r32_set:
                goles_hijo = row.get("goles")
                if goles_hijo is None:
                    goles_hijo = ""
                else:
                    goles_hijo = str(goles_hijo).strip()
                goles_madre = goles_madre_por_celda.get(celda)
                if goles_madre is not None and goles_madre != "":
                    try:
                        if int(goles_hijo) == int(goles_madre):
                            aciertos_goles += 1
                    except (ValueError, TypeError):
                        pass
        total = aciertos_octavos + aciertos_goles
        aciertos_dict[nombre] = total
    return aciertos_dict


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
}
madre_qf_flags = {}
madre_sf_flags = {}
madre_final_flags = {}
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
}
goles_madre_r16 = {}
goles_madre_qf = {}
goles_madre_sf = {}
goles_madre_final = {}
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

    node_els.append(
        f'<circle cx="{CX}" cy="{CY}" r="{RC}" '
        f'fill="#1a1200" stroke="{C["glow"]}" stroke-width="2.5"/>'
    )

    if 0 in champion_loaded:
        node_els.append(
            f'<circle cx="{CX}" cy="{CY}" r="{CHAMP_NODE_R}" '
            f'fill="url(#flag_champion_0)" stroke="{C["glow"]}" stroke-width="2.5" '
            f'class="champion-node" data-node-idx="0"/>'
        )
        gol_label(CX, CY, goles_madre.get(champion_key_map.get(0)))
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
def construir_tabla_detalle_html(titulo, subtitulo, tabla_bloque):
    return f"""<!DOCTYPE html>
    <html>
    <head>
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
      .quiniela-table {{
        width: 100%;
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
      }}
      .quiniela-row td {{
        padding: 11px 10px;
        text-align: center;
        color: #d8cba8;
        font-family: monospace;
        font-size: 13px;
        border-bottom: 1px solid #221a0a;
        transition: background 0.15s;
      }}
      .quiniela-row:hover td {{
        background: rgba(200, 168, 75, 0.08);
        color: #f0d060;
      }}
      .quiniela-row:last-child td {{ border-bottom: none; }}
      .col-num {{ color: #7a6535; width: 6%; }}
      .col-celda {{ width: 10%; }}
      .col-pais {{ width: 32%; text-align: left !important; padding-left: 18px !important; }}
      .col-goles {{ color: #c8a84b; font-weight: bold; width: 12%; }}
      .col-goles-madre {{ color: #e8d080; width: 14%; }}
      .col-estado {{ width: 16%; }}
      .col-comparacion {{ width: 20%; }}
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
    </style>
    </head>
    <body>
      <div class="page-wrap">
        <h2 class="title">{titulo}</h2>
        <div class="subtitle">{subtitulo}</div>
        <div class="divider"></div>
        {tabla_bloque}
      </div>
    </body>
    </html>"""


# ════════════════════════════════════════════════════════════════════
#  DETECCIÓN DE PÁGINA DE PARTICIPANTE (rueda hija)
# ════════════════════════════════════════════════════════════════════
query_params = st.query_params
participante_seleccionado = query_params.get("participant", None)

if participante_seleccionado:
    st.set_page_config(page_title=f"Quiniela de {participante_seleccionado}", layout="wide")
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

    # ── TABLA "OCTAVOS" ──────────────────────────────────────────────
    if datos:
        datos_r16 = [
            row for row in datos
            if (row.get("celda", "") or "").strip() in claves_r16
        ]
        datos_r16_ordenados = sorted(datos_r16, key=lambda x: x["celda"])
        filas_octavos = ""
        total_aciertos_r16 = 0
        total_con_resultado_r16 = 0
        for i, row in enumerate(datos_r16_ordenados, start=1):
            celda = row.get("celda", "")
            pais = row.get("pais", "")

            estado_html = ""
            pais_madre = resultados_madre_por_celda.get(celda)
            if pais_madre:
                total_con_resultado_r16 += 1
                if pais.strip() == pais_madre.strip():
                    estado_html = '<span class="badge-ok">✓ Acierto</span>'
                    total_aciertos_r16 += 1
                else:
                    estado_html = '<span class="badge-fail">✗ Falló</span>'
                pais_html = f'{pais} <span class="madre-ref">(real: {pais_madre})</span>'
            else:
                pais_html = pais

            filas_octavos += f"""
            <tr class="quiniela-row">
                <td class="col-num">{i}</td>
                <td class="col-celda">{celda}</td>
                <td class="col-pais">{pais_html}</td>
                <td class="col-estado">{estado_html}</td>
            </tr>
            """
        num_filas_r16 = len(datos_r16_ordenados)

        footer_octavos = f"""
        <tfoot>
            <tr class="quiniela-footer">
                <td colspan="3" class="footer-label">Total de aciertos</td>
                <td class="footer-valor">{total_aciertos_r16}/{total_con_resultado_r16}</td>
            </tr>
        </tfoot>
        """ if num_filas_r16 > 0 else ""

        tabla_octavos = f"""
        <table class="quiniela-table">
            <thead>
                <tr>
                    <th>#</th><th>Celda</th><th>País</th><th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {filas_octavos}
            </tbody>
            {footer_octavos}
        </table>
        """
        altura_octavos = 280 + num_filas_r16 * 44
    else:
        tabla_octavos = '<div class="empty-state">No se encontraron datos para este participante.</div>'
        altura_octavos = 260

    octavos_html = construir_tabla_detalle_html(
        titulo="QUIEN PASA A Octavos?",
        subtitulo="Verde = acierto vs. resultado real &middot; Rojo = no coincide",
        tabla_bloque=tabla_octavos,
    )
    st.components.v1.html(octavos_html, height=altura_octavos, scrolling=False)

    # ── TABLA "GOLES DIECISEISAVOS" ───────────────────────────────────
    def comparar_goles(goles_p, goles_r):
        if goles_r is None or goles_r == "":
            return '<span class="madre-ref">Pendiente</span>', False, False
        try:
            p_val = int(str(goles_p).strip())
            r_val = int(str(goles_r).strip())
        except (TypeError, ValueError):
            return '<span class="madre-ref">—</span>', False, False
        if p_val == r_val:
            return '<span class="badge-ok">✓ Acierto!</span>', True, True
        return '<span class="badge-fail">✗ Falló</span>', True, False

    if datos:
        datos_r32 = [
            row for row in datos
            if (row.get("celda", "") or "").strip() in claves_r32
        ]
        datos_r32_ordenados = sorted(datos_r32, key=lambda x: x["celda"])
        filas_goles = ""
        total_aciertos_goles = 0
        total_con_resultado_goles = 0
        for i, row in enumerate(datos_r32_ordenados, start=1):
            celda = row.get("celda", "")
            pais = row.get("pais", "")
            goles_p = row.get("goles", "0")
            goles_r = goles_madre_por_celda.get(celda)
            goles_r_html = (
                goles_r if goles_r is not None and goles_r != ""
                else '<span class="madre-ref">—</span>'
            )

            comparacion_html, cuenta, acerto = comparar_goles(goles_p, goles_r)
            if cuenta:
                total_con_resultado_goles += 1
                if acerto:
                    total_aciertos_goles += 1

            filas_goles += f"""
            <tr class="quiniela-row">
                <td class="col-num">{i}</td>
                <td class="col-celda">{celda}</td>
                <td class="col-pais">{pais}</td>
                <td class="col-goles">{goles_p}</td>
                <td class="col-goles-madre">{goles_r_html}</td>
                <td class="col-comparacion">{comparacion_html}</td>
            </tr>
            """
        num_filas_goles = len(datos_r32_ordenados)

        footer_goles = f"""
        <tfoot>
            <tr class="quiniela-footer">
                <td colspan="5" class="footer-label">Total de aciertos</td>
                <td class="footer-valor">{total_aciertos_goles}/{total_con_resultado_goles}</td>
            </tr>
        </tfoot>
        """ if num_filas_goles > 0 else ""

        tabla_goles = f"""
        <table class="quiniela-table">
            <thead>
                <tr>
                    <th>#</th><th>Celda</th><th>País</th><th>Goles P</th><th>Goles R</th><th>Comparación</th>
                </tr>
            </thead>
            <tbody>
                {filas_goles}
            </tbody>
            {footer_goles}
        </table>
        """
        altura_goles = 280 + num_filas_goles * 44
    else:
        tabla_goles = '<div class="empty-state">No se encontraron datos para este participante.</div>'
        altura_goles = 260

    goles_dieciseisavos_html = construir_tabla_detalle_html(
        titulo="Goles Dieciseisavos",
        subtitulo="Verde = goles exactos &middot; Rojo = no coincide",
        tabla_bloque=tabla_goles,
    )
    st.components.v1.html(goles_dieciseisavos_html, height=altura_goles, scrolling=False)

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
st.set_page_config(page_title="Quiniela Fase 2 909", layout="wide", initial_sidebar_state="collapsed")

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
#  TABLA DE PARTICIPANTES (con aciertos y ordenación)
# ════════════════════════════════════════════════════════════════════
participantes = obtener_participantes()

if participantes:
    todos_registros = obtener_todos_los_registros()
    aciertos_por_participante = calcular_aciertos_por_participante(todos_registros)

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
  .part-table {{
    width: 100%;
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
  }}
  .part-row:hover td {{
    background: rgba(200, 168, 75, 0.08);
    color: #f0d060;
  }}
  .part-row:last-child td {{ border-bottom: none; }}
  .p-num {{ color: #7a6535; width: 8%; }}
  .p-name {{ width: 56%; }}
  .p-aciertos {{
    width: 16%;
    text-align: center;
    color: #c8a84b;
    font-weight: bold;
  }}
  .p-arrow {{
    width: 10%;
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
</style>
</head>
<body>
  <div class="page-wrap">
    <div class="glow-bg"></div>
    <div class="content">
      <h2 class="title">Participantes</h2>
      <div class="subtitle">Quiniela &middot; World Cup</div>
      <div class="divider"></div>
      {tabla_bloque}
    </div>
  </div>
</body>
</html>"""

st.components.v1.html(participants_html, height=altura_tabla_section, scrolling=False)