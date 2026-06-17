"""Tests for LoCoMo dialogue role mapping (user1 / user2)."""

from __future__ import annotations

from benchmark_data.locomo_loader import (
    _build_persona_speaker_map,
    _map_dialogue_role,
    _parse_official_locomo_row,
)


def test_build_persona_speaker_map_alphabetical():
    mapping = _build_persona_speaker_map(["Melanie", "Caroline", "Melanie"])
    assert mapping["caroline"] == "user1"
    assert mapping["melanie"] == "user2"


def test_map_dialogue_role_named_speakers():
    speaker_map = _build_persona_speaker_map(["Caroline", "Melanie"])
    assert _map_dialogue_role("Caroline", speaker_map) == "user1"
    assert _map_dialogue_role("Melanie", speaker_map) == "user2"
    assert _map_dialogue_role("caroline", speaker_map) == "user1"


def test_map_dialogue_role_legacy_user_assistant():
    speaker_map: dict[str, str] = {}
    assert _map_dialogue_role("user", speaker_map) == "user1"
    assert _map_dialogue_role("assistant", speaker_map) == "user2"


def test_map_dialogue_role_passthrough():
    speaker_map: dict[str, str] = {}
    assert _map_dialogue_role("user1", speaker_map) == "user1"
    assert _map_dialogue_role("user2", speaker_map) == "user2"
    assert _map_dialogue_role("system", speaker_map) == "system"


def test_persona_speaker_map_stable_when_minority_speaker_starts_session():
    row = {
        "sample_id": "conv-test",
        "conversation": {
            "session_1": [
                {"speaker": "Melanie", "text": "Melanie opens"},
                {"speaker": "Caroline", "text": "Caroline replies"},
            ],
            "session_2": [
                {"speaker": "Caroline", "text": "Caroline opens"},
                {"speaker": "Melanie", "text": "Melanie replies"},
            ],
        },
        "qa": [],
    }
    persona = _parse_official_locomo_row(row, 0)
    assert persona is not None
    assert [m.role for m in persona.sessions[0].messages] == ["user2", "user1"]
    assert [m.role for m in persona.sessions[1].messages] == ["user1", "user2"]
