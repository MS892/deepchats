"""
deepchats CLI — Kommandozeilen-Interface für den Chat-Hypervisor.

Verwendet Typer für Command-Struktur und Rich für
ansprechende Konsolen-Ausgabe.
"""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.db import (
    create_decision,
    get_all_tags,
    get_db_path,
    get_home_dir,
    get_stats,
    init_db,
    link_chats,
    list_chats,
    search_chats,
    tag_chat as db_tag_chat,
    unlink_chats,
    untag_chat,
    update_chat,
    get_chat,
)
from app.init_chat import ChatInitializer
from app.post_chat import run_post_chat
from app.registry import TypeRegistry
from app.types import (
    CHAT_TYPE_CATEGORY,
    CHAT_TYPE_DESCRIPTIONS,
    CHAT_TYPE_ICONS,
    ChatCategory,
    ChatMetadata,
    ChatType,
)

# =============================================================================
# App Setup
# =============================================================================

app = typer.Typer(
    name="deepchats",
    help="Chat-Hypervisor — Verwalte KI-Chat-Kontexte strukturiert",
    add_completion=False,
)

console = Console()


# =============================================================================
# Hilfsfunktionen für Rich-Output
# =============================================================================

def _make_prompt_fn():
    """Erstelle eine Prompt-Funktion mit Rich-Styling."""

    def prompt(text: str, field_type: str, choices: list[str] | None = None) -> str:
        """Zeige einen Prompt und lies Benutzereingabe."""
        if field_type == "choice" and choices:
            # Zeige Choices als nummerierte Liste
            choice_text = "\n".join(
                f"  [{i+1}] {c}" for i, c in enumerate(choices)
            )
            console.print(
                Panel(
                    f"{text}\n\n{choice_text}",
                    title="Frage",
                    border_style="blue",
                )
            )
        elif field_type == "bool":
            console.print(
                Panel(
                    f"{text}\n  [J/N]",
                    title="Frage",
                    border_style="blue",
                )
            )
        else:
            console.print(
                Panel(text, title="Frage", border_style="blue")
            )

        return typer.prompt("→", default="")

    return prompt


def _make_confirm_fn():
    """Erstelle eine Confirm-Funktion mit Rich-Styling."""

    def confirm(text: str) -> bool:
        console.print(Panel(text, title="Bestätigung", border_style="yellow"))
        return typer.confirm("→", default=True)

    return confirm


def _display_chat_summary(metadata: ChatMetadata) -> None:
    """Zeige eine Chat-Zusammenfassung im Rich-Format."""
    icon = CHAT_TYPE_ICONS.get(metadata.chat_type, "❓")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")

    table.add_row("ID", metadata.id)
    table.add_row("Name", metadata.name)
    table.add_row(
        f"{icon} Typ",
        f"{metadata.chat_type.value} "
        f"({CHAT_TYPE_DESCRIPTIONS.get(metadata.chat_type, '')})",
    )
    table.add_row("Thema", metadata.topic or "(kein)")
    table.add_row("Aufgabe", metadata.task or "(kein)")
    table.add_row(
        "Priorität", "⭐" * metadata.priority
    )
    table.add_row("Status", metadata.status)
    table.add_row("Pfad", metadata.dir_path or "(kein)")
    table.add_row("Erstellt", metadata.created_at[:19] if metadata.created_at else "")

    if metadata.repo_url:
        table.add_row("Repo", metadata.repo_url)
    if metadata.language:
        table.add_row("Sprache", metadata.language)
    if metadata.framework:
        table.add_row("Framework", metadata.framework)
    if metadata.tags:
        table.add_row("Tags", ", ".join(f"[blue]{t}[/]" for t in metadata.tags))

    console.print(
        Panel(table, title=f"Chat {metadata.id}", border_style="green")
    )


