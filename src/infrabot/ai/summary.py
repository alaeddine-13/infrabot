from typing import Optional
import logging
from infrabot.ai.config import get_openai_client, MODEL_CONFIG

logger = logging.getLogger(__name__)


def summarize_terraform_plan(plan_output: str) -> Optional[str]:
    """
    Generate a concise summary of a Terraform plan using GPT-3.5-turbo.

    Args:
        plan_output: The raw output from terraform plan

    Returns:
        A concise summary of the plan changes, or None if summarization fails

    Raises:
        Exception: If there's an error communicating with the OpenAI API
    """
    try:
        client = get_openai_client()
        config = MODEL_CONFIG["summary"]

        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes Terraform plans. "
                    "Provide a very concise summary focusing on the key changes: "
                    "resources being added, modified, or destroyed. "
                    "Use bullet points and keep it brief. "
                    "Describe the infrastructure as it is, without explicitly mentioning terraform.",
                },
                {
                    "role": "user",
                    "content": f"Please summarize this Terraform plan:\n\n{plan_output}",
                },
            ],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}", exc_info=True)
        return None
