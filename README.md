# 🚀 SkyBot

![PyPI version](https://img.shields.io/pypi/v/skybot.svg)
![Documentation Status](https://readthedocs.org/projects/skybot/badge/?version=latest)

Create resource on the cloud with natural language using AI-powered Terraform generation

## 📖 Features

* Natural language-based resource creation
* Support for AWS cloud resources (S3 buckets, EC2 instances, etc.)
* Local infrastructure development using LocalStack
* Component-based infrastructure management
* Interactive chat interface for cloud resources
* Support for multiple infrastructure components

## 🛠️ Prerequisites

- Python 3.10 or higher
- Required packages (to be installed via pip):
  ```bash
  pip install skybot
  ```
- Terraform installed:
  ```bash
  brew install terraform
  ```
- AWS CLI configured:
  ```bash
  aws configure
  ```
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
skybot init [--verbose] [--local]
```

Create a new component:
```bash
skybot component create --prompt "Your infrastructure description" --name component-name [--verbose] [--force] [--model MODEL_NAME]
```

Delete a component:
```bash
skybot component delete [--name component-name] [--force]
```

Destroy component infrastructure:
```bash
skybot component destroy [--name component-name] [--force]
```

Edit a component:
```bash
skybot component edit component-name
```

Chat about your infrastructure:
```bash
skybot chat component-name
```

Check SkyBot version:
```bash
skybot version
```

## 📊 Usage Examples

1. Initialize a new project:
```bash
skybot init
```

2. Create a web server component:
```bash
skybot component create --prompt "Create an EC2 instance with nginx installed" --name web-server
```

3. Create a local S3 bucket for testing:
```bash
skybot component create --prompt "Create an S3 bucket" --name test-bucket --local
```

4. Create a database component:
```bash
skybot component create --prompt "Set up an RDS instance for PostgreSQL" --name database
```

5. Chat about your infrastructure:
```bash
skybot chat web-server
```

## 🗂️ Project Structure

When you initialize a project, SkyBot creates a `.skybot` directory with the following structure:

```
.skybot/
└── default/
    ├── backend.tf
    ├── provider.tf
    ├── component1.tf
    ├── component2.tf
    └── ...
```

Each component is stored as a separate Terraform file in the workspace directory.