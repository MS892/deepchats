"""
Datenbankschicht für deepchats.

SQLite-basierte Persistenz für Chat-Registry, Tags, Links,
Decisions und Checklists. Alle Operationen sind thread-safe
durch WAL-Mode und Connection-per-Operation.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.types import ChatCategory, ChatMetadata, ChatType

# =============================================================================
# Konfiguration
# =============================================================================

DEFAULT_DB_NAME = ".deepchats.db"
ENV_HOME = "DEEPCHATS_HOME"
DEFAULT_HOME = "~/.deepcode/projects/chats"


def get_db_path() -> str:
    """Ermittle den Pfad zur SQLite-Datenbank.

    Priorität:
    1. DEEPCHATS_DB_PATH Environment-Variable
    2. DEEPCHATS_HOME + .deepchats.db
    3. ~/.deepcode/projects/chats/.deepchats.db
    """
    if db_path := os.environ.get("DEEPCHATS_DB_PATH"):
        return db_path

    home = os.environ.get(
        ENV_HOME,
        os.path.expanduser(DEFAULT_HOME),
    )
    return str(Path(home) / DEFAULT_DB_NAME)


def get_home_dir() -> str:
    """Ermittle das Hypervisor-Home-Verzeichnis."""
    return os.environ.get(
        ENV_HOME,
        os.path.expanduser(DEFAULT_HOME),
    )


# =============================================================================
# Datenbank-Initialisierung & Migration
# =============================================================================

SCHEMA_SQL = """
-- Chats: Zentrale Tabelle für alle Chat-Kontexte
CREATE TABLE IF NOT EXISTS chats (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    chat_type       TEXT NOT NULL,
    category        TEXT NOT NULL DEFAULT 'aktion',
    topic           TEXT NOT NULL DEFAULT '',
    task            TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    repo_url        TEXT,
    language        TEXT,
    framework       TEXT,
    priority        INTEGER NOT NULL DEFAULT 3,
    parent_chat_id  TEXT,
    dir_path        TEXT,
    message_count   INTEGER NOT NULL DEFAULT 0,
    outcome         TEXT,
    FOREIGN KEY (parent_chat_id) REFERENCES chats(id) ON DELETE SET NULL
);

-- Tags: Wiederverwendbare Schlagwörter
CREATE TABLE IF NOT EXISTS tags (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'general'
);

-- chat_tags: N:M-Verknüpfung Chats ↔ Tags
CREATE TABLE IF NOT EXISTS chat_tags (
    chat_id TEXT NOT NULL,
    tag_id  INTEGER NOT NULL,
    PRIMARY KEY (chat_id, tag_id),
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- chat_links: Gerichtete Verknüpfungen zwischen Chats
CREATE TABLE IF NOT EXISTS chat_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_chat_id  TEXT NOT NULL,
    target_chat_id  TEXT NOT NULL,
    link_type       TEXT NOT NULL DEFAULT 'related',
    weight          REAL NOT NULL DEFAULT 1.0,
    created_at      TEXT NOT NULL,
    UNIQUE(source_chat_id, target_chat_id, link_type),
    FOREIGN KEY (source_chat_id) REFERENCES chats(id) ON DELETE CASCADE,
    FOREIGN KEY (target_chat_id) REFERENCES chats(id) ON DELETE CASCADE
);

-- decisions: Architekturentscheidungen pro Chat
CREATE TABLE IF NOT EXISTS decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL DEFAULT '',
    importance      TEXT NOT NULL DEFAULT 'MEDIUM',
    decision_tree   TEXT,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);

-- checklists: Aufgabenlisten pro Chat
CREATE TABLE IF NOT EXISTS checklists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    content     TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'in_progress',
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);

