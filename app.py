import json
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

st.set_page_config(
    page_title="Envio de WhatsApp",
    page_icon="📲",
    layout="centered"
)

API_URL = "https://wasenderapi.com/api/send-message"
API_TOKEN = os.getenv("WASENDER_API_TOKEN", "") or st.secrets.get("WASENDER_API_TOKEN", "")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORICO_ARQUIVO = os.path.join(BASE_DIR, "historico_envios.json")
ARQUIVO_CSV_PADRAO = os.path.join("/mnt/data", "nomes e contatos.csv")

if ZoneInfo is not None:
    BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
else:
    BRASILIA_TZ = timezone(timedelta(hours=-3))

MENSAGENS_INSCRICAO = {
    "Selecione uma mensagem pronta": "",
    "Mensagem 01": """Ficamos felizes em contar com você no III Seminário “Todas as Águas”!

Vamos juntos mergulhar no tema Variabilidade Climática e Segurança Hídrica com grandes especialistas.

🗓️ Data: 31/03, a partir das 08h30
📍 Local: FATEC Sertão Central (Quixeramobim)

Será um momento rico de diálogo. Aguardamos você! 🌿""",
    "Mensagem 02": """Que bom saber que você estará conosco no III Seminário “Todas as Águas”!

Vamos juntos discutir a Variabilidade Climática e Segurança Hídrica com grandes especialistas.

🗓️ Quando: 31/03, a partir das 08h30
📍 Onde: FATEC Sertão Central (Quixeramobim)

Prepare-se para um momento rico de diálogo. Te esperamos lá! 🌿""",
    "Mensagem 03": """Que alegria saber que você fará parte do III Seminário “Todas as Águas”!

Juntos, vamos refletir sobre Variabilidade Climática e Segurança Hídrica ao lado de grandes especialistas.

🗓️ Quando: 31/03, a partir das 08h30
📍 Onde: FATEC Sertão Central (Quixeramobim)

Prepare-se para um momento rico de diálogo. Te esperamos lá! 🌿""",
    "Mensagem 04": """Que legal! Sua presença está confirmada no III Seminário “Todas as Águas”.

Vamos bater um papo sobre Variabilidade Climática e Segurança Hídrica com quem realmente entende do assunto.

🗓️ Quando: 31/03, a partir das 08h30
📍 Onde: FATEC Sertão Central (Quixeramobim)

Prepare-se para um encontro cheio de troca e boas ideias. Te esperamos por lá! 🌿"""
}

MENSAGENS_LEMBRETE = {
    "Selecione uma mensagem pronta": "",
    "Lembrete 01": """Só passando pra te lembrar 👀

O III Seminário “Todas as Águas” é amanhã!

🗓️ 31/03, a partir das 08h30
📍 FATEC Sertão Central (Quixeramobim)

Chega cedo pra garantir teu credenciamento. Te esperamos! 🌿""",
    "Lembrete 02": """Falta pouco! 🚀

Amanhã tem o III Seminário “Todas as Águas”.

🗓️ 31/03, a partir das 08h30
📍 FATEC Sertão Central (Quixeramobim)

Se organiza e vem com a gente. Vai valer a pena! 🌿""",
    "Lembrete 03": """Ei 👇

Não esquece: amanhã tem o III Seminário “Todas as Águas”.

🗓️ 31/03, a partir das 08h30
📍 FATEC Sertão Central (Quixeramobim)

Nos vemos lá! 🌿""",
    "Lembrete 04": """Tá chegando! ⏰

Amanhã acontece o III Seminário “Todas as Águas”.

🗓️ 31/03, a partir das 08h30
📍 FATEC Sertão Central (Quixeramobim)

Prepara tua agenda e participa com a gente. 🌿""",
    "Lembrete 05": """Já deixa salvo aí 📌

Amanhã tem o III Seminário “Todas as Águas”.

🗓️ 31/03, a partir das 08h30
📍 FATEC Sertão Central (Quixeramobim)

Te esperamos! 🌿"""
}

