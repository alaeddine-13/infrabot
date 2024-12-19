"""Module for generating Terraform configurations using AI."""
import logging
from typing import Optional
from easycloud.ai.config import get_openai_client, OPENAI_MODEL_CONFIG, TERRAFORM_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def gen_terraform(request: str) -> Optional[str]:
    """
    Generate Terraform configuration based on a natural language request.
    
    Args:
        request: Natural language description of the desired infrastructure
        
    Returns:
        Generated Terraform configuration as a string, or None if generation fails
        
    Raises:
        Exception: If there's an error communicating with the OpenAI API
    """
    try:
        client = get_openai_client()
        config = OPENAI_MODEL_CONFIG["terraform"]
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": TERRAFORM_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": request,
                }
            ],
            model=config["model"],
            temperature=config["temperature"],
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to generate Terraform configuration: {str(e)}", exc_info=True)
        return None


if __name__ == "__main__":
    print(gen_terraform("create an S3 bucket that allows public upload of images"))
