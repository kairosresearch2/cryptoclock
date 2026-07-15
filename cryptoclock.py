import streamlit as st
import json
import uuid
from datetime import date, datetime, timedelta

# ---------------------------------------------------------
# CONFIGURAÇÃO BÁSICA
# ---------------------------------------------------------
st.set_page_config(page_title="CryptoClock", page_icon="🕒", layout="centered")


# ---------------------------------------------------------
# "BASE DE DADOS" DESTA SESSÃO (st.session_state)
# ---------------------------------------------------------
# Cada pessoa que abre o link tem o seu próprio st.session_state,
# por isso os dados de cada utilizador ficam sempre privados e
# separados dos dados de outra pessoa que esteja a usar a app
# ao mesmo tempo. Nada é escrito num ficheiro no servidor.
if "compras" not in st.session_state:
    st.session_state.compras = []


def adicionar_id_se_faltar(lista_de_compras):
    """Garante que toda a compra tem um 'id' único, mesmo as importadas."""
    for compra in lista_de_compras:
        if "id" not in compra:
            compra["id"] = uuid.uuid4().hex
    return lista_de_compras


def remover_compra_por_id(id_a_remover):
    st.session_state.compras = [
        c for c in st.session_state.compras if c["id"] != id_a_remover
    ]


def formatar_euros(valor):
    """Formata um número para o estilo português: € 1.234,56"""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return f"€ {texto}"


# ---------------------------------------------------------
# CSS CUSTOMIZADO — VISUAL "FINTECH DARK MODE" + RESPONSIVO
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"], .stMarkdown, p, span, label, div {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #0B0E14;
}

.block-container {
    padding-top: 2.2rem;
    padding-left: 1.2rem;
    padding-right: 1.2rem;
    max-width: 900px;
}

section[data-testid="stSidebar"] {
    background-color: #0F1420;
    border-right: 1px solid #1F2430;
}

/* ---------- Cabeçalho ---------- */
.kc-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1.1;
    background: linear-gradient(90deg, #C6FF3D 0%, #34D8FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    vertical-align: middle;
}
.kc-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    background: rgba(52, 216, 255, 0.12);
    border: 1px solid rgba(52, 216, 255, 0.35);
    color: #7FE6FF;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-left: 10px;
    vertical-align: middle;
}
.kc-subtitle {
    color: #8B92A5;
    font-size: 0.93rem;
    margin-top: 6px;
    margin-bottom: 1.8rem;
}

