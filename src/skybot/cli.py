"""Console script for skybot."""

import os
from typing import Optional
import re
import logging
import warnings

from rich.live import Live
from rich.spinner import Spinner
from rich import print as rprint

import typer
from rich.console import Console

from skybot.ai.terraform_generator import gen_terraform
from skybot.infra_utils.terraform import TerraformWrapper
from skybot.utils.parsing import extract_code_blocks
from skybot import api
from skybot import __version__
from skybot.utils.logging_config import setup_logging
from skybot.ai.summary import summarize_terraform_plan

# Filter out the specific Pydantic warning
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2:*")

WORKDIR = ".skybot/default"

app = typer.Typer()
component_app = typer.Typer(help="Manage components in SkyBot")
logger = logging.getLogger("skybot.cli")

app.add_typer(component_app, name="component")
console = Console()

# Sub-commands for "component"


@app.command("init")
def init_project(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed initialization steps"
    ),
    local: bool = typer.Option(
        False, "--local", "-l", help="Use localstack for infrastructure"
    ),
):
    """Initialize a new project."""
    logger.debug("Initializing new project")
    api.init_project(verbose=verbose, local=local)


@component_app.command("create")
def create_component(
    prompt: str = typer.Option(
        ...,
        "--prompt",
        "-p",
        help="Input prompt for creating resources on the cloud",
        prompt="Please enter your prompt",
    ),
    name: str = typer.Option(
        "main",
        "--name",
        "-n",
        help="Name of the component to create",
        prompt="Please provide component name",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed Terraform plan output"
    ),
    model: str = typer.Option(
        "gpt-4o", "--model", "-m", help="AI model to use for generation"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation and automatically apply changes"
    ),
):
    """Create a new component."""
    # Validate the component name
    logger.debug(f"Creating component with name: {name}")
    if not re.match(r"^[a-zA-Z0-9-_]+$", name):
        logger.error(f"Invalid component name: {name}")
        rprint("Invalid component name. It should contain only A-Z, a-z, 0-9, and -.")
        return

    # Check if Terraform file already exists
    tf_file_path = f"{WORKDIR}/{name}.tf"
    if os.path.exists(tf_file_path):
        logger.warning(f"Terraform file already exists: {tf_file_path}")
        rprint(
            f"Terraform file '{name}.tf' already exists. Please choose a different name or overwrite the existing one."
        )
        return

    terraform_wrapper = TerraformWrapper(WORKDIR)

    # Check if project is already initialized
    if not os.path.exists(WORKDIR):
        logger.error("Project not initialized")
        rprint("Project is not initialized. Run `skybot init` first")
        return

    # Create a spinner
    spinner = Spinner("dots", text="Generating Terraform resources...")

    # Use Live context to manage the spinner
    with Live(spinner, refresh_per_second=10) as live:
        logger.debug(
            f"Generating terraform code for prompt: {prompt} using model: {model}"
        )
        # Generate terraform code
        response = gen_terraform(prompt, model=model)
        terraform_code = extract_code_blocks(response, title="terraform")[0]
        _ = extract_code_blocks(response, title="remarks")[0]

        # Update spinner text before stopping
        spinner.text = "Generation complete!"

    # Save the generated Terraform code to a file named {name}.tf under workdir
    logger.debug(f"Saving terraform code to: {tf_file_path}")
    with open(tf_file_path, "w") as f:
        f.write(terraform_code)
    rprint(
        f"[bold green]Terraform file saved successfully at {tf_file_path}[/bold green]"
    )

    try:
        # Run Terraform plan
        logger.debug("Running terraform plan")
        with Live(Spinner("dots", text="Generating a plan..."), refresh_per_second=10):
            plan_output = terraform_wrapper.plan()

        # Generate and display the plan summary regardless of verbose mode
        summary = summarize_terraform_plan(plan_output)
        if summary:
            rprint("\n[bold]Plan Summary:[/bold]")
            rprint(summary)

        if verbose:
            rprint("\nDetailed Terraform Plan:")
            rprint(plan_output)

        # Skip confirmation if force flag is set
        if force:
            confirmation = True
        else:
            confirmation = typer.confirm(
                "Do you want to apply these changes?", default=False
            )

        if confirmation:
            # Apply the changes
            logger.debug("Applying terraform changes")
            with Live(Spinner("dots"), refresh_per_second=10) as live:
                live.update("[yellow]Applying Terraform changes...[/yellow]")
                terraform_wrapper.apply()
            rprint("[bold green]Changes applied successfully![/bold green]")
        else:
            logger.info("User declined to apply changes")
            # TODO: actually this is not a good idea, because the user can do keyboard interrupt at this point
            # Rollback: delete the created Terraform file
            os.remove(tf_file_path)
            rprint("[bold red]Terraform changes not applied.[/bold red]")
    except Exception as e:
        logger.error(f"Error during terraform operations: {str(e)}")
        rprint(f"An error occurred: {e}")


