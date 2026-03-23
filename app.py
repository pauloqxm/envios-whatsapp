import re
import requests
import streamlit as st

st.set_page_config(
    page_title="Envio de WhatsApp",
    page_icon="📲",
    layout="centered"
)

API_URL = "https://wasenderapi.com/api/send-message"

try:
    API_TOKEN = st.secrets["WASENDER_TOKEN"]
except Exception:
    API_TOKEN = ""

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
    """
    Converte o número para o formato internacional do Brasil.
    Exemplos aceitos:
    88999999999
    88 99999-9999
    (88) 99999-9999
    +55 88 99999-9999
    5588999999999

    Retorno:
    +5588999999999
    """
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
    """
    Valida números brasileiros em formato internacional.
    Exemplo válido:
    +5588999999999
    +558833333333
    """
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
st.write("Envie mensagens personalizadas para números do Brasil com prefixo +55 automático.")

if not API_TOKEN:
    st.warning("Configure o token da API em `st.secrets['WASENDER_TOKEN']` antes de enviar mensagens.")

nome = st.text_input(
    "Nome",
    key="nome",
    placeholder="Ex: Maria"
)

numero_digitado = st.text_input(
    "Número do WhatsApp",
    key="numero",
    placeholder="Ex: 88 99999-9999"
)

mensagem_base = st.text_area(
    "Mensagem",
    key="mensagem_base",
    placeholder="Digite sua mensagem aqui...",
    height=180
)

numero_formatado = normalizar_numero_br(numero_digitado)
mensagem_final = montar_mensagem(nome, mensagem_base)

st.subheader("Prévia")

col_a, col_b = st.columns(2)

with col_a:
    st.text_input(
        "Número formatado",
        value=numero_formatado if numero_formatado else "",
        disabled=True
    )

with col_b:
    status_numero = "Válido" if validar_numero_br(numero_formatado) else "Aguardando número válido"
    st.text_input(
        "Status do número",
        value=status_numero,
        disabled=True
    )

st.text_area(
    "Mensagem final",
    value=mensagem_final if mensagem_final else "",
    height=160,
    disabled=True
)

col1, col2 = st.columns(2)

with col1:
    enviar = st.button("🚀 Enviar mensagem", use_container_width=True)

with col2:
    limpar = st.button("🧹 Limpar campos", use_container_width=True)

if limpar:
    limpar_campos()
    st.rerun()

if enviar:
    if not nome.strip():
        st.error("Informe o nome.")
    elif not numero_digitado.strip():
        st.error("Informe o número do WhatsApp.")
    elif not mensagem_base.strip():
        st.error("Digite a mensagem.")
    elif not API_TOKEN:
        st.error("Token da API não configurado.")
    elif not numero_formatado:
        st.error("Não foi possível formatar o número. Digite um telefone brasileiro válido.")
    elif not validar_numero_br(numero_formatado):
        st.error("Número inválido. Use um telefone do Brasil com DDD.")
    else:
        with st.spinner("Enviando mensagem..."):
            try:
                resposta = enviar_mensagem(numero_formatado, mensagem_final)

                if resposta.status_code in (200, 201):
                    st.success(f"Mensagem enviada com sucesso para {numero_formatado}.")
                    try:
                        retorno = resposta.json()
                        st.json(retorno)
                    except Exception:
                        st.write(resposta.text)
                else:
                    st.error(f"Erro ao enviar. Status HTTP: {resposta.status_code}")
                    try:
                        st.json(resposta.json())
                    except Exception:
                        st.write(resposta.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão com a API: {e}")
