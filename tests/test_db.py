"""Tests für die Datenbankschicht."""

import os
import tempfile

import pytest
from app.db import (
    add_tag,
    create_chat,
    create_checklist,
    delete_chat,
    get_all_tags,
    get_chat,
    get_checklists,
    get_linked_chats,
    get_stats,
    init_db,
    link_chats,
    list_chats,
    search_chats,
    tag_chat,
    update_chat,
    update_checklist_status,
)
from app.types import ChatCategory, ChatMetadata, ChatType


@pytest.fixture
def db_path():
    """Temporäre Datenbank für Tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def sample_chat(db_path):
    """Erstelle einen Beispiel-Chat."""
    meta = ChatMetadata(
        chat_type=ChatType.CODE,
        topic="test-project",
        task="build api",
        language="Python",
        framework="FastAPI",
        priority=4,
    )
    chat_id = create_chat(meta, db_path)
    meta.id = chat_id
    return meta, db_path


class TestDatabaseInit:
    def test_init_creates_db(self, db_path):
        """init_db erstellt eine funktionierende Datenbank."""
        assert os.path.exists(db_path)
        stats = get_stats(db_path)
        assert stats["total_chats"] == 0


class TestChatCRUD:
    def test_create_chat(self, sample_chat):
        """Chat wird erstellt und kann gelesen werden."""
        meta, db_path = sample_chat
        assert meta.id

        loaded = get_chat(meta.id, db_path)
        assert loaded is not None
        assert loaded.chat_type == ChatType.CODE
        assert loaded.topic == "test-project"
        assert loaded.task == "build api"
        assert loaded.language == "Python"

    def test_update_chat(self, sample_chat):
        """Chat-Metadaten können aktualisiert werden."""
        meta, db_path = sample_chat
        result = update_chat(
            meta.id,
            {"status": "completed", "priority": 5},
            db_path,
        )
        assert result is True

        loaded = get_chat(meta.id, db_path)
        assert loaded is not None
        assert loaded.status == "completed"
        assert loaded.priority == 5

    def test_delete_chat(self, sample_chat):
        """Chat kann gelöscht werden."""
        meta, db_path = sample_chat
        result = delete_chat(meta.id, db_path)
        assert result is True

        loaded = get_chat(meta.id, db_path)
        assert loaded is None

    def test_list_chats(self, sample_chat):
        """list_chats gibt alle Chats zurück."""
        meta, db_path = sample_chat
        chats = list_chats(db_path=db_path)
        assert len(chats) >= 1
        assert any(c.id == meta.id for c in chats)

    def test_list_chats_filter_type(self, sample_chat):
        """Filter nach Chat-Typ funktioniert."""
        meta, db_path = sample_chat
        # Erstelle zweiten Chat mit anderem Typ
        meta2 = ChatMetadata(
            chat_type=ChatType.GUIDE,
            topic="learning",
            task="study",
        )
        create_chat(meta2, db_path)

        code_chats = list_chats(
            chat_type=ChatType.CODE, db_path=db_path
        )
        assert len(code_chats) >= 1
        assert all(c.chat_type == ChatType.CODE for c in code_chats)

    def test_search_chats(self, sample_chat):
        """Volltextsuche findet Chats."""
        meta, db_path = sample_chat
        results = search_chats("build api", db_path)
        assert len(results) >= 1

        results_empty = search_chats("xyz_notfound", db_path)
        assert len(results_empty) == 0

    def test_update_nonexistent(self, db_path):
        """Update eines nicht existierenden Chats gibt False."""
        result = update_chat("nonexistent", {"status": "x"}, db_path)
        assert result is False


class TestTags:
    def test_add_tag(self, db_path):
        """Tag kann hinzugefügt werden."""
        tag_id = add_tag("python", "language", db_path)
        assert tag_id > 0

        # Duplikat gibt gleiche ID
        tag_id2 = add_tag("python", "language", db_path)
        assert tag_id2 == tag_id

    def test_tag_chat(self, sample_chat):
        """Chat kann getaggt werden."""
        meta, db_path = sample_chat
        tag_chat(meta.id, "python", db_path)
        tag_chat(meta.id, "fastapi", db_path)

        loaded = get_chat(meta.id, db_path)
        assert loaded is not None
        assert "python" in loaded.tags
        assert "fastapi" in loaded.tags

    def test_get_all_tags(self, sample_chat):
        """get_all_tags listet Tags mit Verwendung."""
        meta, db_path = sample_chat
        tag_chat(meta.id, "python", db_path)

        tags = get_all_tags(db_path)
        assert len(tags) >= 1
        assert any(t["name"] == "python" for t in tags)


class TestLinks:
    def test_link_chats(self, db_path):
        """Chats können verknüpft werden."""
        meta1 = ChatMetadata(
            chat_type=ChatType.CODE, topic="a", task="x"
        )
        id1 = create_chat(meta1, db_path)
        meta2 = ChatMetadata(
            chat_type=ChatType.CODE, topic="b", task="y"
        )
        id2 = create_chat(meta2, db_path)

        link_chats(id1, id2, "related", 0.8, db_path)

        linked = get_linked_chats(id1, db_path)
        assert len(linked) >= 1
        assert any(c.id == id2 for c in linked)


class TestChecklists:
    def test_create_and_get(self, sample_chat):
        """Checklist kann erstellt und gelesen werden."""
        meta, db_path = sample_chat
        cl_id = create_checklist(meta.id, "test content", db_path)
        assert cl_id > 0

        checklists = get_checklists(meta.id, db_path)
        assert len(checklists) >= 1
        assert checklists[0]["content"] == "test content"

    def test_update_status(self, sample_chat):
        """Checklisten-Status kann aktualisiert werden."""
        meta, db_path = sample_chat
        cl_id = create_checklist(meta.id, "x", db_path)

        result = update_checklist_status(cl_id, "completed", db_path)
        assert result is True


class TestStats:
    def test_stats_after_chat_creation(self, sample_chat):
        """Stats reflektieren erstellte Chats."""
        meta, db_path = sample_chat
        stats = get_stats(db_path)
        assert stats["total_chats"] >= 1
        assert "code" in stats["by_type"]
