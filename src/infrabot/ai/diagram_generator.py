"""Module for generating infrastructure diagrams from Terraform files using AI."""

import logging
import os
import subprocess
import tempfile
from typing import Optional
from infrabot.ai.config import (
    MODEL_CONFIG,
    LANGFUSE_ENABLED,
)
from infrabot.ai.completion import completion
from infrabot.utils.parsing import extract_code_blocks

logger = logging.getLogger(__name__)

if LANGFUSE_ENABLED:
    from langfuse.decorators import observe, langfuse_context
    from langfuse import Langfuse

    langfuse = Langfuse()

# System prompt for diagram generation
DIAGRAM_SYSTEM_PROMPT = """You are an expert in generating infrastructure diagrams using the Python diagrams library.
Given a Terraform configuration, generate Python code that creates a visual diagram representing the infrastructure.
The diagram should:
1. Use appropriate icons from the diagrams library
2. Show relationships between resources
3. Group related resources in clusters
4. Include clear labels and descriptions
5. Use appropriate colors and styling
6. The file that you export must be called diagram.jpg, for instance follow this blueprint:

```python
from diagrams import Diagram, Cluster
from diagrams.aws.storage import S3

with Diagram("AWS S3 Bucket Setup", filename="diagram", outformat="jpg", show=False):
    s3_bucket = S3("mys3bucketproj7infrabot")
```

Do not map every terraform resource to a diagram element. Only include resources that are relevant to the diagram.

The code should be complete and ready to run, including all necessary imports."""

# User prompt template for diagram generation
DIAGRAM_USER_PROMPT = """Please generate a Python diagram code for the following Terraform configuration:

{terraform_code}

The code should use the diagrams library and create a clear visual representation of the infrastructure.
Include all necessary imports and make sure the code is complete and runnable."""


@observe(as_type="generation") if LANGFUSE_ENABLED else lambda x: x
def generate_diagram_code(terraform_code: str, session_id: Optional[str] = None) -> str:
    """
    Generate Python code for creating an infrastructure diagram using AI.

    Args:
        terraform_code: The Terraform configuration to visualize
        model: The LLM model to use (default: "gpt-4o")
        session_id: Optional session ID for Langfuse tracing

    Returns:
        str: Python code for generating the diagram
    """
    config = MODEL_CONFIG["diagram"]

    messages = [
        {"role": "system", "content": DIAGRAM_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": DIAGRAM_USER_PROMPT.format(terraform_code=terraform_code),
        },
    ]

    response = completion(
        model=config["model"],
        messages=messages,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
    )

    if LANGFUSE_ENABLED and hasattr(response, "usage"):
        langfuse_context.update_current_trace(
            input=messages,
            metadata={"temperature": config["temperature"]},
            session_id=session_id,
            output=response.choices[0].message.content,
        )

    return response.choices[0].message.content


def generate_diagram(
    terraform_code: str,
    output_path: str = "infrastructure_diagram.png",
    session_id: Optional[str] = None,
) -> str:
    """
    Generate an infrastructure diagram from Terraform code and save it to a file.

    Args:
        terraform_code: The Terraform configuration to visualize
        output_path: Path where to save the generated diagram
        session_id: Optional session ID for Langfuse tracing

    Returns:
        str: Path to the generated diagram file
    """
    # Generate the diagram code using AI
    diagram_code = generate_diagram_code(terraform_code, session_id=session_id)

    # Extract Python code blocks from the LLM output
    python_blocks = extract_code_blocks(diagram_code, "python")
    if not python_blocks:
        raise ValueError("No Python code blocks found in the generated output")

    # Use the first Python code block
    diagram_code = python_blocks[0]
    assert (
        'filename="diagram", outformat="jpg"' in diagram_code
    ), "The diagram code must contain the filename diagram.jpg"
    print(diagram_code)

    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(diagram_code.encode())
        temp_file_path = temp_file.name

    try:
        # Execute the Python code
        subprocess.run(["python", temp_file_path], check=True)

        # Move the generated diagram to the desired output path
        if os.path.exists("diagram.jpg"):
            os.rename("diagram.jpg", output_path)
        else:
            raise RuntimeError("Diagram file was not generated")

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

    return output_path