-- Indizes für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_chats_type ON chats(chat_type);
CREATE INDEX IF NOT EXISTS idx_chats_category ON chats(category);
CREATE INDEX IF NOT EXISTS idx_chats_status ON chats(status);
CREATE INDEX IF NOT EXISTS idx_chats_created ON chats(created_at);
CREATE INDEX IF NOT EXISTS idx_chats_topic ON chats(topic);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_links_source ON chat_links(source_chat_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON chat_links(target_chat_id);
CREATE INDEX IF NOT EXISTS idx_decisions_chat ON decisions(chat_id);
CREATE INDEX IF NOT EXISTS idx_checklists_chat ON checklists(chat_id);
"""


def init_db(db_path: str | None = None) -> str:
    """Initialisiere die Datenbank.

    Erstellt alle Tabellen und Indizes, falls nicht vorhanden.
    Aktiviert WAL-Mode für bessere Concurrency.

    Args:
        db_path: Pfad zur DB-Datei. None = Default-Pfad.

    Returns:
        Den verwendeten DB-Pfad.
    """
    if db_path is None:
        db_path = get_db_path()

    # Stelle sicher, dass das Verzeichnis existiert
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()

    return db_path


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    """Stelle eine Datenbank-Verbindung her."""
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# Hilfsfunktionen
# =============================================================================

def _row_to_chat_metadata(row: sqlite3.Row) -> ChatMetadata:
    """Konvertiere eine DB-Zeile in ein ChatMetadata-Objekt."""
    return ChatMetadata(
        id=row["id"],
        name=row["name"],
        chat_type=ChatType(row["chat_type"]),
        category=ChatCategory(row["category"]),
        topic=row["topic"],
        task=row["task"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=row["status"],
        repo_url=row["repo_url"],
        language=row["language"],
        framework=row["framework"],
        priority=row["priority"],
        parent_chat_id=row["parent_chat_id"],
        dir_path=row["dir_path"],
        message_count=row["message_count"],
        outcome=row["outcome"],
        tags=[],
        related_chat_ids=[],
    )


def _now() -> str:
    """Aktueller UTC-Timestamp in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    """Generiere eine eindeutige Chat-ID."""
    return uuid.uuid4().hex[:12]


# =============================================================================
# Chat CRUD
# =============================================================================

def create_chat(
    metadata: ChatMetadata,
    db_path: str | None = None,
) -> str:
    """Erstelle einen neuen Chat-Eintrag.

    Args:
        metadata: Die Chat-Metadaten.
        db_path: Optionaler DB-Pfad.

    Returns:
        Die generierte Chat-ID.
    """
    if not metadata.id:
        metadata.id = _generate_id()
    if not metadata.created_at:
        metadata.created_at = _now()
    if not metadata.updated_at:
        metadata.updated_at = metadata.created_at

    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO chats (
                id, name, chat_type, category, topic, task,
                created_at, updated_at, status, repo_url,
                language, framework, priority, parent_chat_id,
                dir_path, message_count, outcome
            ) VALUES (
                :id, :name, :chat_type, :category, :topic, :task,
                :created_at, :updated_at, :status, :repo_url,
                :language, :framework, :priority, :parent_chat_id,
                :dir_path, :message_count, :outcome
            )
            """,
            {
                "id": metadata.id,
                "name": metadata.name,
                "chat_type": metadata.chat_type.value,
                "category": metadata.category.value,
                "topic": metadata.topic,
                "task": metadata.task,
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at,
                "status": metadata.status,
                "repo_url": metadata.repo_url,
                "language": metadata.language,
                "framework": metadata.framework,
                "priority": metadata.priority,
                "parent_chat_id": metadata.parent_chat_id,
                "dir_path": metadata.dir_path,
                "message_count": metadata.message_count,
                "outcome": metadata.outcome,
            },
        )
        conn.commit()
        return metadata.id
    finally:
        conn.close()


def get_chat(
    chat_id: str,
    db_path: str | None = None,
) -> ChatMetadata | None:
    """Lese einen Chat anhand seiner ID."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM chats WHERE id = ?", (chat_id,)
        ).fetchone()
        if row is None:
            return None
        metadata = _row_to_chat_metadata(row)
        metadata.tags = _get_tags_for_chat(conn, chat_id)
        metadata.related_chat_ids = _get_related_chat_ids(conn, chat_id)
        return metadata
    finally:
        conn.close()


