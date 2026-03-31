from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

RANKS: Tuple[str, ...] = ("A", "4", "5", "6", "7", "S", "C", "R")
RANK_TO_IDX: Dict[str, int] = {r: i for i, r in enumerate(RANKS)}
DECK: Tuple[int, ...] = (8, 4, 4, 4, 4, 4, 4, 8)


class InvalidHandError(Exception):
    pass


@dataclass(frozen=True)
class Hand:
    counts: Tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.counts) != len(RANKS):
            raise InvalidHandError(
                f"Hand must have {len(RANKS)} rank counts, got {len(self.counts)}."
            )
        if sum(self.counts) != 4:
            raise InvalidHandError(
                f"Hand must contain exactly 4 cards, got {sum(self.counts)}."
            )
        for i, n in enumerate(self.counts):
            if n < 0:
                raise InvalidHandError(f"Negative count for rank {RANKS[i]}.")
            if n > DECK[i]:
                raise InvalidHandError(
                    f"Hand uses {n} cards of rank {RANKS[i]}, but deck allows only {DECK[i]}."
                )

    @classmethod
    def from_string(cls, hand_str: str) -> "Hand":
        raw = hand_str.replace(",", " ").split()
        cards = [x.strip().upper() for x in raw if x.strip()]

        if len(cards) != 4:
            raise InvalidHandError(
                f"Hand must have exactly 4 cards. Got {len(cards)} from: {hand_str}"
            )

        counts = [0] * len(RANKS)
        for c in cards:
            if c not in RANK_TO_IDX:
                raise InvalidHandError(
                    f"Invalid card '{c}'. Allowed ranks: {', '.join(RANKS)}"
                )
            counts[RANK_TO_IDX[c]] += 1

        return cls(tuple(counts))

    def cards(self) -> list[str]:
        out: list[str] = []
        for rank, n in zip(RANKS, self.counts):
            out.extend([rank] * n)
        return out

    def to_string(self) -> str:
        return ",".join(self.cards())


def hand_key(hand: Hand) -> str:
    return "-".join(str(x) for x in hand.counts)


def hand_from_key(key: str) -> Hand:
    return Hand(tuple(int(x) for x in key.split("-")))
