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
        gradDisco.addColorStop(0.55, '#C9CFD5');
        gradDisco.addColorStop(1, '#8F98A1');
        ctx.fillStyle = gradDisco;
        ctx.fillRect(x - r, y - r, r*2, r*2);

        // rotação: automática + inércia do arrasto do utilizador
        anguloRotacaoLua += 0.0022 + velocidadeInerciaLua;
        velocidadeInerciaLua *= 0.94;
        if (Math.abs(velocidadeInerciaLua) < 0.00005) velocidadeInerciaLua = 0;

        for (var i = 0; i < crateras.length; i++){
          var c = crateras[i];
          var thetaEfetivo = c.theta + anguloRotacaoLua;
          var cosT = Math.cos(thetaEfetivo);
          if (cosT < -0.15) continue;
          var cx = x + Math.sin(thetaEfetivo) * r * 0.92;
          var cy = y + c.phi * r * 0.85;
          var escala = Math.max(0.15, cosT);
          var raioCratera = c.tamanho * escala;

          ctx.beginPath();
          ctx.fillStyle = 'rgba(110,116,124,' + (0.55 * escala) + ')';
          ctx.arc(cx + raioCratera*0.25, cy + raioCratera*0.25, raioCratera, 0, Math.PI*2);
          ctx.fill();

          ctx.beginPath();
          ctx.fillStyle = 'rgba(240,242,244,' + (0.55 * escala) + ')';
          ctx.arc(cx - raioCratera*0.2, cy - raioCratera*0.2, raioCratera*0.72, 0, Math.PI*2);
          ctx.fill();
        }

        // terminador — sombra fixa (a "luz" não roda com a superfície)
        var gradSombra = ctx.createLinearGradient(x - r, y - r*0.2, x + r*0.35, y + r);
        gradSombra.addColorStop(0, 'rgba(5,7,11,0)');
        gradSombra.addColorStop(0.55, 'rgba(5,7,11,0)');
        gradSombra.addColorStop(0.75, 'rgba(5,7,11,0.55)');
        gradSombra.addColorStop(1, 'rgba(5,7,11,0.88)');
        ctx.fillStyle = gradSombra;
        ctx.fillRect(x - r, y - r, r*2, r*2);

        ctx.restore();

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI*2);
        ctx.strokeStyle = 'rgba(150,225,255,0.35)';
        ctx.lineWidth = 1.4;
        ctx.stroke();
      }

      function desenhar(){
        ctx.clearRect(0, 0, W, H);

        var gradFundo = ctx.createRadialGradient(W*0.5, H*0.68, 0, W*0.5, H*0.68, Math.max(W,H)*0.8);
        gradFundo.addColorStop(0, 'rgba(35,20,60,0.32)');
        gradFundo.addColorStop(1, 'rgba(3,5,8,0)');
        ctx.fillStyle = gradFundo;
        ctx.fillRect(0, 0, W, H);

        calcularGeometriaLua();
        desenharLua();

        for (var i = 0; i < estrelas.length; i++){
          var s = estrelas[i];
          s.x += s.vx; s.y += s.vy;
          if (s.x < 0) s.x = W; if (s.x > W) s.x = 0;
          if (s.y < 0) s.y = H; if (s.y > H) s.y = 0;

          var dx = 0, dy = 0, dist = 99999;
          if (mouse.ativo && mouse.x !== null){
            dx = s.x - mouse.x; dy = s.y - mouse.y;
            dist = Math.sqrt(dx*dx + dy*dy);
          }
          var offX = 0, offY = 0;
          if (dist < 130){
            var forca = (130 - dist) / 130 * 9;
            offX = (dx/dist) * forca; offY = (dy/dist) * forca;
          }

          ctx.beginPath();
          ctx.fillStyle = 'rgba(150,230,255,0.85)';
          ctx.shadowColor = 'rgba(120,220,255,0.9)';
          ctx.shadowBlur = 4;
          ctx.arc(s.x + offX, s.y + offY, s.r, 0, Math.PI*2);
          ctx.fill();
        }
        ctx.shadowBlur = 0;

        fasePulso += 0.006;
        var pontos = 50;
        ctx.beginPath();
        for (var p = 0; p <= pontos; p++){
          var t = p / pontos;
          var x = W*0.02 + t * (luaGeom.x - W*0.05);
          var baseY = H*0.95 - t*t*(H*0.78);
          var onda = Math.sin(t*10 + fasePulso*20) * 5 * (1 - t*0.6);
          var y = baseY + onda;
          if (p === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = 'rgba(140,255,170,0.85)';
        ctx.lineWidth = 2.2;
        ctx.shadowColor = 'rgba(140,255,170,0.9)';
        ctx.shadowBlur = 11;
        ctx.stroke();
        ctx.shadowBlur = 0;

        requestAnimationFrame(desenhar);
      }

      redimensionar();
      criarEstrelas();
      criarCrateras();
      ligarRastreioDoRato();
      ligarInteracaoDaLua();
      tentarExpandirParaEcraTodo();

      window.addEventListener('resize', function(){ redimensionar(); criarEstrelas(); });
      try { window.parent.addEventListener('resize', function(){ redimensionar(); criarEstrelas(); }); } catch(e) {}

      requestAnimationFrame(desenhar);
    })();
    </script>
    """


# Este TEM de ser o primeiro st.iframe/components renderizado na página,
# para o seletor CSS ":first-of-type" o conseguir "ancorar" como fundo.
st.iframe(gerar_html_fundo_animado(), height=1)


# ---------------------------------------------------------
# LOGO SVG ANIMADO — "O RELÓGIO-TOURO INFINITO"
# ---------------------------------------------------------
def gerar_logo_svg():
    svg = """
    <svg width="56" height="56" viewBox="0 0 100 100" style="filter: drop-shadow(0 0 6px rgba(34,211,238,0.55));">
      <style>
        @keyframes ccHourSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes ccMinSpin  { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .cc-logo-hour { transform-origin: 50px 50px; animation: ccHourSpin 16s linear infinite; }
        .cc-logo-min  { transform-origin: 50px 50px; animation: ccMinSpin 6s linear infinite; }
        .cc-logo-trend { filter: drop-shadow(0 0 4px rgba(163,230,53,0.85)); }
      </style>
      <circle cx="50" cy="50" r="40" fill="none" stroke="#22D3EE" stroke-width="2.5" opacity="0.8"/>
      <line class="cc-logo-hour" x1="50" y1="50" x2="50" y2="30" stroke="#8CFBFF" stroke-width="3.5" stroke-linecap="round"/>
      <line class="cc-logo-min" x1="50" y1="50" x2="68" y2="50" stroke="#22D3EE" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="50" cy="50" r="3" fill="#8CFBFF"/>
      <path class="cc-logo-trend" d="M22,70 L40,58 L52,63 L66,36 L78,24" fill="none" stroke="#A3E635" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
      <polygon class="cc-logo-trend" points="78,24 71,27.5 74.5,33" fill="#A3E635"/>
    </svg>
    """
    return textwrap.dedent(svg).strip()


# ---------------------------------------------------------
# GERADOR DO "CRYPTOCLOCK GRID" — CARTÕES COM RELÓGIO AO VIVO (HTML+JS)
# ---------------------------------------------------------
CSS_CARTOES_LOTES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=JetBrains+Mono:wght@600;700&display=swap');
* { box-sizing: border-box; }
body { margin: 0; padding: 4px; font-family: 'Inter', sans-serif; background: transparent; }

@keyframes ccFadeSlideUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes ccSoftFlicker { 0% { opacity: 0.55; } 100% { opacity: 1; } }
@keyframes ccPulseGlow {
    0%   { box-shadow: 0 0 0 1px rgba(52,211,153,0.08), 0 10px 30px rgba(0,0,0,0.45), 0 0 0px rgba(253, 186, 116, 0.0); }
    50%  { box-shadow: 0 0 0 1px rgba(52,211,153,0.08), 0 10px 30px rgba(0,0,0,0.45), 0 0 22px rgba(253, 186, 116, 0.4); }
    100% { box-shadow: 0 0 0 1px rgba(52,211,153,0.08), 0 10px 30px rgba(0,0,0,0.45), 0 0 0px rgba(253, 186, 116, 0.0); }
}

.cc-grid { display: flex; flex-direction: column; gap: 14px; }
.cc-card {
    background: rgba(13, 17, 23, 0.72);
    border: 1px solid rgba(52, 211, 153, 0.18);
    border-radius: 16px;
    padding: 16px 18px;
    backdrop-filter: blur(16px);
    box-shadow: 0 0 0 1px rgba(34,211,238,0.04), 0 10px 30px rgba(0,0,0,0.45);
    position: relative;
    overflow: hidden;
    transition: transform 0.3s ease-in-out, border-color 0.3s ease-in-out;
    animation: ccFadeSlideUp 0.6s ease-out backwards;
}
.cc-card:hover { transform: translateY(-3px); border-color: rgba(52, 211, 153, 0.55); }
.cc-card.cc-pulse { animation: ccFadeSlideUp 0.6s ease-out backwards, ccPulseGlow 2.6s ease-in-out infinite; }

.cc-card-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.cc-asset-name { font-family: 'Space Grotesk', sans-serif; font-size: 1.18rem; font-weight: 700; color: #ECF3F0; }
.cc-sub { color: #8B92A5; font-size: 0.82rem; margin-top: 4px; }

.cc-badge { display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em; white-space: nowrap; }
.cc-badge-isento { background: rgba(52, 211, 153, 0.14); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.4); }
.cc-badge-contando {
    background: rgba(253, 186, 116, 0.14); color: #FDBA74; border: 1px solid rgba(253, 186, 116, 0.4);
    animation: ccSoftFlicker 1.6s ease-in-out infinite alternate;
}

.cc-progress-track { width: 100%; height: 8px; border-radius: 999px; background: rgba(255,255,255,0.08); margin-top: 12px; overflow: hidden; }
.cc-progress-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #22D3EE 0%, #34D399 100%);
    box-shadow: 0 0 12px rgba(52, 211, 153, 0.6);
    transition: width 0.6s ease;
}

.cc-countdown { font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 700; color: #A9FBEA; margin-top: 12px; letter-spacing: 0.03em; display: flex; gap: 6px; flex-wrap: wrap; }
.cc-countdown span.cc-unit { background: rgba(52, 211, 153, 0.08); border: 1px solid rgba(52, 211, 153, 0.2); border-radius: 8px; padding: 2px 8px; transition: opacity 0.25s ease; }
</style>
"""

SCRIPT_CARTOES_LOTES = """
<script>
function ccPad(n){ return String(n).padStart(2,'0'); }
function ccMontarHTML(d, h, m, s){
    return '<span class="cc-unit">' + d + 'd</span> : ' +
           '<span class="cc-unit">' + ccPad(h) + 'h</span> : ' +
           '<span class="cc-unit">' + ccPad(m) + 'm</span> : ' +
           '<span class="cc-unit">' + ccPad(s) + 's</span>';
}
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
      if (elCd) elCd.innerHTML = '✅ Isento — parabéns!';
      if (elBadge) { elBadge.textContent = 'LIVRE DE IMPOSTOS ✅'; elBadge.className = 'cc-badge cc-badge-isento'; }
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

      if (elCd) {
        elCd.style.opacity = '0.55';
        elCd.innerHTML = ccMontarHTML(d, h, m, s);
        requestAnimationFrame(function(){ elCd.style.opacity = '1'; });
      }
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
    altura_estimada = max(230, 40 + len(lotes_ordenados) * 200)
    st.iframe(html_final, height=altura_estimada)


def widget_tradingview(symbol, container_id, altura=460):
    return f"""
    <div class="tradingview-widget-container">
      <div id="{container_id}"></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>
      new TradingView.widget({{
        "width": "100%", "height": {altura}, "symbol": "{symbol}", "interval": "60",
        "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "pt",
        "toolbar_bg": "#05070B", "enable_publishing": false, "hide_top_toolbar": false,
        "save_image": false, "container_id": "{container_id}"
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
    dados_para_exportar = json.dumps(st.session_state.compras, ensure_ascii=False, indent=2, default=str)
    st.download_button(
        label="Descarregar backup (.json)", data=dados_para_exportar,
        file_name="cryptoclock_backup.json", mime="application/json",
        use_container_width=True, disabled=len(st.session_state.compras) == 0,
    )
    st.markdown("---")
    st.markdown("**⬆️ Importar Dados**")
    ficheiro_importado = st.file_uploader(
        "Carrega o teu ficheiro cryptoclock_backup.json", type=["json"], label_visibility="collapsed",
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
# CABEÇALHO (logo SVG animado + título com gradiente)
# ---------------------------------------------------------
st.markdown(f"""
<div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap;">
{gerar_logo_svg()}
<div>
<span class="kc-title-gold">Crypto</span><span class="kc-title">Clock</span><span class="kc-badge">v1.0 · Portugal Fiscal Compliance</span>
</div>
</div>
<div class="kc-subtitle">Uma experiência cinemática para acompanhar os teus 365 dias de isenção de IRS, o mercado ao vivo e a comunidade.</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# CÁLCULOS DOS LOTES
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

    fracao_concluida = 1.0 if isento else min(max(1 - (diferenca.total_seconds() / SEGUNDOS_EM_365_DIAS), 0.0), 1.0)

    total_investido += compra["valor_pago_eur"]
    if isento:
        total_isento += compra["valor_pago_eur"]
    else:
        total_em_contagem += compra["valor_pago_eur"]

    lotes_calculados.append({
        **compra, "momento_compra": momento_compra, "momento_isencao": momento_isencao,
        "isento": isento, "fracao_concluida": fracao_concluida,
    })

lotes_ordenados = sorted(lotes_calculados, key=lambda x: x["momento_isencao"])


# ---------------------------------------------------------
# ABAS PRINCIPAIS
# ---------------------------------------------------------
tab_meu, tab_mercado, tab_forum = st.tabs([
    "🕒 O Meu CryptoClock", "📈 Cockpit de Mercado", "💬 Fórum Anónimo"
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
                    "id": uuid.uuid4().hex, "data_compra": str(data_compra_input),
                    "ativo": ativo.upper().strip(), "quantidade": quantidade,
                    "valor_pago_eur": valor_pago, "plataforma": plataforma.strip(),
                })
                st.success("✅ Compra guardada com sucesso!")
                st.rerun()

    st.markdown('<div class="kc-section-title">⏱️ Painel de Lotes (CryptoClock Grid)</div>', unsafe_allow_html=True)

    if not lotes_calculados:
        st.info("Ainda não tens nenhuma compra registada. Usa o formulário acima para adicionar a primeira.")
    else:
        renderizar_grid_de_lotes(lotes_ordenados)

        with st.expander("🗑️ Gerir / eliminar um lote"):
            opcoes = {
                lote["id"]: f"{lote['ativo']} · {lote['plataforma']} · {lote['data_compra']} · {formatar_euros(lote['valor_pago_eur'])}"
                for lote in lotes_ordenados
            }
            id_selecionado = st.selectbox(
                "Escolhe o lote que queres remover", options=list(opcoes.keys()),
                format_func=lambda id_lote: opcoes[id_lote], label_visibility="collapsed",
            )
            if st.button("❌ Eliminar Lote Selecionado"):
                remover_compra_por_id(id_selecionado)
                st.success("Lote removido com sucesso!")
                st.rerun()


# ===========================================================
# TAB 2 — COCKPIT DE MERCADO
# ===========================================================
with tab_mercado:
    st.markdown('<div class="kc-section-title">📈 Cockpit de Mercado</div>', unsafe_allow_html=True)
    st.caption("Gráficos oficiais da TradingView, em tempo real, modo escuro absoluto.")

    st.markdown("**🪙 BTC/USDT**")
    st.iframe(widget_tradingview("BINANCE:BTCUSDT", "tv_btc_full", altura=460), height=480)

    st.markdown("**♦️ ETH/USDT**")
    st.iframe(widget_tradingview("BINANCE:ETHUSDT", "tv_eth_full", altura=460), height=480)


# ===========================================================
# TAB 3 — FÓRUM ANÓNIMO
# ===========================================================
@st.fragment(run_every=5)
def widget_forum_ao_vivo():
    if "nick" not in st.session_state:
        st.session_state.nick = ""

    st.session_state.nick = st.text_input(
        "O teu Pseudónimo Neon", value=st.session_state.nick,
        placeholder="Ex: BitcoinWhale99, CryptoAnonymous...",
    )

    with st.form("form_forum", clear_on_submit=True):
        texto_mensagem = st.text_area("Mensagem", placeholder="Partilha a tua previsão de mercado ou opinião...", height=80)
        enviar_mensagem = st.form_submit_button("Enviar 🚀")

        if enviar_mensagem:
            if not st.session_state.nick.strip():
                st.error("Escolhe primeiro um Pseudónimo Neon.")
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
        st.caption("Ainda não há mensagens. Sê o primeiro a partilhar uma previsão! 👋")
    else:
        for msg in reversed(mensagens):
            st.markdown(f"""<div class="kc-chat-bubble">
<span class="kc-chat-nick">{msg.get('nick', 'Anónimo')}</span>
<span class="kc-chat-hora">{msg.get('hora', '')}</span>
<div class="kc-chat-texto">{msg.get('texto', '')}</div>
</div>""", unsafe_allow_html=True)

    st.caption("🟢 Ao vivo — esta zona atualiza-se sozinha a cada 5 segundos.")


with tab_forum:
    st.markdown('<div class="kc-section-title">💬 Fórum Anónimo</div>', unsafe_allow_html=True)
    st.caption("Partilha previsões de mercado e opiniões, de forma totalmente anónima.")

    if not GSHEETS_DISPONIVEL or conn_gsheets is None:
        st.warning(
            "O Fórum ainda não está ligado à Google Sheet. Confirma que:\n\n"
            "1. Adicionaste `st-gsheets-connection` ao `requirements.txt`\n"
            "2. Configuraste os **Secrets** da app em share.streamlit.io → Settings → Secrets\n"
            "3. Partilhaste a folha com o email do teu Service Account, como **Editor**"
        )
        if erro_ligacao_gsheets:
            with st.expander("🔧 Ver detalhe técnico do erro (copia isto e envia ao Claude)"):
                st.code(erro_ligacao_gsheets)
    else:
        widget_forum_ao_vivo()
