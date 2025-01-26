"""Module for generating Terraform configurations using AI."""

import logging
from typing import Optional
from skybot.ai.completion import completion
from skybot.ai.config import MODEL_CONFIG, TERRAFORM_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def gen_terraform(request: str, model: str = "gpt-4o") -> Optional[str]:
    """
    Generate Terraform configuration based on a natural language request.

    Args:
        request: Natural language description of the desired infrastructure
        model: The LLM model to use (default: "gpt-4o")

    Returns:
        Generated Terraform configuration as a string, or None if generation fails
    """
    try:
        config = MODEL_CONFIG["terraform"]

        response = completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": TERRAFORM_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": request,
                },
            ],
            temperature=config["temperature"],
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(
            f"Failed to generate Terraform configuration: {str(e)}", exc_info=True
        )
        return None


if __name__ == "__main__":
    print(gen_terraform("create an S3 bucket that allows public upload of images"))