def _display_chat_list(chats: list[ChatMetadata]) -> None:
    """Zeige eine Liste von Chats als Rich-Tabelle."""
    if not chats:
        console.print("[yellow]Keine Chats gefunden.[/]")
        return

    table = Table(title=f"Chats ({len(chats)})")
    table.add_column("ID", style="dim")
    table.add_column("Typ", style="bold")
    table.add_column("Thema")
    table.add_column("Aufgabe")
    table.add_column("Erstellt")
    table.add_column("Tags")

    for chat in chats:
        icon = CHAT_TYPE_ICONS.get(chat.chat_type, "❓")
        table.add_row(
            chat.id,
            f"{icon} {chat.chat_type.value}",
            chat.topic[:30] if chat.topic else "-",
            chat.task[:40] if chat.task else "-",
            chat.created_at[:10] if chat.created_at else "",
            ", ".join(chat.tags[:3]) if chat.tags else "",
        )

    console.print(table)


# =============================================================================
# Commands
# =============================================================================

@app.command()
def init(
    chat_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Chat-Typ (code, debug, guide, research, ...)",
    ),
    topic: Optional[str] = typer.Option(
        None,
        "--topic",
        help="Thema/Repo",
    ),
    task: Optional[str] = typer.Option(
        None,
        "--task",
        help="Aufgabe/Fragestellung",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive", "-n",
        help="Nicht-interaktiver Modus (erfordert --type, --topic, --task)",
    ),
) -> None:
    """Initialisiere einen neuen Chat-Kontext.

    Führt den interaktiven Init-Prozess mit Fragen,
    Verzeichniserstellung und Registry-Eintrag durch.
    """
    console.print(
        Panel.fit(
            "[bold]🌐 deepchats — Chat-Hypervisor v0.1.0[/]\n"
            "Initialisiere neuen Chat-Kontext...",
            border_style="green",
        )
    )

    # Validiere non-interactive mode
    if non_interactive and (not chat_type or not topic or not task):
        console.print(
            "[red]Fehler: --non-interactive erfordert --type, --topic und --task[/]"
        )
        raise typer.Exit(1)

    # Konvertiere chat_type
    ct = None
    if chat_type:
        try:
            ct = ChatType(chat_type.lower().strip())
        except ValueError:
            console.print(
                f"[red]Unbekannter Chat-Typ: {chat_type}[/]"
            )
            console.print(
                f"Verfügbar: "
                f"{', '.join(t.value for t in ChatType)}"
            )
            raise typer.Exit(1)

    # Starte Initialisierung
    initializer = ChatInitializer(
        prompt_fn=_make_prompt_fn(),
        confirm_fn=_make_confirm_fn(),
    )

    try:
        metadata = initializer.run(
            chat_type=ct,
            topic=topic,
            task=task,
        )

        # Zusammenfassung
        console.print()
        console.print(
            Panel(
                initializer.get_summary(metadata),
                border_style="green",
            )
        )

        console.print(
            f"\n[bold green]✅ Chat {metadata.id} "
            f"erfolgreich initialisiert![/]"
        )
        console.print(
            f"[dim]Verzeichnis: {metadata.dir_path}[/]"
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Init abgebrochen.[/]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Fehler bei der Initialisierung: {e}[/]")
        raise typer.Exit(1)


@app.command("list")
def list_cmd(
    chat_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Nach Chat-Typ filtern"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Nach Kategorie filtern (aktion, wissen, meta)"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Nach Status filtern (active, completed, archived)"
    ),
    topic_filter: Optional[str] = typer.Option(
        None, "--topic", help="Topic-Suche (LIKE)"
    ),
    recent: int = typer.Option(50, "--recent", "-r", help="Anzahl der neuesten Chats"),
    json_output: bool = typer.Option(
        False, "--json", help="JSON-Ausgabe statt Tabelle"
    ),
) -> None:
    """Liste alle Chat-Kontexte."""
    # Konvertiere Filter
    ct = None
    if chat_type:
        try:
            ct = ChatType(chat_type.lower().strip())
        except ValueError:
            console.print(f"[red]Unbekannter Chat-Typ: {chat_type}[/]")
            raise typer.Exit(1)

    cat = None
    if category:
        try:
            cat = ChatCategory(category.lower().strip())
        except ValueError:
            console.print(f"[red]Unbekannte Kategorie: {category}[/]")
            raise typer.Exit(1)

    chats = list_chats(
        chat_type=ct,
        category=cat,
        status=status,
        topic=topic_filter,
        limit=recent,
    )

    if json_output:
        import json
        data = [
            {
                "id": c.id,
                "name": c.name,
                "chat_type": c.chat_type.value,
                "category": c.category.value,
                "topic": c.topic,
                "task": c.task,
                "status": c.status,
                "tags": c.tags,
                "created_at": c.created_at,
            }
            for c in chats
        ]
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _display_chat_list(chats)

    if not json_output:
        console.print(f"\n[dim]Gesamt: {len(chats)} Chats[/]")


