"""Configuration for AI services."""
from typing import Dict
from openai import OpenAI

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
    "chat": {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 1000
    }
}

# Prompts
TERRAFORM_SYSTEM_PROMPT = """
You are a terraform developer, with focus on AWS cloud.
When the user requests to create an AWS resource, translate his request to terraform infrastructure as code.
Present all the resources under one file. Format the file like this:
```terraform
<your terraform code here>
```
Also present your remarks to the user, explicitly in this format:
```remarks
<your remarks to the user here>
```
Make sure that your terraform code handles all the dependencies to create the requested resource.
IMPORTANT: Do not generate any provider blocks in your terraform code. The provider configuration will be handled separately.
"""

# OpenAI client singleton
_client = None

def get_openai_client() -> OpenAI:
    """Get or create OpenAI client instance."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client