/* ---------- KPI Cards ---------- */
.kc-card {
    background: #131720;
    border: 1px solid #1F2430;
    border-radius: 16px;
    padding: 16px 18px;
    height: 100%;
}
.kc-metric-label {
    color: #8B92A5;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
}
.kc-metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: #E6E8EC;
}
.kc-metric-value.green { color: #34D399; }
.kc-metric-value.orange { color: #FDBA74; }

/* ---------- Secções ---------- */
.kc-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    background: linear-gradient(90deg, #C6FF3D 0%, #34D8FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
    margin-top: 2rem;
    margin-bottom: 0.9rem;
}

/* ---------- Grid / Tabela de Lotes ---------- */
.kc-grid-wrap {
    background: #131720;
    border: 1px solid #1F2430;
    border-radius: 16px;
    padding: 4px 14px;
    overflow-x: auto;
}
.kc-grid {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.kc-grid th {
    text-align: left;
    color: #8B92A5;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 10px;
    border-bottom: 1px solid #1F2430;
    white-space: nowrap;
}
.kc-grid td {
    padding: 13px 10px;
    border-bottom: 1px solid #191D26;
    color: #E6E8EC;
    white-space: nowrap;
}
.kc-grid tr:last-child td { border-bottom: none; }
.kc-grid tr:hover td { background: #171B24; }
.kc-mono { font-family: 'JetBrains Mono', monospace; }
.kc-asset { font-weight: 700; color: #E6E8EC; }
.kc-provider { color: #8B92A5; font-size: 0.76rem; }

.kc-pill {
    display: inline-block;
    padding: 4px 11px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 600;
    white-space: nowrap;
}
.kc-pill.isento {
    background: rgba(52, 211, 153, 0.12);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
}
.kc-pill.contando {
    background: rgba(251, 146, 60, 0.12);
    color: #FDBA74;
    border: 1px solid rgba(251, 146, 60, 0.35);
}

/* ---------- Formulário compacto ---------- */
div[data-testid="stForm"] {
    background: #131720;
    border: 1px solid #1F2430;
    border-radius: 18px;
    padding: 1.2rem 1.2rem 0.2rem 1.2rem;
}

/* ---------- Zona de remoção ---------- */
.kc-remove-wrap {
    background: #17121A;
    border: 1px solid #3A1F26;
    border-radius: 16px;
    padding: 1rem 1.2rem 1.2rem 1.2rem;
    margin-top: 0.6rem;
}

/* botão vermelho "Remover Lote Selecionado" */
div[data-testid="stButton"] button {
    background-color: #FF4D5E;
    color: #0B0E14;
    border: none;
    font-weight: 700;
    border-radius: 10px;
    padding: 0.55rem 1rem;
    width: 100%;
}
div[data-testid="stButton"] button:hover {
    background-color: #FF6B7A;
    color: #0B0E14;
}

/* botão de exportar (download), verde-ciano para combinar com a marca */
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #C6FF3D 0%, #34D8FF 100%);
    color: #0B0E14;
    border: none;
    font-weight: 700;
    border-radius: 10px;
    width: 100%;
}

/* ---------- Toques de acessibilidade tátil (telemóvel) ---------- */
button, input, select, textarea, div[data-baseweb="select"] {
    min-height: 42px;
}

/* ---------- Responsivo: ecrãs pequenos (telemóvel) ---------- */
@media (max-width: 640px) {
    .block-container { padding-left: 0.7rem; padding-right: 0.7rem; }
    .kc-title { font-size: 1.9rem; }
    .kc-badge { display: block; margin-left: 0; margin-top: 8px; width: fit-content; }
    .kc-metric-value { font-size: 1.15rem; }
    .kc-grid { font-size: 0.76rem; }
    .kc-grid th, .kc-grid td { padding: 9px 6px; }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# BARRA LATERAL — DISPOSITIVO & BACKUP
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### Dispositivo & Backup 💾")
    st.caption(
        "Este app não guarda os teus dados num servidor. "
        "Eles existem apenas enquanto esta aba do browser estiver aberta. "
        "Exporta o teu ficheiro sempre que quiseres guardar o progresso, "
        "e importa-o na próxima vez que abrires a app."
    )

    st.markdown("**⬇️ Exportar Dados**")
    dados_para_exportar = json.dumps(st.session_state.compras, ensure_ascii=False, indent=2, default=str)
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

            st.warning(
                f"Encontrei {len(dados_lidos)} transação(ões) neste ficheiro. "
                "Isto vai substituir os dados atuais desta sessão."
            )
            if st.button("📥 Confirmar Importação"):
                st.session_state.compras = adicionar_id_se_faltar(dados_lidos)
                st.success("Dados importados com sucesso!")
                st.rerun()
        except (json.JSONDecodeError, ValueError):
            st.error("Este ficheiro não parece ser um backup válido do CryptoClock.")


# ---------------------------------------------------------
# CABEÇALHO
# ---------------------------------------------------------
st.markdown("""
<span class="kc-title">🕒 CryptoClock</span><span class="kc-badge">v1.0 · Portugal Fiscal Compliance</span>
<div class="kc-subtitle">Regista as tuas compras de cripto e acompanha a contagem para a isenção de IRS ao fim de 365 dias, lote a lote.</div>
""", unsafe_allow_html=True)

st.info(
    "🔒 **Privado por sessão:** os teus dados só aparecem para ti neste browser. "
    "Ninguém mais vê as tuas transações, mesmo partilhando o mesmo link. "
    "Usa o **Exportar Dados** na barra lateral para não perderes o progresso.",
    icon="🔒",
)


# ---------------------------------------------------------
# CÁLCULOS (a partir do st.session_state)
# ---------------------------------------------------------
hoje = date.today()

total_investido = 0.0
total_isento = 0.0
total_em_contagem = 0.0
lotes_calculados = []

for compra in st.session_state.compras:
    data_compra = datetime.strptime(compra["data_compra"], "%Y-%m-%d").date()
    data_isencao = data_compra + timedelta(days=365)
    dias_restantes = (data_isencao - hoje).days
    isento = dias_restantes <= 0

    total_investido += compra["valor_pago_eur"]
    if isento:
        total_isento += compra["valor_pago_eur"]
    else:
        total_em_contagem += compra["valor_pago_eur"]

    lotes_calculados.append({
        **compra,
        "data_isencao": data_isencao,
        "dias_restantes": dias_restantes,
        "isento": isento,
    })

lotes_ordenados = sorted(lotes_calculados, key=lambda x: x["data_isencao"])


# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(f"""
    <div class="kc-card">
        <div class="kc-metric-label">Total Investido</div>
        <div class="kc-metric-value">{formatar_euros(total_investido)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kc-card">
        <div class="kc-metric-label">✅ Ativos Isentos</div>
        <div class="kc-metric-value green">{formatar_euros(total_isento)}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kc-card">
        <div class="kc-metric-label">⏳ Em Contagem</div>
        <div class="kc-metric-value orange">{formatar_euros(total_em_contagem)}</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# FORMULÁRIO — REGISTAR NOVA COMPRA (compacto, em colunas)
# ---------------------------------------------------------
st.markdown('<div class="kc-section-title">➕ Registar nova compra</div>', unsafe_allow_html=True)

with st.form("form_nova_compra", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        data_compra_input = st.date_input("Data da Compra", value=date.today())
        ativo = st.text_input("Ativo (Ex: BTC, USDT, ETH)")
        quantidade = st.number_input(
            "Quantidade Comprada",
            min_value=0.0,
            value=0.0,
            step=0.0001,
            format="%.8f",
        )

    with col2:
        valor_pago = st.number_input(
            "Valor Pago em Euros (€)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
        )
        plataforma = st.text_input("Plataforma/Provedor (Ex: BingX, Ledger)")

    enviado = st.form_submit_button("Guardar Compra")

    if enviado:
        if not ativo or quantidade <= 0 or valor_pago <= 0 or not plataforma:
            st.error("Por favor, preenche todos os campos corretamente antes de guardar.")
        else:
            nova_compra = {
                "id": uuid.uuid4().hex,
                "data_compra": str(data_compra_input),
                "ativo": ativo.upper().strip(),
                "quantidade": quantidade,
                "valor_pago_eur": valor_pago,
                "plataforma": plataforma.strip(),
            }
            st.session_state.compras.append(nova_compra)
            st.success("✅ Compra guardada com sucesso!")
            st.rerun()


# ---------------------------------------------------------
# PAINEL DE LOTES — O "CRYPTOCLOCK GRID"
# ---------------------------------------------------------
st.markdown('<div class="kc-section-title">⏱️ Painel de Lotes (CryptoClock Grid)</div>', unsafe_allow_html=True)

if not lotes_calculados:
    st.info("Ainda não tens nenhuma compra registada. Usa o formulário acima para adicionar a primeira.")
else:
    linhas_html = ""
    for lote in lotes_ordenados:
        if lote["isento"]:
            pill_html = '<span class="kc-pill isento">🟢 Isento (Tax Free)</span>'
        else:
            pill_html = f'<span class="kc-pill contando">⚡ {lote["dias_restantes"]} dias</span>'

        linhas_html += f"""
        <tr>
            <td>
                <div class="kc-asset">{lote['ativo']}</div>
                <div class="kc-provider">{lote['plataforma']}</div>
            </td>
            <td class="kc-mono">{lote['quantidade']}</td>
            <td class="kc-mono">{formatar_euros(lote['valor_pago_eur'])}</td>
            <td class="kc-mono">{lote['data_compra']}</td>
            <td class="kc-mono">{lote['data_isencao'].strftime('%Y-%m-%d')}</td>
            <td>{pill_html}</td>
        </tr>
        """

    tabela_html = f"""
    <div class="kc-grid-wrap">
        <table class="kc-grid">
            <thead>
                <tr>
                    <th>Ativo / Provedor</th>
                    <th>Quantidade</th>
                    <th>Valor Pago</th>
                    <th>Data da Compra</th>
                    <th>Data de Isenção</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {linhas_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(tabela_html, unsafe_allow_html=True)

    # -------------------------------------------------------
    # REMOVER / LIQUIDAR UM LOTE
    # -------------------------------------------------------
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
