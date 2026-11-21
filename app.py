import uuid
import requests
import streamlit as st
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

st.set_page_config(page_title="Analizador de reseñas", page_icon="📝")

@st.cache_resource
def get_language_client():
    """Crea el cliente de Language una sola vez y lo reutiliza."""
    return TextAnalyticsClient(
        endpoint=st.secrets["LANGUAGE_ENDPOINT"],
        credential=AzureKeyCredential(st.secrets["LANGUAGE_KEY"]),
    )


def analizar_sentimiento(texto):
    """Servicio 1: Azure AI Language. Devuelve la etiqueta y los puntajes."""
    client = get_language_client()
    resultado = client.analyze_sentiment([texto], language="es")[0]
    if resultado.is_error:
        raise Exception(resultado.error.message)
    return resultado.sentiment, resultado.confidence_scores


def traducir_a_ingles(texto):
    """Servicio 2: Azure Translator. Devuelve el texto en inglés."""
    url = "https://api.cognitive.microsofttranslator.com/translate"
    params = {"api-version": "3.0", "from": "es", "to": ["en"]}
    headers = {
        "Ocp-Apim-Subscription-Key": st.secrets["TRANSLATOR_KEY"],
        "Ocp-Apim-Subscription-Region": st.secrets["TRANSLATOR_REGION"],
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }
    cuerpo = [{"text": texto}]
    respuesta = requests.post(url, params=params, headers=headers, json=cuerpo, timeout=15)
    respuesta.raise_for_status()
    return respuesta.json()[0]["translations"][0]["text"]

ETIQUETAS = {
    "positive": ("Positivo", "😊"),
    "neutral": ("Neutral", "😐"),
    "negative": ("Negativo", "😞"),
    "mixed": ("Mixto", "🤔"),
}

st.title("📝 Analizador de reseñas")
st.write("Escribe una reseña en español. La app detecta el sentimiento "
         "con **Azure AI Language** y la traduce al inglés con **Azure Translator**.")

texto = st.text_area("Reseña:", height=150, max_chars=1000,
                     placeholder="Ej: La atención fue excelente, pero los precios son muy altos.")

if st.button("Analizar", type="primary"):
    if not texto.strip():
        st.warning("Escribe una reseña antes de analizar.")
    else:
        try:
            with st.spinner("Consultando los servicios de Azure..."):
                sentimiento, puntajes = analizar_sentimiento(texto)
                traduccion = traducir_a_ingles(texto)

            nombre, emoji = ETIQUETAS[sentimiento]
            st.subheader(f"{emoji} Sentimiento: {nombre}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Positivo", f"{puntajes.positive:.0%}")
            col2.metric("Neutral", f"{puntajes.neutral:.0%}")
            col3.metric("Negativo", f"{puntajes.negative:.0%}")

            st.subheader("🌎 Traducción al inglés")
            st.success(traduccion)

        except Exception as e:
            st.error(f"No se pudo completar el análisis: {e}")
