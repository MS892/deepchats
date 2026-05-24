"""
Typ-System für deepchats.

Definiert die Taxonomie aller Chat-Typen, Kategorien und Metadaten.
Erweiterbar durch die TypeRegistry ohne Änderung an diesem Modul.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Chat-Kategorien
# =============================================================================

class ChatCategory(StrEnum):
    """Top-Level-Kategorien für Chat-Interaktionstypen.

    Die drei Kategorien decken das vollständige Spektrum von
    Mensch-KI-Kollaboration ab:
    - AKTION: Ausführungsorientierte Tasks (produzierend)
    - WISSEN: Erkenntnisorientierte Tasks (analysierend)
    - META: Steuerungsorientierte Tasks (organisierend)
    """

    AKTION = "aktion"
    WISSEN = "wissen"
    META = "meta"


# =============================================================================
# Chat-Typen
# =============================================================================

class ChatType(StrEnum):
    """Vollständige Taxonomie der Chat-Interaktionstypen.

    Erweiterbarkeit:
    Neue Typen können via TypeRegistry.register() hinzugefügt werden,
    ohne diesen Enum zu ändern. Der Enum dient als Basis-Set.
    """

    # === AKTION ===
    CODE = "code"
    DEBUG = "debug"
    REFACTOR = "refactor"
    REVIEW = "review"
    DEPLOY = "deploy"
    TEST = "test"
    SETUP = "setup"

    # === WISSEN ===
    GUIDE = "guide"
    RESEARCH = "research"
    DESIGN = "design"
    ANALYZE = "analyze"
    LEARN = "learn"
    DOCS = "docs"

    # === META ===
    PLAN = "plan"
    CHAT = "chat"
    META = "meta"


# =============================================================================
# Typ-Metadaten (Registry-Defaults)
# =============================================================================

# Mapping Typ → Kategorie
CHAT_TYPE_CATEGORY: dict[ChatType, ChatCategory] = {
    # AKTION
    ChatType.CODE: ChatCategory.AKTION,
    ChatType.DEBUG: ChatCategory.AKTION,
    ChatType.REFACTOR: ChatCategory.AKTION,
    ChatType.REVIEW: ChatCategory.AKTION,
    ChatType.DEPLOY: ChatCategory.AKTION,
    ChatType.TEST: ChatCategory.AKTION,
    ChatType.SETUP: ChatCategory.AKTION,
    # WISSEN
    ChatType.GUIDE: ChatCategory.WISSEN,
    ChatType.RESEARCH: ChatCategory.WISSEN,
    ChatType.DESIGN: ChatCategory.WISSEN,
    ChatType.ANALYZE: ChatCategory.WISSEN,
    ChatType.LEARN: ChatCategory.WISSEN,
    ChatType.DOCS: ChatCategory.WISSEN,
    # META
    ChatType.PLAN: ChatCategory.META,
    ChatType.CHAT: ChatCategory.META,
    ChatType.META: ChatCategory.META,
}

# Beschreibungen (Deutsch)
CHAT_TYPE_DESCRIPTIONS: dict[ChatType, str] = {
    ChatType.CODE: "Feature-Entwicklung, Programmierung, Code schreiben",
    ChatType.DEBUG: "Fehlersuche, Bugfixing, Problem-Analyse",
    ChatType.REFACTOR: "Code-Umstrukturierung, Cleanup, Architektur-Verbesserung",
    ChatType.REVIEW: "Code-Review, Qualitätsprüfung, Pull-Request-Begutachtung",
    ChatType.DEPLOY: "Deployment, CI/CD, Infrastruktur, Containerisierung",
    ChatType.TEST: "Tests schreiben, Teststrategie, Testabdeckung",
    ChatType.SETUP: "Projekt-Initialisierung, Environment-Setup, Konfiguration",
    ChatType.GUIDE: "Anleitung, Tutorial, How-To, Schritt-für-Schritt-Erklärung",
    ChatType.RESEARCH: "Technologie-Evaluierung, Marktanalyse, Bibliotheksvergleich",
    ChatType.DESIGN: "Architektur-Design, System-Planung, Modellierung",
    ChatType.ANALYZE: "Code-Analyse, Datenauswertung, Performance-Profiling",
    ChatType.LEARN: "Konzeptverständnis, Lernen, Wissensaufbau",
    ChatType.DOCS: "Dokumentation erstellen, überarbeiten, API-Dokumentation",
    ChatType.PLAN: "Planung, Roadmap, Strategie, Meilenstein-Definition",
    ChatType.CHAT: "Allgemeines Gespräch, Brainstorming, freier Austausch",
    ChatType.META: "Tooling, Prozess-Verbesserung, Metakognition",
}

# Icons für CLI-Darstellung
CHAT_TYPE_ICONS: dict[ChatType, str] = {
    ChatType.CODE: "🔨",
    ChatType.DEBUG: "🐛",
    ChatType.REFACTOR: "♻️",
    ChatType.REVIEW: "👁️",
    ChatType.DEPLOY: "🚀",
    ChatType.TEST: "🧪",
    ChatType.SETUP: "🏗️",
    ChatType.GUIDE: "📖",
    ChatType.RESEARCH: "🔍",
    ChatType.DESIGN: "📐",
    ChatType.ANALYZE: "📊",
    ChatType.LEARN: "🎓",
    ChatType.DOCS: "📝",
    ChatType.PLAN: "🗺️",
    ChatType.CHAT: "💬",
    ChatType.META: "⚙️",
}

# Beispiel-Tasks für jeden Typ
CHAT_TYPE_EXAMPLES: dict[ChatType, list[str]] = {
    ChatType.CODE: [
        "Neuen API-Endpoint für Benutzerverwaltung bauen",
        "Frontend-Komponente für Dashboard entwickeln",
        "CLI-Tool für Datenmigration schreiben",
    ],
    ChatType.DEBUG: [
        "Memory-Leak in Worker-Thread finden",
        "Race-Condition bei parallelen Requests beheben",
        "Falsche Berechnung im Abrechnungsmodul korrigieren",
    ],
    ChatType.REFACTOR: [
        "Monolithischen Service in Module aufteilen",
        "Legacy-Funktionen durch moderne Patterns ersetzen",
        "Code-Duplizierung eliminieren",
    ],
    ChatType.REVIEW: [
        "PR #42 auf Sicherheitslücken prüfen",
        "Architektur-Entscheidung im Code-Review validieren",
        "Code-Qualität vor Release begutachten",
    ],
    ChatType.DEPLOY: [
        "Docker-Compose für Microservices aufsetzen",
        "CI/CD-Pipeline mit GitHub Actions konfigurieren",
        "Kubernetes-Manifeste für Produktion erstellen",
    ],
    ChatType.TEST: [
        "Unit-Tests für Payment-Modul schreiben",
        "Integrationstests für API-Gateway entwickeln",
        "Teststrategie für Microservice-Architektur entwerfen",
    ],
    ChatType.SETUP: [
        "Neues Python-Projekt mit pyproject.toml initialisieren",
        "Entwicklungsumgebung für Team standardisieren",
        "GitHub-Repo mit Branch-Protection einrichten",
    ],
    ChatType.GUIDE: [
        "FastAPI von Grund auf erklärt bekommen",
        "Schritt-für-Schritt durch Dockerisierung geführt werden",
        "Best Practices für asyncio erlernen",
    ],
    ChatType.RESEARCH: [
        "Beste Python-Bibliothek für PDF-Generierung finden",
        "Technologievergleich: gRPC vs REST vs GraphQL",
        "State of the Art: PV-Ertragssimulation",
    ],
    ChatType.DESIGN: [
        "Microservice-Architektur für E-Commerce entwerfen",
        "Datenbankschema für Multi-Tenant-System designen",
        "Event-getriebene Architektur modellieren",
    ],
    ChatType.ANALYZE: [
        "Performance-Bottleneck in API identifizieren",
        "SQL-Query-Plan analysieren und optimieren",
        "Code-Qualitätsmetriken auswerten",
    ],
    ChatType.LEARN: [
        "Async/Await-Konzept in Python verstehen",
        "Domain-Driven Design Grundlagen lernen",
        "Kryptographie-Grundlagen verstehen",
    ],
    ChatType.DOCS: [
        "API-Dokumentation für REST-Service generieren",
        "Architecture Decision Records aufsetzen",
        "README und Contributing-Guide schreiben",
    ],
    ChatType.PLAN: [
        "Sprint-Planung für nächstes Quartal",
        "Roadmap für Produkt-MVP definieren",
        "Migration-Strategie für Legacy-System entwickeln",
    ],
    ChatType.CHAT: [
        "Ideen für neues Feature brainstormen",
        "Projekt-Retro durchsprechen",
        "Technologische Trends diskutieren",
    ],
    ChatType.META: [
        "Chat-Hypervisor-Konzept verbessern",
        "Neue Chat-Typen definieren und registrieren",
        "Entscheidungsprozess dokumentieren",
    ],
}

# Default-Fragen pro Typ (werden im Init-Prozess gestellt)
CHAT_TYPE_DEFAULT_QUESTIONS: dict[ChatType, list[str]] = {
    ChatType.CODE: [
        "Welche Programmiersprache/Framework wird verwendet?",
        "Welche Dateien/Module sind betroffen?",
        "Gibt es bestehende Tests, die aktualisiert werden müssen?",
    ],
    ChatType.DEBUG: [
        "Welche Fehlermeldung tritt auf?",
        "Seit wann tritt der Fehler auf (Commit/Version)?",
        "Konnte der Fehler eingegrenzt werden (Modul/Datei)?",
    ],
    ChatType.REFACTOR: [
        "Welcher Code-Bereich soll umstrukturiert werden?",
        "Gibt es ein Ziel-Muster (z.B. Strategy, Repository)?",
        "Müssen Schnittstellen erhalten bleiben?",
    ],
    ChatType.REVIEW: [
        "Welche PR-Nummer oder Branch soll reviewt werden?",
        "Worauf soll besonders geachtet werden (Security, Performance)?",
        "Ist das Review vor oder nach Merge?",
    ],
    ChatType.DEPLOY: [
        "Welche Umgebung (Dev/Staging/Prod)?",
        "Welche Infrastruktur (Docker, K8s, Bare-Metal)?",
        "Gibt es einen Rollback-Plan?",
    ],
    ChatType.TEST: [
        "Welche Test-Ebene (Unit, Integration, E2E)?",
        "Welches Test-Framework soll verwendet werden?",
        "Gibt es kritische Pfade, die priorisiert werden müssen?",
    ],
    ChatType.SETUP: [
        "Welche Art von Projekt (Library, CLI, Web, Mobile)?",
        "Welche Tools sollen konfiguriert werden (Linting, CI)?",
        "Gibt es Vorlagen oder bestehende Projekte als Referenz?",
    ],
    ChatType.GUIDE: [
        "Welcher Wissensstand besteht bereits?",
        "Soll das Ergebnis praktisch anwendbar sein?",
        "Bevorzugte Tiefe (Überblick vs. Details)?",
    ],
    ChatType.RESEARCH: [
        "Gibt es Budget- oder Lizenz-Einschränkungen?",
        "Wie viele Alternativen sollen verglichen werden?",
        "Welche Bewertungskriterien sind wichtig?",
    ],
    ChatType.DESIGN: [
        "Gibt es nicht-funktionale Anforderungen (Skalierung, Sicherheit)?",
        "Welche Systeme/Schnittstellen existieren bereits?",
        "Soll ein bestimmtes Architekturmuster verwendet werden?",
    ],
    ChatType.ANALYZE: [
        "Was soll analysiert werden (Code, Daten, Performance)?",
        "Gibt es konkrete Metriken oder KPIs?",
        "Soll ein Bericht oder nur Erkenntnisse geliefert werden?",
    ],
    ChatType.LEARN: [
        "Welches Vorwissen ist vorhanden?",
        "Bevorzugtes Lernformat (theoretisch, praktisch, gemischt)?",
        "Soll das Gelernte direkt angewendet werden?",
    ],
    ChatType.DOCS: [
        "Zielgruppe der Dokumentation (Entwickler, Endnutzer, Ops)?",
        "Format (Markdown, OpenAPI, Sphinx, Wiki)?",
        "Soll bestehende Doku ergänzt oder neu erstellt werden?",
    ],
    ChatType.PLAN: [
        "Zeithorizont (Sprint, Quartal, Jahr)?",
        "Wer sind die Stakeholder?",
        "Gibt es feste Deadlines oder Abhängigkeiten?",
    ],
    ChatType.CHAT: [
        "Gibt es ein grobes Thema oder völlig offen?",
        "Sollen Entscheidungen vorbereitet oder nur exploriert werden?",
        "Werden Ergebnisse dokumentiert?",
    ],
    ChatType.META: [
        "Welcher Prozess soll verbessert werden?",
        "Gibt es konkrete Schmerzpunkte?",
        "Soll die Änderung generisch oder spezifisch sein?",
    ],
}


# =============================================================================
# Chat-Metadaten (Pydantic-Modell)
# =============================================================================

class ChatMetadata(BaseModel):
    """Vollständige Metadaten eines Chat-Kontexts.

    Dieses Modell ist die kanonische Repräsentation eines Chats
    in der SQLite-Datenbank und im Knowledge Graph.
    """

    # Identität
    id: str = Field(
        default="",
        description="Eindeutige Chat-ID (UUID oder Timestamp-basiert)",
    )
    name: str = Field(
        default="",
        description="Verzeichnisname nach Schema: YYYYMMDD_HHMMSS_Typ_Thema_Aufgabe",
    )

    # Klassifikation
    chat_type: ChatType = Field(
        description="Primärer Chat-Typ aus der Taxonomie",
    )
    category: ChatCategory = Field(
        default=ChatCategory.AKTION,
        description="Kategorie (AKTION, WISSEN, META)",
    )

    # Inhalt
    topic: str = Field(
        default="",
        description="Thema/Repo/Projekt-Bezug",
    )
    task: str = Field(
        default="",
        description="Konkrete Aufgabe/Fragestellung",
    )

    # Zeit
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Erstellungszeitpunkt (ISO 8601 UTC)",
    )
    updated_at: str = Field(
        default="",
        description="Letzter Änderungszeitpunkt",
    )

    # Status
    status: str = Field(
        default="active",
        description="Chat-Status: active, completed, archived, abandoned",
    )

    # Technischer Kontext
    repo_url: Optional[str] = Field(
        default=None,
        description="GitHub-Repository-URL",
    )
    language: Optional[str] = Field(
        default=None,
        description="Verwendete Programmiersprache",
    )
    framework: Optional[str] = Field(
        default=None,
        description="Verwendetes Framework",
    )

    # Organisation
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Priorität 1 (niedrig) bis 5 (kritisch)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Schlagwörter für Suche und Ähnlichkeitsanalyse",
    )

    # Beziehungen
    parent_chat_id: Optional[str] = Field(
        default=None,
        description="ID des übergeordneten Chats (fortgesetzte Sessions)",
    )
    related_chat_ids: list[str] = Field(
        default_factory=list,
        description="IDs verwandter Chats",
    )

    # Pfade
    dir_path: Optional[str] = Field(
        default=None,
        description="Absoluter Pfad zum Chat-Verzeichnis",
    )

    # Statistik
    message_count: int = Field(
        default=0,
        description="Geschätzte oder gezählte Nachrichten",
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Ergebnis: success, partial, failed, undefined",
    )

    def model_post_init(self, __context) -> None:
        """Setze category automatisch aus chat_type."""
        if self.category == ChatCategory.AKTION and self.chat_type:
            self.category = CHAT_TYPE_CATEGORY.get(
                self.chat_type, ChatCategory.AKTION
            )
        if not self.updated_at:
            self.updated_at = self.created_at


# =============================================================================
# Hilfsfunktionen
# =============================================================================

def get_types_by_category(category: ChatCategory) -> list[ChatType]:
    """Gib alle Chat-Typen einer Kategorie zurück."""
    return [t for t, c in CHAT_TYPE_CATEGORY.items() if c == category]


def get_category_description(category: ChatCategory) -> str:
    """Gib die Beschreibung einer Kategorie zurück."""
    descriptions = {
        ChatCategory.AKTION: "Ausführungsorientiert: Code schreiben, debuggen, deployen, testen",
        ChatCategory.WISSEN: "Erkenntnisorientiert: Lernen, recherchieren, analysieren, designen",
        ChatCategory.META: "Steuerungsorientiert: Planen, reflektieren, Prozesse verbessern",
    }
    return descriptions.get(category, "Unbekannte Kategorie")
