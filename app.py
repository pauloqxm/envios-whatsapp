import re
import requests
import streamlit as st

st.set_page_config(
    page_title="Envio de WhatsApp",
    page_icon="📲",
    layout="centered"
)

API_URL = "https://wasenderapi.com/api/send-message"
API_TOKEN = "70f1099889818e905a405f586bf151aef6a6706c5ca531ccf81030e607de37e6"

MENSAGENS_PRONTAS = {
    "Selecione uma mensagem pronta": "",
    "Mensagem 01": """Ficamos felizes em contar com você no III Seminário “Todas as Águas”!

Vamos juntos mergulhar no tema Variabilidade Climática e Segurança Hídrica com grandes especialistas.

🗓️ Data: 31/03 – a partir das 08h30 (chegue cedo!)
📍 Local: FATEC Sertão Central (Quixeramobim)

Será um momento rico de diálogo. Aguardamos você! 🌿""",
    "Mensagem 02": """Que bom saber que você estará conosco no III Seminário “Todas as Águas”!
Vamos juntos discutir a Variabilidade Climática e Segurança Hídrica com grandes especialistas.

🗓️ Quando: 31/03, a partir das 08h30 (chegue cedo para o credenciamento!)
📍 Onde: FATEC Sertão Central (Quixeramobim)

Prepare-se para um momento rico de diálogo. Te esperamos lá! 🌿""",
    "Mensagem 03": """Que alegria saber que você fará parte do III Seminário “Todas as Águas”!
Juntos, vamos refletir sobre Variabilidade Climática e Segurança Hídrica ao lado de grandes especialistas.

🗓️ Quando: 31/03, a partir das 08h30 (chegue cedinho para o credenciamento!)
📍 Onde: FATEC Sertão Central (Quixeramobim)

Prepare-se para um momento rico de diálogo. Te esperamos lá! 🌿""",
    "Mensagem 04": """Que legal! Sua presença está confirmada no III Seminário “Todas as Águas”.
Vamos bater um papo sobre Variabilidade Climática e Segurança Hídrica com quem realmente entende do assunto.

🗓️ Quando: 31/03, a partir das 08h30 (já separa o café da manhã e vem!)
📍 Onde: FATEC Sertão Central (Quixeramobim)

Prepare-se para um encontro cheio de troca e boas ideias. Te esperamos por lá! 🌿"""
}

if "nome" not in st.session_state:
    st.session_state.nome = ""

if "numero" not in st.session_state:
    st.session_state.numero = ""

if "mensagem_base" not in st.session_state:
    st.session_state.mensagem_base = ""

if "mensagem_escolhida" not in st.session_state:
    st.session_state.mensagem_escolhida = "Selecione uma mensagem pronta"


def limpar_campos():
    st.session_state.nome = ""
    st.session_state.numero = ""
    st.session_state.mensagem_base = ""
    st.session_state.mensagem_escolhida = "Selecione uma mensagem pronta"


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
    return bool(re.match(r"^\+55\d{10,11}$", numero_formatado))


def montar_mensagem(nome: str, mensagem_base: str) -> str:
    nome = nome.strip()
    mensagem_base = mensagem_base.strip()

    if nome and mensagem_base:
        return f"Olá, {nome}.\n\n{mensagem_base}"

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


def status_numero_texto(numero_formatado: str) -> str:
    if not numero_formatado:
        return "Aguardando preenchimento"
    if validar_numero_br(numero_formatado):
        return "Número válido"
    return "Número inválido"


def aplicar_mensagem_pronta():
    opcao = st.session_state.mensagem_escolhida
    st.session_state.mensagem_base = MENSAGENS_PRONTAS.get(opcao, "")


numero_formatado = normalizar_numero_br(st.session_state.numero)
mensagem_final = montar_mensagem(st.session_state.nome, st.session_state.mensagem_base)
status_texto = status_numero_texto(numero_formatado)
status_ok = validar_numero_br(numero_formatado)