def _validate_component_and_project(
    component_name: Optional[str] = None,
) -> tuple[list[str], Optional[str]]:
    """Validate project initialization and component existence."""
    if not os.path.exists(WORKDIR):
        logger.error("Project not initialized")
        rprint("Project is not initialized. Run `skybot init` first")
        return [], None

    if component_name:
        tf_file_path = f"{WORKDIR}/{component_name}.tf"
        if not os.path.exists(tf_file_path):
            logger.error(f"Component not found: {component_name}")
            rprint(f"[bold red]Component '{component_name}' not found![/bold red]")
            return [], None

    # Get list of component files
    components = [
        file[:-3]
        for file in os.listdir(WORKDIR)
        if file.endswith(".tf")
        and not file.endswith("backend.tf")
        and not file.endswith("provider.tf")
    ]

    return components, tf_file_path if component_name else None


def _confirm_action(
    action: str,
    component_name: Optional[str],
    components: list[str],
    force: bool,
    action_description: str = "",
) -> bool:
    """Get user confirmation for an action."""
    if component_name is None:
        message = f"Are you sure you want to {action} all components? {action_description}Components affected: {', '.join(components)}"
    else:
        message = f"Are you sure you want to {action} component '{component_name}'? {action_description}"

    if force or typer.confirm(message, default=False):
        return True

    logger.info(f"User cancelled {action}")
    rprint(f"[yellow]{action.capitalize()} cancelled.[/yellow]")
    return False


@component_app.command("destroy")
def destroy_component(
    component_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Name of the component to destroy infrastructure for",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force destruction without confirmation"
    ),
):
    """Destroy a component's cloud infrastructure while keeping its configuration."""
    logger.debug("Destroying component infrastructure")

    components, _ = _validate_component_and_project(component_name)
    if not components:
        return

    if not _confirm_action(
        "destroy",
        component_name,
        components,
        force,
        "This action will remove resources while keeping their corresponding configuration.",
    ):
        return

    terraform_wrapper = TerraformWrapper(WORKDIR)
    try:
        with Live(
            Spinner("dots", text="Destroying infrastructure..."), refresh_per_second=10
        ):
            result = terraform_wrapper.destroy(component_name)
        logger.debug("result from terraform:", result)
        if component_name:
            rprint(
                f"[bold green]Infrastructure for component '{component_name}' has been successfully destroyed![/bold green]"
            )
        else:
            rprint(
                "[bold green]All infrastructure has been successfully destroyed![/bold green]"
            )

    except Exception as e:
        logger.error(f"Error destroying component infrastructure: {str(e)}")
        rprint(
            f"[bold red]An error occurred while destroying the infrastructure: {str(e)}[/bold red]"
        )


@component_app.command("delete")
def delete_component(
    component_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Name of the component configuration to delete",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
):
    """Delete a component's configuration file."""
    logger.debug("Deleting component configuration")

    # Check if project is initialized
    components, tf_file_path = _validate_component_and_project(component_name)
    if not components:
        return

    # Check for existing infrastructure and warn user
    terraform_wrapper = TerraformWrapper(WORKDIR)

    # Confirm deletion unless force flag is used
    if not _confirm_action(
        "delete",
        component_name,
        components,
        force,
        "This action will remove resources and their corresponding configuration.",
    ):
        return

    try:
        # Run terraform destroy for the specific component
        with Live(
            Spinner("dots", text="Destroying infrastructure'..."), refresh_per_second=10
        ):
            terraform_wrapper.destroy(component_name)

        if component_name:
            # Delete the Terraform file
            tf_file_path = f"{WORKDIR}/{component_name}.tf"
            os.remove(tf_file_path)
            logger.info(f"Deleted terraform file: {tf_file_path}")
            rprint(
                f"[bold green]Component '{component_name}' and its infrastructure have been successfully deleted![/bold green]"
            )
        else:
            # Delete all Terraform files
            for file in os.listdir(WORKDIR):
                if (
                    file.endswith(".tf")
                    and not file.endswith("backend.tf")
                    and not file.endswith("provider.tf")
                ):
                    tf_file_path = os.path.join(WORKDIR, file)
                    os.remove(tf_file_path)
                    logger.debug(f"Deleted terraform file: {tf_file_path}")
            rprint(
                "[bold green]All component configurations have been deleted![/bold green]"
            )

    except Exception as e:
        logger.error(f"Error deleting component configuration: {str(e)}")
        rprint(
            f"[bold red]An error occurred while deleting the configuration: {str(e)}[/bold red]"
        )


@component_app.command("edit")
def edit_component(
    component_name: str = typer.Argument(..., help="Name of the component to edit"),
):
    """Edit a component."""
    logger.debug(f"Editing component: {component_name}")
    rprint(f"[bold red]Component '{component_name}' edited successfully![/bold red]")


@app.command(name="chat")
def chat(
    component_name: Optional[str] = typer.Argument(
        ..., help="Name of the component to chat about"
    ),
):
    """Chat with your cloud using SkyBot."""
    logger.debug(f"Chatting about component: {component_name}")
    rprint(
        f"[bold red]Component '{component_name}' chatted with successfully![/bold red]"
    )


@app.command("version")
def version():
    """Display the version of SkyBot."""
    rprint(f"SkyBot version: {__version__}")


if __name__ == "__main__":
    # Initialize logging with debug mode set to True
    setup_logging(debug_mode=True)
    logger.debug("Starting skybot CLI")
    app()
