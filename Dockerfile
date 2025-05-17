FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN pip install --no-cache-dir awscli

# Install Terraform
RUN curl -fsSL https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip

# Install Node.js (LTS) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs \
    && npm install -g npm \
    && rm -rf /var/lib/apt/lists/*

# Copy webapp code
COPY webapp /app/webapp

# Set working directory to /app/webapp
WORKDIR /app/webapp

# Clean any previously copied node_modules and install fresh dependencies
RUN rm -rf node_modules && \
    npm install --legacy-peer-deps && \
    npm install esbuild --save-dev && \
    npm run build

# Optional: Remove node_modules and caches to reduce image size
# RUN rm -rf node_modules ~/.npm

# Set working directory to /app
WORKDIR /app

# Copy pyproject.toml for dependency installation
COPY pyproject.toml poetry.lock* README.md ./

# Copy application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi


# Install the project
RUN pip install --no-cache-dir "."
RUN pip install langfuse

# Make the start_server script executable
RUN chmod +x /app/scripts/start_server.sh

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GENERATE_DIAGRAM=true

# Install supervisord
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

COPY assets/supervisord.conf /app/supervisord.conf

COPY assets/terraform /usr/local/lib/python3.10/assets/terraform

# Run the application
ENTRYPOINT ["/app/scripts/start_server.sh"]
