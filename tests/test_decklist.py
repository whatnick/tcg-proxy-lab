import pytest

from app.decklist import parse_decklist


def test_parses_limitless_sections_and_cards():
    cards = parse_decklist(
        """Pokémon: 1
4 Pikachu SVI 94

Trainer: 1
2 Ultra Ball SVI 196

Total Cards: 6
"""
    )

    assert len(cards) == 2
    assert sum(card.quantity for card in cards) == 6
    assert cards[0].set_code == "SVI"


def test_rejects_unrecognized_lines():
    with pytest.raises(ValueError, match="Unsupported decklist line"):
        parse_decklist("this is not a card")


def test_rejects_more_than_one_hundred_cards():
    with pytest.raises(ValueError, match="100-card limit"):
        parse_decklist("60 Pikachu SVI 94\n41 Ultra Ball SVI 196")
