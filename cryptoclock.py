import streamlit as st
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
# DADOS DAS COMPRAS (privados — vivem no st.session_state de cada utilizador)
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
erro_ligacao_gsheets = None
if GSHEETS_DISPONIVEL:
    try:
        conn_gsheets = st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        conn_gsheets = None
        erro_ligacao_gsheets = str(e)
else:
    erro_ligacao_gsheets = "O pacote 'st-gsheets-connection' não está instalado (verifica o requirements.txt)."


def carregar_mensagens():
    global erro_ligacao_gsheets
    if conn_gsheets is None:
        return []
    try:
        df = conn_gsheets.read(worksheet="Mensagens", ttl=5)
        df = df.dropna(how="all")
        erro_ligacao_gsheets = None
        return df.to_dict("records")
    except Exception as e:
        erro_ligacao_gsheets = str(e)
        return []


def guardar_mensagem(nick, texto):
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
# CSS GLOBAL — WEB3 DARK THEME, GLASSMORPHISM, GRADIENTES
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 12% -10%, rgba(34, 211, 238, 0.10), transparent 42%),
        radial-gradient(circle at 88% 108%, rgba(163, 230, 53, 0.08), transparent 45%),
        #080B10;
}

.block-container { padding-top: 2.2rem; padding-left: 1.1rem; padding-right: 1.1rem; max-width: 920px; }
section[data-testid="stSidebar"] {
    background-color: #0B0F16;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ---------- Cabeçalho ---------- */
.kc-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.5rem; font-weight: 700; line-height: 1.1;
    background: linear-gradient(90deg, #22D3EE 0%, #A3E635 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; vertical-align: middle;
}
.kc-badge {
    display: inline-block; padding: 5px 12px; border-radius: 999px;
    background: rgba(34, 211, 238, 0.10); border: 1px solid rgba(34, 211, 238, 0.30);
    color: #7FE9F7; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em;
    text-transform: uppercase; margin-left: 10px; vertical-align: middle;
}
.kc-subtitle { color: #8B92A5; font-size: 0.93rem; margin-top: 8px; margin-bottom: 1.6rem; }

.kc-section-title {
    font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 700;
    background: linear-gradient(90deg, #22D3EE 0%, #A3E635 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; margin-top: 1.8rem; margin-bottom: 0.9rem;
}

/* ---------- Cartões "vidro fosco" (KPIs) ---------- */
.kc-glass-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px 20px;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
    height: 100%;
}
.kc-metric-label { color: #8B92A5; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.kc-metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.45rem; font-weight: 700; color: #E9ECF2; }
.kc-metric-value.green { color: #34D399; }
.kc-metric-value.orange { color: #FDBA74; }

/* ---------- Formulário (glassmorphism) ---------- */
div[data-testid="stForm"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 1.3rem 1.3rem 0.3rem 1.3rem;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
}

/* ---------- Zona de remoção ---------- */
.kc-remove-wrap {
    background: rgba(255, 77, 94, 0.05);
    border: 1px solid rgba(255, 77, 94, 0.25);
    border-radius: 18px;
    padding: 1rem 1.2rem 1.2rem 1.2rem;
    margin-top: 0.8rem;
    backdrop-filter: blur(10px);
}

/* ---------- Botões, com transições suaves ---------- */
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button {
    transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
    border: none; font-weight: 700; border-radius: 12px; width: 100%;
    padding: 0.6rem 1rem;
}

/* botão "Remover Lote Selecionado" — vermelho-neon */
div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #FF3B5C 0%, #FF6B7A 100%);
    color: #0B0F16;
    box-shadow: 0 0 0 rgba(255, 59, 92, 0);
}
div[data-testid="stButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(255, 59, 92, 0.45);
    filter: brightness(1.08);
}

/* botões de submeter formulário (Guardar Compra, Enviar no chat) — ciano-lima */
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #22D3EE 0%, #A3E635 100%);
    color: #080B10;
}
div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(34, 211, 238, 0.35);
    filter: brightness(1.06);
}

/* botão de exportar */
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #22D3EE 0%, #A3E635 100%);
    color: #080B10;
}
div[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(163, 230, 53, 0.3);
}

/* ---------- Acessibilidade tátil ---------- */
button, input, select, textarea, div[data-baseweb="select"] { min-height: 44px; }

/* ---------- Responsivo ---------- */
@media (max-width: 640px) {
    .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    .kc-title { font-size: 1.9rem; }
    .kc-badge { display: block; margin-left: 0; margin-top: 8px; width: fit-content; }
    .kc-metric-value { font-size: 1.15rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# GERADOR DO "CRYPTOCLOCK GRID" — CARTÕES COM RELÓGIO AO VIVO (HTML+JS)
# ---------------------------------------------------------
CSS_CARTOES_LOTES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@600;700&display=swap');
* { box-sizing: border-box; }
body {
    margin: 0; padding: 4px;
    font-family: 'Inter', sans-serif;
    background: transparent;
}
.cc-grid { display: flex; flex-direction: column; gap: 14px; }
.cc-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px 18px;
    backdrop-filter: blur(14px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    position: relative;
    overflow: hidden;
}
.cc-card.cc-pulse {
    animation: ccPulseGlow 2.4s ease-in-out infinite;
}
@keyframes ccPulseGlow {
    0%   { box-shadow: 0 8px 24px rgba(0,0,0,0.35), 0 0 0px rgba(253, 186, 116, 0.0); }
    50%  { box-shadow: 0 8px 24px rgba(0,0,0,0.35), 0 0 22px rgba(253, 186, 116, 0.35); }
    100% { box-shadow: 0 8px 24px rgba(0,0,0,0.35), 0 0 0px rgba(253, 186, 116, 0.0); }
}
.cc-card-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.cc-asset-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem; font-weight: 700; color: #E9ECF2;
}
.cc-sub { color: #8B92A5; font-size: 0.82rem; margin-top: 4px; }
.cc-badge {
    display: inline-block; padding: 5px 12px; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em; white-space: nowrap;
}
.cc-badge-isento {
    background: rgba(52, 211, 153, 0.14); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.4);
}
.cc-badge-contando {
    background: rgba(253, 186, 116, 0.14); color: #FDBA74; border: 1px solid rgba(253, 186, 116, 0.4);
    animation: ccBadgePulse 1.6s ease-in-out infinite;
}
@keyframes ccBadgePulse {
    0%, 100% { opacity: 1; } 50% { opacity: 0.55; }
}
.cc-progress-track {
    width: 100%; height: 8px; border-radius: 999px;
    background: rgba(255,255,255,0.08); margin-top: 12px; overflow: hidden;
}
.cc-progress-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #22D3EE 0%, #A3E635 100%);
    box-shadow: 0 0 10px rgba(163, 230, 53, 0.55);
    transition: width 0.6s ease;
}
.cc-countdown {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem; font-weight: 700; color: #C9F5FF;
    margin-top: 10px; letter-spacing: 0.02em;
}
</style>
"""

SCRIPT_CARTOES_LOTES = """
<script>
function ccPad(n){ return String(n).padStart(2,'0'); }
function ccTick(){
  var agora = new Date();
  document.querySelectorAll('.cc-card').forEach(function(card){
    var inicio = new Date(card.getAttribute('data-start'));
    var fim = new Date(card.getAttribute('data-end'));
    var diferenca = fim - agora;
    var elFill = card.querySelector('.cc-progress-fill');
    var elCd = card.querySelector('.cc-countdown');
    var elBadge = card.querySelector('.cc-badge');

    if (diferenca <= 0) {
      if (elFill) elFill.style.width = '100%';
      if (elCd) elCd.textContent = '✅ Isento — parabéns!';
      if (elBadge) {
        elBadge.textContent = 'LIVRE DE IMPOSTOS ✅';
        elBadge.className = 'cc-badge cc-badge-isento';
      }
      card.classList.remove('cc-pulse');
    } else {
      var totalMs = fim - inicio;
      var decorridoMs = agora - inicio;
      var pct = Math.max(0, Math.min(100, (decorridoMs / totalMs) * 100));
      if (elFill) elFill.style.width = pct.toFixed(2) + '%';

      var totalSeg = Math.floor(diferenca / 1000);
      var d = Math.floor(totalSeg / 86400);
      var h = Math.floor((totalSeg % 86400) / 3600);
      var m = Math.floor((totalSeg % 3600) / 60);
      var s = totalSeg % 60;
      if (elCd) elCd.textContent = d + 'd ' + ccPad(h) + 'h ' + ccPad(m) + 'm ' + ccPad(s) + 's restantes';
    }
  });
}
ccTick();
setInterval(ccTick, 1000);
</script>
"""


def html_cartao_lote(lote):
    pulso_classe = "" if lote["isento"] else "cc-pulse"
    if lote["isento"]:
        badge_html = '<div class="cc-badge cc-badge-isento">LIVRE DE IMPOSTOS ✅</div>'
    else:
        badge_html = '<div class="cc-badge cc-badge-contando">EM CONTRIBUIÇÃO ⚡</div>'

    return f"""
    <div class="cc-card {pulso_classe}" data-start="{lote['momento_compra'].isoformat()}" data-end="{lote['momento_isencao'].isoformat()}">
        <div class="cc-card-top">
            <div class="cc-asset-name">🪙 {lote['ativo']}</div>
            {badge_html}
        </div>
        <div class="cc-sub">{lote['quantidade']} · {lote['plataforma']} · {formatar_euros(lote['valor_pago_eur'])}</div>
        <div class="cc-progress-track"><div class="cc-progress-fill" style="width:{lote['fracao_concluida']*100:.1f}%;"></div></div>
        <div class="cc-countdown">a calcular...</div>
    </div>
    """


def renderizar_grid_de_lotes(lotes_ordenados):
    cartoes_html = "".join(html_cartao_lote(lote) for lote in lotes_ordenados)
    html_final = CSS_CARTOES_LOTES + f'<div class="cc-grid">{cartoes_html}</div>' + SCRIPT_CARTOES_LOTES
    altura_estimada = max(220, 40 + len(lotes_ordenados) * 190)
    st.iframe(html_final, height=altura_estimada)


def widget_tradingview(symbol, container_id, altura=420):
    return f"""
    <div class="tradingview-widget-container">
      <div id="{container_id}"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>
      new TradingView.widget({{
        "width": "100%",
        "height": {altura},
        "symbol": "{symbol}",
        "interval": "60",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "pt",
        "toolbar_bg": "#0B0F16",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "save_image": false,
        "container_id": "{container_id}"
      }});
      </script>
    </div>
    """


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
<div class="kc-subtitle">Regista as tuas compras de cripto, acompanha os 365 dias de isenção em tempo real e conversa com a comunidade.</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# CÁLCULOS DOS LOTES (usados na Tab 1)
# ---------------------------------------------------------
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
    isento = diferenca.total_seconds() <= 0

    fracao_concluida = 1.0 if isento else min(
        max(1 - (diferenca.total_seconds() / SEGUNDOS_EM_365_DIAS), 0.0), 1.0
    )

    total_investido += compra["valor_pago_eur"]
    if isento:
        total_isento += compra["valor_pago_eur"]
    else:
        total_em_contagem += compra["valor_pago_eur"]

    lotes_calculados.append({
        **compra,
        "momento_compra": momento_compra,
        "momento_isencao": momento_isencao,
        "isento": isento,
        "fracao_concluida": fracao_concluida,
    })

lotes_ordenados = sorted(lotes_calculados, key=lambda x: x["momento_isencao"])


# ---------------------------------------------------------
# ABAS PRINCIPAIS
# ---------------------------------------------------------
tab_meu, tab_mercado, tab_chat = st.tabs([
    "🕒 O meu CryptoClock", "📈 Mercado Real-Time", "💬 Chat da Comunidade"
])


# ===========================================================
# TAB 1 — O MEU CRYPTOCLOCK
# ===========================================================
with tab_meu:
    st.info(
        "🔒 **Privado por sessão:** as tuas compras só aparecem para ti neste browser. "
        "Usa o **Exportar Dados** na barra lateral para não perderes o progresso.",
        icon="🔒",
    )

    # -------- KPI CARDS --------
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""<div class="kc-glass-card"><div class="kc-metric-label">Total Investido</div>
        <div class="kc-metric-value">{formatar_euros(total_investido)}</div></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="kc-glass-card"><div class="kc-metric-label">✅ Ativos Isentos</div>
        <div class="kc-metric-value green">{formatar_euros(total_isento)}</div></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class="kc-glass-card"><div class="kc-metric-label">⏳ Em Contagem</div>
        <div class="kc-metric-value orange">{formatar_euros(total_em_contagem)}</div></div>""", unsafe_allow_html=True)

    # -------- FORMULÁRIO --------
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

    # -------- CRYPTOCLOCK GRID (cartões com relógio ao vivo) --------
    st.markdown('<div class="kc-section-title">⏱️ Painel de Lotes (CryptoClock Grid)</div>', unsafe_allow_html=True)

    if not lotes_calculados:
        st.info("Ainda não tens nenhuma compra registada. Usa o formulário acima para adicionar a primeira.")
    else:
        renderizar_grid_de_lotes(lotes_ordenados)

        # -------- REMOVER / LIQUIDAR UM LOTE --------
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
# TAB 2 — MERCADO REAL-TIME
# ===========================================================
with tab_mercado:
    st.markdown('<div class="kc-section-title">📈 Mercado ao Vivo</div>', unsafe_allow_html=True)
    st.caption("Gráficos oficiais da TradingView, em tempo real, tema escuro.")

    st.markdown("**🪙 BTC/USDT**")
    st.iframe(widget_tradingview("BINANCE:BTCUSDT", "tv_btc_full", altura=460), height=480)

    st.markdown("**♦️ ETH/USDT**")
    st.iframe(widget_tradingview("BINANCE:ETHUSDT", "tv_eth_full", altura=460), height=480)


