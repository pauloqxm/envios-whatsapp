import streamlit as st
import requests

st.set_page_config(
    page_title="Envio de WhatsApp",
    page_icon="📲",
    layout="centered"
)

API_URL = "https://wasenderapi.com/api/send-message"

# Token no secrets
try:
    API_TOKEN = st.secrets["WASENDER_TOKEN"]
except Exception:
    API_TOKEN = ""

st.title("📲 Disparo de Mensagens WhatsApp")
st.write("Envie mensagens personalizadas com nome.")

# CAMPOS
nome = st.text_input(
    "Nome da pessoa",
    placeholder="Ex: João"
)

numero = st.text_input(
    "Número do WhatsApp",
    placeholder="+5588999999999"
)

mensagem_base = st.text_area(
    "Mensagem",
    placeholder="Digite a mensagem base...",
    height=150
)

# PREVIEW
if nome and mensagem_base:
    mensagem_final = f"Olá {nome}, {mensagem_base}"
else:
    mensagem_final = mensagem_base

st.subheader("📩 Prévia da mensagem")
st.info(mensagem_final if mensagem_final else "Digite os dados para ver a mensagem...")

def enviar_mensagem(numero_destino: str, texto: str):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": numero_destino,
        "text": texto
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    return response

# BOTÕES
col1, col2 = st.columns(2)

with col1:
    enviar = st.button("🚀 Enviar", use_container_width=True)

with col2:
    limpar = st.button("🧹 Limpar", use_container_width=True)

# AÇÕES
if limpar:
    st.rerun()

if enviar:
    if not nome.strip():
        st.error("Informe o nome.")
    elif not numero.strip():
        st.error("Informe o número.")
    elif not mensagem_base.strip():
        st.error("Digite a mensagem.")
    elif not API_TOKEN:
        st.error("Configure o token no secrets.")
    else:
        with st.spinner("Enviando..."):
            try:
                resposta = enviar_mensagem(numero.strip(), mensagem_final.strip())

                if resposta.status_code in [200, 201]:
                    st.success("Mensagem enviada com sucesso.")
                else:
                    st.error(f"Erro: {resposta.status_code}")
                    try:
                        st.json(resposta.json())
                    except:
                        st.write(resposta.text)

            except Exception as e:
                st.error(f"Erro de conexão: {e}")