def update_chat(
    chat_id: str,
    updates: dict[str, Any],
    db_path: str | None = None,
) -> bool:
    """Aktualisiere die Metadaten eines Chats.

    Args:
        chat_id: Die Chat-ID.
        updates: Dict mit zu aktualisierenden Feldern.
        db_path: Optionaler DB-Pfad.

    Returns:
        True wenn der Chat existierte und aktualisiert wurde.
    """
    # Konvertiere Enum-Werte
    if "chat_type" in updates and isinstance(updates["chat_type"], ChatType):
        updates["chat_type"] = updates["chat_type"].value
    if "category" in updates and isinstance(
        updates["category"], ChatCategory
    ):
        updates["category"] = updates["category"].value

    # Setze updated_at automatisch
    updates["updated_at"] = _now()

    # Baue SET-Klausel
    allowed_fields = {
        "name", "chat_type", "category", "topic", "task",
        "updated_at", "status", "repo_url", "language",
        "framework", "priority", "parent_chat_id", "dir_path",
        "message_count", "outcome",
    }
    filtered = {
        k: v for k, v in updates.items() if k in allowed_fields
    }
    if not filtered:
        return False

    set_clause = ", ".join(f"{k} = :{k}" for k in filtered)
    filtered["id"] = chat_id

    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            f"UPDATE chats SET {set_clause} WHERE id = :id",
            filtered,
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_chat(
    chat_id: str,
    db_path: str | None = None,
) -> bool:
    """Lösche einen Chat und alle zugehörigen Daten (CASCADE)."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM chats WHERE id = ?", (chat_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def list_chats(
    chat_type: ChatType | None = None,
    category: ChatCategory | None = None,
    status: str | None = None,
    topic: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db_path: str | None = None,
) -> list[ChatMetadata]:
    """Liste Chats mit optionalen Filtern."""
    conn = _connect(db_path)
    try:
        query = "SELECT * FROM chats WHERE 1=1"
        params: list[Any] = []

        if chat_type:
            query += " AND chat_type = ?"
            params.append(chat_type.value)
        if category:
            query += " AND category = ?"
            params.append(category.value)
        if status:
            query += " AND status = ?"
            params.append(status)
        if topic:
            query += " AND topic LIKE ?"
            params.append(f"%{topic}%")

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        results = []
        for row in rows:
            metadata = _row_to_chat_metadata(row)
            metadata.tags = _get_tags_for_chat(conn, row["id"])
            results.append(metadata)
        return results
    finally:
        conn.close()


def search_chats(
    query: str,
    db_path: str | None = None,
    limit: int = 20,
) -> list[ChatMetadata]:
    """Volltextsuche über Chats (name, topic, task)."""
    conn = _connect(db_path)
    try:
        like = f"%{query}%"
        rows = conn.execute(
            """
            SELECT * FROM chats
            WHERE name LIKE ? OR topic LIKE ? OR task LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        results = []
        for row in rows:
            metadata = _row_to_chat_metadata(row)
            metadata.tags = _get_tags_for_chat(conn, row["id"])
            results.append(metadata)
        return results
    finally:
        conn.close()


def get_recent_chats(
    limit: int = 10,
    db_path: str | None = None,
) -> list[ChatMetadata]:
    """Gib die zuletzt erstellten Chats zurück."""
    return list_chats(limit=limit, db_path=db_path)


def get_chats_by_type(
    chat_type: ChatType,
    db_path: str | None = None,
) -> list[ChatMetadata]:
    """Gib alle Chats eines bestimmten Typs zurück."""
    return list_chats(chat_type=chat_type, limit=1000, db_path=db_path)


