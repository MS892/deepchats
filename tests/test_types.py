"""Tests für das Typ-System."""

import pytest
from app.types import (
    ChatCategory,
    ChatMetadata,
    ChatType,
    CHAT_TYPE_CATEGORY,
    CHAT_TYPE_DESCRIPTIONS,
    CHAT_TYPE_EXAMPLES,
    CHAT_TYPE_ICONS,
    get_types_by_category,
)


class TestChatType:
    def test_all_types_have_category(self):
        """Jeder ChatType muss eine Kategorie haben."""
        for chat_type in ChatType:
            assert chat_type in CHAT_TYPE_CATEGORY
            assert isinstance(CHAT_TYPE_CATEGORY[chat_type], ChatCategory)

    def test_all_types_have_description(self):
        """Jeder ChatType muss eine Beschreibung haben."""
        for chat_type in ChatType:
            assert chat_type in CHAT_TYPE_DESCRIPTIONS
            assert len(CHAT_TYPE_DESCRIPTIONS[chat_type]) > 10

    def test_all_types_have_icon(self):
        """Jeder ChatType muss ein Icon haben."""
        for chat_type in ChatType:
            assert chat_type in CHAT_TYPE_ICONS
            assert len(CHAT_TYPE_ICONS[chat_type]) > 0

    def test_all_types_have_examples(self):
        """Jeder ChatType muss Beispiele haben."""
        for chat_type in ChatType:
            assert chat_type in CHAT_TYPE_EXAMPLES
            assert len(CHAT_TYPE_EXAMPLES[chat_type]) >= 1

    def test_count_is_16(self):
        """Es muss genau 16 Chat-Typen geben."""
        assert len(list(ChatType)) == 16

    def test_aktion_types(self):
        """Aktionstypen: 7 Stück."""
        aktion_types = get_types_by_category(ChatCategory.AKTION)
        assert len(aktion_types) == 7
        assert ChatType.CODE in aktion_types
        assert ChatType.DEBUG in aktion_types

    def test_wissen_types(self):
        """Wissenstypen: 6 Stück."""
        wissen_types = get_types_by_category(ChatCategory.WISSEN)
        assert len(wissen_types) == 6
        assert ChatType.GUIDE in wissen_types
        assert ChatType.RESEARCH in wissen_types

    def test_meta_types(self):
        """Metatypen: 3 Stück."""
        meta_types = get_types_by_category(ChatCategory.META)
        assert len(meta_types) == 3
        assert ChatType.PLAN in meta_types
        assert ChatType.META in meta_types


class TestChatMetadata:
    def test_default_values(self):
        """Default-Werte werden korrekt gesetzt."""
        meta = ChatMetadata(
            chat_type=ChatType.CODE,
            topic="test",
            task="teste etwas",
        )
        assert meta.status == "active"
        assert meta.priority == 3
        assert meta.tags == []
        assert meta.category == ChatCategory.AKTION

    def test_category_auto_set(self):
        """Kategorie wird automatisch aus ChatType gesetzt."""
        meta = ChatMetadata(
            chat_type=ChatType.GUIDE, topic="t", task="x"
        )
        assert meta.category == ChatCategory.WISSEN

    def test_timestamps_generated(self):
        """Timestamps werden generiert."""
        meta = ChatMetadata(
            chat_type=ChatType.CHAT, topic="t", task="x"
        )
        assert meta.created_at
        assert meta.updated_at
        assert "T" in meta.created_at  # ISO 8601

    def test_serialization(self):
        """Modell kann serialisiert werden."""
        meta = ChatMetadata(
            id="abc123",
            chat_type=ChatType.CODE,
            topic="test",
            task="hello world",
            tags=["python", "api"],
        )
        d = meta.model_dump()
        assert d["id"] == "abc123"
        assert d["chat_type"] == "code"
        assert d["tags"] == ["python", "api"]

    def test_priority_bounds(self):
        """Priorität muss zwischen 1 und 5 liegen."""
        # Gültig
        meta = ChatMetadata(
            chat_type=ChatType.CODE, topic="t", task="x", priority=5
        )
        assert meta.priority == 5

        # Ungültig
        with pytest.raises(Exception):
            ChatMetadata(
                chat_type=ChatType.CODE, topic="t", task="x", priority=0
            )
        with pytest.raises(Exception):
            ChatMetadata(
                chat_type=ChatType.CODE, topic="t", task="x", priority=6
            )
