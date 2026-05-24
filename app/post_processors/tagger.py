"""
AutoTagger — Automatische Verschlagwortung nach Chat-Ende.

Analysiert Chat-Metadaten und schlägt Tags vor.
Lernt aus manuellen Korrekturen durch Gewichtung häufig
verwendeter Tag-Kombinationen.
"""

from __future__ import annotations

from app.db import add_tag, get_all_tags, tag_chat
from app.post_processors.base import PostProcessResult


class AutoTagger:
    """Schlägt Tags basierend auf Chat-Metadaten vor."""

    name = "auto_tagger"
    description = "Automatische Verschlagwortung von Chats"
    priority = 10
    requires_llm = False

    # Mapping von Chat-Typ zu vorgeschlagenen Tags
    _TYPE_TAG_MAP: dict[str, list[str]] = {
        "code": ["coding", "implementation", "development"],
        "debug": ["debugging", "bugfix", "troubleshooting"],
        "refactor": ["refactoring", "clean-code", "architecture"],
        "review": ["code-review", "quality", "pull-request"],
        "deploy": ["deployment", "devops", "infrastructure"],
        "test": ["testing", "quality-assurance", "coverage"],
        "setup": ["setup", "configuration", "initialization"],
        "guide": ["tutorial", "how-to", "learning"],
        "research": ["research", "evaluation", "comparison"],
        "design": ["design", "architecture", "modeling"],
        "analyze": ["analysis", "performance", "metrics"],
        "learn": ["learning", "education", "concepts"],
        "docs": ["documentation", "writing", "api-docs"],
        "plan": ["planning", "roadmap", "strategy"],
        "chat": ["discussion", "brainstorming"],
        "meta": ["meta", "tooling", "process-improvement"],
    }

    # Keywords zu Tags
    _KEYWORD_TAG_MAP: dict[str, str] = {
        "python": "python",
        "fastapi": "fastapi",
        "typescript": "typescript",
        "javascript": "javascript",
        "react": "react",
        "docker": "docker",
        "kubernetes": "kubernetes",
        "sql": "sql",
        "sqlite": "sqlite",
        "postgresql": "postgresql",
        "api": "api",
        "rest": "rest-api",
        "graphql": "graphql",
        "cli": "cli",
        "web": "web",
        "frontend": "frontend",
        "backend": "backend",
        "database": "database",
        "testing": "testing",
        "git": "git",
        "github": "github",
        "ci/cd": "ci-cd",
        "security": "security",
        "performance": "performance",
        "pydantic": "pydantic",
    }

    def process(
        self,
        chat_id: str,
        db_path: str,
        context: dict[str, Any],
    ) -> PostProcessResult:
        """Analysiere und tagge einen Chat.

        Args:
            chat_id: Chat-ID.
            db_path: Datenbank-Pfad.
            context: Sollte 'topic', 'task', 'chat_type', 'language',
                     'framework' enthalten.

        Returns:
            PostProcessResult mit vorgeschlagenen Tags.
        """
        suggestions: list[str] = []

        # 1. Typ-basierte Tags
        chat_type = context.get("chat_type", "")
        if chat_type in self._TYPE_TAG_MAP:
            suggestions.extend(self._TYPE_TAG_MAP[chat_type])

        # 2. Keyword-basierte Tags aus topic und task
        topic = (context.get("topic") or "").lower()
        task = (context.get("task") or "").lower()
        combined = f"{topic} {task}"

        for keyword, tag in self._KEYWORD_TAG_MAP.items():
            if keyword in combined:
                if tag not in suggestions:
                    suggestions.append(tag)

        # 3. Sprache und Framework als Tags
        language = context.get("language", "")
        if language and language.lower() != "andere":
            lang_tag = language.lower().replace(" ", "-")
            if lang_tag not in suggestions:
                suggestions.append(lang_tag)

        framework = context.get("framework", "")
        if framework:
            fw_tag = framework.lower().replace(" ", "-")
            if fw_tag not in suggestions:
                suggestions.append(fw_tag)

        # 4. Tags in DB anlegen und verknüpfen
        added_tags = []
        for tag_name in suggestions:
            tag_id = add_tag(tag_name, "auto", db_path)
            if tag_id > 0:
                tag_chat(chat_id, tag_name, db_path)
                added_tags.append(tag_name)

        return PostProcessResult(
            processor_name=self.name,
            success=True,
            data={"tags_added": added_tags, "count": len(added_tags)},
            suggestions=suggestions,
        )


# Export für Plugin-Discovery
processor = AutoTagger()