# =============================================================================
# Tag-Operationen
# =============================================================================

def _get_tags_for_chat(
    conn: sqlite3.Connection, chat_id: str
) -> list[str]:
    """Interne Hilfsfunktion: Tags eines Chats lesen."""
    rows = conn.execute(
        """
        SELECT t.name FROM tags t
        JOIN chat_tags ct ON t.id = ct.tag_id
        WHERE ct.chat_id = ?
        ORDER BY t.name
        """,
        (chat_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _get_related_chat_ids(
    conn: sqlite3.Connection, chat_id: str
) -> list[str]:
    """Interne Hilfsfunktion: Verknüpfte Chat-IDs lesen."""
    rows = conn.execute(
        """
        SELECT DISTINCT target_chat_id FROM chat_links
        WHERE source_chat_id = ?
        UNION
        SELECT DISTINCT source_chat_id FROM chat_links
        WHERE target_chat_id = ?
        """,
        (chat_id, chat_id),
    ).fetchall()
    return [r[0] for r in rows]


def add_tag(
    name: str,
    category: str = "general",
    db_path: str | None = None,
) -> int:
    """Füge einen Tag hinzu (oder gib existierende ID zurück)."""
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO tags (name, category) VALUES (?, ?)",
            (name.lower().strip(), category),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM tags WHERE name = ?",
            (name.lower().strip(),),
        ).fetchone()
        return row["id"] if row else -1
    finally:
        conn.close()


def tag_chat(
    chat_id: str,
    tag_name: str,
    db_path: str | None = None,
) -> None:
    """Verknüpfe einen Tag mit einem Chat."""
    tag_id = add_tag(tag_name, db_path=db_path)
    if tag_id < 0:
        return
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO chat_tags (chat_id, tag_id) VALUES (?, ?)",
            (chat_id, tag_id),
        )
        conn.commit()
    finally:
        conn.close()


def untag_chat(
    chat_id: str,
    tag_name: str,
    db_path: str | None = None,
) -> None:
    """Entferne einen Tag von einem Chat."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            DELETE FROM chat_tags
            WHERE chat_id = ? AND tag_id = (
                SELECT id FROM tags WHERE name = ?
            )
            """,
            (chat_id, tag_name.lower().strip()),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_tags(
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Liste alle Tags mit Verwendungshäufigkeit."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT t.name, t.category, COUNT(ct.chat_id) as usage_count
            FROM tags t
            LEFT JOIN chat_tags ct ON t.id = ct.tag_id
            GROUP BY t.id
            ORDER BY usage_count DESC, t.name
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================================
# Link-Operationen
# =============================================================================

def link_chats(
    source_chat_id: str,
    target_chat_id: str,
    link_type: str = "related",
    weight: float = 1.0,
    db_path: str | None = None,
) -> None:
    """Erstelle eine Verknüpfung zwischen zwei Chats."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO chat_links
                (source_chat_id, target_chat_id, link_type, weight, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_chat_id, target_chat_id, link_type, weight, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def unlink_chats(
    source_chat_id: str,
    target_chat_id: str,
    link_type: str | None = None,
    db_path: str | None = None,
) -> None:
    """Entferne eine Verknüpfung zwischen zwei Chats."""
    conn = _connect(db_path)
    try:
        if link_type:
            conn.execute(
                """
                DELETE FROM chat_links
                WHERE source_chat_id = ? AND target_chat_id = ?
                AND link_type = ?
                """,
                (source_chat_id, target_chat_id, link_type),
            )
        else:
            conn.execute(
                """
                DELETE FROM chat_links
                WHERE source_chat_id = ? AND target_chat_id = ?
                """,
                (source_chat_id, target_chat_id),
            )
        conn.commit()
    finally:
        conn.close()


def get_linked_chats(
    chat_id: str,
    db_path: str | None = None,
) -> list[ChatMetadata]:
    """Gib alle mit einem Chat verknüpften Chats zurück."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT c.* FROM chats c
            JOIN chat_links l ON (
                (l.source_chat_id = ? AND l.target_chat_id = c.id)
                OR (l.target_chat_id = ? AND l.source_chat_id = c.id)
            )
            ORDER BY c.created_at DESC
            """,
            (chat_id, chat_id),
        ).fetchall()
        results = []
        for row in rows:
            metadata = _row_to_chat_metadata(row)
            metadata.tags = _get_tags_for_chat(conn, row["id"])
            results.append(metadata)
        return results
    finally:
        conn.close()


# =============================================================================
# Decision-Operationen
# =============================================================================

def create_decision(
    chat_id: str,
    title: str,
    content: str = "",
    importance: str = "MEDIUM",
    decision_tree: str | None = None,
    db_path: str | None = None,
) -> int:
    """Erstelle einen Decision-Eintrag."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO decisions
                (chat_id, timestamp, title, content, importance, decision_tree)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chat_id, _now(), title, content, importance, decision_tree),
        )
        conn.commit()
        return cursor.lastrowid or -1
    finally:
        conn.close()