# ===========================================================
# TAB 3 — CHAT DA COMUNIDADE (partilhado via Google Sheets)
# ===========================================================
@st.fragment(run_every=5)
def widget_chat_ao_vivo():
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

    if erro_ligacao_gsheets:
        st.error("Não consegui ler as mensagens da Google Sheet.")
        with st.expander("🔧 Ver detalhe técnico do erro (copia isto e envia ao Claude)"):
            st.code(erro_ligacao_gsheets)
    elif not mensagens:
        st.caption("Ainda não há mensagens. Sê o primeiro a dizer olá! 👋")
    else:
        for msg in reversed(mensagens):
            st.markdown(f"""
            <div class="kc-glass-card" style="margin-bottom:8px; padding:10px 14px;">
                <span style="color:#7FE9F7; font-weight:700; font-size:0.85rem;">{msg.get('nick', 'Anónimo')}</span>
                <span style="color:#5C6270; font-size:0.7rem; float:right;">{msg.get('hora', '')}</span>
                <div style="color:#E9ECF2; font-size:0.92rem; margin-top:3px;">{msg.get('texto', '')}</div>
            </div>
            """, unsafe_allow_html=True)

    st.caption("🟢 Ao vivo — esta zona atualiza-se sozinha a cada 5 segundos.")


with tab_chat:
    st.markdown('<div class="kc-section-title">💬 Chat da Comunidade</div>', unsafe_allow_html=True)

    if not GSHEETS_DISPONIVEL or conn_gsheets is None:
        st.warning(
            "O chat ainda não está ligado à Google Sheet. Confirma que:\n\n"
            "1. Adicionaste `st-gsheets-connection` ao `requirements.txt`\n"
            "2. Configuraste os **Secrets** da app em share.streamlit.io → Settings → Secrets\n"
            "3. Partilhaste a folha com o email do teu Service Account, como **Editor**"
        )
        if erro_ligacao_gsheets:
            with st.expander("🔧 Ver detalhe técnico do erro (copia isto e envia ao Claude)"):
                st.code(erro_ligacao_gsheets)
    else:
        widget_chat_ao_vivo()
