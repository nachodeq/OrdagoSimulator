from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_SRC = Path(__file__).resolve().parent / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from ordagosimulator.core import Hand, hand_key

TABLE_PATH = Path(__file__).resolve().parent / "data" / "partner_known_exact_master.parquet"
RANKS = ["A", "4", "5", "6", "7", "S", "C", "R"]

st.set_page_config(
    page_title="OrdagoSimulator",
    page_icon="🃏",
    layout="wide",
)

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

def build_hand(cards: list[str]) -> Hand:
    return Hand.from_string(",".join(cards))

def pct(x: float) -> str:
    return f"{100*x:.2f}%"

def query_table(my_pos: int, my_cards: list[str], partner_cards: list[str]) -> dict:
    partner_pos = (my_pos + 2) % 4
    my_hand = build_hand(my_cards)
    partner_hand = build_hand(partner_cards)

    key = f"{my_pos}|{partner_pos}|{hand_key(my_hand)}|{hand_key(partner_hand)}"
    if key not in table.index:
        raise KeyError(f"Combination not found in master table: {key}")

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

def card_select_row(prefix: str):
    cols = st.columns(4)
    return [
        cols[0].selectbox("Carta 1", RANKS, key=f"{prefix}_1"),
        cols[1].selectbox("Carta 2", RANKS, key=f"{prefix}_2"),
        cols[2].selectbox("Carta 3", RANKS, key=f"{prefix}_3"),
        cols[3].selectbox("Carta 4", RANKS, key=f"{prefix}_4"),
    ]

st.title("OrdagoSimulator")
st.caption("Consulta exacta de probabilidades de mus a partir de tabla maestra precomputada")

left, right = st.columns([1, 2])

with left:
    st.subheader("Entrada")
    my_pos = st.selectbox(
        "Tu posición",
        [0, 1, 2, 3],
        help="0 = mano, 3 = postre",
    )
    partner_pos = (my_pos + 2) % 4
    st.write(f"Posición deducida del compañero: **{partner_pos}**")

    st.markdown("### Tus cartas")
    my_cards = card_select_row("my")

    st.markdown("### Cartas del compañero")
    partner_cards = card_select_row("partner")

    run = st.button("Calcular probabilidades", use_container_width=True)

with right:
    st.subheader("Resultados")

    if run:
        try:
            res = query_table(my_pos, my_cards, partner_cards)

            st.write(f"**Tus cartas:** {res['my_hand_str']}")
            st.write(f"**Cartas del compañero:** {res['partner_hand_str']}")

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

            with st.expander("Detalles técnicos"):
                st.json(res)

        except Exception as e:
            st.error(str(e))
    else:
        st.info("Selecciona posición y cartas, y pulsa el botón para consultar.")
