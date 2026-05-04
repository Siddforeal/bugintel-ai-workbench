"""
Optional terminal UFO intro for Blackhole AI Workbench.

The intro is shown only for human-facing startup/intro flows. Normal CLI
commands, JSON-output workflows, tests, CI, and automation should stay clean.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel


UFO_ASCII = r"""
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⢉⣠⣤⣤⣤⣤⣄⡉⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⣴⠃⠀⣸⣿⣿⣿⣿⣿⣦⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⠟⠛⠉⣿⡀⢿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢀⣿⠉⠛⠻⣿⣿⣿⣿⣿
⣿⣿⣿⠋⣀⣀⠀⠀⠘⢷⣤⣈⣉⡉⠉⠉⢉⣉⣁⣤⡾⠃⠀⢀⣀⣀⠙⣿⣿⣿
⣿⣿⡇⢸⡏⠉⢻⡆⠀⠀⠈⠉⠙⠛⠛⠛⠛⠋⠉⠁⠀⠀⣴⡏⠉⣹⡇⢸⣿⣿
⣿⣿⣿⣌⠻⠶⠾⠃⠀⠀⠀⠀⢀⣴⠾⠷⣦⡀⠀⠀⠀⠀⠙⠷⠾⠛⣠⣿⣿⣿
⣿⣿⣿⣿⣿⣦⣤⣀⡀⠀⠀⠀⠘⢷⣤⣤⡾⠃⠀⠀⠀⢀⣀⣤⣴⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡶⠶⠶⣾⣷⠶⠶⢶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁⠀⠀⠀⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
""".strip("\n")


@dataclass(frozen=True)
class IntroConfig:
    version: str = "0.37.0"
    force: bool = False
    clear_screen: bool = True


def should_show_intro(force: bool = False) -> bool:
    if force:
        return True

    if os.environ.get("BUGINTEL_NO_INTRO") == "1":
        return False

    if os.environ.get("CI"):
        return False

    return sys.stdout.isatty()


def render_intro_panel(version: str) -> Panel:
    body = (
        f"[bold bright_green]Welcome to Blackhole AI Workbench[/bold bright_green] "
        f"[dim]{version}[/dim]\n"
        f"[green]{'.' * 72}[/green]\n"
        f"[bright_green]{UFO_ASCII}[/bright_green]\n"
        f"[green]{'.' * 72}[/green]\n"
        "[bold green]Scope Guard online[/bold green]  "
        "[bold cyan]Evidence engine ready[/bold cyan]  "
        "[bold magenta]Research planner ready[/bold magenta]  "
        "[bold yellow]LLM bridge safe-mode[/bold yellow]\n"
        "[dim]Let's hunt safely.[/dim]"
    )

    return Panel(
        body,
        title="[bold bright_green]Blackhole Signal[/bold bright_green]",
        border_style="green",
    )


def show_intro(
    *,
    console: Console | None = None,
    config: IntroConfig | None = None,
) -> None:
    console = console or Console()
    config = config or IntroConfig()

    if not should_show_intro(force=config.force):
        return

    if config.clear_screen:
        console.clear()

    console.print(render_intro_panel(config.version))
