FROM python:3.13

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

# Define and activate the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Creating folders, and files for a project:
COPY . /app
