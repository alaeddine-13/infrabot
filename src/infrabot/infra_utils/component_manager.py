"""Module for managing Terraform component files."""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TerraformComponent:
    """Class to hold terraform component code and metadata."""

    name: str
    terraform_code: str
    tfvars_code: Optional[str] = None
    workdir: str = ".infrabot/default"

    @classmethod
    def from_workdir(
        cls, component_name: str, workdir: str = ".infrabot/default"
    ) -> "TerraformComponent":
        """Create a TerraformComponent instance by reading files from the workdir.

        Args:
            component_name: Name of the component to read
            workdir: Directory containing the component files

        Returns:
            TerraformComponent instance

        Raises:
            FileNotFoundError: If the component's .tf file doesn't exist
        """
        tf_file_path = os.path.join(workdir, f"{component_name}.tf")
        tfvars_file_path = os.path.join(workdir, f"{component_name}.auto.tfvars")

        # Read terraform code (required)
        with open(tf_file_path, "r") as f:
            terraform_code = f.read()

        # Read tfvars code (optional)
        tfvars_code = None
        if os.path.exists(tfvars_file_path):
            with open(tfvars_file_path, "r") as f:
                tfvars_code = f.read()

        return cls(
            name=component_name,
            terraform_code=terraform_code,
            tfvars_code=tfvars_code,
            workdir=workdir,
        )

    @property
    def tf_file_path(self) -> str:
        return os.path.join(self.workdir, self.tf_file_name)

    @property
    def tf_file_name(self) -> str:
        return f"{self.name}.tf"

    @property
    def tfvars_file_name(self) -> str:
        return f"{self.name}.auto.tfvars"

    @property
    def tfvars_file_path(self) -> str:
        return os.path.join(self.workdir, self.tfvars_file_name)


class TerraformComponentManager:
    """Class to manage terraform component files."""

    @staticmethod
    def ensure_project_initialized(workdir: str) -> bool:
        """Check if the project is initialized."""
        if not os.path.exists(workdir):
            logger.error("Project not initialized")
            return False
        return True

    @staticmethod
    def component_exists(component: TerraformComponent) -> bool:
        """Check if a component exists."""
        return os.path.exists(component.tf_file_path)

    @staticmethod
    def save_component(component: TerraformComponent, overwrite: bool = False) -> bool:
        """Save terraform component files."""
        if not TerraformComponentManager.ensure_project_initialized(component.workdir):
            return False

        if TerraformComponentManager.component_exists(component) and not overwrite:
            logger.error(f"Component {component.name} already exists")
            return False

        try:
            # Save terraform file
            with open(component.tf_file_path, "w") as f:
                f.write(component.terraform_code)

            # Save tfvars file if it exists
            if component.tfvars_code:
                with open(component.tfvars_file_path, "w") as f:
                    f.write(component.tfvars_code)

            return True
        except Exception as e:
            logger.error(f"Error saving component files: {str(e)}")
            TerraformComponentManager.cleanup_component(component)
            return False

    @staticmethod
    def cleanup_component(component: TerraformComponent) -> None:
        """Remove component files."""
        for file_path in [component.tf_file_path, component.tfvars_file_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing file {file_path}: {str(e)}")

    @staticmethod
    def list_components(workdir: str = ".infrabot/default") -> list[str]:
        """List all components in the project."""
        if not TerraformComponentManager.ensure_project_initialized(workdir):
            return []

        return [
            file[:-3]
            for file in os.listdir(workdir)
            if file.endswith(".tf")
            and not file.endswith("backend.tf")
            and not file.endswith("provider.tf")
        ]
