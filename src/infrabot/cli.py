"""Console script for infrabot."""

import os
from typing import Optional
import re
import logging
import warnings
import uuid

from rich.live import Live
from rich.spinner import Spinner
from rich import print as rprint

import typer
from rich.console import Console

from infrabot.ai.terraform_generator import (
    gen_terraform,
    fix_terraform,
    log_terraform_error,
)
from infrabot.infra_utils.terraform import TerraformWrapper
from infrabot.infra_utils.component_manager import (
    TerraformComponentManager,
    TerraformComponent,
)
from infrabot.utils.parsing import extract_code_blocks
from infrabot import api
from infrabot import __version__
from infrabot.utils.logging_config import setup_logging
from infrabot.ai.summary import summarize_terraform_plan

# Filter out the specific Pydantic warning
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2:*")

WORKDIR = ".infrabot/default"

app = typer.Typer()
component_app = typer.Typer(help="Manage components in InfraBot")
logger = logging.getLogger("infrabot.cli")

app.add_typer(component_app, name="component")
console = Console()


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
    self_healing: bool = typer.Option(
        False,
        "--self-healing",
        "-s",
        help="Enable self-healing mode to automatically fix terraform errors",
    ),
    max_attempts: int = typer.Option(
        3, "--max-attempts", help="Maximum number of self-healing attempts"
    ),
    keep_on_failure: bool = typer.Option(
        False,
        "--keep-on-failure",
        help="Keep generated Terraform files even if an error occurs",
    ),
    langfuse_session_id: Optional[str] = typer.Option(
        None,
        "--langfuse-session-id",
        help="Session ID for Langfuse tracking. Auto-generated if not provided",
    ),
):
    """Create a new component."""
    # Validate the component name
    logger.debug(f"Creating component with name: {name}")

    if not re.match(r"^[a-zA-Z0-9-_]+$", name):
        logger.error(f"Invalid component name: {name}")
        rprint("Invalid component name. It should contain only A-Z, a-z, 0-9, and -.")
        return

    # Check if project is initialized
    if not TerraformComponentManager.ensure_project_initialized(WORKDIR):
        rprint("Project is not initialized. Run `infrabot init` first")
        return

    # Create component object to check existence
    component = TerraformComponent(name=name, terraform_code="", workdir=WORKDIR)
    if TerraformComponentManager.component_exists(component):
        rprint(f"Component '{name}' already exists. Please choose a different name.")
        return

    terraform_wrapper = TerraformWrapper(WORKDIR)
    session_id = langfuse_session_id or str(uuid.uuid4())

    # Create a spinner for generation
    spinner = Spinner("dots", text="Generating Terraform resources...")

    # Generate terraform code
    with Live(spinner, refresh_per_second=10) as live:
        logger.debug(
            f"Generating terraform code for prompt: {prompt} using model: {model}"
        )
        response = gen_terraform(prompt, model=model, session_id=session_id)

        # in case the response is coming from a reasoning model
        # Remove content between <think></think> tags
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

        terraform_code = extract_code_blocks(response, title="terraform")[0]
        tfvars_code = next(
            iter(extract_code_blocks(response, title="module.tfvars")), ""
        )
        _ = next(iter(extract_code_blocks(response, title="remarks")), "")

        # Update spinner text before stopping
        spinner.text = "Generation complete!"

    # Update component with generated code
    component.terraform_code = terraform_code
    component.tfvars_code = tfvars_code

    attempt = 1
    while attempt <= max_attempts:
        try:
            # Save the component files
            if not TerraformComponentManager.save_component(component, overwrite=True):
                return

            try:
                # Run Terraform plan
                logger.debug("Running terraform plan")
                with Live(
                    Spinner("dots", text="Generating a plan..."), refresh_per_second=10
                ):
                    plan_output = terraform_wrapper.plan(component)

                # Generate and display the plan summary regardless of verbose mode
                summary = summarize_terraform_plan(plan_output)
                if summary:
                    rprint("\n[bold]Plan Summary:[/bold]")
                    rprint(summary)

                if verbose:
                    rprint("\nDetailed Terraform Plan:")
                    rprint(plan_output)

                # Skip confirmation if force flag is set
                if not force and not typer.confirm(
                    "Do you want to apply these changes?", default=False
                ):
                    logger.info("User declined to apply changes")
                    TerraformComponentManager.cleanup_component(component)
                    rprint("[bold red]Terraform changes not applied.[/bold red]")
                    return

                # Apply the changes
                logger.debug("Applying terraform changes")
                with Live(Spinner("dots"), refresh_per_second=10) as live:
                    live.update("[yellow]Applying Terraform changes...[/yellow]")
                    terraform_wrapper.apply(component)
                rprint("[bold green]Changes applied successfully![/bold green]")
                break  # Success, exit the loop

            except Exception as e:
                error_output = str(e)
                log_terraform_error(error_output, session_id)

                if not self_healing or attempt >= max_attempts:
                    if not keep_on_failure:
                        TerraformComponentManager.cleanup_component(component)
                    rprint(f"An error occurred: {error_output}")
                    if not self_healing:
                        raise
                    break

                # Try to fix the error with self-healing
                logger.info(
                    f"Attempting self-healing (attempt {attempt}/{max_attempts})"
                )
                rprint(
                    f"\n[yellow]Attempting to fix Terraform errors (attempt {attempt}/{max_attempts})...[/yellow]"
                )

                with Live(
                    Spinner("dots", text="Fixing Terraform code..."),
                    refresh_per_second=10,
                ):
                    response = fix_terraform(
                        prompt,
                        terraform_code,
                        tfvars_code,
                        error_output,
                        model=model,
                        session_id=session_id,
                    )
                    if not response:
                        raise Exception("Failed to fix Terraform code")

                    terraform_code = extract_code_blocks(response, title="terraform")[0]
                    tfvars_code = next(
                        iter(extract_code_blocks(response, title="module.tfvars")), ""
                    )
                    _ = next(iter(extract_code_blocks(response, title="remarks")), "")

                    # Update component with fixed code
                    component.terraform_code = terraform_code
                    component.tfvars_code = tfvars_code

        except Exception:
            if not keep_on_failure:
                TerraformComponentManager.cleanup_component(component)
            raise

        attempt += 1

    if attempt > max_attempts and self_healing:
        rprint(
            "[bold red]Maximum self-healing attempts reached. Could not fix the errors.[/bold red]"
        )


