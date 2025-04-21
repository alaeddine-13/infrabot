"""Service layer for infrabot providing programmatic access to functionality.

This module provides both programmatic functions and FastAPI endpoints for InfraBot.
"""

import os
import re
import logging
import uuid
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from infrabot.ai.terraform_generator import (
    gen_terraform,
    fix_terraform,
    log_terraform_error,
)
from infrabot.infra_utils.terraform import TerraformWrapper
from infrabot.infra_utils.component_manager import (
    TerraformComponentManager,
    TerraformComponent,
)
from infrabot.utils.parsing import extract_code_blocks
from infrabot.ai.summary import summarize_terraform_plan
from infrabot.utils.os import get_package_directory, copy_assets

logger = logging.getLogger("infrabot.service")
WORKDIR = ".infrabot/default"

# Create FastAPI app
app = FastAPI(
    title="InfraBot API",
    description="API for creating and managing infrastructure components with natural language",
    version="0.1.0",
)


# Pydantic models for API requests and responses
class InitProjectRequest(BaseModel):
    """Request model for initializing a project."""

    workdir: str = Field(
        default=".infrabot/default", description="Working directory for the project"
    )
    verbose: bool = Field(
        default=False, description="Show detailed initialization steps"
    )
    local: bool = Field(default=False, description="Use localstack for infrastructure")


class InitProjectResponse(BaseModel):
    """Response model for initializing a project."""

    success: bool = Field(..., description="Whether the initialization was successful")
    message: str = Field(..., description="Information message")
    workdir: str = Field(..., description="Working directory that was initialized")


class ErrorInfo(BaseModel):
    """Information about an error and its fix attempt."""

    attempt: int = Field(..., description="The attempt number")
    error: str = Field(..., description="The error message")


class ComponentCreationRequest(BaseModel):
    """Request model for creating a component."""

    prompt: str = Field(
        ..., description="Input prompt for creating resources on the cloud"
    )
    name: str = Field(default="main", description="Name of the component to create")
    model: str = Field(default="gpt-4o", description="AI model to use for generation")
    self_healing: bool = Field(
        default=False,
        description="Enable self-healing mode to automatically fix terraform errors",
    )
    max_attempts: int = Field(
        default=3, description="Maximum number of self-healing attempts"
    )
    keep_on_failure: bool = Field(
        default=False,
        description="Keep generated Terraform files even if an error occurs",
    )
    langfuse_session_id: Optional[str] = Field(
        default=None, description="Session ID for Langfuse tracking"
    )
    workdir: str = Field(
        default=".infrabot/default", description="Working directory for the project"
    )


class ComponentCreationResponse(BaseModel):
    """Response model for component creation."""

    success: bool = Field(
        ..., description="Whether the component creation was successful"
    )
    error_message: str = Field(
        default="", description="Error message if creation failed"
    )
    component_name: str = Field(..., description="Name of the component")
    terraform_code: str = Field(default="", description="Generated Terraform code")
    tfvars_code: str = Field(
        default="", description="Generated Terraform variables code"
    )
    plan_summary: str = Field(default="", description="Summary of the Terraform plan")
    outputs: Dict[str, Any] = Field(
        default_factory=dict, description="Terraform outputs"
    )
    self_healing_attempts: int = Field(
        default=0, description="Number of self-healing attempts"
    )
    fixed_errors: List[ErrorInfo] = Field(
        default_factory=list, description="Errors that were fixed during self-healing"
    )


class ComponentCreationResult:
    """Result of a component creation operation."""

    def __init__(self):
        self.success = False
        self.error_message = ""
        self.terraform_code = ""
        self.tfvars_code = ""
        self.plan_output = ""
        self.plan_summary = ""
        self.apply_output = ""
        self.outputs = {}
        self.self_healing_attempts = 0
        self.fixed_errors = []

    def to_response(self, component_name: str) -> ComponentCreationResponse:
        """Convert to API response."""
        return ComponentCreationResponse(
            success=self.success,
            error_message=self.error_message,
            component_name=component_name,
            terraform_code=self.terraform_code,
            tfvars_code=self.tfvars_code,
            plan_summary=self.plan_summary,
            outputs=self.outputs,
            self_healing_attempts=self.self_healing_attempts,
            fixed_errors=[
                ErrorInfo(attempt=e["attempt"], error=e["error"])
                for e in self.fixed_errors
            ],
        )


class ListProjectsRequest(BaseModel):
    """Request model for listing projects."""

    parent_dir: str = Field(
        default=".", description="Parent directory to scan for InfraBot projects"
    )


