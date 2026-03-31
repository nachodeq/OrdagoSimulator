from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_SRC = Path(__file__).resolve().parent / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from ordagosimulator.core import Hand, hand_key

TABLE_PATH = Path(
    os.getenv(
        "TABLE_PATH",
        str(Path(__file__).resolve().parent / "data" / "partner_known_exact_master.parquet"),
    )
)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

app = FastAPI(title="OrdagoSimulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Table not found: {path}")

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


TABLE = load_table(TABLE_PATH)


class QueryRequest(BaseModel):
    my_pos: int = Field(..., ge=0, le=3)
    my_cards: list[str]
    partner_cards: list[str]


class QueryResponse(BaseModel):
    my_pos: int
    partner_pos: int
    p_grande_win: float
    p_chica_win: float
    p_pares_reached: float
    p_pares_win_given_reached: float
    p_pares_win: float
    p_juego_reached: float
    p_juego_win_given_reached: float
    p_juego_win: float
    p_punto_reached: float
    p_punto_win_given_reached: float
    p_punto_win: float
    total_weight: float


def normalize_hand(cards: list[str]) -> Hand:
    if len(cards) != 4:
        raise HTTPException(status_code=400, detail="Each hand must contain exactly 4 cards.")
    try:
        return Hand.from_string(",".join(cards))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid hand: {e}")


@app.get("/health")
def health():
    return {
        "ok": True,
        "rows": int(len(TABLE)),
        "table_path": str(TABLE_PATH),
    }


@app.post("/query", response_model=QueryResponse)
def query_probs(req: QueryRequest):
    my_hand = normalize_hand(req.my_cards)
    partner_hand = normalize_hand(req.partner_cards)

    my_pos = req.my_pos
    partner_pos = (my_pos + 2) % 4

    key = f"{my_pos}|{partner_pos}|{hand_key(my_hand)}|{hand_key(partner_hand)}"

    if key not in TABLE.index:
        raise HTTPException(
            status_code=404,
            detail=f"Combination not found in master table: {key}",
        )

    row = TABLE.loc[key]

    return {
        "my_pos": int(row["my_pos"]),
        "partner_pos": int(row["partner_pos"]),
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
