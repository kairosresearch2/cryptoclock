import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import uuid
import json
from datetime import date, datetime, timedelta

try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_DISPONIVEL = True
except ImportError:
    GSHEETS_DISPONIVEL = False

# ---------------------------------------------------------
# CONFIGURAÇÃO BÁSICA
# ---------------------------------------------------------
st.set_page_config(page_title="CryptoClock", page_icon="🕒", layout="centered")

SEGUNDOS_EM_365_DIAS = 365 * 24 * 60 * 60


# ---------------------------------------------------------
# "BASE DE DADOS" DAS COMPRAS (por sessão / privada de cada utilizador)
# ---------------------------------------------------------
if "compras" not in st.session_state:
    st.session_state.compras = []


def adicionar_id_se_faltar(lista_de_compras):
    for compra in lista_de_compras:
        if "id" not in compra:
            compra["id"] = uuid.uuid4().hex
    return lista_de_compras


def remover_compra_por_id(id_a_remover):
    st.session_state.compras = [
        c for c in st.session_state.compras if c["id"] != id_a_remover
    ]


def formatar_euros(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return f"€ {texto}"


# ---------------------------------------------------------
# LIGAÇÃO AO GOOGLE SHEETS (para o chat, que é partilhado por todos)
# ---------------------------------------------------------
conn_gsheets = None
if GSHEETS_DISPONIVEL:
    try:
        conn_gsheets = st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        conn_gsheets = None


def carregar_mensagens():
    """Lê as mensagens do chat a partir da Google Sheet (aba 'Mensagens')."""
    if conn_gsheets is None:
        return []
    try:
        df = conn_gsheets.read(worksheet="Mensagens", ttl=5)
        df = df.dropna(how="all")
        return df.to_dict("records")
    except Exception:
        return []


def guardar_mensagem(nick, texto):
    """Acrescenta uma mensagem nova e regrava a folha inteira (é assim que
    esta ligação funciona: lê tudo, adiciona uma linha, escreve tudo de novo)."""
    mensagens = carregar_mensagens()
    mensagens.append({
        "id": uuid.uuid4().hex,
        "nick": nick,
        "texto": texto,
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    df_atualizado = pd.DataFrame(mensagens)
    conn_gsheets.update(worksheet="Mensagens", data=df_atualizado)


# ---------------------------------------------------------
# CSS CUSTOMIZADO — VISUAL "FINTECH DARK MODE" + RESPONSIVO
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'Inter', sans-serif;
}
.stApp { background-color: #0B0E14; }
.block-container { padding-top: 2.2rem; padding-left: 1.2rem; padding-right: 1.2rem; max-width: 900px; }
section[data-testid="stSidebar"] { background-color: #0F1420; border-right: 1px solid #1F2430; }

.kc-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.5rem; font-weight: 700; line-height: 1.1;
    background: linear-gradient(90deg, #C6FF3D 0%, #34D8FF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; vertical-align: middle;
}
.kc-badge {
    display: inline-block; padding: 5px 12px; border-radius: 999px;
    background: rgba(52, 216, 255, 0.12); border: 1px solid rgba(52, 216, 255, 0.35);
    color: #7FE6FF; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em;
    text-transform: uppercase; margin-left: 10px; vertical-align: middle;
}
.kc-subtitle { color: #8B92A5; font-size: 0.93rem; margin-top: 6px; margin-bottom: 1.4rem; }

.kc-card {
    background: #131720; border: 1px solid #1F2430; border-radius: 16px;
    padding: 16px 18px; height: 100%;
}
.kc-metric-label { color: #8B92A5; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.kc-metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #E6E8EC; }
.kc-metric-value.green { color: #34D399; }
.kc-metric-value.orange { color: #FDBA74; }

.kc-section-title {
    font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700;
    background: linear-gradient(90deg, #C6FF3D 0%, #34D8FF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; margin-top: 2rem; margin-bottom: 0.9rem;
}

.kc-asset { font-weight: 700; color: #E6E8EC; font-size: 1.02rem; }
.kc-provider { color: #8B92A5; font-size: 0.78rem; }
.kc-mono { font-family: 'JetBrains Mono', monospace; }
.kc-countdown { color: #8B92A5; font-size: 0.8rem; margin-top: 4px; }

.kc-pill {
    display: inline-block; padding: 4px 11px; border-radius: 999px;
    font-size: 0.74rem; font-weight: 600; white-space: nowrap;
}
.kc-pill.isento { background: rgba(52, 211, 153, 0.12); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.35); }
.kc-pill.contando { background: rgba(251, 146, 60, 0.12); color: #FDBA74; border: 1px solid rgba(251, 146, 60, 0.35); }

div[data-testid="stForm"] {
    background: #131720; border: 1px solid #1F2430; border-radius: 18px;
    padding: 1.2rem 1.2rem 0.2rem 1.2rem;
}

/* cartão de cada lote (usa o container nativo com borda do Streamlit) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #131720 !important;
    border: 1px solid #1F2430 !important;
    border-radius: 16px !important;
}

.kc-remove-wrap {
    background: #17121A; border: 1px solid #3A1F26; border-radius: 16px;
    padding: 1rem 1.2rem 1.2rem 1.2rem; margin-top: 0.6rem;
}

div[data-testid="stButton"] button {
    background-color: #FF4D5E; color: #0B0E14; border: none; font-weight: 700;
    border-radius: 10px; padding: 0.55rem 1rem; width: 100%;
}
div[data-testid="stButton"] button:hover { background-color: #FF6B7A; color: #0B0E14; }

div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #C6FF3D 0%, #34D8FF 100%);
    color: #0B0E14; border: none; font-weight: 700; border-radius: 10px; width: 100%;
}

/* balões de chat */
.kc-chat-bubble {
    background: #131720; border: 1px solid #1F2430; border-radius: 14px;
    padding: 10px 14px; margin-bottom: 8px;
}
.kc-chat-nick { color: #7FE6FF; font-weight: 700; font-size: 0.85rem; }
.kc-chat-hora { color: #5C6270; font-size: 0.7rem; float: right; }
.kc-chat-texto { color: #E6E8EC; font-size: 0.92rem; margin-top: 3px; }

button, input, select, textarea, div[data-baseweb="select"] { min-height: 42px; }

@media (max-width: 640px) {
    .block-container { padding-left: 0.7rem; padding-right: 0.7rem; }
    .kc-title { font-size: 1.9rem; }
    .kc-badge { display: block; margin-left: 0; margin-top: 8px; width: fit-content; }
    .kc-metric-value { font-size: 1.15rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# BARRA LATERAL — DISPOSITIVO & BACKUP
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### Dispositivo & Backup 💾")
    st.caption(
        "As tuas COMPRAS existem só nesta aba do browser (privadas, ninguém mais vê). "
        "Exporta sempre que quiseres guardar o progresso."
    )

    st.markdown("**⬇️ Exportar Dados**")
    dados_para_exportar = json.dumps(
        st.session_state.compras, ensure_ascii=False, indent=2, default=str
    )
    st.download_button(
        label="Descarregar backup (.json)",
        data=dados_para_exportar,
        file_name="cryptoclock_backup.json",
        mime="application/json",
        use_container_width=True,
        disabled=len(st.session_state.compras) == 0,
    )

    st.markdown("---")
    st.markdown("**⬆️ Importar Dados**")
    ficheiro_importado = st.file_uploader(
        "Carrega o teu ficheiro cryptoclock_backup.json",
        type=["json"],
        label_visibility="collapsed",
    )
    if ficheiro_importado is not None:
        try:
            dados_lidos = json.load(ficheiro_importado)
            if not isinstance(dados_lidos, list):
                raise ValueError("formato inesperado")
            st.warning(f"Encontrei {len(dados_lidos)} transação(ões). Isto vai substituir os dados atuais.")
            if st.button("📥 Confirmar Importação"):
                st.session_state.compras = adicionar_id_se_faltar(dados_lidos)
                st.success("Dados importados com sucesso!")
                st.rerun()
        except Exception:
            st.error("Este ficheiro não parece ser um backup válido do CryptoClock.")


# ---------------------------------------------------------
# CABEÇALHO
# ---------------------------------------------------------
st.markdown("""
<span class="kc-title">🕒 CryptoClock</span><span class="kc-badge">v1.0 · Portugal Fiscal Compliance</span>
<div class="kc-subtitle">Regista as tuas compras de cripto, acompanha os 365 dias de isenção e conversa com a comunidade.</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# ABAS PRINCIPAIS
# ---------------------------------------------------------
aba_painel, aba_chat = st.tabs(["🏠 Painel CryptoClock", "💬 Chat da Comunidade"])


# ===========================================================
# ABA 1 — PAINEL PRINCIPAL
# ===========================================================
with aba_painel:

    st.info(
        "🔒 **Privado por sessão:** as tuas compras só aparecem para ti neste browser. "
        "Usa o **Exportar Dados** na barra lateral para não perderes o progresso.",
        icon="🔒",
    )

    # -------------------------------------------------------
    # GRÁFICOS AO VIVO — BTC E ETH (TRADINGVIEW)
    # -------------------------------------------------------
    st.markdown('<div class="kc-section-title">📈 Mercado ao Vivo</div>', unsafe_allow_html=True)

    def widget_tradingview(symbol, container_id):
        return f"""
        <div class="tradingview-widget-container">
          <div id="{container_id}"></div>
          <script src="https://s3.tradingview.com/tv.js"></script>
          <script>
          new TradingView.widget({{
            "width": "100%",
            "height": 360,
            "symbol": "{symbol}",
            "interval": "60",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "pt",
            "toolbar_bg": "#131720",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "save_image": false,
            "container_id": "{container_id}"
          }});
          </script>
        </div>
        """

    col_btc, col_eth = st.columns(2)
    with col_btc:
        components.html(widget_tradingview("BINANCE:BTCUSDT", "tv_btc"), height=380)
    with col_eth:
        components.html(widget_tradingview("BINANCE:ETHUSDT", "tv_eth"), height=380)

    # -------------------------------------------------------
    # CÁLCULOS
    # -------------------------------------------------------
    agora = datetime.now()
    total_investido = 0.0
    total_isento = 0.0
    total_em_contagem = 0.0
    lotes_calculados = []

    for compra in st.session_state.compras:
        data_compra = datetime.strptime(compra["data_compra"], "%Y-%m-%d").date()
        momento_compra = datetime.combine(data_compra, datetime.min.time())
        momento_isencao = momento_compra + timedelta(days=365)
        diferenca = momento_isencao - agora
        segundos_restantes = diferenca.total_seconds()
        isento = segundos_restantes <= 0

        fracao_concluida = 1.0 if isento else min(
            max(1 - (segundos_restantes / SEGUNDOS_EM_365_DIAS), 0.0), 1.0
        )

        if isento:
            texto_contagem = "Isento — já passaram os 365 dias"
        else:
            dias = diferenca.days
            horas = diferenca.seconds // 3600
            minutos = (diferenca.seconds % 3600) // 60
            texto_contagem = f"{dias} dias, {horas} horas e {minutos} minutos restantes"

        total_investido += compra["valor_pago_eur"]
        if isento:
            total_isento += compra["valor_pago_eur"]
        else:
            total_em_contagem += compra["valor_pago_eur"]

        lotes_calculados.append({
            **compra,
            "data_isencao": momento_isencao.date(),
            "isento": isento,
            "fracao_concluida": fracao_concluida,
            "texto_contagem": texto_contagem,
        })

    lotes_ordenados = sorted(lotes_calculados, key=lambda x: x["data_isencao"])

    # -------------------------------------------------------
    # KPI CARDS
    # -------------------------------------------------------
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""<div class="kc-card"><div class="kc-metric-label">Total Investido</div>
        <div class="kc-metric-value">{formatar_euros(total_investido)}</div></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="kc-card"><div class="kc-metric-label">✅ Ativos Isentos</div>
        <div class="kc-metric-value green">{formatar_euros(total_isento)}</div></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class="kc-card"><div class="kc-metric-label">⏳ Em Contagem</div>
        <div class="kc-metric-value orange">{formatar_euros(total_em_contagem)}</div></div>""", unsafe_allow_html=True)

    # -------------------------------------------------------
    # FORMULÁRIO
    # -------------------------------------------------------
    st.markdown('<div class="kc-section-title">➕ Registar nova compra</div>', unsafe_allow_html=True)

    with st.form("form_nova_compra", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_compra_input = st.date_input("Data da Compra", value=date.today())
            ativo = st.text_input("Ativo (Ex: BTC, USDT, ETH)")
            quantidade = st.number_input("Quantidade Comprada", min_value=0.0, value=0.0, step=0.0001, format="%.8f")
        with col2:
            valor_pago = st.number_input("Valor Pago em Euros (€)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            plataforma = st.text_input("Plataforma/Provedor (Ex: BingX, Ledger)")

        enviado = st.form_submit_button("Guardar Compra")
        if enviado:
            if not ativo or quantidade <= 0 or valor_pago <= 0 or not plataforma:
                st.error("Por favor, preenche todos os campos corretamente antes de guardar.")
            else:
                st.session_state.compras.append({
                    "id": uuid.uuid4().hex,
                    "data_compra": str(data_compra_input),
                    "ativo": ativo.upper().strip(),
                    "quantidade": quantidade,
                    "valor_pago_eur": valor_pago,
                    "plataforma": plataforma.strip(),
                })
                st.success("✅ Compra guardada com sucesso!")
                st.rerun()

    # -------------------------------------------------------
    # PAINEL DE LOTES (CRYPTOCLOCK GRID) — com relógio e barra de progresso
    # -------------------------------------------------------
    st.markdown('<div class="kc-section-title">⏱️ Painel de Lotes (CryptoClock Grid)</div>', unsafe_allow_html=True)

    if not lotes_calculados:
        st.info("Ainda não tens nenhuma compra registada. Usa o formulário acima para adicionar a primeira.")
    else:
        for lote in lotes_ordenados:
            with st.container(border=True):
                if lote["isento"]:
                    pill_html = '<span class="kc-pill isento">🟢 Isento (Tax Free)</span>'
                else:
                    pill_html = f'<span class="kc-pill contando">⚡ {int(lote["fracao_concluida"]*100)}%</span>'

                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="kc-asset">{lote['ativo']}</span>
                        <span class="kc-provider"> · {lote['plataforma']}</span>
                    </div>
                    {pill_html}
                </div>
                <div class="kc-mono" style="margin-top:6px; color:#8B92A5; font-size:0.82rem;">
                    {lote['quantidade']} · {formatar_euros(lote['valor_pago_eur'])} · comprado a {lote['data_compra']}
                </div>
                """, unsafe_allow_html=True)

                st.progress(lote["fracao_concluida"])
                st.markdown(f'<div class="kc-countdown">⏳ {lote["texto_contagem"]}</div>', unsafe_allow_html=True)

        # ---------------------------------------------------
        # REMOVER / LIQUIDAR UM LOTE
        # ---------------------------------------------------
        st.markdown('<div class="kc-remove-wrap">', unsafe_allow_html=True)
        st.markdown("**🗑️ Remover ou liquidar um lote**")

        opcoes = {
            lote["id"]: f"{lote['ativo']} · {lote['plataforma']} · {lote['data_compra']} · {formatar_euros(lote['valor_pago_eur'])}"
            for lote in lotes_ordenados
        }
        id_selecionado = st.selectbox(
            "Escolhe o lote que queres remover",
            options=list(opcoes.keys()),
            format_func=lambda id_lote: opcoes[id_lote],
            label_visibility="collapsed",
        )
        if st.button("❌ Remover Lote Selecionado"):
            remover_compra_por_id(id_selecionado)
            st.success("Lote removido com sucesso!")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# ===========================================================
# ABA 2 — CHAT DA COMUNIDADE (partilhado via Google Sheets)
# ===========================================================
with aba_chat:
    st.markdown('<div class="kc-section-title">💬 Chat da Comunidade</div>', unsafe_allow_html=True)

    if not GSHEETS_DISPONIVEL or conn_gsheets is None:
        st.warning(
            "O chat ainda não está ligado à Google Sheet. Confirma que:\n\n"
            "1. Adicionaste `st-gsheets-connection` ao `requirements.txt`\n"
            "2. Configuraste os **Secrets** da app em share.streamlit.io → Settings → Secrets\n"
            "3. Partilhaste a folha com o email do teu Service Account, como **Editor**"
        )
    else:
        if "nick" not in st.session_state:
            st.session_state.nick = ""

        st.session_state.nick = st.text_input(
            "O teu Nick Anónimo",
            value=st.session_state.nick,
            placeholder="Ex: BitcoinWhale99, CryptoAnonymous...",
        )

        with st.form("form_chat", clear_on_submit=True):
            texto_mensagem = st.text_area("Mensagem", placeholder="Escreve aqui a tua mensagem...", height=80)
            enviar_mensagem = st.form_submit_button("Enviar 🚀")

            if enviar_mensagem:
                if not st.session_state.nick.strip():
                    st.error("Escolhe primeiro um Nick Anónimo.")
                elif not texto_mensagem.strip():
                    st.error("Escreve uma mensagem antes de enviar.")
                else:
                    try:
                        guardar_mensagem(st.session_state.nick.strip(), texto_mensagem.strip())
                        st.success("Mensagem enviada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Não consegui enviar a mensagem. Verifica a ligação à Google Sheet. ({e})")

        st.markdown("---")

        mensagens = carregar_mensagens()
        if not mensagens:
            st.caption("Ainda não há mensagens. Sê o primeiro a dizer olá! 👋")
        else:
            for msg in reversed(mensagens):
                st.markdown(f"""
                <div class="kc-chat-bubble">
                    <span class="kc-chat-nick">{msg.get('nick', 'Anónimo')}</span>
                    <span class="kc-chat-hora">{msg.get('hora', '')}</span>
                    <div class="kc-chat-texto">{msg.get('texto', '')}</div>
                </div>
                """, unsafe_allow_html=True)

        st.caption("As mensagens atualizam-se sempre que a página recarrega ou envias uma nova mensagem.")
