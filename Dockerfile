FROM python:3.11.9

ARG DJANGO_ENV

ENV DJANGO_ENV=${DJANGO_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

# Install uv
RUN pip install uv

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY uv.lock pyproject.toml .python-version /app/

# Project initialization:
RUN uv sync --frozen

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Creating folders, and files for a project:
COPY . /app
