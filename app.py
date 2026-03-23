import json
import os
import re
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

import requests
import streamlit as st

st.set_page_config(
    page_title="Envio de WhatsApp",
    page_icon="📲",
    layout="centered"
)

API_URL = "https://wasenderapi.com/api/send-message"
API_TOKEN = os.getenv("WASENDER_API_TOKEN", "") or st.secrets.get("WASENDER_API_TOKEN", "")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORICO_ARQUIVO = os.path.join(BASE_DIR, "historico_envios.json")
if ZoneInfo is not None:
    BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
else:
    BRASILIA_TZ = timezone(timedelta(hours=-3))

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

if "limpar_apos_envio_ok" not in st.session_state:
    st.session_state.limpar_apos_envio_ok = False

if "notificacao_envio" not in st.session_state:
    st.session_state.notificacao_envio = None


def agora_formatado():
    return datetime.now(BRASILIA_TZ).strftime("%d/%m/%Y %H:%M:%S")


def limpar_campos():
    st.session_state.nome = ""
    st.session_state.numero = ""
    st.session_state.mensagem_base = ""
    st.session_state.mensagem_escolhida = "Selecione uma mensagem pronta"


def aplicar_mensagem_pronta():
    opcao = st.session_state.mensagem_escolhida
    st.session_state.mensagem_base = MENSAGENS_PRONTAS.get(opcao, "")


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
    # DDD válido (11-99) + número fixo (8 dígitos começando de 2-5) ou móvel (9 dígitos começando em 9)
    return bool(re.match(r"^\+55([1-9][1-9])(9\d{8}|[2-5]\d{7})$", numero_formatado))


def montar_mensagem(nome: str, mensagem_base: str) -> str:
    nome = nome.strip()
    mensagem_base = mensagem_base.strip()

    if nome and mensagem_base:
        return f"Olá, {nome}.\n\n{mensagem_base}"

    return mensagem_base


def enviar_mensagem(numero_destino: str, texto: str):
    if not API_TOKEN:
        raise RuntimeError(
            "Token da API não configurado. Defina WASENDER_API_TOKEN no ambiente "
            "ou em .streamlit/secrets.toml."
        )

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


def carregar_historico():
    if not os.path.exists(HISTORICO_ARQUIVO):
        return []

    try:
        with open(HISTORICO_ARQUIVO, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, list) else []
    except (json.JSONDecodeError, OSError) as e:
        st.warning(f"Não foi possível carregar o histórico ({e}). Um novo histórico será iniciado.")
        return []


def salvar_historico(historico):
    try:
        with open(HISTORICO_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise RuntimeError(f"Não foi possível salvar o histórico: {e}") from e


def registrar_envio(nome, numero, mensagem, status_api):
    historico = carregar_historico()

    historico.insert(0, {
        "data_hora": agora_formatado(),
        "nome": nome,
        "telefone": numero,
        "status": status_api,
        "mensagem": mensagem
    })

    try:
        salvar_historico(historico)
    except RuntimeError as e:
        st.warning(str(e))


def limpar_historico():
    try:
        salvar_historico([])
        return True
    except RuntimeError as e:
        st.error(str(e))
        return False


if st.session_state.limpar_apos_envio_ok:
    limpar_campos()
    st.session_state.limpar_apos_envio_ok = False

numero_formatado = normalizar_numero_br(st.session_state.numero)
mensagem_final = montar_mensagem(st.session_state.nome, st.session_state.mensagem_base)
status_texto = status_numero_texto(numero_formatado)
status_ok = validar_numero_br(numero_formatado)
historico_envios = carregar_historico()

st.title("📲 Envio de WhatsApp")
with st.container(border=True):
    st.subheader("Comunicação rápida e organizada")
    st.caption("Digite o nome, o telefone e escolha uma mensagem pronta ou escreva manualmente.")

if st.session_state.notificacao_envio:
    notif = st.session_state.notificacao_envio
    if notif.get("tipo") == "success":
        st.success(notif.get("mensagem", "Mensagem enviada com sucesso."))
    elif notif.get("tipo") == "info":
        st.info(notif.get("mensagem", "Envio concluído."))
    elif notif.get("tipo") == "warning":
        st.warning(notif.get("mensagem", "Envio concluído com observações."))
    st.session_state.notificacao_envio = None

with st.container(border=True):
    st.markdown("### Dados do envio")

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

with st.container(border=True):
    st.markdown("### Prévia do envio")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Número formatado", numero_formatado if numero_formatado else "Não informado")

    with col2:
        st.metric("Status", status_texto)

    preview_segura = mensagem_final if mensagem_final else "A mensagem aparecerá aqui."
    st.text_area(
        "Mensagem final (somente leitura)",
        value=preview_segura,
        height=190,
        disabled=True
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        enviar = st.button("🚀 Enviar mensagem", use_container_width=True, type="primary")
    with col_btn2:
        st.button("🧹 Limpar campos", use_container_width=True, on_click=limpar_campos)

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

                try:
                    retorno = resposta.json()
                except Exception:
                    retorno = {}

                if resposta.status_code in (200, 201) and retorno.get("success") is True:
                    status_api = retorno.get("data", {}).get("status", "enviado")
                    registrar_envio(
                        nome=st.session_state.nome.strip(),
                        numero=numero_formatado,
                        mensagem=mensagem_final,
                        status_api=status_api
                    )

                    if status_api == "in_progress":
                        status_msg = "Status atual: mensagem em processamento/envio."
                    elif status_api == "sent":
                        status_msg = "Status atual: mensagem enviada."
                    else:
                        status_msg = f"Status atual: {status_api}"

                    st.session_state.notificacao_envio = {
                        "tipo": "success",
                        "mensagem": f"Mensagem enviada com sucesso para {numero_formatado}. {status_msg}"
                    }
                    st.session_state.limpar_apos_envio_ok = True
                    st.rerun()

                else:
                    msg_api = (
                        retorno.get("message")
                        or retorno.get("error")
                        or (resposta.text[:200] if resposta.text else "")
                    )
                    st.error(
                        f"Não foi possível concluir o envio (HTTP {resposta.status_code}). "
                        f"{msg_api if msg_api else 'Verifique os dados e tente novamente.'}"
                    )

            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão: {e}")
            except RuntimeError as e:
                st.error(str(e))

with st.container(border=True):
    col_hist_1, col_hist_2 = st.columns([3, 1])

    with col_hist_1:
        st.markdown("### Histórico de envios")

    with col_hist_2:
        if st.button("🗑️ Limpar histórico", use_container_width=True):
            if limpar_historico():
                st.success("Histórico limpo com sucesso.")
                st.rerun()

    if historico_envios:
        st.dataframe(
            [
                {
                    "Data/Hora": item.get("data_hora", ""),
                    "Nome": item.get("nome", ""),
                    "Telefone": item.get("telefone", ""),
                    "Status": item.get("status", "")
                }
                for item in historico_envios
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Ainda não há envios registrados.")