if "nome" not in st.session_state:
    st.session_state.nome = ""

if "numero" not in st.session_state:
    st.session_state.numero = ""

if "mensagem_base" not in st.session_state:
    st.session_state.mensagem_base = ""

if "mensagem_escolhida_inscricao" not in st.session_state:
    st.session_state.mensagem_escolhida_inscricao = "Selecione uma mensagem pronta"

if "mensagem_escolhida_lembrete" not in st.session_state:
    st.session_state.mensagem_escolhida_lembrete = "Selecione uma mensagem pronta"

if "aba_ativa" not in st.session_state:
    st.session_state.aba_ativa = "Inscrição / Confirmação"

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
    st.session_state.mensagem_escolhida_inscricao = "Selecione uma mensagem pronta"
    st.session_state.mensagem_escolhida_lembrete = "Selecione uma mensagem pronta"


def aplicar_mensagem_inscricao():
    opcao = st.session_state.mensagem_escolhida_inscricao
    st.session_state.aba_ativa = "Inscrição / Confirmação"
    st.session_state.mensagem_base = MENSAGENS_INSCRICAO.get(opcao, "")
    st.session_state.mensagem_escolhida_lembrete = "Selecione uma mensagem pronta"


def aplicar_mensagem_lembrete():
    opcao = st.session_state.mensagem_escolhida_lembrete
    st.session_state.aba_ativa = "Lembretes"
    st.session_state.mensagem_base = MENSAGENS_LEMBRETE.get(opcao, "")
    st.session_state.mensagem_escolhida_inscricao = "Selecione uma mensagem pronta"


def obter_mensagens_aba_ativa():
    if st.session_state.aba_ativa == "Lembretes":
        return [v for k, v in MENSAGENS_LEMBRETE.items() if k != "Selecione uma mensagem pronta" and v.strip()]
    return [v for k, v in MENSAGENS_INSCRICAO.items() if k != "Selecione uma mensagem pronta" and v.strip()]


def normalizar_numero_br(numero: str) -> str:
    numero = str(numero).strip()
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
    return bool(re.match(r"^\+55([1-9][1-9])(9\d{8}|[2-5]\d{7})$", numero_formatado))


def montar_mensagem(nome: str, mensagem_base: str) -> str:
    nome = str(nome).strip()
    mensagem_base = str(mensagem_base).strip()

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


def carregar_contatos_csv(caminho_csv: str):
    if not os.path.exists(caminho_csv):
        return pd.DataFrame()

    try:
        df = pd.read_csv(caminho_csv)
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]

    mapa_colunas = {}
    for col in df.columns:
        col_limpa = re.sub(r"\s+", " ", col.strip().lower())
        if "nome" in col_limpa:
            mapa_colunas[col] = "nome"
        elif "whatsapp" in col_limpa or "telefone" in col_limpa or "celular" in col_limpa:
            mapa_colunas[col] = "whatsapp"
        elif col_limpa in ("nº", "n", "numero", "número"):
            mapa_colunas[col] = "ordem"

    df = df.rename(columns=mapa_colunas)

    if "nome" not in df.columns or "whatsapp" not in df.columns:
        return pd.DataFrame()

    if "ordem" not in df.columns:
        df["ordem"] = range(1, len(df) + 1)

    df["nome"] = df["nome"].astype(str).str.strip()
    df["whatsapp"] = df["whatsapp"].astype(str).str.strip()
    df["numero_formatado"] = df["whatsapp"].apply(normalizar_numero_br)
    df["numero_valido"] = df["numero_formatado"].apply(validar_numero_br)

    return df[["ordem", "nome", "whatsapp", "numero_formatado", "numero_valido"]]


