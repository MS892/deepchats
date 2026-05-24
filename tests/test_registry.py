"""Tests für die TypeRegistry."""

from app.registry import (
    QuestionSet,
    QuestionTemplate,
    TypeRegistry,
    PostProcessorRegistry,
)
from app.types import ChatCategory, ChatType


class TestTypeRegistry:
    def setup_method(self):
        self.registry = TypeRegistry()

    def test_builtins_registered(self):
        """Alle 16 Built-in-Typen sind registriert."""
        assert len(self.registry) == 16

    def test_get_returns_entry(self):
        """get() gibt einen Registry-Eintrag zurück."""
        entry = self.registry.get(ChatType.CODE)
        assert entry is not None
        assert entry.chat_type == ChatType.CODE
        assert entry.category == ChatCategory.AKTION
        assert entry.icon == "🔨"

    def test_list_all(self):
        """list_all() gibt alle Einträge zurück."""
        entries = self.registry.list_all()
        assert len(entries) == 16

    def test_list_by_category(self):
        """list_by_category() filtert korrekt."""
        aktion = self.registry.list_by_category(ChatCategory.AKTION)
        assert len(aktion) == 7

        wissen = self.registry.list_by_category(ChatCategory.WISSEN)
        assert len(wissen) == 6

        meta = self.registry.list_by_category(ChatCategory.META)
        assert len(meta) == 3

    def test_get_categories(self):
        """get_categories() gruppiert korrekt."""
        cats = self.registry.get_categories()
        assert len(cats) == 3
        assert ChatCategory.AKTION in cats
        assert ChatCategory.WISSEN in cats
        assert ChatCategory.META in cats

    def test_search(self):
        """search() findet relevante Typen."""
        results = self.registry.search("code")
        assert len(results) >= 1
        assert any(
            r.chat_type == ChatType.CODE for r in results
        )

    def test_contains(self):
        """in-Operator funktioniert."""
        assert ChatType.CODE in self.registry
        assert ChatType.GUIDE in self.registry

    def test_register_custom_type(self):
        """Manuelle Registrierung funktioniert."""
        # Registriere einen existierenden Typ mit Custom-Daten
        custom_qs = QuestionSet(
            chat_type=ChatType.CODE,
            fixed_questions=[
                QuestionTemplate(
                    key="custom",
                    text="Custom-Frage?",
                    field_type="text",
                )
            ],
        )
        self.registry.register(
            chat_type=ChatType.CODE,
            question_set=custom_qs,
            description="Custom Code-Type",
        )

        entry = self.registry.get(ChatType.CODE)
        assert entry is not None
        assert entry.description == "Custom Code-Type"
        assert len(entry.question_set.fixed_questions) == 1
        assert (
            entry.question_set.fixed_questions[0].key == "custom"
        )

    def test_plugin_discovery(self):
        """Plugin-Discovery findet chat_types Plugins."""
        count = self.registry.discover_plugins()
        # Mindestens code.py, guide.py, meta.py
        assert count >= 3

        # Verifiziere dass code-Plugin registriert wurde
        entry = self.registry.get(ChatType.CODE)
        assert entry is not None
        # Das code-Plugin sollte spezifische Fragen haben
        questions = entry.question_set.fixed_questions
        assert len(questions) >= 4  # code-Plugin definiert 5 Fragen
        assert any(q.key == "language" for q in questions)


class TestQuestionTemplate:
    def test_basic_question(self):
        """Einfache Frage ohne Bedingungen."""
        q = QuestionTemplate(
            key="test", text="Testfrage?", field_type="text"
        )
        assert q.should_ask({})

    def test_conditional_question_true(self):
        """Konditionale Frage: Bedingung erfüllt."""
        q = QuestionTemplate(
            key="test",
            text="Test?",
            condition=lambda ctx: ctx.get("has_repo", False),
        )
        assert q.should_ask({"has_repo": True})

    def test_conditional_question_false(self):
        """Konditionale Frage: Bedingung nicht erfüllt."""
        q = QuestionTemplate(
            key="test",
            text="Test?",
            condition=lambda ctx: ctx.get("has_repo", False),
        )
        assert not q.should_ask({})

    def test_required_question(self):
        """Pflichtfrage."""
        q = QuestionTemplate(
            key="req",
            text="Pflicht?",
            field_type="text",
            required=True,
        )
        assert q.required is True


class TestPostProcessorRegistry:
    def test_empty_registry(self):
        """Leere Registry."""
        reg = PostProcessorRegistry()
        assert len(reg) == 0
        assert reg.get_all_sorted() == []

    def test_plugin_discovery(self):
        """Plugin-Discovery findet post_processors."""
        reg = PostProcessorRegistry()
        count = reg.discover_plugins()
        assert count >= 3  # tagger, similarity, metrics

        processors = reg.get_all_sorted()
        assert len(processors) >= 3

        # Prüfe Sortierung nach priority
        for i in range(len(processors) - 1):
            assert (
                processors[i].priority <= processors[i + 1].priority
            )
