#!/bin/bash
# Setup script for WeAllCode Django application

# Load environment variables from .env file
set -a
source .env
set +a

# Set any missing variables with placeholder values
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-PLACEHOLDER}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-PLACEHOLDER}
export AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME:-PLACEHOLDER}
export SENDGRID_API_KEY=${SENDGRID_API_KEY:-PLACEHOLDER}
export DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL:-hello+local@weallcode.org}
export CONTACT_EMAIL=${CONTACT_EMAIL:-hello+local@weallcode.org}
export SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-PLACEHOLDER}
export SLACK_ALERTS_CHANNEL=${SLACK_ALERTS_CHANNEL:-PLACEHOLDER}
export SENTRY_DSN=${SENTRY_DSN:-}
export RECAPTCHA_PUBLIC_KEY=${RECAPTCHA_PUBLIC_KEY:-}
export RECAPTCHA_PRIVATE_KEY=${RECAPTCHA_PRIVATE_KEY:-}
export META_SITE_PROTOCOL=${META_SITE_PROTOCOL:-http}
export META_SITE_DOMAIN=${META_SITE_DOMAIN:-localhost:8000}
export META_TWITTER_SITE=${META_TWITTER_SITE:-@weallcode}
export META_FB_APPID=${META_FB_APPID:-1454178301519376}
export DEFAULT_META_TITLE=${DEFAULT_META_TITLE:-We All Code}

# Activate virtual environment
source .venv/bin/activate

# Run the command passed as arguments
exec "$@"