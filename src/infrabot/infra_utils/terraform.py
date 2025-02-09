import subprocess
import logging
from typing import Optional
from .component_manager import TerraformComponent

logger = logging.getLogger("infrabot.terraform")


class TerraformWrapper:
    def __init__(self, working_directory):
        self.working_directory = working_directory
        self.main_tf_file_path = f"{working_directory}/main.tf"

    def run_command(self, command, verbose=False):
        """Run a command in the subprocess and return the output and error message."""
        logger.debug(
            f"Running terraform command: {command} in directory: {self.working_directory}"
        )
        if verbose:
            pipe = None
        else:
            pipe = subprocess.PIPE
        process = subprocess.Popen(
            command,
            cwd=self.working_directory,
            stdout=pipe,
            stderr=pipe,
            shell=True,
            text=True,
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(f"Terraform command failed: {stderr}")
            raise Exception(f"Error: {stderr}")
        logger.debug(f"Terraform command completed successfully. Output: {stdout}")
        return stdout

    def init(self, verbose=False):
        """Initialize a Terraform working directory."""
        return self.run_command("terraform init", verbose=verbose)

    def plan(self, component: Optional[TerraformComponent] = None):
        """Generate and show an execution plan.

        Args:
            component: Optional TerraformComponent to plan for. If None, plans for all components.
        """
        command = "terraform plan"
        # if component:
        #     command += f" -target={component.tf_file_name}"
        #     if component.tfvars_code:
        #         command += f" -var-file={component.tfvars_file_name}"
        return self.run_command(command)

    def apply(self, component: Optional[TerraformComponent] = None, auto_approve=True):
        """Apply the changes required to reach the desired state.

        Args:
            component: Optional TerraformComponent to apply. If None, applies all components.
            auto_approve: Whether to skip interactive approval.
        """
        command = "terraform apply"
        # if component:
        #     command += f" -target={component.tf_file_name}"
        #     if component.tfvars_code:
        #         command += f" -var-file={component.tfvars_file_name}"
        if auto_approve:
            command += " -auto-approve"
        return self.run_command(command)

    def destroy(
        self, component: Optional[TerraformComponent] = None, auto_approve=True
    ):
        """Destroy all Terraform-managed infrastructure or a specific component.

        Args:
            component: Optional TerraformComponent to destroy. If None, destroys all components.
            auto_approve: Whether to skip interactive approval.
        """
        command = "terraform destroy"
        # if component:
        #     command += f" -target={component.tf_file_name}"
        #     if component.tfvars_code:
        #         command += f" -var-file={component.tfvars_file_name}"
        if auto_approve:
            command += " -auto-approve"
        return self.run_command(command)

    def _ensure_working_directory_exists(self):
        """Ensure the working directory exists before proceeding"""
        import os

        if not os.path.exists(self.working_directory):
            try:
                os.mkdir(self.working_directory)
                logger.info(f"Created working directory at {self.working_directory}")
            except Exception as e:
                raise Exception(f"Failed to create working directory: {e}")

    def save_main_tf_file(self, file_content):
        """Save the main.tf file with the given content."""
        self._ensure_working_directory_exists()
        with open(self.main_tf_file_path, "w") as f:
            f.write(file_content)
        print(f"Main TF file saved successfully at {self.main_tf_file_path}")

    def load_main_tf_file(self):
        """Load the content of the main.tf file."""
        try:
            with open(self.main_tf_file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            print("No main.tf file found in the working directory")
            return None


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as working_directory:  # Create a temporary directory using context manager
        # Initialize a TerraformWrapper object with the path to your temporary working directory
        terraform_wrapper = TerraformWrapper(working_directory)

    # Save an example main.tf file content
    import uuid

    unique_bucket_name = "my-terraform-bucket-" + str(uuid.uuid4())
    example_main_tf_file_content = """
provider "aws" {{
  region = "us-west-2"
}}

resource "aws_s3_bucket" "example" {{
  bucket = "{unique_bucket_name}"
}}
""".format(unique_bucket_name=unique_bucket_name)
    terraform_wrapper.save_main_tf_file(example_main_tf_file_content)

    try:
        # Run Terraform init, plan, apply and destroy commands
        print(terraform_wrapper.init())
        print(terraform_wrapper.plan())
        print(terraform_wrapper.apply())
        print(terraform_wrapper.destroy(component_name="aws_s3_bucket.example"))
    except Exception as e:
        print(e)
