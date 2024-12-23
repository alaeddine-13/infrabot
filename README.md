# 🚀 SkyBot

![PyPI version](https://img.shields.io/pypi/v/skybot.svg)
![Documentation Status](https://readthedocs.org/projects/skybot/badge/?version=latest)

Create resource on the cloud with natural language using AI-powered Terraform generation

## 📖 Features

* Natural language-based resource creation
* Support for AWS cloud resources (S3 buckets, EC2 instances, etc.)
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

## 📚 Command Structure

Initialize a new project:
```bash
skybot init [--verbose]
```

Create a new component:
```bash
skybot component create --prompt "Your infrastructure description" --name component-name
```

Delete a component:
```bash
skybot component delete --name component-name [--force]
```

Edit a component:
```bash
skybot component edit --name component-name
```

Chat about your infrastructure:
```bash
skybot chat --name component-name
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

3. Create a database component:
```bash
skybot component create --prompt "Set up an RDS instance for PostgreSQL" --name database
```

4. Chat about your infrastructure:
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