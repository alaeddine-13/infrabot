# 🚀 InfraBot

![PyPI version](https://img.shields.io/pypi/v/infrabot.svg)
![Documentation Status](https://readthedocs.org/projects/infrabot/badge/?version=latest)
[![codecov](https://codecov.io/github/alaeddine-13/infrabot/graph/badge.svg?token=XKIQV0FNC6)](https://codecov.io/github/alaeddine-13/infrabot)

Create resource on the cloud with natural language using AI-powered Terraform generation

![Demo](assets/demo.gif)

## 📖 Features

* Natural language-based resource creation
* Support for AWS cloud resources (S3 buckets, EC2 instances, etc.)
* Local infrastructure development using LocalStack
* Component-based infrastructure management
* Interactive chat interface for cloud resources
* Support for multiple infrastructure components
* Self-healing infrastructure creation with automatic error fixing

## 🛠️ Prerequisites

- Python 3.10 or higher
- Required packages (to be installed via pip):
  ```bash
  pip install infrabot
  ```
- Terraform installed:
  ```bash
  brew install terraform
  ```
- AWS CLI configured:
  ```bash
  aws configure
  ```

P.S, make sure to configure the default region as well.
- OpenAI API key:
  ```bash
  export OPENAI_API_KEY='your_api_key_here'
  ```
- For local development:
  ```bash
  docker pull localstack/localstack
  docker run -d -p 4566:4566 localstack/localstack
  ```

## 📚 Command Structure

Initialize a new project:
```bash
infrabot init [--verbose] [--local]
```

Create a new component:
```bash
infrabot component create --prompt "Your infrastructure description" --name component-name [--verbose] [--force] [--model MODEL_NAME] [--self-healing] [--max-attempts N] [--keep-on-failure]
```

Delete all components:
```bash
infrabot component delete [--force]
```

Destroy all components infrastructure:
```bash
infrabot component destroy [--force]
```

Edit a component:
```bash
infrabot component edit component-name
```

Chat about your infrastructure:
```bash
infrabot chat component-name
```

Check InfraBot version:
```bash
infrabot version
```

## 📊 Usage Examples

1. Initialize a new project:
```bash
infrabot init
```

2. Create a web server component with self-healing:
```bash
infrabot component create --prompt "Create an EC2 instance with nginx installed" --name web-server --self-healing
```

3. Create a local S3 bucket for testing:
```bash
infrabot component create --prompt "Create an S3 bucket" --name test-bucket --local
```

4. Create a database component with custom retry attempts:
```bash
infrabot component create --prompt "Set up an RDS instance for PostgreSQL" --name database --self-healing --max-attempts 5
```

5. Chat about your infrastructure:
```bash
infrabot chat web-server
```

## 🗂️ Project Structure

When you initialize a project, InfraBot creates a `.infrabot` directory with the following structure:

```
.infrabot/
└── default/
    ├── backend.tf
    ├── provider.tf
    ├── component1.tf
    ├── component2.tf
    └── ...
```

Each component is stored as a separate Terraform file in the workspace directory.

## 🔧 Advanced Features

### Self-Healing Infrastructure Creation

InfraBot includes a self-healing feature that automatically fixes Terraform errors during resource creation:

- Enable with `--self-healing` flag
- Set maximum retry attempts with `--max-attempts N` (default: 3)
- Uses AI to analyze errors and fix configuration issues
- Maintains original infrastructure intent while resolving dependencies
- Shows detailed fix explanations for transparency
- Use `--keep-on-failure` to preserve generated Terraform files even when errors occur (useful for debugging)

Example with self-healing:
```bash
infrabot component create \
  --prompt "Create a highly available EC2 setup with auto-scaling" \
  --name ha-web \
  --self-healing \
  --max-attempts 5 \
  --keep-on-failure
```

If Terraform encounters errors during plan or apply:
1. InfraBot analyzes the error output
2. AI suggests fixes while preserving the original intent
3. Retries the operation with fixed configuration
4. Continues until success or max attempts reached
5. If `--keep-on-failure` is set, preserves the generated Terraform files for inspection even if errors occur

### Langfuse Monitoring

InfraBot supports observability and monitoring of AI interactions through Langfuse:

- Install Langfuse:
  ```bash
  pip install langfuse
  ```

- Set up Langfuse credentials:
  ```bash
  export LANGFUSE_PUBLIC_KEY='your_public_key'
  export LANGFUSE_SECRET_KEY='your_secret_key'
  ```

- All AI interactions are automatically logged to your Langfuse dashboard

### Alternative Models

InfraBot supports multiple AI models for infrastructure generation through LiteLLM integration. While OpenAI is the default provider, you can use other models by setting the appropriate API key and specifying the model:

Note: Even when using alternative models, the `OPENAI_API_KEY` environment variable is still required for certain auxiliary tasks within InfraBot.

#### Using Groq Models
```bash
export GROQ_API_KEY='your_api_key'
infrabot component create \
  --name eks-cluster-1 \
  --prompt "create an EKS cluster named MyKubernetesCluster" \
  --self-healing \
  --model "groq/deepseek-r1-distill-llama-70b"
```

#### Using Perplexity Models
```bash
export PERPLEXITY_API_KEY='your_api_key'
infrabot component create \
  --name eks-cluster-1 \
  --prompt "create an EKS cluster named MyKubernetesCluster" \
  --self-healing \
  --model "perplexity/sonar-pro"
```

> **Recommendation**: We recommend using the `perplexity/sonar-pro` model for its enhanced factuality and accuracy in infrastructure generation.

The `--model` flag allows you to specify which model to use for infrastructure generation. Make sure to set the corresponding API key as an environment variable before running the command.

InfraBot supports all models available through LiteLLM (see [LiteLLM Documentation](https://docs.litellm.ai/docs/)), including but not limited to:
- OpenAI (default), for instance: `gpt-4o`, `o3-mini`
- Groq, for instance: `groq/deepseek-r1-distill-llama-70b`
- Perplexity, for instance: `perplexity/sonar-pro`
- Anthropic, for instance: `anthropic/claude-3-5-sonnet`
- Google VertexAI
- AWS Bedrock
- Azure OpenAI
- Hugging Face
- And many more

Each provider requires its own API key to be set as an environment variable. Common examples:
- `OPENAI_API_KEY` for OpenAI models (required for all setups)
- `GROQ_API_KEY` for Groq models
- `PERPLEXITY_API_KEY` for Perplexity models
- `ANTHROPIC_API_KEY` for Anthropic models
- `AZURE_API_KEY` for Azure OpenAI models

Refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/) for the complete list of supported models and their corresponding environment variables.