def _validate_component_and_project(
    component_name: Optional[str] = None,
) -> tuple[list[str], Optional[str]]:
    """Validate project initialization and component existence."""
    if not TerraformComponentManager.ensure_project_initialized(WORKDIR):
        logger.error("Project not initialized")
        rprint("Project is not initialized. Run `infrabot init` first")
        return [], None

    if component_name:
        temp_component = TerraformComponent(
            name=component_name, terraform_code="", workdir=WORKDIR
        )
        if not TerraformComponentManager.component_exists(temp_component):
            logger.error(f"Component not found: {component_name}")
            rprint(f"[bold red]Component '{component_name}' not found![/bold red]")
            return [], None

    # Get list of component files
    components = TerraformComponentManager.list_components(WORKDIR)
    return components, os.path.join(
        WORKDIR, f"{component_name}.tf"
    ) if component_name else None


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
    # component_name: Optional[str] = typer.Option(
    #     None,
    #     "--name",
    #     "-n",
    #     help="Name of the component to destroy infrastructure for",
    # ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force destruction without confirmation"
    ),
):
    """Destroy all cloud infrastructure while keeping configurations."""
    logger.debug("Destroying component infrastructure")

    components = TerraformComponentManager.list_components(WORKDIR)

    if not components:
        rprint("No components found to destroy.")
        return

    # Create component object if name is specified
    # component = None
    # if component_name:
    #     component = TerraformComponent(
    #         name=component_name, terraform_code="", workdir=WORKDIR
    #     )
    # if not TerraformComponentManager.component_exists(component):
    #     rprint(f"[bold red]Component '{component_name}' not found![/bold red]")
    #     return

    # Confirm destruction unless force flag is used
    if not _confirm_action(
        "destroy",
        # component_name,
        None,
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
            # result = terraform_wrapper.destroy(component)
            result = terraform_wrapper.destroy(None)
        logger.debug("result from terraform:", result)
        # if component_name:
        #     rprint(
        #         f"[bold green]Infrastructure for component '{component_name}' has been successfully destroyed![/bold green]"
        #     )
        # else:
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
    # component_name: Optional[str] = typer.Option(
    #     None,
    #     "--name",
    #     "-n",
    #     help="Name of the component configuration to delete",
    # ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
):
    """Delete all component configurations."""
    logger.debug("Deleting component configuration")

    components = TerraformComponentManager.list_components(WORKDIR)

    if not components:
        rprint("No components found to delete.")
        return

    # Create component object if name is specified
    # component = None
    # if component_name:
    #     component = TerraformComponent(
    #         name=component_name, terraform_code="", workdir=WORKDIR
    #     )
    #     if not TerraformComponentManager.component_exists(component):
    #         rprint(f"[bold red]Component '{component_name}' not found![/bold red]")
    #         return

    # Confirm deletion unless force flag is used
    if not _confirm_action(
        "delete",
        # component_name,
        None,
        force,
        "This action will remove resources and their corresponding configuration.",
    ):
        return

    try:
        # Run terraform destroy for the specific component
        terraform_wrapper = TerraformWrapper(WORKDIR)
        with Live(
            Spinner("dots", text="Destroying infrastructure..."), refresh_per_second=10
        ):
            # terraform_wrapper.destroy(component)
            terraform_wrapper.destroy(None)

        # Delete the component files
        # if component_name:
        #     TerraformComponentManager.cleanup_component(component)
        #     rprint(
        #         f"[bold green]Component '{component_name}' and its infrastructure have been successfully deleted![/bold green]"
        #     )
        # else:
        # Delete all components
        for comp_name in components:
            comp = TerraformComponent(
                name=comp_name, terraform_code="", workdir=WORKDIR
            )
            TerraformComponentManager.cleanup_component(comp)
        rprint(
            "[bold green]All component configurations have been deleted![/bold green]"
        )

    except Exception as e:
        logger.error(f"Error deleting component configuration: {str(e)}")
        rprint(
            f"[bold red]An error occurred while deleting the configuration: {str(e)}[/bold red]"
        )


# @component_app.command("edit")
# def edit_component(
#     component_name: str = typer.Argument(..., help="Name of the component to edit"),
# ):
#     """Edit a component."""
#     logger.debug(f"Editing component: {component_name}")
#     rprint(f"[bold red]Component '{component_name}' edited successfully![/bold red]")


# @app.command(name="chat")
# def chat(
#     component_name: Optional[str] = typer.Argument(
#         ..., help="Name of the component to chat about"
#     ),
# ):
#     """Chat with your cloud using InfraBot."""
#     logger.debug(f"Chatting about component: {component_name}")
#     rprint(
#         f"[bold red]Component '{component_name}' chatted with successfully![/bold red]"
#     )


@app.command("version")
def version():
    """Display the version of InfraBot."""
    rprint(f"InfraBot version: {__version__}")


if __name__ == "__main__":
    # Initialize logging with debug mode set to True
    setup_logging(debug_mode=True)
    logger.debug("Starting infrabot CLI")
    app()
