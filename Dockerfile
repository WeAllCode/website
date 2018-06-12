FROM python:3.6

# Force stdin, stdout and stderr to be totally unbuffered.
ENV PYTHONUNBUFFERED 1

# Disable the version check
ENV PIP_DISABLE_PIP_VERSION_CHECK 1

# Install pipenv
RUN pip install pipenv

# Install Application into container
RUN set -ex && mkdir /app
WORKDIR /app

# Adding Pipfiles
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install dependencies:
RUN set -ex && pipenv install --deploy --system

COPY . /app
