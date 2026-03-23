import re
import requests
import streamlit as st

st.set_page_config(
    page_title="Envio de WhatsApp",
    page_icon="📲",
    layout="centered"
)

API_URL = "https://wasenderapi.com/api/send-message"

# TOKEN DIRETO (uso local)
API_TOKEN = "70f1099889818e905a405f586bf151aef6a6706c5ca531ccf81030e607de37e6"


if "nome" not in st.session_state:
    st.session_state.nome = ""

if "numero" not in st.session_state:
    st.session_state.numero = ""

if "mensagem_base" not in st.session_state:
    st.session_state.mensagem_base = ""


def limpar_campos():
    st.session_state.nome = ""
    st.session_state.numero = ""
    st.session_state.mensagem_base = ""


def normalizar_numero_br(numero: str) -> str:
    numero = numero.strip()
    tem_mais = numero.startswith("+")
    digits = re.sub(r"\D", "", numero)

    if not digits:
        return ""

    if tem_mais and digits.startswith("55"):
        return f"+{digits}"

    if digits.startswith("55"):
        return f"+{digits}"

    if len(digits) in (10, 11):
        return f"+55{digits}"

    return ""


def validar_numero_br(numero_formatado: str) -> bool:
    padrao = r"^\+55\d{10,11}$"
    return bool(re.match(padrao, numero_formatado))


def montar_mensagem(nome: str, mensagem_base: str) -> str:
    nome = nome.strip()
    mensagem_base = mensagem_base.strip()

    if nome and mensagem_base:
        return f"Olá, {nome}. {mensagem_base}"

    return mensagem_base


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


st.title("📲 Envio de WhatsApp")
st.write("Envie mensagens para números do Brasil automaticamente com +55.")

nome = st.text_input("Nome", key="nome", placeholder="Ex: João")

numero_digitado = st.text_input(
    "Número do WhatsApp",
    key="numero",
    placeholder="Ex: 88 99999-9999"
)

mensagem_base = st.text_area(
    "Mensagem",
    key="mensagem_base",
    placeholder="Digite sua mensagem...",
    height=180
)

numero_formatado = normalizar_numero_br(numero_digitado)
mensagem_final = montar_mensagem(nome, mensagem_base)

st.subheader("Prévia")

col_a, col_b = st.columns(2)

with col_a:
    st.text_input("Número formatado", value=numero_formatado, disabled=True)

with col_b:
    status = "Válido" if validar_numero_br(numero_formatado) else "Inválido"
    st.text_input("Status", value=status, disabled=True)

st.text_area("Mensagem final", value=mensagem_final, height=150, disabled=True)

col1, col2 = st.columns(2)

with col1:
    enviar = st.button("🚀 Enviar", use_container_width=True)

with col2:
    limpar = st.button("🧹 Limpar", use_container_width=True)

if limpar:
    limpar_campos()
    st.rerun()

if enviar:
    if not nome.strip():
        st.error("Informe o nome.")
    elif not numero_digitado.strip():
        st.error("Informe o número.")
    elif not mensagem_base.strip():
        st.error("Digite a mensagem.")
    elif not numero_formatado or not validar_numero_br(numero_formatado):
        st.error("Número inválido.")
    else:
        with st.spinner("Enviando..."):
            try:
                resposta = enviar_mensagem(numero_formatado, mensagem_final)

                if resposta.status_code in (200, 201):
                    st.success(f"Mensagem enviada para {numero_formatado}")
                else:
                    st.error(f"Erro: {resposta.status_code}")
                    st.write(resposta.text)

            except Exception as e:
                st.error(f"Erro de conexão: {e}")
