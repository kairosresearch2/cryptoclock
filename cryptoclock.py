import streamlit as st
import pandas as pd
import uuid
import json
import textwrap
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

if "chat_aberto" not in st.session_state:
    st.session_state.chat_aberto = False

# Aviso de privacidade — aparece como notificação num canto e desaparece
# sozinho ao fim de alguns segundos, uma única vez por sessão.
if "aviso_privacidade_mostrado" not in st.session_state:
    st.toast(
        "🔒 Os teus dados de compras não são guardados em nenhum servidor — "
        "vivem só neste browser.",
        icon="🔒",
    )
    st.session_state.aviso_privacidade_mostrado = True


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
# LIGAÇÃO AO GOOGLE SHEETS (para o Fórum Anónimo, partilhado por todos)
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
# CSS GLOBAL — "CINEMATIC DARK WEALTH" + ANCORAGEM DO FUNDO ANIMADO
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'Inter', sans-serif;
}

@keyframes ccFadeSlideUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

.stApp { background: #030508; }

/* -----------------------------------------------------------------
   Truque para "ancorar" o 1º iframe da página (o nosso Canvas de
   fundo "To The Moon") como um fundo fixo, atrás de todo o conteúdo.
   Isto usa o testid interno do Streamlit para o wrapper de iframes —
   funciona hoje, mas por não ser uma API oficial, pode deixar de
   funcionar numa futura atualização do Streamlit.
------------------------------------------------------------------ */
div[data-testid="stIFrame"]:first-of-type {
    position: fixed !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1 !important;
    pointer-events: none !important;
}
div[data-testid="stIFrame"]:first-of-type iframe {
    width: 100% !important;
    height: 100% !important;
    border: none !important;
}

.block-container { padding-top: 2.2rem; padding-left: 1.1rem; padding-right: 1.1rem; max-width: 920px; position: relative; z-index: 1; }
section[data-testid="stSidebar"] {
    background-color: rgba(7, 10, 16, 0.85);
    border-right: 1px solid rgba(255,255,255,0.06);
    position: relative; z-index: 1;
}

/* ---------- Cabeçalho ---------- */
.kc-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem; font-weight: 700; line-height: 1.1;
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; vertical-align: middle;
    animation: ccFadeSlideUp 0.7s ease-out backwards;
}
.kc-title-gold {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.4rem; font-weight: 700; line-height: 1.1;
    background: linear-gradient(90deg, #FFD700 0%, #F0B90B 45%, #FFE292 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; vertical-align: middle;
    filter: drop-shadow(0 0 6px rgba(240, 185, 11, 0.35));
    animation: ccFadeSlideUp 0.7s ease-out backwards;
}
.kc-badge {
    display: inline-block; padding: 5px 12px; border-radius: 999px;
    background: rgba(34, 211, 238, 0.10); border: 1px solid rgba(34, 211, 238, 0.30);
    color: #7FE9F7; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em;
    text-transform: uppercase; margin-left: 10px; vertical-align: middle;
}
.kc-subtitle {
    color: #9AA3B2; font-size: 0.93rem; margin-top: 8px; margin-bottom: 1.6rem;
    animation: ccFadeSlideUp 0.8s ease-out 0.1s backwards;
}

.kc-section-title {
    font-family: 'Space Grotesk', sans-serif; font-size: 1.15rem; font-weight: 700;
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: inline-block; margin-top: 1.8rem; margin-bottom: 0.9rem;
    animation: ccFadeSlideUp 0.6s ease-out backwards;
}

/* ---------- Cartões "vidro líquido" (KPIs) ---------- */
.kc-glass-card {
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid rgba(52, 211, 153, 0.18);
    border-radius: 16px;
    padding: 18px 20px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 0 0 1px rgba(34,211,238,0.04), 0 10px 30px rgba(0,0,0,0.5);
    height: 100%;
    transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out, border-color 0.3s ease-in-out;
    animation: ccFadeSlideUp 0.7s ease-out backwards;
}
.kc-glass-card:hover {
    transform: translateY(-3px);
    border-color: rgba(52, 211, 153, 0.5);
    box-shadow: 0 0 24px rgba(52, 211, 153, 0.18), 0 14px 34px rgba(0,0,0,0.55);
}
.kc-metric-label { color: #8B92A5; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.kc-metric-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.55rem; font-weight: 700; color: #ECF3F0; letter-spacing: -0.01em; }
.kc-metric-value.green { color: #34D399; }
.kc-metric-value.orange { color: #FDBA74; }

/* ---------- Formulário (glassmorphism líquido) ---------- */
div[data-testid="stForm"] {
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid rgba(34, 211, 238, 0.18);
    border-radius: 16px;
    padding: 1.3rem 1.3rem 0.3rem 1.3rem;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 0 0 1px rgba(52,211,153,0.04), 0 10px 30px rgba(0,0,0,0.5);
    transition: border-color 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
    animation: ccFadeSlideUp 0.75s ease-out 0.05s backwards;
}
div[data-testid="stForm"]:hover {
    border-color: rgba(34, 211, 238, 0.4);
    box-shadow: 0 0 22px rgba(34, 211, 238, 0.12), 0 12px 30px rgba(0,0,0,0.55);
}

/* ---------- Botões ---------- */
div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
div[data-testid="stDownloadButton"] button {
    transition: all 0.3s ease-in-out;
    border: none; font-weight: 700; border-radius: 12px; width: 100%;
    padding: 0.6rem 1rem;
}
div[data-testid="stButton"] button {
    background: rgba(255, 59, 92, 0.12);
    border: 1px solid rgba(255, 59, 92, 0.4) !important;
    color: #FF7C8E;
}
div[data-testid="stButton"] button:hover {
    transform: translateY(-3px);
    background: rgba(255, 59, 92, 0.2);
    box-shadow: 0 0 20px rgba(255, 59, 92, 0.35);
}
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%);
    color: #05070B;
}
div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 22px rgba(52, 211, 153, 0.4);
}
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%);
    color: #05070B;
}
div[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 22px rgba(34, 211, 238, 0.35);
}

