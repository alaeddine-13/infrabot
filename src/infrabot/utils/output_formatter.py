"""Utilities for formatting and displaying outputs."""

import json
from rich import print as rprint
from rich.panel import Panel
from rich.text import Text


def display_terraform_outputs(outputs):
    """Display terraform outputs in a nicely formatted way.

    Args:
        outputs (dict): Dictionary of terraform outputs containing value and description
    """
    if not outputs:
        return

    rprint("\n[bold]Resource Outputs:[/bold]")
    for output_name, output_data in outputs.items():
        value = output_data.get("value")
        description = output_data.get("description", "")

        # Create a formatted panel for each output
        output_text = Text()
        if description:
            output_text.append(f"{description}\n", style="italic")

        # Format the value based on type
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2)
        else:
            value_str = str(value)

        output_text.append(value_str, style="bold green")

        rprint(
            Panel(output_text, title=f"[blue]{output_name}[/blue]", border_style="blue")
        )