class ListProjectsResponse(BaseModel):
    """Response model for listing projects."""

    success: bool = Field(..., description="Whether the listing was successful")
    message: str = Field(..., description="Information message")
    projects: List[str] = Field(
        default_factory=list,
        description="List of directories containing InfraBot projects",
    )


# API endpoints
@app.post("/init", response_model=InitProjectResponse)
async def api_init_project(request: InitProjectRequest) -> InitProjectResponse:
    """Initialize a new project."""
    try:
        workdir = request.workdir or WORKDIR
        os.makedirs(workdir, exist_ok=True)

        # Copy boilerplate assets from assets/ to workdir
        package_dir = get_package_directory("infrabot")
        assets_dir = os.path.join(package_dir, "../../assets/terraform/")
        copy_assets(
            assets_dir,
            workdir,
            whitelist=[
                "provider.tf" if not request.local else "provider_local.tf",
                "backend.tf",
            ],
        )

        # Initialize Terraform in the directory
        terraform_wrapper = TerraformWrapper(workdir)
        terraform_wrapper.init(verbose=request.verbose)

        return InitProjectResponse(
            success=True, message="Project initialized successfully", workdir=workdir
        )
    except Exception as e:
        logger.error(f"Error initializing project: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Project initialization failed: {str(e)}"
        )


@app.post("/component/create", response_model=ComponentCreationResponse)
async def api_create_component(
    request: ComponentCreationRequest, background_tasks: BackgroundTasks
) -> ComponentCreationResponse:
    """Create a new infrastructure component."""
    # Call the service function
    result = create_component(
        prompt=request.prompt,
        name=request.name,
        model=request.model,
        self_healing=request.self_healing,
        max_attempts=request.max_attempts,
        keep_on_failure=request.keep_on_failure,
        langfuse_session_id=request.langfuse_session_id,
        workdir=request.workdir,
    )

    # Convert to response model
    return result.to_response(request.name)


@app.get("/projects", response_model=ListProjectsResponse)
async def api_list_projects(parent_dir: str = ".") -> ListProjectsResponse:
    """List all InfraBot projects in the specified directory."""
    try:
        request = ListProjectsRequest(parent_dir=parent_dir)
        result = list_projects(parent_dir=request.parent_dir)
        return result
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Project listing failed: {str(e)}")


def init_project(
    workdir: str = ".infrabot/default", verbose: bool = False, local: bool = False
) -> InitProjectResponse:
    """
    Initialize a new project programmatically.

    Args:
        workdir: Working directory for the project
        verbose: Show detailed initialization steps
        local: Use localstack for infrastructure

    Returns:
        InitProjectResponse: Object containing the result of initialization
    """
    request = InitProjectRequest(workdir=workdir, verbose=verbose, local=local)
    try:
        return api_init_project(request)
    except HTTPException as e:
        return InitProjectResponse(
            success=False, message=str(e.detail), workdir=workdir
        )