def enviar_lote_contatos(df_contatos, mensagens_disponiveis, intervalo_min, intervalo_max, limite_envios):
    resultados = []
    contatos_validos = df_contatos[df_contatos["numero_valido"]].copy()

    if limite_envios > 0:
        contatos_validos = contatos_validos.head(limite_envios)

    if contatos_validos.empty:
        return resultados

    if not mensagens_disponiveis:
        return resultados

    progresso = st.progress(0)
    status_box = st.empty()
    total = len(contatos_validos)

    for idx, (_, row) in enumerate(contatos_validos.iterrows(), start=1):
        mensagem_base = mensagens_disponiveis[(idx - 1) % len(mensagens_disponiveis)]
        mensagem_final = montar_mensagem(row["nome"], mensagem_base)

        status_box.info(f"Enviando {idx}/{total} para {row['nome']}...")

        try:
            resposta = enviar_mensagem(row["numero_formatado"], mensagem_final)

            try:
                retorno = resposta.json()
            except Exception:
                retorno = {}

            if resposta.status_code in (200, 201) and retorno.get("success") is True:
                status_api = retorno.get("data", {}).get("status", "enviado")
                registrar_envio(
                    nome=row["nome"],
                    numero=row["numero_formatado"],
                    mensagem=mensagem_final,
                    status_api=status_api
                )
                resultados.append({
                    "Nome": row["nome"],
                    "Telefone": row["numero_formatado"],
                    "Resultado": "Enviado",
                    "Status API": status_api
                })
            else:
                msg_api = (
                    retorno.get("message")
                    or retorno.get("error")
                    or (resposta.text[:200] if resposta.text else "Falha no envio")
                )
                resultados.append({
                    "Nome": row["nome"],
                    "Telefone": row["numero_formatado"],
                    "Resultado": "Erro",
                    "Status API": msg_api
                })

        except requests.exceptions.RequestException as e:
            resultados.append({
                "Nome": row["nome"],
                "Telefone": row["numero_formatado"],
                "Resultado": "Erro de conexão",
                "Status API": str(e)
            })
        except RuntimeError as e:
            resultados.append({
                "Nome": row["nome"],
                "Telefone": row["numero_formatado"],
                "Resultado": "Erro",
                "Status API": str(e)
            })

        progresso.progress(idx / total)

        if idx < total:
            espera = random.uniform(intervalo_min, intervalo_max)
            status_box.warning(f"Aguardando {espera:.1f}s antes do próximo envio...")
            time.sleep(espera)

    status_box.success("Envio em lote finalizado.")
    return resultados


if st.session_state.limpar_apos_envio_ok:
    limpar_campos()
    st.session_state.limpar_apos_envio_ok = False

numero_formatado = normalizar_numero_br(st.session_state.numero)
mensagem_final = montar_mensagem(st.session_state.nome, st.session_state.mensagem_base)
status_texto = status_numero_texto(numero_formatado)
status_ok = validar_numero_br(numero_formatado)
historico_envios = carregar_historico()
df_contatos = carregar_contatos_csv(ARQUIVO_CSV_PADRAO)

st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #0f1117 0%, #151924 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 980px;
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
        padding: 18px;
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
        Envio individual e automático em lote com alternância de mensagens e intervalo variável.
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.notificacao_envio:
    notif = st.session_state.notificacao_envio
    if notif.get("tipo") == "success":
        st.success(notif.get("mensagem", "Mensagem enviada com sucesso."))
    elif notif.get("tipo") == "info":
        st.info(notif.get("mensagem", "Envio concluído."))
    elif notif.get("tipo") == "warning":
        st.warning(notif.get("mensagem", "Envio concluído com observações."))
    st.session_state.notificacao_envio = None

aba_individual, aba_lote = st.tabs(["Envio individual", "Envio automático em lote"])