st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #0f1117 0%, #151924 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 820px;
    }

    .hero-box {
        background: linear-gradient(135deg, #16a34a 0%, #0f172a 100%);
        padding: 28px;
        border-radius: 24px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .hero-title {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 8px;
        line-height: 1.1;
    }

    .hero-subtitle {
        font-size: 15px;
        color: rgba(255,255,255,0.85);
    }

    .section-card {
        background: #111827;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 22px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 16px;
        color: #f9fafb;
    }

    .mini-card {
        background: #0b1220;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px;
        padding: 16px;
        text-align: center;
        height: 100%;
    }

    .mini-label {
        font-size: 13px;
        color: #9ca3af;
        margin-bottom: 6px;
    }

    .mini-value {
        font-size: 16px;
        font-weight: 700;
        color: #f9fafb;
        word-break: break-word;
    }

    .status-ok {
        color: #22c55e;
        font-weight: 700;
    }

    .status-bad {
        color: #f59e0b;
        font-weight: 700;
    }

    .preview-box {
        background: #0b1220;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 18px;
        min-height: 170px;
        white-space: pre-wrap;
        color: #f3f4f6;
        font-size: 15px;
        line-height: 1.6;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 14px !important;
    }

    .stButton > button {
        border-radius: 14px !important;
        font-weight: 700 !important;
        padding: 0.7rem 1rem !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-box">
    <div class="hero-title">📲 Envio de WhatsApp</div>
    <div class="hero-subtitle">
        Digite o nome, o telefone e escolha uma mensagem pronta ou escreva manualmente.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Dados do envio</div>', unsafe_allow_html=True)

st.text_input(
    "Nome",
    key="nome",
    placeholder="Ex: João Silva"
)

st.text_input(
    "Número do WhatsApp",
    key="numero",
    placeholder="Ex: 88 99999-9999"
)

st.selectbox(
    "Mensagens prontas",
    options=list(MENSAGENS_PRONTAS.keys()),
    key="mensagem_escolhida",
    on_change=aplicar_mensagem_pronta
)

st.text_area(
    "Mensagem",
    key="mensagem_base",
    placeholder="Digite sua mensagem aqui...",
    height=220
)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Prévia do envio</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="mini-card">
        <div class="mini-label">Número formatado</div>
        <div class="mini-value">{numero_formatado if numero_formatado else "Não informado"}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    classe_status = "status-ok" if status_ok else "status-bad"
    st.markdown(f"""
    <div class="mini-card">
        <div class="mini-label">Status</div>
        <div class="mini-value {classe_status}">{status_texto}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="preview-box">{mensagem_final if mensagem_final else "A mensagem aparecerá aqui."}</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    enviar = st.button("🚀 Enviar mensagem", use_container_width=True)

with col_btn2:
    limpar = st.button("🧹 Limpar campos", use_container_width=True)

if limpar:
    limpar_campos()
    st.rerun()

if enviar:
    if not st.session_state.nome.strip():
        st.error("Informe o nome.")
    elif not st.session_state.numero.strip():
        st.error("Informe o número do WhatsApp.")
    elif not st.session_state.mensagem_base.strip():
        st.error("Digite a mensagem.")
    elif not numero_formatado or not validar_numero_br(numero_formatado):
        st.error("Número inválido. Digite um telefone brasileiro com DDD.")
    else:
        with st.spinner("Enviando mensagem..."):
            try:
                resposta = enviar_mensagem(numero_formatado, mensagem_final)

                if resposta.status_code in (200, 201):
                    st.success(f"Mensagem enviada com sucesso para {numero_formatado}.")
                    try:
                        st.json(resposta.json())
                    except Exception:
                        st.write(resposta.text)
                else:
                    st.error(f"Erro ao enviar. Status: {resposta.status_code}")
                    try:
                        st.json(resposta.json())
                    except Exception:
                        st.write(resposta.text)

            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão: {e}")