def create_component(
    prompt: str,
    name: str = "main",
    model: str = "gpt-4o",
    self_healing: bool = False,
    max_attempts: int = 3,
    keep_on_failure: bool = False,
    langfuse_session_id: Optional[str] = None,
    workdir: str = ".infrabot/default",
) -> ComponentCreationResult:
    """
    Create a new infrastructure component programmatically.

    Args:
        prompt: Input prompt for creating resources on the cloud
        name: Name of the component to create
        model: AI model to use for generation
        self_healing: Enable self-healing mode to automatically fix terraform errors
        max_attempts: Maximum number of self-healing attempts
        keep_on_failure: Keep generated Terraform files even if an error occurs
        langfuse_session_id: Session ID for Langfuse tracking
        workdir: Working directory for the project

    Returns:
        ComponentCreationResult: Object containing the results of the operation
    """
    result = ComponentCreationResult()

    # Validate the component name
    logger.debug(f"Creating component with name: {name}")

    if not re.match(r"^[a-zA-Z0-9-_]+$", name):
        logger.error(f"Invalid component name: {name}")
        result.error_message = (
            "Invalid component name. It should contain only A-Z, a-z, 0-9, and -."
        )
        return result

    # Check if project is initialized
    if not TerraformComponentManager.ensure_project_initialized(workdir):
        result.error_message = "Project is not initialized. Call init_project first."
        return result

    # Create component object to check existence
    component = TerraformComponent(name=name, terraform_code="", workdir=workdir)
    if TerraformComponentManager.component_exists(component):
        result.error_message = (
            f"Component '{name}' already exists. Please choose a different name."
        )
        return result

    terraform_wrapper = TerraformWrapper(workdir)
    session_id = langfuse_session_id or str(uuid.uuid4())

    # Generate terraform code
    logger.debug(f"Generating terraform code for prompt: {prompt} using model: {model}")
    response = gen_terraform(prompt, model=model, session_id=session_id)

    # In case the response is coming from a reasoning model
    # Remove content between <think></think> tags
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

    terraform_code = extract_code_blocks(response, title="terraform")[0]
    tfvars_code = next(iter(extract_code_blocks(response, title="module.tfvars")), "")
    _ = next(iter(extract_code_blocks(response, title="remarks")), "")

    # Store generated code in result
    result.terraform_code = terraform_code
    result.tfvars_code = tfvars_code

    # Update component with generated code
    component.terraform_code = terraform_code
    component.tfvars_code = tfvars_code

    attempt = 1
    while attempt <= max_attempts:
        try:
            # Save the component files
            if not TerraformComponentManager.save_component(component, overwrite=True):
                result.error_message = f"Failed to save component {name}"
                return result

            try:
                # Run Terraform plan
                logger.debug("Running terraform plan")
                plan_output = terraform_wrapper.plan(component)
                result.plan_output = plan_output

                # Generate plan summary
                summary = summarize_terraform_plan(plan_output)
                if summary:
                    result.plan_summary = summary

                # Apply the changes - skipping confirmation since we're in a service
                logger.debug("Applying terraform changes")
                apply_output = terraform_wrapper.apply(component)
                result.apply_output = apply_output

                # Get outputs
                outputs = terraform_wrapper.get_outputs()
                result.outputs = outputs

                # Mark as successful
                result.success = True
                break  # Success, exit the loop

            except Exception as e:
                error_output = str(e)
                log_terraform_error(error_output, session_id)

                if not self_healing or attempt >= max_attempts:
                    if not keep_on_failure:
                        TerraformComponentManager.cleanup_component(component)
                    result.error_message = f"An error occurred: {error_output}"
                    return result

                # Try to fix the error with self-healing
                logger.info(
                    f"Attempting self-healing (attempt {attempt}/{max_attempts})"
                )
                result.self_healing_attempts += 1

                response = fix_terraform(
                    prompt,
                    terraform_code,
                    tfvars_code,
                    error_output,
                    model=model,
                    session_id=session_id,
                )

                if not response:
                    result.error_message = "Failed to fix Terraform code"
                    return result

                terraform_code = extract_code_blocks(response, title="terraform")[0]
                tfvars_code = next(
                    iter(extract_code_blocks(response, title="module.tfvars")), ""
                )
                _ = next(iter(extract_code_blocks(response, title="remarks")), "")

                # Update component with fixed code
                component.terraform_code = terraform_code
                component.tfvars_code = tfvars_code

                # Store the fixed code in result
                result.terraform_code = terraform_code
                result.tfvars_code = tfvars_code
                result.fixed_errors.append({"attempt": attempt, "error": error_output})

        except Exception as e:
            if not keep_on_failure:
                TerraformComponentManager.cleanup_component(component)
            result.error_message = f"An unexpected error occurred: {str(e)}"
            return result

        attempt += 1

    if attempt > max_attempts and self_healing:
        result.error_message = (
            "Maximum self-healing attempts reached. Could not fix the errors."
        )

    return result


def list_projects(parent_dir: str = ".") -> ListProjectsResponse:
    """
    List all InfraBot projects in the specified directory.

    A directory is considered to contain an InfraBot project if it has a .infrabot subdirectory.

    Args:
        parent_dir: Directory to scan for InfraBot projects

    Returns:
        ListProjectsResponse: Object containing the list of project directories
    """
    projects = []

    try:
        # Ensure parent_dir exists
        if not os.path.isdir(parent_dir):
            return ListProjectsResponse(
                success=False,
                message=f"Parent directory '{parent_dir}' does not exist or is not a directory",
                projects=[],
            )

        # Function to check if a directory contains an InfraBot project
        def is_infrabot_project(directory):
            infrabot_dir = os.path.join(directory, ".infrabot")
            return os.path.isdir(infrabot_dir)

        # Check if the parent directory itself contains a project
        if is_infrabot_project(parent_dir):
            projects.append(os.path.abspath(parent_dir))

        # Scan direct children (and optionally recurse)
        for item in os.listdir(parent_dir):
            item_path = os.path.join(parent_dir, item)

            if os.path.isdir(item_path):
                # Check if this directory has an .infrabot folder
                if is_infrabot_project(item_path):
                    projects.append(os.path.abspath(item_path))

        return ListProjectsResponse(
            success=True,
            message=f"Found {len(projects)} InfraBot projects",
            projects=projects,
        )

    except Exception as e:
        logger.error(f"Error while listing projects: {str(e)}")
        return ListProjectsResponse(
            success=False, message=f"Failed to list projects: {str(e)}", projects=[]
        )
