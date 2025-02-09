"""Module for generating Terraform configurations using AI."""

import logging
from typing import Optional
from infrabot.ai.completion import completion
from infrabot.ai.config import (
    MODEL_CONFIG,
    TERRAFORM_SYSTEM_PROMPT,
    TERRAFORM_FIX_SYSTEM_PROMPT,
    LANGFUSE_ENABLED,
)

logger = logging.getLogger(__name__)

if LANGFUSE_ENABLED:
    from langfuse.decorators import observe, langfuse_context
    from langfuse import Langfuse

    langfuse = Langfuse()


@observe(as_type="generation") if LANGFUSE_ENABLED else lambda x: x
def gen_terraform(
    request: str, model: str = "gpt-4o", session_id: Optional[str] = None
) -> str:
    """
    Generate Terraform configuration based on a natural language request.

    Args:
        request: Natural language description of the desired infrastructure
        model: The LLM model to use (default: "gpt-4o")
        session_id: Optional session ID for Langfuse tracing

    Returns:
        Generated Terraform configuration as a string
    """
    config = MODEL_CONFIG["terraform"]

    messages = [
        {
            "role": "system",
            "content": TERRAFORM_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": request,
        },
    ]

    response = completion(
        model=model,
        messages=messages,
        temperature=config["temperature"],
    )

    if LANGFUSE_ENABLED and hasattr(response, "usage"):
        langfuse_context.update_current_trace(
            input=messages,
            metadata={"temperature": config["temperature"]},
            session_id=session_id,
            output=response.choices[0].message.content,
        )

    return response.choices[0].message.content


@observe(as_type="generation") if LANGFUSE_ENABLED else lambda x: x
def fix_terraform(
    request: str,
    current_code: str,
    tfvars_code: str,
    error_output: str,
    model: str = "gpt-4o",
    session_id: Optional[str] = None,
) -> str:
    """
    Fix Terraform configuration based on error output using predicted outputs for faster response.

    Args:
        request: Original natural language request
        current_code: Current terraform code that produced the error
        tfvars_code: Current tfvars code that produced the error
        error_output: Error output from terraform plan/apply
        model: The LLM model to use (default: "gpt-4o")
        session_id: Optional session ID for Langfuse tracing

    Returns:
        Fixed Terraform configuration as a string
    """
    config = MODEL_CONFIG["terraform_fix"]

    prompt = f"""Original request: {request}

Current terraform code:
```terraform
{current_code}
```

Current tfvars code:
```tfvars
{tfvars_code}
```

Error output:
```
{error_output}
```

Please fix the terraform code to resolve these errors."""

    messages = [
        {
            "role": "system",
            "content": TERRAFORM_FIX_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    # Only use prediction for gpt-4o and gpt-4o-mini models
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": config["temperature"],
    }

    if model in ["gpt-4o", "gpt-4o-mini"]:
        kwargs["prediction"] = {"type": "content", "content": current_code}

    response = completion(**kwargs)

    if LANGFUSE_ENABLED and hasattr(response, "usage"):
        langfuse_context.update_current_trace(
            input=messages,
            metadata={
                "temperature": config["temperature"],
                "error_output": error_output,
            },
            session_id=session_id,
            output=response.choices[0].message.content,
        )

    return response.choices[0].message.content


def log_terraform_error(error: str, session_id: Optional[str] = None) -> None:
    """
    Log a Terraform error to Langfuse.

    Args:
        error: The error message from Terraform
        session_id: Optional session ID for Langfuse tracing
    """
    if LANGFUSE_ENABLED:
        langfuse.trace(
            name="terraform-error",
            session_id=session_id,
            level="ERROR",
            status_message="Terraform operation failed",
            output=error,
            metadata={
                "error_output": error,
                "error_type": "TerraformError",
            },
        )


if __name__ == "__main__":
    print(gen_terraform("create an S3 bucket that allows public upload of images"))
