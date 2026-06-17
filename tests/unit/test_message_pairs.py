"""Tests for utils.message_pairs."""

from models.records import LoCoMoMessage
from utils.message_pairs import iter_message_pairs, pair_count


def _msg(role: str, content: str) -> LoCoMoMessage:
    return LoCoMoMessage(role=role, content=content)


def test_fixture_alternating_user_assistant():
    messages = [
        _msg("user", "a"),
        _msg("assistant", "b"),
        _msg("user", "c"),
        _msg("assistant", "d"),
    ]
    pairs = list(iter_message_pairs(messages))
    assert pairs == [
        [_msg("user", "a"), _msg("assistant", "b")],
        [_msg("user", "c"), _msg("assistant", "d")],
    ]
    assert pair_count(messages) == 2


def test_locomo_user1_user2_roles():
    """LoCoMo maps two speakers to user1/user2; pair by index."""
    messages = [
        _msg("user1", "Caroline hi"),
        _msg("user2", "Melanie hi"),
        _msg("user1", "Caroline again"),
        _msg("user2", "Melanie again"),
        _msg("user1", "Caroline last"),
    ]
    pairs = list(iter_message_pairs(messages))
    assert len(pairs) == 3
    assert len(pairs[0]) == 2
    assert len(pairs[1]) == 2
    assert len(pairs[2]) == 1
    assert pair_count(messages) == 3


def test_empty():
    assert list(iter_message_pairs([])) == []
    assert pair_count([]) == 0


def test_single_message():
    messages = [_msg("user", "solo")]
    pairs = list(iter_message_pairs(messages))
    assert pairs == [messages]
    assert pair_count(messages) == 1
