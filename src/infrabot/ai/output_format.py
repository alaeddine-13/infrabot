"""Module for formatting Terraform outputs using AI."""

from typing import Dict, Any
import logging
from infrabot.ai.config import (
    get_openai_client,
    MODEL_CONFIG,
    OUTPUT_FORMAT_SYSTEM_PROMPT,
    OUTPUT_FORMAT_USER_PROMPT,
)

logger = logging.getLogger(__name__)


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

    try:
        response = client.chat.completions.create(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            messages=[
                {"role": "system", "content": OUTPUT_FORMAT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": OUTPUT_FORMAT_USER_PROMPT.format(outputs=outputs),
                },
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to format outputs: {str(e)}", exc_info=True)
        # Fallback to simple formatting if LLM call fails
        formatted = "# Terraform Outputs\n\n"
        for key, value in outputs.items():
            formatted += f"## {key}\n```\n{value}\n```\n\n"
        return formatted
