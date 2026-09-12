import re
from dataclasses import dataclass


CARD_LINE = re.compile(r"^(\d+)\s+(.+?)\s+(\S+)\s+(\S+)$")
MAX_CARDS = 100
MAX_DECKLIST_BYTES = 16_384


@dataclass(frozen=True)
class CardLine:
    quantity: int
    name: str
    set_code: str
    number: str


def parse_decklist(decklist: str) -> list[CardLine]:
    if len(decklist.encode("utf-8")) > MAX_DECKLIST_BYTES:
        raise ValueError("Decklist is too large")

    cards: list[CardLine] = []
    for raw_line in decklist.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("Pokémon:", "Pokemon:", "Trainer:", "Energy:", "Total Cards:")):
            continue

        match = CARD_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"Unsupported decklist line: {line}")

        quantity = int(match.group(1))
        if quantity < 1 or quantity > MAX_CARDS:
            raise ValueError(f"Invalid quantity on line: {line}")

        cards.append(
            CardLine(
                quantity=quantity,
                name=match.group(2).strip(),
                set_code=match.group(3).strip(),
                number=match.group(4).strip(),
            )
        )

    if not cards:
        raise ValueError("Decklist contains no cards")
    if sum(card.quantity for card in cards) > MAX_CARDS:
        raise ValueError(f"Decklist exceeds the {MAX_CARDS}-card limit")
    return cards