/* ---------- Fórum Anónimo — bolhas de chat ---------- */
.kc-chat-bubble {
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid rgba(52, 211, 153, 0.15);
    border-radius: 16px;
    padding: 10px 16px;
    margin-bottom: 10px;
    backdrop-filter: blur(14px);
    transition: border-color 0.3s ease-in-out;
    animation: ccFadeSlideUp 0.5s ease-out backwards;
}
.kc-chat-bubble:hover { border-color: rgba(52, 211, 153, 0.4); }
.kc-chat-nick {
    font-weight: 700; font-size: 0.85rem;
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.kc-chat-hora { color: #55606E; font-size: 0.7rem; float: right; }
.kc-chat-texto { color: #DCE6E1; font-size: 0.92rem; margin-top: 4px; }

button, input, select, textarea, div[data-baseweb="select"] { min-height: 44px; }

/* ---------- Abas modernas (navegação em pílula) ---------- */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(13, 17, 23, 0.55);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 999px;
    padding: 5px;
    backdrop-filter: blur(12px);
}
div[data-testid="stTabs"] button[role="tab"] {
    border-radius: 999px !important;
    color: #8B92A5;
    font-weight: 600;
    padding: 8px 18px;
    transition: all 0.25s ease-in-out;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%) !important;
    color: #05070B !important;
}
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { display: none; }
div[data-testid="stTabs"] div[data-baseweb="tab-border"] { display: none; }

/* ---------- Lei / retenção ---------- */
.kc-lei-card {
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid rgba(240, 185, 11, 0.25);
    border-radius: 16px;
    padding: 20px 22px;
    backdrop-filter: blur(16px);
    margin-bottom: 1.4rem;
    animation: ccFadeSlideUp 0.7s ease-out backwards;
}
.kc-lei-titulo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem; font-weight: 700; color: #F0B90B;
    margin-bottom: 10px;
}
.kc-lei-texto { color: #DCE6E1; font-size: 0.94rem; line-height: 1.65; }
.kc-lei-disclaimer { color: #6B7280; font-size: 0.74rem; margin-top: 10px; font-style: italic; }

/* ---------- Botão flutuante de chat ---------- */
.st-key-chat_toggle_wrap {
    position: fixed !important;
    bottom: 24px; right: 24px;
    z-index: 999 !important;
    width: 60px !important;
}
.st-key-chat_toggle_wrap button {
    border-radius: 50% !important;
    width: 58px !important; height: 58px !important;
    padding: 0 !important;
    font-size: 1.5rem !important;
    box-shadow: 0 6px 22px rgba(34, 211, 238, 0.35) !important;
}

/* ---------- Painel flutuante de chat ---------- */
.st-key-chat_painel_wrap {
    position: fixed !important;
    bottom: 92px; right: 24px;
    z-index: 998 !important;
    width: 360px !important;
    max-height: 66vh;
    overflow-y: auto;
    background: rgba(13, 17, 23, 0.88);
    border: 1px solid rgba(52, 211, 153, 0.25);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    backdrop-filter: blur(18px);
    box-shadow: 0 14px 40px rgba(0,0,0,0.55);
    animation: ccFadeSlideUp 0.35s ease-out;
}

@media (max-width: 640px) {
    .st-key-chat_painel_wrap {
        width: calc(100vw - 32px) !important;
        right: 16px; left: 16px;
    }
    .st-key-chat_toggle_wrap { right: 16px; bottom: 16px; }
}

@media (max-width: 640px) {
    .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
    .kc-title { font-size: 1.7rem; }
    .kc-title-gold { font-size: 1.7rem; }
    .kc-badge { display: block; margin-left: 0; margin-top: 8px; width: fit-content; }
    .kc-metric-value { font-size: 1.2rem; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# FUNDO IMERSIVO "TO THE MOON" — CANVAS ANIMADO (deve ser o 1º iframe da página)
# ---------------------------------------------------------
def gerar_html_fundo_animado():
    return """
    <style>
      html, body { margin:0; padding:0; overflow:hidden; background:transparent; }
      canvas { display:block; }
    </style>
    <canvas id="ccBgCanvas"></canvas>
    <script>
    (function(){
      var canvas = document.getElementById('ccBgCanvas');
      var ctx = canvas.getContext('2d');
      var mouse = { x: null, y: null, ativo: false };
      var estrelas = [];
      var W = 0, H = 0, DPR = 1;
      var fasePulso = 0;

      // ---------- estado da Lua interativa ----------
      var luaGeom = { x: 0, y: 0, r: 0 };
      var crateras = [];
      var anguloRotacaoLua = 0;
      var velocidadeInerciaLua = 0;
      var arrastoAtivoLua = false;
      var ultimoXArrasto = 0;

      function medirJanela(){
        var pw = window.innerWidth, ph = window.innerHeight;
        try { pw = window.parent.innerWidth; ph = window.parent.innerHeight; } catch(e) {}
        return { pw: pw, ph: ph };
      }

      function redimensionar(){
        var medida = medirJanela();
        W = medida.pw; H = medida.ph;
        DPR = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(W * DPR);
        canvas.height = Math.floor(H * DPR);
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      }

      function criarEstrelas(){
        estrelas = [];
        var quantidade = W < 640 ? 42 : 95;
        for (var i = 0; i < quantidade; i++){
          estrelas.push({
            x: Math.random() * W, y: Math.random() * H,
            r: Math.random() * 1.5 + 0.5,
            vx: (Math.random() - 0.5) * 0.06, vy: (Math.random() - 0.5) * 0.06,
          });
        }
      }

      function calcularGeometriaLua(){
        luaGeom.x = W * 0.93;
        luaGeom.y = H * 0.05;
        luaGeom.r = Math.min(W, H) * (W < 640 ? 0.30 : 0.24);
      }

      function criarCrateras(){
        crateras = [];
        var quantidade = 150;
        for (var i = 0; i < quantidade; i++){
          var pequena = Math.random() < 0.85;
          crateras.push({
            theta: Math.random() * Math.PI * 2,
            phi: (Math.random() - 0.5) * 1.6,
            tamanho: pequena ? (Math.random() * 1.3 + 0.4) : (Math.random() * 5 + 3),
          });
        }
      }

      function distanciaEntrePontos(x1, y1, x2, y2){
        var dx = x2 - x1, dy = y2 - y1; return Math.sqrt(dx*dx + dy*dy);
      }

      function ligarRastreioDoRato(){
        function aoMover(e){
          var px = e.clientX, py = e.clientY;
          if (e.touches && e.touches.length) { px = e.touches[0].clientX; py = e.touches[0].clientY; }
          mouse.x = px; mouse.y = py; mouse.ativo = true;
        }
        function aoSair(){ mouse.ativo = false; }
        try {
          window.parent.document.addEventListener('mousemove', aoMover, { passive: true });
          window.parent.document.addEventListener('touchmove', aoMover, { passive: true });
          window.parent.document.addEventListener('mouseleave', aoSair, { passive: true });
        } catch (e) {
          document.addEventListener('mousemove', aoMover, { passive: true });
          document.addEventListener('touchmove', aoMover, { passive: true });
        }
      }

      function ligarInteracaoDaLua(){
        function extrairXY(e){
          if (e.touches && e.touches.length) return { x: e.touches[0].clientX, y: e.touches[0].clientY };
          return { x: e.clientX, y: e.clientY };
        }
        function aoDescer(e){
          var p = extrairXY(e);
          if (distanciaEntrePontos(p.x, p.y, luaGeom.x, luaGeom.y) < luaGeom.r * 1.3){
            arrastoAtivoLua = true;
            ultimoXArrasto = p.x;
          }
        }
        function aoMoverArrasto(e){
          if (!arrastoAtivoLua) return;
          var p = extrairXY(e);
          var delta = p.x - ultimoXArrasto;
          anguloRotacaoLua += delta * 0.012;
          velocidadeInerciaLua = delta * 0.012;
          ultimoXArrasto = p.x;
        }
        function aoSoltar(){ arrastoAtivoLua = false; }

        try {
          window.parent.document.addEventListener('mousedown', aoDescer, { passive: true });
          window.parent.document.addEventListener('touchstart', aoDescer, { passive: true });
          window.parent.document.addEventListener('mousemove', aoMoverArrasto, { passive: true });
          window.parent.document.addEventListener('touchmove', aoMoverArrasto, { passive: true });
          window.parent.document.addEventListener('mouseup', aoSoltar, { passive: true });
          window.parent.document.addEventListener('touchend', aoSoltar, { passive: true });
        } catch (e) {
          document.addEventListener('mousedown', aoDescer, { passive: true });
          document.addEventListener('touchstart', aoDescer, { passive: true });
          document.addEventListener('mousemove', aoMoverArrasto, { passive: true });
          document.addEventListener('touchmove', aoMoverArrasto, { passive: true });
          document.addEventListener('mouseup', aoSoltar, { passive: true });
          document.addEventListener('touchend', aoSoltar, { passive: true });
        }
      }

      function tentarExpandirParaEcraTodo(){
        try {
          var frame = window.frameElement;
          if (frame) {
            frame.style.position = 'fixed';
            frame.style.top = '0'; frame.style.left = '0';
            frame.style.width = '100vw'; frame.style.height = '100vh';
            frame.style.zIndex = '-1';
            frame.style.pointerEvents = 'none';
            frame.style.border = 'none';
          }
        } catch (e) {}
      }

      function desenharLua(){
        var x = luaGeom.x, y = luaGeom.y, r = luaGeom.r;

        // halo néon exterior (mantém a linguagem visual do resto da app)
        var gradHalo = ctx.createRadialGradient(x, y, r*0.7, x, y, r*2.0);
        gradHalo.addColorStop(0, 'rgba(180,225,255,0.30)');
        gradHalo.addColorStop(1, 'rgba(120,200,255,0)');
        ctx.fillStyle = gradHalo;
        ctx.beginPath(); ctx.arc(x, y, r*2.0, 0, Math.PI*2); ctx.fill();

        ctx.save();
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI*2); ctx.clip();

        // disco base (cinza claro, como a foto real da Lua)
        var gradDisco = ctx.createRadialGradient(x - r*0.3, y - r*0.3, r*0.1, x, y, r*1.3);
        gradDisco.addColorStop(0, '#EDF0F2');
        gradDisco.addColorStop(0.55, '#C9CFD5'
