import streamlit as st
import os
import base64
import json

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .block-container, [data-testid="stAppViewBlockContainer"] {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_data
def cargar_banderas():
    banderas_path = "Banderas"
    banderas_base64_dict = {}
    if os.path.exists(banderas_path):
        banderas = [f for f in os.listdir(banderas_path) if f.endswith('.svg')]
        for bandera in banderas:
            ruta_bandera = os.path.join(banderas_path, bandera)
            with open(ruta_bandera, "rb") as f:
                svg_content = f.read()
                banderas_base64_dict[bandera] = base64.b64encode(svg_content).decode('utf-8')
    return banderas_base64_dict



def main():
    banderas_path = "Banderas"
    banderas = []
    if os.path.exists(banderas_path):
        banderas = [f for f in os.listdir(banderas_path) if f.endswith('.svg')]

    banderas_html = ""
    banderas_base64_dict = {}
    for bandera in banderas:
        ruta_bandera = os.path.join(banderas_path, bandera)
        with open(ruta_bandera, "rb") as f:
            svg_content = f.read()
            svg_base64 = base64.b64encode(svg_content).decode('utf-8')
            banderas_base64_dict[bandera] = svg_base64
            banderas_html += f'<img src="data:image/svg+xml;base64,{svg_base64}" data-nombre="{bandera}" onclick="seleccionarBandera(this, \'data:image/svg+xml;base64,{svg_base64}\')">'

    # Listas de claves (sin cambios)
    claves_izquierda_1 = ["A1", "A2", "A3", "A4"]
    claves_izquierda_2 = ["A5", "A6", "A7", "A8"]
    claves_izquierda_3 = ["A9", "A10", "A11", "A12"]
    claves_izquierda_4 = ["C1", "C2", "C3", "C4"]
    claves_izquierda_5 = ["C5", "C6", "C7", "C8"]
    claves_izquierda_6 = ["C9", "C10", "C11", "C12"]

    claves_derecha_1 = ["B1", "B2", "B3", "B4"]
    claves_derecha_2 = ["B5", "B6", "B7", "B8"]
    claves_derecha_3 = ["B9", "B10", "B11", "B12"]
    claves_derecha_4 = ["D1", "D2", "D3", "D4"]
    claves_derecha_5 = ["D5", "D6", "D7", "D8"]
    claves_derecha_6 = ["D9", "D10", "D11", "D12"]

    claves_a13 = ["A13"]
    claves_a14 = ["A14"]
    claves_a15 = ["A15"]
    claves_b13 = ["B13"]
    claves_b14 = ["B14"]
    claves_c13 = ["C13"]
    claves_c14 = ["C14"]
    claves_d13 = ["D13"]
    claves_d14 = ["D14"]

    claves_b15 = ["B15"]
    claves_c15 = ["C15"]
    claves_d15 = ["D15"]

    claves_s1 = ["S1"]
    claves_w1 = ["W1"]
    claves_s2 = ["S2"]

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
        "B8": "gb-eng.svg", "B4": "",
        
        # Grupo C
        "C1": "hr.svg", "C5": "",
        "C2": "es.svg", "C6": "",
        "C3": "us.svg", "C7": "ba.svg",
        "C4": "be.svg", "C8": "",
        
        # Grupo D
        "D1": "ar.svg", "D5": "cv.svg",
        "D2": "au.svg", "D6": "ir.svg",
        "D3": "ch.svg", "D7": "",
        "D4": "gh.svg", "D8": ""
    }

    HERENCIA_CONEXIONES = {
        "A9": ["A1","A5"], "A10": ["A2","A6"],
        "A11": ["A3","A7"], "A12": ["A4","A8"],
        "A13": ["A9","A10"], "A14": ["A11","A12"],
        "A15": ["A13","A14"],
        "B9": ["B5","B1"], "B10": ["B6","B2"],
        "B11": ["B7","B3"], "B12": ["B8","B4"],
        "B13": ["B9","B10"], "B14": ["B11","B12"],
        "B15": ["B13","B14"],
        "C9": ["C5","C1"], "C10": ["C6","C2"],
        "C11": ["C7","C3"], "C12": ["C8","C4"],
        "C13": ["C9","C10"], "C14": ["C11","C12"],
        "C15": ["C13","C14"],
        "D9": ["D5","D1"], "D10": ["D6","D2"],
        "D11": ["D7","D3"], "D12": ["D8","D4"],
        "D13": ["D9","D10"], "D14": ["D11","D12"],
        "D15": ["D13","D14"],
        "S1": ["A15","C15"], "S2": ["B15","D15"],
        "W1": ["S1","S2"]
    }

    restricciones_banderas = {}
    for clave, padres in HERENCIA_CONEXIONES.items():
        todos_padres_fijos = all(padre in herencia_fija for padre in padres)
        if todos_padres_fijos:
            banderas_permitidas = set()
            for padre in padres:
                banderas_permitidas.add(herencia_fija[padre])
            restricciones_banderas[clave] = sorted(list(banderas_permitidas))

    claves_con_linea_derecha = {"A1","A2","A3","A4","C1","C2","C3","C4","B5","B6","B7","B8","D5","D6","D7","D8"}
    claves_con_linea_izquierda = {"A5","A6","A7","A8","C5","C6","C7","C8","B1","B2","B3","B4","D1","D2","D3","D4"}
    claves_con_avance_derecha = {"A5","A6","A7","A8","C5","C6","C7","C8"}
    claves_con_avance_izquierda = {"B5","B6","B7","B8","D5","D6","D7","D8"}
    claves_con_linea_abajo = {"A9","A11","B9","B11","C9","C11","D9","D11"}
    claves_con_linea_arriba = {"A10","A12","B10","B12","C10","C12","D10","D12"}

    def generar_html_rectangulos(claves, prefijo, clase_menu="", restricciones=None):
        html = ""
        for i, clave in enumerate(claves):
            bandera_fija = herencia_fija.get(clave, None)
            contenido_inicial = ""
            if bandera_fija:
                b64 = banderas_base64_dict.get(bandera_fija, "")
                if b64:
                    contenido_inicial = f'<img src="data:image/svg+xml;base64,{b64}" class="bandera-seleccionada bandera-fija">'

            if restricciones and clave in restricciones:
                banderas_menu = ""
                for bandera in restricciones[clave]:
                    if bandera in banderas_base64_dict:
                        b64 = banderas_base64_dict[bandera]
                        banderas_menu += f'<img src="data:image/svg+xml;base64,{b64}" data-nombre="{bandera}" onclick="seleccionarBandera(this, \'data:image/svg+xml;base64,{b64}\')">'
            elif clave in HERENCIA_CONEXIONES:
                banderas_menu = ""
            else:
                banderas_menu = ""

            lineas_html = ""
            if clave in claves_con_linea_derecha:
                lineas_html += '<div class="linea-conectora linea-derecha"></div>'
            if clave in claves_con_linea_izquierda:
                lineas_html += '<div class="linea-conectora linea-izquierda"></div>'
            if clave in claves_con_avance_derecha:
                lineas_html += '<div class="linea-conectora linea-avance-derecha"></div>'
            if clave in claves_con_avance_izquierda:
                lineas_html += '<div class="linea-conectora linea-avance-izquierda"></div>'
            if clave in claves_con_linea_abajo:
                lineas_html += '<div class="linea-vertical linea-abajo"></div>'
            if clave in claves_con_linea_arriba:
                lineas_html += '<div class="linea-vertical linea-arriba"></div>'

            html += f"""
            <div class="rectangulo-container">
                {lineas_html}
                <div class="rectangulo-pulse" data-key="{clave}" data-bloqueado="{str(bandera_fija is not None).lower()}" onclick="mostrarMenu(event, '{prefijo}-{i}')">
                    {contenido_inicial}
                    <span class="clave-texto">{clave}</span>
                </div>
                
                <input type="number" class="input-goles" id="goles-{clave}" data-key="{clave}" min="0" placeholder="-" style="display: none;" oninput="guardarGoles(this)">
                
                <div class="menu-banderas {clase_menu}" id="menu-{prefijo}-{i}">
                    {banderas_menu}
                </div>
            </div>
            """
        return html

    html_izquierda_1 = generar_html_rectangulos(claves_izquierda_1, "izq1", restricciones=restricciones_banderas)
    html_izquierda_2 = generar_html_rectangulos(claves_izquierda_2, "izq2", restricciones=restricciones_banderas)
    html_izquierda_3 = generar_html_rectangulos(claves_izquierda_3, "izq3", restricciones=restricciones_banderas)
    html_izquierda_4 = generar_html_rectangulos(claves_izquierda_4, "izq4", restricciones=restricciones_banderas)
    html_izquierda_5 = generar_html_rectangulos(claves_izquierda_5, "izq5", restricciones=restricciones_banderas)
    html_izquierda_6 = generar_html_rectangulos(claves_izquierda_6, "izq6", restricciones=restricciones_banderas)

    html_a13 = generar_html_rectangulos(claves_a13, "a13", restricciones=restricciones_banderas)
    html_a14 = generar_html_rectangulos(claves_a14, "a14", restricciones=restricciones_banderas)
    html_a15 = generar_html_rectangulos(claves_a15, "a15", restricciones=restricciones_banderas)
    html_c13 = generar_html_rectangulos(claves_c13, "c13", restricciones=restricciones_banderas)
    html_c14 = generar_html_rectangulos(claves_c14, "c14", restricciones=restricciones_banderas)

    html_b15 = generar_html_rectangulos(claves_b15, "b15", "menu-derecha", restricciones=restricciones_banderas)
    html_c15 = generar_html_rectangulos(claves_c15, "c15", restricciones=restricciones_banderas)
    html_d15 = generar_html_rectangulos(claves_d15, "d15", "menu-derecha", restricciones=restricciones_banderas)

    html_s1 = generar_html_rectangulos(claves_s1, "s1", restricciones=restricciones_banderas)
    html_w1 = generar_html_rectangulos(claves_w1, "w1", restricciones=restricciones_banderas)
    html_s2 = generar_html_rectangulos(claves_s2, "s2", "menu-derecha", restricciones=restricciones_banderas)

    html_derecha_1 = generar_html_rectangulos(claves_derecha_1, "der1", "menu-derecha", restricciones=restricciones_banderas)
    html_derecha_2 = generar_html_rectangulos(claves_derecha_2, "der2", "menu-derecha", restricciones=restricciones_banderas)
    html_derecha_3 = generar_html_rectangulos(claves_derecha_3, "der3", "menu-derecha", restricciones=restricciones_banderas)
    html_derecha_4 = generar_html_rectangulos(claves_derecha_4, "der4", "menu-derecha", restricciones=restricciones_banderas)
    html_derecha_5 = generar_html_rectangulos(claves_derecha_5, "der5", "menu-derecha", restricciones=restricciones_banderas)
    html_derecha_6 = generar_html_rectangulos(claves_derecha_6, "der6", "menu-derecha", restricciones=restricciones_banderas)

    html_b13 = generar_html_rectangulos(claves_b13, "b13", "menu-derecha", restricciones=restricciones_banderas)
    html_b14 = generar_html_rectangulos(claves_b14, "b14", "menu-derecha", restricciones=restricciones_banderas)
    html_d13 = generar_html_rectangulos(claves_d13, "d13", "menu-derecha", restricciones=restricciones_banderas)
    html_d14 = generar_html_rectangulos(claves_d14, "d14", "menu-derecha", restricciones=restricciones_banderas)

    herencia_fija_js = json.dumps(herencia_fija)
    herencia_conexiones_js = json.dumps(HERENCIA_CONEXIONES)
    banderas_disponibles_js = []
    for nombre, b64 in banderas_base64_dict.items():
        banderas_disponibles_js.append({"nombre": nombre, "src": f"data:image/svg+xml;base64,{b64}"})
    banderas_disponibles_js = json.dumps(banderas_disponibles_js)

    html_completo = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    
    /* Estilos del Loader */
    #loader-container {{
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: #0E1117;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 999999;
        transition: opacity 0.5s ease;
    }}
    .spinner {{
        border: 5px solid #333;
        border-top: 5px solid #4CAF50;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
    }}
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    /* Estilos para el botón deshabilitado */
    #boton-enviar:disabled {{
        background-color: #666;
        cursor: not-allowed;
        opacity: 0.6;
    }}
    
    /* Animación de carga en el botón */
    #boton-enviar.cargando {{
        position: relative;
        color: transparent;
    }}
    
    #boton-enviar.cargando::after {{
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 20px;
        height: 20px;
        border: 3px solid #ffffff;
        border-top: 3px solid #4CAF50;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }}
    
    /* Mensaje de éxito */
    .mensaje-exito {{
        display: none;
        padding: 15px;
        background-color: #45a049;
        color: white;
        border-radius: 8px;
        text-align: center;
        margin: 40px auto 20px auto;
        max-width: 400px;
        font-weight: bold;
        font-size: 18px;
    }}
    
    /* 1. IMPORTAR LA FUENTE ROBOTO DESDE GOOGLE FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* 2. APLICARLA DE FORMA GLOBAL A TODO EL PROYECTO */
    * {{
        margin: 0; 
        padding: 0; 
        box-sizing: border-box; 
        font-family: 'Roboto', sans-serif;
    }}
    
    html, body {{ width: 100%; 
        height: 100%; 
        background-color: #0E1117; 
        overflow: hidden; /* Evita que el navegador móvil colapse */
        margin: 0;
        padding: 0;}}
        
    body {{ padding: 20px; }}
    
    
    #contenedor-master {{
        width: 100%;
        height: 100%;
        overflow: auto;
        -webkit-overflow-scrolling: touch; /* Activa el scroll suave en iOS y Android */
        padding: 20px;
    }}
    

    /* PANTALLA DE BIENVENIDA */
    #pantalla-bienvenida {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(14, 17, 23, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        transition: opacity 0.8s ease, visibility 0.8s ease;
    }}

    #pantalla-bienvenida.oculta {{
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
    }}

    .contenedor-bienvenida {{
        background-color: #161b22;
        border: 1px solid #4CAF50;
        border-radius: 14px;
        padding: 45px 35px;
        width: 380px;
        text-align: center;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.7);
        transition: opacity 0.5s ease;
        opacity: 1;
    }}

    .contenedor-bienvenida h1 {{
        color: white;
        font-size: 28px;
        margin-bottom: 30px;
    }}

    .contenedor-bienvenida label {{
        color: #03a9f4;
        font-size: 18px;
        display: block;
        margin-bottom: 10px;
    }}

    .contenedor-bienvenida input {{
        width: 300px;
        height: 45px;
        background-color: #1a1e26;
        color: white;
        border: 2px solid #4CAF50;
        border-radius: 8px;
        font-size: 18px;
        padding: 0 15px;
        text-align: center;
        outline: none;
    }}

    .contenedor-bienvenida input:focus {{
        outline: 0.5px solid #272ac5;
        border: 0.5px solid #272ac5;
        box-shadow: auto;
    }}

    .contenedor-bienvenida button {{
        display: block;
        margin: 25px auto 0;
        padding: 12px 40px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 18px;
        cursor: pointer;
        font-weight: bold;
    }}

    .contenedor-bienvenida button:hover {{
        background-color: #45a049;
    }}

    #layout-principal {{
        display: flex;
        justify-content: flex-start; /* <-- EL CAMBIO CLAVE: Alinea a la izquierda en vez del centro */
        gap: 40px;
        width: fit-content; /* <-- Ayuda a que el contenedor respete el ancho de los hijos */
        min-width: 1400px; 
        position: relative;
        padding-left: 20px; /* Un pequeño margen para que las banderas no se peguen al borde de la pantalla */
        padding-right: 20px;
        margin: 0 auto;
        
        zoom: 0.7;
    }}

    .lado-izquierdo, .lado-derecho {{
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: calc(100vh - 120px);
        position: relative;
    }}

    .columna {{ display: flex; flex-direction: column; align-items: flex-start; }}
    .columna-desalineada {{ display: flex; flex-direction: column; align-items: flex-start; margin-top: 35px; position: relative; }}

    .columna-s1, .columna-s2, .columna-w1 {{
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; align-self: center;
    }}
    .columna-w1 {{ transform: translateY(-200px); }}
    .columna-s1 {{ transform: translateX(-50px); }}
    .columna-s2 {{ transform: translateX(50px); }}

    .columna-s1 .rectangulo-pulse, .columna-s2 .rectangulo-pulse {{ width: 150px; height: 150px; }}
    .columna-w1 .rectangulo-pulse {{ width: 180px; height: 180px; }}

    .columna-a15, .columna-c15 {{ display: flex; flex-direction: column; align-items: flex-start; margin-top: 70px; }}
    .columna-b15, .columna-d15 {{ display: flex; flex-direction: column; align-items: flex-end; margin-top: 70px; }}

    .columna-a15 .rectangulo-pulse, .columna-b15 .rectangulo-pulse,
    .columna-c15 .rectangulo-pulse, .columna-d15 .rectangulo-pulse {{ width: 110px; height: 110px; }}

    .columna-a15 .bandera-seleccionada, .columna-b15 .bandera-seleccionada,
    .columna-c15 .bandera-seleccionada, .columna-d15 .bandera-seleccionada,
    .columna-s1 .bandera-seleccionada, .columna-s2 .bandera-seleccionada,
    .columna-w1 .bandera-seleccionada {{ object-fit: cover; }}

    .espaciador-a14 {{ margin-top: 58px; }}

    .columna-derecha {{ display: flex; flex-direction: column; align-items: flex-end; }}
    .columna-derecha-desalineada {{ display: flex; flex-direction: column; align-items: flex-end; margin-top: 35px; position: relative; }}

    .grupo-superior-izquierdo, .grupo-inferior-izquierdo,
    .grupo-superior-derecho, .grupo-inferior-derecho {{
        display: flex;
        gap: 20px;
        position: relative;
    }}

    .rectangulo-container {{
        position: relative;
        display: inline-block;
        margin-bottom: 10px;
    }}
    .rectangulo-pulse {{
        width: 77px; height: 54px; background-color: #FFFFFF; border-radius: 15px;
        cursor: pointer; transition: transform 0.1s ease-in-out; border: 1px solid #ddd;
        display: flex; align-items: center; justify-content: center; overflow: hidden;
        position: relative;
    }}
    .clave-texto {{
        display: none;
        color: #000000; font-size: 12px; font-weight: bold;
        pointer-events: none; position: relative; z-index: 1;
    }}
    .rectangulo-pulse:active {{ animation: pulse 0.4s ease-in-out; }}
    @keyframes pulse {{
        0% {{ transform: scale(1); }} 50% {{ transform: scale(0.92); }} 100% {{ transform: scale(1); }}
    }}

    .menu-banderas {{
        display: none; position: absolute; top: 0; left: 0;
        background-color: #595959; border: 1px solid #444444; border-radius: 8px;
        padding: 8px; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}
    .menu-derecha {{ left: auto; right: 0; }}

    .menu-banderas img {{
        width: 40px; height: 30px; margin: 4px; cursor: pointer;
        border: 2px solid transparent; border-radius: 3px;
    }}
    .menu-banderas img:hover {{ border-color: #4CAF50; }}
    .bandera-seleccionada {{
        width: 100%; height: 100%; object-fit: cover; border-radius: 15px;
        position: absolute; top: 0; left: 0;
    }}
    .bandera-fija {{ opacity: 0.9; }}

    /* Líneas horizontales (eje X) */
    .linea-conectora {{
        position: absolute;
        top: 50%;
        height: 2px;
        width: 50px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
    }}
    .linea-derecha {{ right: -50px; }}
    .linea-izquierda {{ left: -50px; }}
    .linea-avance-derecha {{ right: -20px; width: 20px; }}
    .linea-avance-izquierda {{ left: -20px; width: 20px; }}

    /* Líneas verticales (eje Y) para pares */
    .linea-vertical {{
        position: absolute;
        left: 50%;
        width: 2px;
        height: 8px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
    }}
    .linea-abajo {{ bottom: -8px; }}
    .linea-arriba {{ top: -8px; }}

    /* VS reducido */
    .vs-separator {{
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 0;
        margin: 0 30px;
    }}
    .vs-texto {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #00be3b;
        font-size: 20px;
        font-weight: bold;
        background-color: #0E1117;
        padding: 4px 8px;
        border-radius: 3px;
        z-index: 2;
        pointer-events: none;
        line-height: 1;
    }}

    /* Conectores horizontales (SVG) */
    .conector-a13 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-a13 svg {{
        position: absolute; top: 0; left: 54%; width: 60px; height: 100%;
    }}
    .conector-a14 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-a14 svg {{
        position: absolute; top: 0; left: 54%; width: 60px; height: 100%;
    }}
    .conector-c13 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-c13 svg {{
        position: absolute; top: 0; left: 54%; width: 60px; height: 100%;
    }}
    .conector-c14 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-c14 svg {{
        position: absolute; top: 0; left: 54%; width: 60px; height: 100%;
    }}
    .conector-b13 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-b13 svg {{
        position: absolute; top: 0; right: 54%; width: 60px; height: 100%;
    }}
    .conector-b14 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-b14 svg {{
        position: absolute; top: 0; right: 54%; width: 60px; height: 100%;
    }}
    .conector-d13 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;
    }}
    .conector-d13 svg {{
        position: absolute; top: 0; right: 54%; width: 60px; height: 100%;
    }}
    .conector-d14 {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; 
    }}
    .conector-d14 svg {{
        position: absolute; top: 0; right: 54%; width: 60px; height: 100%; 
    }}

    /* Conectores verticales dentro de columnas */
    .conector-a13-a14 {{
        position: absolute; top: 54px; left: 50%; width: 2px; height: 68px;
        background-color: white; pointer-events: none; z-index: 0;
    }}
    .conector-c13-c14 {{
        position: absolute; top: 54px; left: 50%; width: 2px; height: 68px;
        background-color: white; pointer-events: none; z-index: 0;
    }}
    .conector-b13-b14 {{
        position: absolute; top: 54px; left: 50%; width: 3px; height: 68px;
        background-color: white; pointer-events: none; z-index: 0;
    }}
    .conector-d13-d14 {{
        position: absolute; top: 54px; left: 50%; width: 3px; height: 68px;
        background-color: white; pointer-events: none; z-index: 0;
    }}

    /* Horizontales hacia A15, B15, C15, D15 */
    .conector-a15-horizontal {{
        position: absolute; top: 88px; left: 50%; width: 130px; height: 3px;
        background-color: white; pointer-events: none; z-index: 0;
    }}
    .conector-c15-horizontal {{
        position: absolute; top: 88px; left: 50%; width: 130px; height: 3px;
        background-color: white; pointer-events: none; z-index: 0;
    }}
    .conector-b15-horizontal {{
        position: absolute; top: 88px; right: 50%; width: 60px; height: 3px;
        background-color: white; pointer-events: none; z-index: 0;
    }}
    .conector-d15-horizontal {{
        position: absolute; top: 88px; right: 50%; width: 60px; height: 3px;
        background-color: white; pointer-events: none; z-index: 0;
    }}

    /* LÍNEAS VERTICALES A15‑C15 y B15‑D15 */
    .conector-a15-c15 {{
        position: absolute;
        left: 90%;
        margin-left: -1px;
        width: 2px;
        top: 50%;
        transform: translateY(-50%);
        height: 415px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
    }}

    .conector-b15-d15 {{
        position: absolute;
        left: 10%;
        margin-left: -1px;
        width: 2px;
        top: 50%;
        transform: translateY(-50%);
        height: 415px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
    }}

    /* NUEVA LÍNEA HORIZONTAL DESDE EL CENTRO DE A15‑C15 HACIA S1 */
    .conector-s1-horizontal {{
        position: absolute;
        top: 387px;
        left: 90%;
        width: 100px;
        height: 2px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
        transform: translateY(-50%);
    }}
    
    .conector-s2-horizontal {{
        position: absolute;
        top: 360px;
        right: 10%;
        width: 100px;
        height: 2px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
        transform: translateX(-142%);
    }}
    
    .conector-s1-s2 {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 420px;
        height: 2px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
    }}
    
    .conector-w1-vertical {{
        position: absolute;
        bottom: 50%;
        left: 50%;
        transform: translateX(-50%);
        width: 2px;
        height: 115px;
        background-color: white;
        pointer-events: none;
        z-index: 0;
    }}
    
    /* NUEVO: INPUT DE GOLES */
    .input-goles {{
        position: absolute;
        bottom: 0px;
        left: 50%;
        transform: translateX(-50%);
        width: 32px;
        height: 20px;
        background-color: #0E1117;
        color: white;
        border: 2px solid #4CAF50;
        border-radius: 5px;
        text-align: center;
        font-size: 12px;
        font-weight: bold;
        z-index: 10;
        outline: none;
        display: none;
    }}

    .input-goles:focus {{
        border-color: #03a9f4;
        background-color: #1a1e26;
    }}

    .input-goles::-webkit-inner-spin-button, 
    .input-goles::-webkit-outer-spin-button {{
        -webkit-appearance: none; 
        margin: 0; 
    }}
    .input-goles[type=number] {{
        -moz-appearance: textfield;
    }}

    #boton-enviar {{
        display: block; margin: 20px auto; padding: 10px 20px;
        background-color: #4CAF50; color: white; border: none;
        border-radius: 5px; cursor: pointer; font-size: 16px;
    }}
    #boton-enviar:hover {{ background-color: #45a049; }}
    #mensaje-terminal {{ color: white; text-align: center; margin-top: 30px;}}
    </style>
    </head>
    <body>
    
    <div id="loader-container">
        <div class="spinner"></div>
    </div>

    
    <div id="contenedor-master">


        <!-- PANTALLA DE BIENVENIDA -->
        <div id="pantalla-bienvenida">
            <div class="contenedor-bienvenida" id="paso-1">
                <h1 style="margin-bottom: 12px; font-size: 24px;">Quiniela 90.9 // Fase 2</h1>
                <p style="color: #8b949e; font-size: 14px; margin-bottom: 25px; line-height: 1.5;">Por favor ingresa tu nombre para comenzar :)</p>
                <input type="text" id="input-nombre" placeholder="Ingresa tu nombre" autocomplete="off" style="margin-bottom: 25px; width: 100%; box-sizing: border-box;">
                <button onclick="irAPaso2()" style="width: 100%;">SIGUIENTE</button>
            </div>
            <div class="contenedor-bienvenida" id="paso-2" style="display: none; opacity: 0;">
                <h1 style="margin-bottom: 12px; font-size: 24px;">Instrucciones</h1>
                <ul style="color: #8b949e; font-size: 14px; margin-bottom: 25px; line-height: 1.6; text-align: left; padding-left: 20px;">
                    <li><strong></strong> Selecciona los equipos ganadores haciendo clic en los espacios vacíos de cada llave.</li>
                    <li><strong></strong> Una vez elegida la bandera, ingresa los goles del equipo en el recuadro que aparecerá debajo.</li>
                    <li><strong></strong> Continúa este proceso hasta llegar al recuadro central del Campeón.</li>
                    <li><strong></strong> Importante: Sigue las llaves correctamente.</li>
                    <li><strong></strong> Al finalizar, haz clic en el botón verde "LISTO!!".</li>
                </ul>
                <button onclick="iniciarApp()" style="width: 100%;">COMENZAR</button>
            </div>
        </div>

        <div id="layout-principal">
            <div class="lado-izquierdo">
                <div class="grupo-superior-izquierdo">
                    <div class="columna"> {html_izquierda_1} </div>
                    <div class="vs-separator"><span class="vs-texto">VS</span></div>
                    <div class="columna"> {html_izquierda_2} </div>
                    <div class="columna"> {html_izquierda_3} </div>
                    <div class="conector-a13">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="0" y1="70" x2="55" y2="70" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="conector-a14">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="0" y1="220" x2="55" y2="220" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="columna-desalineada">
                        {html_a13}
                        <div class="conector-a13-a14"></div>
                        <div class="conector-a15-horizontal"></div>
                        <div class="espaciador-a14"> {html_a14} </div>
                    </div>
                    <div class="columna-a15"> {html_a15} </div>
                </div>
                <div class="conector-a15-c15"></div>
                <div class="conector-s1-horizontal"></div>
                <div class="grupo-inferior-izquierdo">
                    <div class="columna"> {html_izquierda_4} </div>
                    <div class="vs-separator"><span class="vs-texto">VS</span></div>
                    <div class="columna"> {html_izquierda_5} </div>
                    <div class="columna"> {html_izquierda_6} </div>
                    <div class="conector-c13">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="0" y1="70" x2="55" y2="70" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="conector-c14">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="0" y1="220" x2="55" y2="220" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="columna-desalineada">
                        {html_c13}
                        <div class="conector-c13-c14"></div>
                        <div class="conector-c15-horizontal"></div>
                        <div class="espaciador-a14"> {html_c14} </div>
                    </div>
                    <div class="columna-c15"> {html_c15} </div>
                </div>
            </div>
            
            <div class="conector-s1-s2"></div>
            <div class="conector-w1-vertical"></div>

            <div class="columna-s1"> {html_s1} </div>
            <div class="columna-w1"> {html_w1} </div>
            <div class="columna-s2"> {html_s2} </div>

            <div class="lado-derecho">
                <div class="grupo-superior-derecho">
                    <div class="columna-b15"> {html_b15} </div>
                    <div class="columna-derecha-desalineada">
                        {html_b13}
                        <div class="conector-b13-b14"></div>
                        <div class="conector-b15-horizontal"></div>
                        <div class="conector-s2-horizontal"></div>
                        <div class="espaciador-a14"> {html_b14} </div>
                    </div>
                    <div class="conector-b13">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="55" y1="70" x2="0" y2="70" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="conector-b14">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="55" y1="220" x2="0" y2="220" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="columna-derecha"> {html_derecha_3} </div>
                    <div class="columna-derecha"> {html_derecha_2} </div>
                    <div class="vs-separator"><span class="vs-texto">VS</span></div>
                    <div class="columna-derecha"> {html_derecha_1} </div>
                </div>
                <div class="conector-b15-d15"></div>
                <div class="grupo-inferior-derecho">
                    <div class="columna-d15"> {html_d15} </div>
                    <div class="columna-derecha-desalineada">
                        {html_d13}
                        <div class="conector-d13-d14"></div>
                        <div class="conector-d15-horizontal"></div>
                        <div class="espaciador-a14"> {html_d14} </div>
                    </div>
                    <div class="conector-d13">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="55" y1="70" x2="0" y2="70" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="conector-d14">
                        <svg viewBox="0 0 55 300" preserveAspectRatio="none">
                            <line x1="55" y1="220" x2="0" y2="220" stroke="white" stroke-width="2" />
                        </svg>
                    </div>
                    <div class="columna-derecha"> {html_derecha_6} </div>
                    <div class="columna-derecha"> {html_derecha_5} </div>
                    <div class="vs-separator"><span class="vs-texto">VS</span></div>
                    <div class="columna-derecha"> {html_derecha_4} </div>
                </div>
            </div>
        </div>

        <button id="boton-enviar" onclick="enviarDatos()">LISTO!!</button>
        <div class="mensaje-exito" id="mensaje-exito">¡Datos enviados correctamente!</div>
        <div id="mensaje-terminal"></div>

    </div>
    <script>
    var datosRectangulos = {{}};
    var HERENCIA_FIJA = {herencia_fija_js};
    var HERENCIA_CONEXIONES = {herencia_conexiones_js};
    var BANDERAS_DISPONIBLES = {banderas_disponibles_js};
    var datosGoles = {{}};
    var nombreParticipante = "";
    var datosEnviados = false;

    var NOMBRES_PAISES = {{
        "de.svg": "Alemania", "gb-sct.svg": "Escocia", "no.svg": "Noruega",
        "se.svg": "Suecia", "kr.svg": "Corea del Sur", "ch.svg": "Suiza",
        "nl.svg": "Países Bajos", "ma.svg": "Marruecos", "br.svg": "Brasil",
        "jp.svg": "Japón", "ci.svg": "Costa de Marfil", "fr.svg": "Francia",
        "mx.svg": "México", "cv.svg": "Cabo Verde", "gb-eng.svg": "Inglaterra",
        "pt.svg": "Portugal", "cd.svg": "RD Congo", "gh.svg": "Ghana",
        "es.svg": "España", "at.svg": "Austria", "us.svg": "Estados Unidos",
        "ec.svg": "Ecuador", "eg.svg": "Egipto", "cz.svg": "República Checa",
        "ar.svg": "Argentina", "uy.svg": "Uruguay", "au.svg": "Australia",
        "ir.svg": "Irán", "ca.svg": "Canadá", "be.svg": "Bélgica",
        "py.svg": "Paraguay", "sn.svg": "Senegal", "pl.svg": "Polonia",
        "za.svg": "Sudáfrica", "dk.svg": "Dinamarca", "tn.svg": "Túnez",
        "ba.svg": "Bosnia y Herzegovina",
        "co.svg": "Colombia", "hr.svg": "Croacia"
    }};

    for (var clave in HERENCIA_FIJA) {{
        datosRectangulos[clave] = HERENCIA_FIJA[clave];
    }}
    
    // Lógica para ocultar el loader cuando la página cargue totalmente
    setTimeout(function() {{
        var loader = document.getElementById('loader-container');
        if (loader) {{
            loader.style.opacity = '0';
            setTimeout(function() {{
                loader.style.display = 'none';
            }}, 500);
        }}
    }}, 1000);

    // Prevenir recarga accidental
    window.addEventListener('beforeunload', function(e) {{
        if (datosEnviados) {{
            return;
        }}
        
        var hayDatos = false;
        for (var clave in datosRectangulos) {{
            if (!HERENCIA_FIJA.hasOwnProperty(clave)) {{
                hayDatos = true;
                break;
            }}
        }}
        
        if (hayDatos && !datosEnviados) {{
            e.preventDefault();
            e.returnValue = 'Tienes datos sin guardar. ¿Estás seguro de que quieres salir?';
            return e.returnValue;
        }}
    }});

    function irAPaso2() {{
        var input = document.getElementById('input-nombre');
        var nombre = input.value.trim();
        
        if (nombre === "") {{
            alert("Por favor escribe tu nombre antes de continuar.");
            return;
        }}
        
        nombreParticipante = nombre;

        var paso1 = document.getElementById('paso-1');
        paso1.style.opacity = '0';

        setTimeout(function() {{
            paso1.style.display = 'none';
            
            var paso2 = document.getElementById('paso-2');
            paso2.style.display = 'block';
            
            setTimeout(function() {{
                paso2.style.opacity = '1';
            }}, 50);
        }}, 500);
    }}

    function iniciarApp() {{
        document.getElementById('pantalla-bienvenida').classList.add('oculta');
        console.log("Participante: " + nombreParticipante);
    }}

    (function() {{
        var clavesFijas = Object.keys(HERENCIA_FIJA);
        clavesFijas.forEach(function(clave) {{
            var input = document.getElementById('goles-' + clave);
            if (input) {{
                input.style.display = 'block';
            }}
        }});
    }})();

    function mostrarMenu(event, rectanguloId) {{
        if (datosEnviados) return;
        
        var menu = document.getElementById('menu-' + rectanguloId);
        if (!menu) return;
        var container = menu.parentElement;
        var rectangulo = container.querySelector('.rectangulo-pulse');
        var clave = rectangulo.getAttribute('data-key');
        var bloqueado = rectangulo.getAttribute('data-bloqueado');
        
        if (bloqueado === 'true' || HERENCIA_FIJA.hasOwnProperty(clave)) {{
            return;
        }}

        // Lógica optimizada: Solo dibujamos las banderas necesarias
        var banderasParaMostrar = [];
        
        if (HERENCIA_CONEXIONES.hasOwnProperty(clave)) {{
            var padres = HERENCIA_CONEXIONES[clave];
            var banderasPermitidas = [];
            for (var p = 0; p < padres.length; p++) {{
                var banderaPadre = datosRectangulos[padres[p]];
                if (banderaPadre && banderasPermitidas.indexOf(banderaPadre) === -1) {{
                    banderasPermitidas.push(banderaPadre);
                }}
            }}
            for (var b = 0; b < BANDERAS_DISPONIBLES.length; b++) {{
                if (banderasPermitidas.indexOf(BANDERAS_DISPONIBLES[b].nombre) !== -1) {{
                    banderasParaMostrar.push(BANDERAS_DISPONIBLES[b]);
                }}
            }}
        }} else {{
            banderasParaMostrar = BANDERAS_DISPONIBLES; // Nodos iniciales libres
        }}

        // Construir el menú dinámicamente SOLO si está vacío
        if (menu.innerHTML.trim() === '') {{
            for (var i = 0; i < banderasParaMostrar.length; i++) {{
                var img = document.createElement('img');
                img.src = banderasParaMostrar[i].src;
                img.setAttribute('data-nombre', banderasParaMostrar[i].nombre);
                img.onclick = function() {{ seleccionarBandera(this, this.src); }};
                menu.appendChild(img);
            }}
        }}

        event.stopPropagation();
        var menus = document.getElementsByClassName('menu-banderas');
        for (var i = 0; i < menus.length; i++) {{
            if (menus[i].id !== 'menu-' + rectanguloId) menus[i].style.display = 'none';
        }}
        menu.style.display = (menu.style.display === 'block') ? 'none' : 'block';
    }}

    function seleccionarBandera(imgElement, banderaSrc) {{
        // No permitir interacción si ya se enviaron los datos
        if (datosEnviados) {{
            return;
        }}
        
        var menu = imgElement.parentElement;
        var container = menu.parentElement;
        var rectangulo = container.querySelector('.rectangulo-pulse');
        var clave = rectangulo.getAttribute('data-key');
        if (HERENCIA_FIJA.hasOwnProperty(clave)) {{
            console.log("No se puede modificar " + clave);
            menu.style.display = 'none';
            return;
        }}
        var claveSpan = rectangulo.querySelector('.clave-texto');
        var claveTexto = claveSpan ? claveSpan.textContent : clave;
        rectangulo.innerHTML = '<img src="' + banderaSrc + '" class="bandera-seleccionada">';
        var claveSpanNuevo = document.createElement('span');
        claveSpanNuevo.className = 'clave-texto';
        claveSpanNuevo.textContent = claveTexto;
        rectangulo.appendChild(claveSpanNuevo);
        menu.style.display = 'none';
        var nombreBandera = imgElement.getAttribute('data-nombre');
        datosRectangulos[clave] = nombreBandera;
        
        var inputGoles = container.querySelector('.input-goles');
        if (inputGoles) {{
            inputGoles.style.display = 'block';
            inputGoles.value = '';
            datosGoles[clave] = '';
        }}
        console.log("Bandera actualizada | Clave: " + clave + " | Bandera: " + nombreBandera);
    }}
    
        function obtenerISO8601CDMX() {{
        var d = new Date();
        var y = d.getUTCFullYear();
        var m = d.getUTCMonth();      // 0-11
        var dia = d.getUTCDate();
        var h = d.getUTCHours();
        var min = d.getUTCMinutes();
        var s = d.getUTCSeconds();
        var ms = d.getUTCMilliseconds();
        // Restar 6 horas para CDMX (UTC-6, sin horario de verano)
        h -= 6;
        if (h < 0) {{
            h += 24;
            dia--;
            if (dia < 1) {{
                m--;
                if (m < 0) {{
                    m = 11;
                    y--;
                }}
                var diasMes = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
                dia = diasMes;
            }}
        }}
        var pad = function(n) {{ return n < 10 ? '0' + n : '' + n; }};
        var padMs = function(n) {{
            if (n < 10) return '00' + n;
            if (n < 100) return '0' + n;
            return '' + n;
        }};
        return y + '-' + pad(m + 1) + '-' + pad(dia) + 'T' +
               pad(h) + ':' + pad(min) + ':' + pad(s) + '.' + padMs(ms);
    }}
    

    async function enviarDatos() {{
        // Verificar si ya se enviaron los datos
        if (datosEnviados) {{
            alert("Los datos ya fueron enviados. No es posible enviarlos nuevamente.");
            return;
        }}
        
        var boton = document.getElementById('boton-enviar');
        var mensajeExito = document.getElementById('mensaje-exito');
        
        // Deshabilitar el botón inmediatamente
        boton.disabled = true;
        boton.classList.add('cargando');
        boton.textContent = 'Enviando...';
        
        var filas = [];
        for (var clave in datosRectangulos) {{
            var nombreArchivo = datosRectangulos[clave];
            var pais = NOMBRES_PAISES[nombreArchivo] || nombreArchivo;
            var goles = datosGoles[clave];
            var golesInt = (goles !== undefined && goles !== "") ? parseInt(goles) : null;
            filas.push({{
                nombre: nombreParticipante,
                celda: clave,
                pais: pais,
                goles: golesInt,
                created_at: obtenerISO8601CDMX()
            }});
        }}

        console.log("Enviando a Supabase...");
        console.log(JSON.stringify(filas, null, 2));

        var SUPABASE_URL = "{st.secrets['SUPABASE_URL']}";
        var SUPABASE_ANON_KEY = "{st.secrets['SUPABASE_KEY']}";

        try {{
            var response = await fetch(SUPABASE_URL + "/rest/v1/Quiniela_Fase2", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json",
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": "Bearer " + SUPABASE_ANON_KEY,
                    "Prefer": "return=minimal"
                }},
                body: JSON.stringify(filas)
            }});

            if (response.ok) {{
                // Marcar como enviado
                datosEnviados = true;
                
                // Ocultar el botón
                boton.style.display = 'none';
                
                // Mostrar mensaje de éxito
                mensajeExito.style.display = 'block';
                
                document.getElementById('mensaje-terminal').textContent = 
                    "Registros guardados para " + nombreParticipante;
                    
                // Deshabilitar la interacción con los rectángulos
                deshabilitarInteraccion();
                
                console.log("Datos enviados exitosamente");
            }} else {{
                // Si hay error, rehabilitar el botón
                boton.disabled = false;
                boton.classList.remove('cargando');
                boton.textContent = 'LISTO!!';
                
                var error = await response.text();
                console.error("Error Supabase:", error);
                alert("Error al guardar los datos. Revisa conexión o intenta nuevamente.");
            }}
        }} catch (err) {{
            // Si hay error de red, rehabilitar el botón
            boton.disabled = false;
            boton.classList.remove('cargando');
            boton.textContent = 'LISTO!!';
            
            console.error("Error de red:", err);
            alert("No se pudo conectar a la base de datos.");
        }}
    }}
    
    // Función para deshabilitar la interacción después del envío
    function deshabilitarInteraccion() {{
        // Deshabilitar todos los rectángulos
        var rectangulos = document.querySelectorAll('.rectangulo-pulse');
        rectangulos.forEach(function(rect) {{
            rect.style.pointerEvents = 'none';
            rect.style.opacity = '0.7';
        }});
        
        // Deshabilitar todos los inputs de goles
        var inputs = document.querySelectorAll('.input-goles');
        inputs.forEach(function(input) {{
            input.disabled = true;
            input.style.opacity = '0.7';
        }});
        
        // Ocultar todos los menús de banderas
        var menus = document.querySelectorAll('.menu-banderas');
        menus.forEach(function(menu) {{
            menu.style.display = 'none';
        }});
    }}
    
    function guardarGoles(inputElement) {{
        // No permitir modificar goles si ya se enviaron los datos
        if (datosEnviados) {{
            inputElement.value = datosGoles[inputElement.getAttribute('data-key')] || '';
            return;
        }}
        
        var clave = inputElement.getAttribute('data-key');
        var goles = inputElement.value;
        datosGoles[clave] = goles;
        console.log("Goles actualizados | Clave: " + clave + " | Goles: " + goles);
    }}

    document.addEventListener('click', function(event) {{
        var menus = document.getElementsByClassName('menu-banderas');
        for (var i = 0; i < menus.length; i++) {{
            if (!menus[i].contains(event.target)) {{
                var rectanguloContainer = menus[i].parentElement;
                var rectangulo = rectanguloContainer.querySelector('.rectangulo-pulse');
                if (rectangulo && !rectangulo.contains(event.target)) menus[i].style.display = 'none';
            }}
        }}
    }});
    </script>
    </body>
    </html>
    """

    st.components.v1.html(html_completo, height=900, scrolling=True)

if __name__ == "__main__":
    main()