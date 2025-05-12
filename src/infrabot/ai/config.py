"""Configuration for AI services."""

from typing import Dict, Any
import os
from openai import OpenAI

# Check if Langfuse is enabled
LANGFUSE_ENABLED = bool(
    os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY")
)

if LANGFUSE_ENABLED:
    from langfuse.openai import OpenAI

# Model Configuration
MODEL_CONFIG: Dict[str, Dict] = {
    "summary": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 200,
    },
    "terraform": {
        "model": "gpt-4o",
        "temperature": 0.7,
    },
    "terraform_fix": {
        "model": "gpt-4o",
        "temperature": 0.5,
    },
    "chat": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000},
    "output_format": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 500,
    },
    "diagram": {
        "model": "gpt-4o",  # Using gpt-4o for better code generation
        "temperature": 0.3,
        "max_tokens": 1000,
    },
}

# Prompts
TERRAFORM_SYSTEM_PROMPT = """
You are a terraform developer, with focus on AWS cloud.
When the user requests to create an AWS resource, translate his request into production-ready terraform infrastructure as code.
Present all the resources under one file. Format the file like this:
```terraform
<your terraform code here>

# include relevant outputs that would be useful to the user
output "resource_info" {
  value = <useful resource information>
  description = "Useful information about the created resource"
}
```
Also present your remarks to the user, explicitly in this format:
```remarks
<your remarks to the user here>
```

There is a provider block in the terraform project like this:
```provider.tf
provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = null
}
```

Define the region in a .tfvars file, if the user specifies it, in the following format:
```module.tfvars
aws_region = <region>
```

Make sure that your terraform code handles all the dependencies to create the requested resource.
IMPORTANT:
- Do not generate any provider blocks in your terraform code. The provider configuration will be handled separately.
- Include relevant outputs that would be useful for the user, such as resource IDs, endpoints, or connection information.
"""

TERRAFORM_FIX_SYSTEM_PROMPT = """
You are a terraform developer expert in debugging and fixing terraform code. Your task is to analyze terraform errors and fix the code.
Given the original user request, the generated terraform code, and the error output from terraform plan/apply, you should:
1. Identify the root cause of the error
2. Fix the terraform code while maintaining the original intent
3. Ensure all dependencies and configurations are correct

Present your fixed code in this format:
```terraform
<your fixed terraform code here>

# include relevant outputs that would be useful to the user
output "resource_info" {
  value = <useful resource information>
  description = "Useful information about the created resource"
}
```
If no changes are required, rewrite the terraform code as it is.

Also present your explanation of the fixes in this format:
```remarks
<explanation of what was wrong and how you fixed it>
```

There is a provider block in the terraform project like this:
```provider.tf
provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = null
}
```

Define the region in a .tfvars file, if the user specifies it, in the following format:
```module.tfvars
aws_region = <region>
```

IMPORTANT:
- Do not generate any provider blocks in your terraform code. The provider configuration will be handled separately.
- Include relevant outputs that would be useful for the user, such as resource IDs, endpoints, or connection information.
"""

OUTPUT_FORMAT_SYSTEM_PROMPT = """You are a technical documentation expert who specializes in formatting infrastructure outputs in markdown."""

OUTPUT_FORMAT_USER_PROMPT = """Please format the following Terraform outputs into a clear, well-structured markdown document.
Include a title, descriptions for each output, and organize them in a logical way.
Here are the outputs to format:

{outputs}

Format the response as markdown with appropriate headers, lists, and code blocks where needed.
Focus on making the information clear and easy to understand for users."""

# OpenAI client singleton
_client = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        if LANGFUSE_ENABLED:
            _client = (
                OpenAI()
            )  # This will automatically use Langfuse's wrapper when enabled
        else:
            _client = OpenAI()
    return _client


def ai_format_output(outputs: Dict[str, Any]) -> str:
    """
    Format Terraform outputs into a markdown string using LLM.

    Args:
        outputs: Dictionary of Terraform outputs to format

    Returns:
        str: Formatted markdown string
    """
    if not outputs:
        return "No outputs available."

    client = get_openai_client()
    config = MODEL_CONFIG["output_format"]

    # Create a prompt that asks for markdown formatting
    prompt = f"""Please format the following Terraform outputs into a clear, well-structured markdown document.
Include a title, descriptions for each output, and organize them in a logical way.
Here are the outputs to format:

{outputs}

Format the response as markdown with appropriate headers, lists, and code blocks where needed.
Focus on making the information clear and easy to understand for users."""

    try:
        response = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical documentation expert who specializes in formatting infrastructure outputs in markdown.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception:
        # Fallback to simple formatting if LLM call fails
        formatted = "# Terraform Outputs\n\n"
        for key, value in outputs.items():
            formatted += f"## {key}\n```\n{value}\n```\n\n"
        return formatted
