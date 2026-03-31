from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

# ============================================================
# PATH DEL PAQUETE
# ============================================================

PROJECT_SRC = Path(__file__).resolve().parent / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from ordagosimulator.core import Hand, hand_key

# ============================================================
# CONFIG
# ============================================================

TABLE_PATH = Path(__file__).resolve().parent / "data" / "partner_known_exact_master.parquet"
RANKS = ["A", "4", "5", "6", "7", "S", "C", "R"]

POSITION_OPTIONS = {
    "1 (mano)": 0,
    "2": 1,
    "3": 2,
    "4 (postre)": 3,
}
POSITION_LABELS = {v: k for k, v in POSITION_OPTIONS.items()}

st.set_page_config(
    page_title="OrdagoSimulator",
    page_icon="🃏",
    layout="wide",
)

# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top, rgba(255,255,255,0.08), transparent 25%),
            linear-gradient(180deg, #0d5f36 0%, #0c4d2d 55%, #09341f 100%);
    }

    .main-title {
        font-size: 2.7rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.15rem;
    }

    .subtitle {
        color: rgba(255,255,255,0.82);
        font-size: 1rem;
        margin-bottom: 0.2rem;
    }

    .subsubtitle {
        color: rgba(255,255,255,0.70);
        font-size: 0.92rem;
        margin-bottom: 1.2rem;
    }

    .panel {
        background: rgba(0,0,0,0.18);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 24px;
        padding: 18px 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 14px 34px rgba(0,0,0,0.18);
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.75rem;
    }

    .small-note {
        color: rgba(255,255,255,0.74);
        font-size: 0.92rem;
    }

    .player-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 999px;
        background: rgba(0,0,0,0.20);
        border: 1px solid rgba(255,255,255,0.10);
        color: rgba(255,255,255,0.90);
        font-size: 0.95rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 0 auto 0.9rem auto;
    }

    .player-wrap {
        text-align: center;
        margin-top: 1.2rem;
        margin-bottom: 2rem;
    }

    .card-box {
        background: white;
        border-radius: 20px;
        border: 2px solid rgba(0,0,0,0.08);
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
        padding: 10px 10px 14px 10px;
        text-align: center;
        margin-bottom: 0.35rem;
    }

    .card-rank-top {
        text-align: left;
        font-size: 1rem;
        font-weight: 900;
        color: #111827;
        line-height: 1.1;
        min-height: 2rem;
    }

    .card-rank-center {
        font-size: 1.8rem;
        font-weight: 900;
        color: #111827;
        padding: 16px 0 10px 0;
        line-height: 1.1;
        min-height: 3.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .card-caption {
        color: rgba(255,255,255,0.74);
        font-size: 0.78rem;
        text-align: center;
        margin-bottom: 0.3rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }

    .button-panel {
        margin-top: 0.8rem;
        margin-bottom: 1.2rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(0,0,0,0.20);
        border: 1px solid rgba(255,255,255,0.10);
        padding: 12px 14px;
        border-radius: 18px;
    }

    div[data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.72);
    }

    div[data-testid="stMetricValue"] {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_table(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["lookup_key"] = (
        df["my_pos"].astype(str)
        + "|"
        + df["partner_pos"].astype(str)
        + "|"
        + df["my_hand_key"]
        + "|"
        + df["partner_hand_key"]
    )
    return df.set_index("lookup_key")


table = load_table(str(TABLE_PATH))

# ============================================================
# HELPERS
# ============================================================

def build_hand(cards: list[str]) -> Hand:
    return Hand.from_string(",".join(cards))


def pct(x: float) -> str:
    return f"{100*x:.2f}%"


def partner_pos_of(my_pos: int) -> int:
    return (my_pos + 2) % 4


def rank_label(rank: str) -> str:
    if rank == "A":
        return "As / 2"
    if rank == "S":
        return "Sota"
    if rank == "C":
        return "Caballo"
    if rank == "R":
        return "Rey / 3"
    return rank


def render_card_selector(col, label: str, key_prefix: str):
    rank = col.selectbox(label, RANKS, key=key_prefix)
    shown = rank_label(rank)
    col.markdown(
        f"""
        <div class="card-caption">{label}</div>
        <div class="card-box">
            <div class="card-rank-top">{shown}</div>
            <div class="card-rank-center">{shown}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return rank


def query_table(my_pos: int, my_cards: list[str], partner_cards: list[str]) -> dict:
    partner_pos = partner_pos_of(my_pos)
    my_hand = build_hand(my_cards)
    partner_hand = build_hand(partner_cards)

    key = f"{my_pos}|{partner_pos}|{hand_key(my_hand)}|{hand_key(partner_hand)}"
    if key not in table.index:
        raise KeyError("La combinación no existe en la tabla maestra.")

    row = table.loc[key]
    return {
        "my_pos": int(row["my_pos"]),
        "partner_pos": int(row["partner_pos"]),
        "my_hand_str": my_hand.to_string(),
        "partner_hand_str": partner_hand.to_string(),
        "p_grande_win": float(row["p_grande_win"]),
        "p_chica_win": float(row["p_chica_win"]),
        "p_pares_reached": float(row["p_pares_reached"]),
        "p_pares_win_given_reached": float(row["p_pares_win_given_reached"]),
        "p_pares_win": float(row["p_pares_win"]),
        "p_juego_reached": float(row["p_juego_reached"]),
        "p_juego_win_given_reached": float(row["p_juego_win_given_reached"]),
        "p_juego_win": float(row["p_juego_win"]),
        "p_punto_reached": float(row["p_punto_reached"]),
        "p_punto_win_given_reached": float(row["p_punto_win_given_reached"]),
        "p_punto_win": float(row["p_punto_win"]),
        "total_weight": float(row["total_weight"]),
    }

# ============================================================
# HEADER
# ============================================================

st.markdown('<div class="main-title">OrdagoSimulator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Consulta exacta de probabilidades de mus.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subsubtitle">Configurado para mus de 8 reyes.</div>',
    unsafe_allow_html=True,
)

# ============================================================
# CONFIGURACIÓN SUPERIOR
# ============================================================

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Configuración de la mesa</div>', unsafe_allow_html=True)

position_label = st.selectbox(
    "Tu posición",
    list(POSITION_OPTIONS.keys()),
    index=0,
)
my_pos = POSITION_OPTIONS[position_label]
partner_pos = partner_pos_of(my_pos)
partner_label = POSITION_LABELS[partner_pos]

st.markdown(
    f'<div class="small-note">Posición deducida del compañero: <b>{partner_label}</b></div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# CARTAS: TÚ ARRIBA
# ============================================================

st.markdown('<div class="player-wrap"><div class="player-badge">Tú</div></div>', unsafe_allow_html=True)
top_cols = st.columns([1, 1, 1, 1, 1, 1])
my_cards = [
    render_card_selector(top_cols[1], "Carta 1", "my_1"),
    render_card_selector(top_cols[2], "Carta 2", "my_2"),
    render_card_selector(top_cols[3], "Carta 3", "my_3"),
    render_card_selector(top_cols[4], "Carta 4", "my_4"),
]

st.markdown("<br><br>", unsafe_allow_html=True)

# ============================================================
# CARTAS: COMPAÑERO ABAJO
# ============================================================

st.markdown('<div class="player-wrap"><div class="player-badge">Compañero</div></div>', unsafe_allow_html=True)
bottom_cols = st.columns([1, 1, 1, 1, 1, 1])
partner_cards = [
    render_card_selector(bottom_cols[1], "Carta 1", "partner_1"),
    render_card_selector(bottom_cols[2], "Carta 2", "partner_2"),
    render_card_selector(bottom_cols[3], "Carta 3", "partner_3"),
    render_card_selector(bottom_cols[4], "Carta 4", "partner_4"),
]

# ============================================================
# BOTÓN ABAJO
# ============================================================

st.markdown('<div class="button-panel">', unsafe_allow_html=True)
run = st.button("Calcular probabilidades", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# RESULTADOS ABAJO
# ============================================================

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Resultados</div>', unsafe_allow_html=True)

if run:
    try:
        res = query_table(my_pos, my_cards, partner_cards)

        st.markdown(
            f'<div class="small-note"><b>Tus cartas:</b> {res["my_hand_str"]} &nbsp;&nbsp; '
            f'<b>Cartas del compañero:</b> {res["partner_hand_str"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### Grande / Chica")
        c1, c2 = st.columns(2)
        c1.metric("Grande", pct(res["p_grande_win"]))
        c2.metric("Chica", pct(res["p_chica_win"]))

        st.markdown("### Pares")
        c1, c2, c3 = st.columns(3)
        c1.metric("Llegar a pares", pct(res["p_pares_reached"]))
        c2.metric("Ganar pares | pares", pct(res["p_pares_win_given_reached"]))
        c3.metric("Ganar pares", pct(res["p_pares_win"]))

        st.markdown("### Juego")
        c1, c2, c3 = st.columns(3)
        c1.metric("Llegar a juego", pct(res["p_juego_reached"]))
        c2.metric("Ganar juego | juego", pct(res["p_juego_win_given_reached"]))
        c3.metric("Ganar juego", pct(res["p_juego_win"]))

        st.markdown("### Punto")
        c1, c2, c3 = st.columns(3)
        c1.metric("Llegar a punto", pct(res["p_punto_reached"]))
        c2.metric("Ganar punto | punto", pct(res["p_punto_win_given_reached"]))
        c3.metric("Ganar punto", pct(res["p_punto_win"]))

    except Exception as e:
        st.error(str(e))
else:
    st.info("Selecciona posición y cartas, y pulsa el botón para consultar.")

st.markdown("</div>", unsafe_allow_html=True)
