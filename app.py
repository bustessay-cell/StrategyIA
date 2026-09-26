import time
import yfinance as yf
import streamlit as st
from google import genai

st.set_page_config(page_title="StrategyIA", page_icon="🤖", layout="centered")

st.title("🤖 StrategyIA - Asistente Estratégico de Inversión")
st.markdown("Selecciona una empresa y el enfoque estratégico deseado:")

# Configurar API Key de forma segura (lee de Streamlit Secrets o pide introducirla)
api_key = None
try:
    api_key = st.secrets["StrategyIA"]
except Exception:
    pass

if not api_key:
    api_key = st.sidebar.text_input("Introduce tu Gemini API Key", type="password")

# --- AVISO LEGAL / DISCLAIMER ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚠️ Aviso Legal")
st.sidebar.markdown(
    "**StrategyIA** es una herramienta experimental de análisis automatizado con fines "
    "exclusivamente **educativos e informativos**. Los informes y tesis generadas "
    "**no constituyen asesoramiento financiero, recomendación formal de inversión "
    "ni una invitación a la compra o venta** de activos financieros. Consulte con un "
    "profesional certificado antes de realizar cualquier inversión."
)

# Elementos de la interfaz web
ticker = st.text_input("Ticker de la empresa (Ej: AAPL, TSLA, DDOG):", "").strip().upper()

opcion = st.selectbox(
    "Tipo de Análisis:",
    [
        ("1. Valoración y Precio Justo (Margen de seguridad y PER)", "1"),
        ("2. Crecimiento y Matriz BCG (¿Es negocio Estrella / Star?)", "2"),
        ("3. Ventajas Competitivas (Moat) y Riesgos a largo plazo", "3"),
        ("4. Tesis Táctica Completa (Comprar / Mantener / Vender)", "4")
    ],
    format_func=lambda x: x[0]
)[1]

if st.button("Generar Informe StrategyIA", type="primary"):
    if not api_key:
        st.error("⚠️ Por favor, introduce tu Gemini API Key (en la barra lateral o en los secrets).")
    elif not ticker:
        st.warning("⚠️ Por favor, introduce un ticker válido.")
    else:
        with st.spinner(f"Analizando estrategia y mercado para {ticker}..."):
            
            def obtener_datos_financieros(ticker_simbolo, reintentos=3):
                for intento in range(reintentos):
                    try:
                        stock = yf.Ticker(ticker_simbolo)
                        info = stock.info
                        datos_utiles = {
                            "Nombre": info.get("longName", "Desconocido"),
                            "Sector": info.get("sector", "Desconocido"),
                            "Industria": info.get("industry", "Desconocido"),
                            "Precio Actual": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                            "PER (P/E Ratio)": info.get("trailingPE", "N/A"),
                            "Capitalización de Mercado": info.get("marketCap", "N/A"),
                            "Margen de Beneficio": info.get("profitMargins", "N/A"),
                            "Crecimiento de Ingresos": info.get("revenueGrowth", "N/A")
                        }
                        if datos_utiles["Nombre"] != "Desconocido":
                            return datos_utiles
                    except Exception:
                        if intento < reintentos - 1:
                            time.sleep(1.5)
                            continue
                        else:
                            return None
                return None

            datos = obtener_datos_financieros(ticker)
            
            if not datos or datos["Nombre"] == "Desconocido":
                st.error(f"⚠️ No se pudieron obtener datos válidos para el ticker '{ticker}'. Comprueba que esté bien escrito.")
            else:
                client = genai.Client(api_key=api_key)
                preguntas_map = {
                    "1": "Analiza si su precio actual ofrece un buen margen de seguridad, desglosando su PER y justificando su capitalización actual.",
                    "2": "Evalúa a fondo su perfil de crecimiento puro y si cumple los requisitos para ser considerada un negocio 'Estrella' (Star) en su sector.",
                    "3": "¿Cuáles son las principales barreras de entrada o ventajas competitivas (moat) que la protegen y qué riesgos sectoriales amenazan su futuro?",
                    "4": "Haz una valoración de contexto sobre su posición de mercado (enfoque analítico de compra, mantenimiento o venta teórico) basada estrictamente en sus fundamentales y perspectivas de negocio actuales."
                }
                pregunta_usuario = preguntas_map.get(opcion)
                
                contexto = f"""
                Eres un analista financiero y estratega de negocios senior en StrategyIA. 
                Vas a realizar un análisis profundo de la empresa {datos['Nombre']} ({ticker}):
                - Sector e Industria: {datos['Sector']} / {datos['Industria']}
                - Precio Actual: {datos['Precio Actual']}
                - Ratio P/E (PER): {datos['PER (P/E Ratio)']}
                - Capitalización de Mercado: {datos['Capitalización de Mercado']}
                - Margen de Beneficio: {datos['Margen de Beneficio']}
                - Crecimiento de Ingresos (Revenue Growth): {datos['Crecimiento de Ingresos']}
                
                Responde a la petición del usuario estructurando tu análisis bajo los siguientes pilares clave:
                1. **Perfil de Inversión de Crecimiento (Growth) y Matriz BCG:** Evalúa si es una acción de crecimiento y si encaja como negocio 'Estrella' (Star).
                2. **Valoración y Aspectos Estratégicos:** Ventajas competitivas, drivers de valor y riesgos sectoriales.
                
                Enfoque / Petición específica del usuario: {pregunta_usuario}
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash', 
                        contents=contexto,
                    )
                    st.success(f"--- INFORME ESTRATÉGICO DE STRATEGYIA PARA: {ticker} ---")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"⚠️ Error al conectar con Gemini: {e}")
