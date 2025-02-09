"""Module for handling chat functionality with LLM."""

import os
from typing import Optional, List, Dict
from infrabot.ai.completion import completion
from rich import print as rprint
from infrabot.ai.config import MODEL_CONFIG

default_model = MODEL_CONFIG["chat"]["model"]


class ChatSession:
    def __init__(self, workdir: str = ".infrabot/default", model: str = default_model):
        self.workdir = workdir
        self.model = model
        self.conversation_history: List[Dict] = []
        self.system_prompt = """You are an AI assistant specialized in cloud infrastructure and Terraform.
        Help users understand and work with their infrastructure components by providing clear, accurate information
        based on their Terraform configurations."""

    def _load_component_context(self, component_name: Optional[str] = None) -> str:
        """Load the Terraform configuration for the specified component or all components."""
        context = ""
        if component_name:
            tf_file = os.path.join(self.workdir, f"{component_name}.tf")
            if os.path.exists(tf_file):
                with open(tf_file, "r") as f:
                    context = f.read()
        else:
            # Load all .tf files in the workdir
            for file in os.listdir(self.workdir):
                if file.endswith(".tf"):
                    with open(os.path.join(self.workdir, file), "r") as f:
                        context += f"\n# File: {file}\n{f.read()}\n"
        return context

    def start_chat(self, component_name: Optional[str] = None):
        """Start an interactive chat session."""
        context = self._load_component_context(component_name)
        if not context:
            if component_name:
                rprint(
                    f"[bold red]No Terraform configuration found for component '{component_name}'[/bold red]"
                )
                return
            else:
                rprint(
                    "[bold yellow]No Terraform configurations found in the project[/bold yellow]"
                )
                return

        # Initialize conversation with system message and context
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "system",
                "content": f"Here is the Terraform configuration context:\n{context}",
            },
        ]

        rprint(
            "[bold green]Chat session started. Type 'exit' or 'quit' to end the session.[/bold green]"
        )

        while True:
            try:
                user_input = input("\n[You]: ")
                if user_input.lower() in ["exit", "quit"]:
                    rprint("[bold green]Chat session ended.[/bold green]")
                    break

                # Add user message to history
                self.conversation_history.append(
                    {"role": "user", "content": user_input}
                )

                # Get AI response
                response = self._get_ai_response()
                rprint(f"\n[Assistant]: {response}")

                # Add assistant response to history
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )

            except KeyboardInterrupt:
                rprint("\n[bold green]Chat session ended.[/bold green]")
                break
            except Exception as e:
                rprint(f"[bold red]An error occurred: {e}[/bold red]")
                break

    def _get_ai_response(self) -> str:
        """Get response from the AI model using LiteLLM."""
        try:
            response = completion(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to get AI response: {str(e)}")
