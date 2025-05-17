#!/bin/bash

# Configure AWS CLI from environment variables
aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
aws configure set region ${AWS_REGION:-us-east-1}

# Start supervisord
exec /usr/bin/supervisord -c /app/supervisord.conf