def get_decisions(
    chat_id: str,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Gib alle Decisions eines Chats zurück."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM decisions
            WHERE chat_id = ?
            ORDER BY timestamp DESC
            """,
            (chat_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================================
# Checklist-Operationen
# =============================================================================

def create_checklist(
    chat_id: str,
    content: str = "",
    db_path: str | None = None,
) -> int:
    """Erstelle eine neue Checkliste für einen Chat."""
    conn = _connect(db_path)
    try:
        now = _now()
        cursor = conn.execute(
            """
            INSERT INTO checklists (chat_id, created_at, updated_at, content, status)
            VALUES (?, ?, ?, ?, 'in_progress')
            """,
            (chat_id, now, now, content),
        )
        conn.commit()
        return cursor.lastrowid or -1
    finally:
        conn.close()


def get_checklists(
    chat_id: str,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    """Gib alle Checklists eines Chats zurück."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT * FROM checklists
            WHERE chat_id = ?
            ORDER BY created_at DESC
            """,
            (chat_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_checklist_status(
    checklist_id: int,
    status: str,
    db_path: str | None = None,
) -> bool:
    """Aktualisiere den Status einer Checkliste."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            """
            UPDATE checklists
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, _now(), checklist_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =============================================================================
# Statistik-Operationen
# =============================================================================

def get_stats(db_path: str | None = None) -> dict[str, Any]:
    """Sammle Statistiken über alle Chats."""
    conn = _connect(db_path)
    try:
        total = conn.execute(
            "SELECT COUNT(*) as count FROM chats"
        ).fetchone()["count"]

        by_type = {}
        for row in conn.execute(
            """
            SELECT chat_type, COUNT(*) as count
            FROM chats GROUP BY chat_type ORDER BY count DESC
            """
        ).fetchall():
            by_type[row["chat_type"]] = row["count"]

        by_status = {}
        for row in conn.execute(
            """
            SELECT status, COUNT(*) as count
            FROM chats GROUP BY status ORDER BY count DESC
            """
        ).fetchall():
            by_status[row["status"]] = row["count"]

        total_tags = conn.execute(
            "SELECT COUNT(*) as count FROM tags"
        ).fetchone()["count"]

        total_links = conn.execute(
            "SELECT COUNT(*) as count FROM chat_links"
        ).fetchone()["count"]

        # Aktivität über Zeit (letzte 30 Tage)
        recent_activity = conn.execute(
            """
            SELECT DATE(created_at) as day, COUNT(*) as count
            FROM chats
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY day
            ORDER BY day
            """
        ).fetchall()

        return {
            "total_chats": total,
            "by_type": by_type,
            "by_status": by_status,
            "total_tags": total_tags,
            "total_links": total_links,
            "recent_activity": [dict(r) for r in recent_activity],
        }
    finally:
        conn.close()
