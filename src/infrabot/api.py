from typing import Optional

from rich import print as rprint

from infrabot.ai.chat import ChatSession
from infrabot.service import (
    create_component,
    init_project as service_init_project,
    InitProjectResponse,
)

# Export functions to make them available through the API
__all__ = ["init_project", "start_chat_session", "create_component"]


def init_project(
    workdir: str = ".infrabot/default", verbose: bool = False, local: bool = False
) -> InitProjectResponse:
    """Initialize a new project.

    This function now delegates to the service function but maintains the original CLI output.
    """
    # Call the service function
    result = service_init_project(workdir=workdir, verbose=verbose, local=local)

    # Still provide the CLI output for backward compatibility
    if result.success:
        rprint(f"[green] Initialized project directory ({workdir})[/green]")
        rprint("[green]Initialized terraform[/green]")
        rprint("[bold green]Project initialized successfully[/bold green]")
    else:
        rprint(f"[bold red]{result.message}[/bold red]")

    return result


def start_chat_session(
    component_name: Optional[str] = None, workdir: str = ".infrabot/default"
):
    """Start an interactive chat session about infrastructure components."""
    chat_session = ChatSession(workdir=workdir)
    chat_session.start_chat(component_name)
