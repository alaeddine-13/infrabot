"""Tests for the CLI commands."""

import os
import shutil
import pytest
from typer.testing import CliRunner
import subprocess

TERRAFORM_MOCK_RESPONSE = """
```terraform
resource "aws_s3_bucket" "mybucket" {
  bucket = "mybucket"

  # Enable versioning
  versioning {
    enabled = true
  }

  # Enable server-side encryption by default
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
```
```remarks
The above configuration will create an S3 bucket named "mybucket" with versioning enabled and server-side encryption using the AES256
algorithm. Ensure that the bucket name "mybucket" is unique across all existing bucket names in AWS S3, as bucket names are globally unique.
Adjust any additional settings like ACLs, policies, or lifecycle rules based on your specific needs.
```
"""


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
def initialized_project(runner, temp_dir, monkeypatch):
    """Create an initialized project for testing."""

    def mock_terraform(*args, **kwargs):
        return TERRAFORM_MOCK_RESPONSE

    def mock_summary(*args, **kwargs):
        return "Created S3 bucket 'mybucket'"

    # Use monkeypatch to replace the real function with our mock
    monkeypatch.setattr("infrabot.ai.terraform_generator.gen_terraform", mock_terraform)
    monkeypatch.setattr("infrabot.ai.summary.summarize_terraform_plan", mock_summary)

    from infrabot.cli import app

    result = runner.invoke(app, ["init", "--local"])
    assert result.exit_code == 0
    assert os.path.exists(".infrabot/default")
    return temp_dir


def test_version(runner):
    """Test the version command."""
    from infrabot.cli import app

    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "InfraBot version:" in result.stdout


def test_init_project(runner, temp_dir):
    """Test project initialization."""
    from infrabot.cli import app

    result = runner.invoke(app, ["init", "--local"])
    assert result.exit_code == 0
    assert os.path.exists(".infrabot/default")
    assert os.path.exists(".infrabot/default/provider_local.tf")


def test_create_component(runner, initialized_project, monkeypatch):
    """Test component creation with AWS CLI verification."""
    from infrabot.cli import app

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
    assert os.path.exists(".infrabot/default/test-bucket.tf")

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
#     assert not os.path.exists(".infrabot/default/test-bucket.tf")

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
