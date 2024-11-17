"""Console script for easycloud."""
from typing import Optional

from rich.live import Live
from rich.spinner import Spinner
from rich import print as rprint

import typer
from rich.console import Console

from easycloud.ai.terraform_generator import gen_terraform
from easycloud.utils.parsing import extract_code_blocks

app = typer.Typer()
component_app = typer.Typer(help="Manage components in EasyCloud")

app.add_typer(component_app, name="component")
console = Console()

# Sub-commands for "component"

@app.command("init")
def init_project():
    """Initialize a new project."""
    rprint(f"[bold green]Project initialized successfully![/bold green]")

@component_app.command("create")
def create_component(
    prompt: str = typer.Option(
        ...,
        "--prompt", "-p",
        help="Input prompt for creating resources on the cloud",
        prompt="Please enter your prompt"
    )
):
    """Create a new component."""
    # Create a spinner
    spinner = Spinner("dots", text="Generating Terraform resources...")

    # Use Live context to manage the spinner
    with Live(spinner, refresh_per_second=10) as live:
        # Generate terraform code
        response = gen_terraform(prompt)
        terraform_code = extract_code_blocks(response, title="terraform")[0]
        remarks = extract_code_blocks(response, title="remarks")[0]

        # Update spinner text before stopping
        spinner.text = "Generation complete!"

    # Print the generated terraform code with syntax highlighting
    rprint(f"\n[bold green]Generated Terraform Code:[/bold green]")
    console.print(terraform_code, style="blue")
    rprint(f"\n[bold green]Remarks:[/bold green]")
    console.print(remarks, style="blue")

@component_app.command("delete")
def delete_component(
    component_name: str = typer.Argument(..., help="Name of the component to delete")
):
    """Delete a component."""
    rprint(f"[bold red]Component '{component_name}' deleted successfully![/bold red]")

@component_app.command("edit")
def edit_component(
    component_name: str = typer.Argument(..., help="Name of the component to edit")
):
    """Edit a component."""
    rprint(f"[bold red]Component '{component_name}' edited successfully![/bold red]")

@app.command(name="chat")
def chat(
    component_name: Optional[str] = typer.Argument(..., help="Name of the component to chat about")
):
    """Chat with your cloud using EasyCloud."""
    rprint(f"[bold red]Component '{component_name}' chatted with successfully![/bold red]")



if __name__ == "__main__":
    app()