@app.command()
def show(
    chat_id: str = typer.Argument(..., help="Chat-ID"),
    json_output: bool = typer.Option(
        False, "--json", help="JSON-Ausgabe statt Formatierung"
    ),
) -> None:
    """Zeige Details eines Chat-Kontexts."""
    metadata = get_chat(chat_id)

    if metadata is None:
        console.print(f"[red]Chat {chat_id} nicht gefunden.[/]")
        raise typer.Exit(1)

    if json_output:
        import json
        console.print(
            json.dumps(
                metadata.model_dump(),
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
    else:
        _display_chat_summary(metadata)


@app.command()
def search(
    query: str = typer.Argument(..., help="Suchbegriff"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximale Ergebnisse"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Durchsuche Chat-Kontexte."""
    results = search_chats(query, limit=limit)

    if json_output:
        import json
        data = [
            {"id": c.id, "name": c.name, "topic": c.topic, "task": c.task, "tags": c.tags}
            for c in results
        ]
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _display_chat_list(results)

    if not json_output:
        console.print(f"\n[dim]{len(results)} Ergebnisse für '{query}'[/]")


@app.command()
def tag(
    chat_id: str = typer.Argument(..., help="Chat-ID"),
    add: Optional[list[str]] = typer.Option(None, "--add", "-a", help="Tags hinzufügen"),
    remove: Optional[list[str]] = typer.Option(None, "--remove", "-r", help="Tags entfernen"),
    list_tags: bool = typer.Option(False, "--list", "-l", help="Tags des Chats anzeigen"),
) -> None:
    """Verwalte Tags eines Chat-Kontexts."""
    if list_tags:
        metadata = get_chat(chat_id)
        if metadata:
            if metadata.tags:
                console.print(
                    Panel(
                        "\n".join(f"• {t}" for t in metadata.tags),
                        title=f"Tags für {chat_id}",
                        border_style="blue",
                    )
                )
            else:
                console.print("[yellow]Keine Tags.[/]")
        else:
            console.print(f"[red]Chat {chat_id} nicht gefunden.[/]")
        return

    if add:
        for tag_name in add:
            db_tag_chat(chat_id, tag_name)
            console.print(f"[green]✓ Tag '{tag_name}' hinzugefügt[/]")

    if remove:
        for tag_name in remove:
            untag_chat(chat_id, tag_name)
            console.print(f"[yellow]✓ Tag '{tag_name}' entfernt[/]")

    if not add and not remove and not list_tags:
        console.print("[yellow]Keine Aktion. Nutze --add, --remove oder --list[/]")


@app.command()
def link(
    source: str = typer.Argument(..., help="Quell-Chat-ID"),
    target: str = typer.Argument(..., help="Ziel-Chat-ID"),
    link_type: str = typer.Option("related", "--type", "-t", help="Art der Verknüpfung"),
    weight: float = typer.Option(1.0, "--weight", "-w", help="Gewichtung (0-1)"),
    remove: bool = typer.Option(False, "--remove", help="Verknüpfung entfernen"),
) -> None:
    """Verknüpfe zwei Chat-Kontexte."""
    if remove:
        unlink_chats(source, target, link_type if link_type != "related" else None)
        console.print(f"[yellow]✓ Verknüpfung {source} ↔ {target} entfernt[/]")
    else:
        link_chats(source, target, link_type, weight)
        console.print(
            f"[green]✓ {source} → {target} "
            f"({link_type}, weight={weight})[/]"
        )


@app.command()
def stats() -> None:
    """Zeige Statistiken über alle Chats."""
    data = get_stats()

    # Übersicht
    overview = Table(title="Chat-Statistiken", show_header=False)
    overview.add_column("Metrik", style="bold cyan")
    overview.add_column("Wert")
    overview.add_row("Gesamt Chats", str(data["total_chats"]))
    overview.add_row("Tags", str(data["total_tags"]))
    overview.add_row("Verknüpfungen", str(data["total_links"]))
    console.print(overview)

    # Nach Typ
    if data["by_type"]:
        type_table = Table(title="Chats nach Typ")
        type_table.add_column("Typ")
        type_table.add_column("Anzahl")
        type_table.add_column("Verteilung")

        max_count = max(data["by_type"].values()) if data["by_type"] else 1
        for chat_type, count in sorted(
            data["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            icon = CHAT_TYPE_ICONS.get(
                ChatType(chat_type) if chat_type in ChatType.__members__ else ChatType.CHAT,
                "❓",
            )
            bar = "█" * int(30 * count / max_count)
            type_table.add_row(f"{icon} {chat_type}", str(count), bar)
        console.print(type_table)

    # Nach Status
    if data["by_status"]:
        status_table = Table(title="Chats nach Status")
        status_table.add_column("Status")
        status_table.add_column("Anzahl")
        for st, cnt in data["by_status"].items():
            status_table.add_row(st, str(cnt))
        console.print(status_table)


@app.command()
def config(
    set_home: Optional[str] = typer.Option(
        None, "--set-home", help="DEEPCHATS_HOME setzen"
    ),
    show: bool = typer.Option(False, "--show", help="Aktuelle Konfiguration anzeigen"),
) -> None:
    """Konfiguriere deepchats."""
    if show:
        info = Table(show_header=False)
        info.add_column("Key", style="bold cyan")
        info.add_column("Value")
        info.add_row("DEEPCHATS_HOME", get_home_dir())
        info.add_row("DB_PATH", get_db_path())
        console.print(Panel(info, title="Konfiguration", border_style="blue"))
        return

    if set_home:
        os.environ["DEEPCHATS_HOME"] = str(set_home)
        console.print(
            f"[green]✓ DEEPCHATS_HOME = {set_home}[/]"
        )
        console.print("[dim]Hinweis: Nur für diese Session gültig.[/]")
        # Initialisiere DB am neuen Pfad
        init_db()
        return

    console.print("[yellow]Keine Aktion. Nutze --show oder --set-home[/]")


@app.command()
def post_chat(
    chat_id: str = typer.Argument(..., help="Chat-ID für Nachbereitung"),
) -> None:
    """Führe Post-Chat-Analyse für einen Chat durch."""
    console.print(f"Führe Post-Chat-Analyse für {chat_id} durch...")

    try:
        results = run_post_chat(chat_id)

        success_count = sum(1 for r in results if r.success)

        table = Table(title=f"Post-Chat Ergebnisse: {chat_id}")
        table.add_column("Processor")
        table.add_column("Status")
        table.add_column("Details")

        for result in results:
            status_text = "[green]✓[/]" if result.success else "[red]✗[/]"
            details = (
                ", ".join(result.suggestions[:3])
                if result.suggestions
                else (
                    result.errors[0][:50]
                    if result.errors
                    else "-"
                )
            )
            table.add_row(result.processor_name, status_text, details)

        console.print(table)
        console.print(
            f"\n[green]{success_count}/{len(results)} "
            f"Processoren erfolgreich[/]"
        )

    except Exception as e:
        console.print(f"[red]Fehler: {e}[/]")
        raise typer.Exit(1)


@app.command()
def decision(
    chat_id: str = typer.Argument(..., help="Chat-ID"),
    title: str = typer.Option(..., "--title", "-t", help="Titel der Entscheidung"),
    content: str = typer.Option("", "--content", "-c", help="Inhalt (Markdown)"),
    importance: str = typer.Option("MEDIUM", "--importance", "-i", help="LOW, MEDIUM, HIGH, CRITICAL"),
) -> None:
    """Dokumentiere eine Architekturentscheidung."""
    decision_id = create_decision(chat_id, title, content, importance)
    console.print(
        f"[green]✓ Decision #{decision_id} erstellt: {title}[/]"
    )


# =============================================================================
# Entry Point
# =============================================================================

def main() -> None:
    """Entry point für deepchats CLI."""
    app()


if __name__ == "__main__":
    main()
