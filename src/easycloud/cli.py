"""Console script for easycloud."""
from rich.live import Live
from rich.spinner import Spinner
from rich import print as rprint

import easycloud

import typer
from rich.console import Console

from easycloud.ai.terraform_generator import gen_terraform
from easycloud.utils.parsing import extract_code_blocks

app = typer.Typer()
console = Console()


@app.command()
def main(
    prompt: str = typer.Option(
        ...,
        "--prompt", "-p",
        help="Input prompt for creating resources on the cloud",
        prompt="Please enter your prompt"
    )
):
    """Console script for easycloud."""
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



if __name__ == "__main__":
    app()
