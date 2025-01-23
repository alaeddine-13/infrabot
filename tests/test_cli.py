"""Tests for the CLI commands."""

import os
import shutil
import time
import pytest
from typer.testing import CliRunner
from skybot.cli import app
import subprocess
from skybot.ai import terraform_generator, summary


@pytest.fixture(scope="session")
def localstack():
    yield
    return
    """Start localstack container for testing."""
    # Start localstack
    subprocess.run(
        "docker run -d --name skybot-test-localstack "
        "-p 4566:4566 -p 4571:4571 "
        "-e SERVICES=s3 "
        "localstack/localstack:latest",
        shell=True,
        check=True,
    )

    # Wait for localstack to be ready
    max_retries = 30
    for i in range(max_retries):
        health_check = subprocess.run(
            "curl http://localhost:4566/_localstack/health",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if health_check.returncode == 0 and b'"s3": "running"' in health_check.stdout:
            break
        time.sleep(1)
    else:
        raise RuntimeError("Localstack failed to start")

    yield

    # Cleanup
    subprocess.run(
        "docker stop skybot-test-localstack && docker rm skybot-test-localstack",
        shell=True,
        check=True,
    )


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    original_dir = os.getcwd()
    os.chdir(test_dir)
    yield test_dir
    os.chdir(original_dir)
    shutil.rmtree(test_dir)


@pytest.fixture
def initialized_project(runner, temp_dir):
    """Create an initialized project for testing."""
    result = runner.invoke(app, ["init", "--local"])
    assert result.exit_code == 0
    assert os.path.exists(".skybot/default")
    return temp_dir


@pytest.fixture
def mock_gen_terraform(monkeypatch):
    """Mock the terraform generation function."""

    def mock_terraform(*args, **kwargs):
        return """
resource "aws_s3_bucket" "test" {
  bucket = "mybucket"
}
"""

    monkeypatch.setattr(terraform_generator, "gen_terraform", mock_terraform)


@pytest.fixture
def mock_summarize_plan(monkeypatch):
    """Mock the terraform plan summarization function."""

    def mock_summary(*args, **kwargs):
        return "Created S3 bucket 'mybucket'"

    monkeypatch.setattr(summary, "summarize_terraform_plan", mock_summary)


def test_version(runner):
    """Test the version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "SkyBot version:" in result.stdout


def test_init_project(runner, temp_dir):
    """Test project initialization."""
    result = runner.invoke(app, ["init", "--local"])
    assert result.exit_code == 0
    assert os.path.exists(".skybot/default")
    assert os.path.exists(".skybot/default/provider_local.tf")


def test_create_component(
    runner, initialized_project, localstack, mock_gen_terraform, mock_summarize_plan
):
    """Test component creation with AWS CLI verification."""
    # Create the component
    result = runner.invoke(
        app,
        [
            "component",
            "create",
            "--name",
            "test-bucket",
            "--prompt",
            "Create an S3 bucket called mybucket",
            "--force",
        ],
        input="y\n",  # Automatically confirm any prompts
    )
    assert result.exit_code == 0
    assert os.path.exists(".skybot/default/test-bucket.tf")

    # Verify using AWS CLI that the bucket exists
    # Note: Using --endpoint-url for localstack compatibility
    verify_cmd = "aws s3 ls --endpoint-url http://localhost:4566"
    verify_result = subprocess.run(
        verify_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert (
        verify_result.returncode == 0
    ), f"AWS CLI verification failed: {verify_result.stderr}"
    assert "mybucket" in verify_result.stdout, "bucket `mybucket` was not created"

    # Clean up
    runner.invoke(app, ["component", "destroy", "--name", "test-bucket", "--force"])


# def test_destroy_component(runner, initialized_project, localstack):
#     """Test component destruction."""
#     # First create a component
#     create_result = runner.invoke(
#         app,
#         ["component", "create", "--name", "test-bucket", "--prompt", "Create an S3 bucket called test-bucket-123", "--force"],
#     )
#     assert create_result.exit_code == 0

#     # Wait briefly for bucket creation
#     time.sleep(2)

#     # Verify bucket was created
#     verify_cmd = "aws s3 ls --endpoint-url http://localhost:4566"
#     verify_result = subprocess.run(
#         verify_cmd,
#         shell=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True
#     )
#     assert verify_result.returncode == 0, f"AWS CLI verification failed: {verify_result.stderr}"
#     assert "test-bucket-123" in verify_result.stdout, "bucket `test-bucket-123` was not created"

#     # Then destroy it
#     result = runner.invoke(
#         app,
#         ["component", "destroy", "--name", "test-bucket", "--force"]
#     )
#     assert result.exit_code == 0

#     # Wait briefly for bucket deletion
#     time.sleep(3)

#     # Verify bucket was destroyed
#     verify_result = subprocess.run(
#         verify_cmd,
#         shell=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True
#     )
#     assert verify_result.returncode == 0, f"AWS CLI verification failed: {verify_result.stderr}"
#     assert "test-bucket-123" not in verify_result.stdout, "bucket `test-bucket-123` was not destroyed"

# def test_delete_component(runner, initialized_project, localstack):
#     """Test component deletion."""
#     # First create a component
#     create_result = runner.invoke(
#         app,
#         ["component", "create", "--name", "test-bucket", "--prompt", "Create an S3 bucket called test-bucket-456", "--force"],
#         input="y\n"
#     )
#     assert create_result.exit_code == 0

#     # Wait briefly for bucket creation
#     time.sleep(2)

#     # Verify bucket was created
#     verify_cmd = "aws s3 ls --endpoint-url http://localhost:4566"
#     verify_result = subprocess.run(
#         verify_cmd,
#         shell=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True
#     )
#     assert verify_result.returncode == 0, f"AWS CLI verification failed: {verify_result.stderr}"
#     assert "test-bucket-456" in verify_result.stdout, "bucket `test-bucket-456` was not created"

#     # Then delete it
#     result = runner.invoke(
#         app,
#         ["component", "delete", "--name", "test-bucket", "--force"]
#     )
#     assert result.exit_code == 0
#     assert not os.path.exists(".skybot/default/test-bucket.tf")

#     # Verify bucket still exists (delete only removes configuration)
#     verify_result = subprocess.run(
#         verify_cmd,
#         shell=True,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True
#     )
#     assert verify_result.returncode == 0, f"AWS CLI verification failed: {verify_result.stderr}"
#     assert "test-bucket-456" in verify_result.stdout, "bucket `test-bucket-456` was unexpectedly destroyed"
