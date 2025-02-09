import os
from typing import Optional
from rich.spinner import Spinner
from rich.live import Live

from infrabot.infra_utils.terraform import TerraformWrapper
from rich import print as rprint

from infrabot.utils.os import get_package_directory, copy_assets
from infrabot.ai.chat import ChatSession


def init_project(
    workdir: str = ".infrabot/default", verbose: bool = False, local: bool = False
):
    """Initialize a new project."""

    # Ensure default directory exists inside .infrabot
    os.makedirs(workdir, exist_ok=True)

    # Copy boilerplate assets from assets/ to workdir
    package_dir = get_package_directory("infrabot")
    assets_dir = os.path.join(package_dir, "../../assets/terraform/")
    copy_assets(
        assets_dir,
        workdir,
        whitelist=["provider.tf" if not local else "provider_local.tf", "backend.tf"],
    )
    # copy_assets(assets_dir, workdir, whitelist=["backend.tf"])
    rprint(f"[green] Initialized project directory ({workdir})[/green]")

    # Initialize Terraform in the default directory
    terraform_wrapper = TerraformWrapper(workdir)

    # Create a spinner
    spinner = Spinner("dots", text="Initializing terraform (backend, plugins, etc)...")

    try:
        # Use Live context to manage the spinner
        # TODO: Actually a live spinner does not play well with stdout outputs from terraform init
        with Live(spinner, refresh_per_second=10):
            terraform_wrapper.init(verbose=verbose)
        rprint("[green]Initialized terraform[/green]")
    except Exception as e:
        rprint(f"[bold red]{e}[/bold red]")

    rprint("[bold green]Project initialized successfully[/bold green]")


def start_chat_session(
    component_name: Optional[str] = None, workdir: str = ".infrabot/default"
):
    """Start an interactive chat session about infrastructure components."""
    chat_session = ChatSession(workdir=workdir)
    chat_session.start_chat(component_name)