with aba_individual:
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

    st.segmented_control(
        "Tipo de mensagem",
        options=["Inscrição / Confirmação", "Lembretes"],
        key="aba_ativa"
    )

    if st.session_state.aba_ativa == "Inscrição / Confirmação":
        st.selectbox(
            "Mensagens prontas de inscrição",
            options=list(MENSAGENS_INSCRICAO.keys()),
            key="mensagem_escolhida_inscricao",
            on_change=aplicar_mensagem_inscricao
        )
    else:
        st.selectbox(
            "Mensagens prontas de lembrete",
            options=list(MENSAGENS_LEMBRETE.keys()),
            key="mensagem_escolhida_lembrete",
            on_change=aplicar_mensagem_lembrete
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

    preview_segura = mensagem_final if mensagem_final else "A mensagem aparecerá aqui."
    st.text_area(
        "Mensagem final (somente leitura)",
        value=preview_segura,
        height=190,
        disabled=True
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        enviar = st.button("🚀 Enviar mensagem", use_container_width=True)
    with col_btn2:
        st.button("🧹 Limpar campos", use_container_width=True, on_click=limpar_campos)

    st.markdown('</div>', unsafe_allow_html=True)

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

                        st.session_state.notificacao_envio = {
                            "tipo": "success",
                            "mensagem": f"Mensagem enviada com sucesso para {numero_formatado}."
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

with aba_lote:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Envio automático em lote</div>', unsafe_allow_html=True)

    st.segmented_control(
        "Tipo de mensagem para o lote",
        options=["Inscrição / Confirmação", "Lembretes"],
        key="aba_ativa_lote"
    )

    mensagens_lote = (
        [v for k, v in MENSAGENS_LEMBRETE.items() if k != "Selecione uma mensagem pronta" and v.strip()]
        if st.session_state.get("aba_ativa_lote", "Inscrição / Confirmação") == "Lembretes"
        else [v for k, v in MENSAGENS_INSCRICAO.items() if k != "Selecione uma mensagem pronta" and v.strip()]
    )

    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        limite_envios = st.number_input("Qtd. máxima nesta rodada", min_value=1, max_value=1000, value=min(30, len(df_contatos)) if not df_contatos.empty else 30, step=1)
    with col_cfg2:
        intervalo_min = st.number_input("Intervalo mínimo (seg)", min_value=3, max_value=300, value=8, step=1)
    with col_cfg3:
        intervalo_max = st.number_input("Intervalo máximo (seg)", min_value=3, max_value=600, value=18, step=1)

    if intervalo_max < intervalo_min:
        st.warning("O intervalo máximo não pode ser menor que o mínimo.")

    if df_contatos.empty:
        st.error("Não foi possível carregar o arquivo nomes e contatos.csv.")
    else:
        total = len(df_contatos)
        validos = int(df_contatos["numero_valido"].sum())
        invalidos = total - validos

        c1, c2, c3 = st.columns(3)
        c1.metric("Contatos no CSV", total)
        c2.metric("Válidos", validos)
        c3.metric("Inválidos", invalidos)

        st.dataframe(
            df_contatos.rename(columns={
                "ordem": "Nº",
                "nome": "Nome",
                "whatsapp": "WhatsApp original",
                "numero_formatado": "WhatsApp formatado",
                "numero_valido": "Válido"
            }),
            use_container_width=True,
            hide_index=True,
            height=320
        )

        iniciar_lote = st.button("🚀 Iniciar envio automático", use_container_width=True)

        if iniciar_lote:
            if intervalo_max < intervalo_min:
                st.error("Ajuste o intervalo mínimo e máximo antes de iniciar.")
            elif not mensagens_lote:
                st.error("Nenhuma mensagem disponível para a aba selecionada.")
            else:
                resultados = enviar_lote_contatos(
                    df_contatos=df_contatos,
                    mensagens_disponiveis=mensagens_lote,
                    intervalo_min=float(intervalo_min),
                    intervalo_max=float(intervalo_max),
                    limite_envios=int(limite_envios)
                )

                if resultados:
                    df_resultados = pd.DataFrame(resultados)
                    enviados = int((df_resultados["Resultado"] == "Enviado").sum())
                    erros = len(df_resultados) - enviados

                    st.success(f"Lote finalizado. Enviados: {enviados}. Erros: {erros}.")
                    st.dataframe(df_resultados, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nenhum envio foi realizado.")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)

col_hist_1, col_hist_2 = st.columns([3, 1])

with col_hist_1:
    st.markdown('<div class="section-title">Histórico de envios</div>', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)
