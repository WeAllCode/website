# Technology Stack

## Framework & Language

- **Django 5.2** - Python web framework
- **Python 3.11.9** - Programming language
- **PostgreSQL 16** - Primary database

## Development Environment

- **Docker & Docker Compose** - Containerized development
- **uv** - Python dependency management and package installer
- **Gunicorn** - WSGI HTTP Server for production

## Key Dependencies

- **django-allauth** - Authentication with social login (Facebook, Google)
- **django-storages** - AWS S3 integration for static/media files
- **boto3** - AWS SDK for Python
- **django-anymail** - Email backend (SendGrid integration)
- **sentry-sdk** - Error tracking and monitoring
- **django-debug-toolbar** - Development debugging
- **Pillow** - Image processing
- **psycopg** - PostgreSQL adapter

## Code Quality Tools

- **Black** - Code formatter (line length: 79)
- **isort** - Import sorting with Black profile
- **django-nose** - Test runner

## Common Commands

### Development Setup

```bash
# Initial setup
cp .env.sample .env
# Add SECRET_KEY to .env file
docker compose up --build
```

### Daily Development

```bash
# Start development server
docker compose up --build

# Run commands in container
docker compose run --rm app <command>
docker compose run --rm app /bin/bash
docker compose run --rm app python manage.py makemigrations
docker compose run --rm app python manage.py migrate
```

### Database Operations

```bash
# Run migrations
invoke migrate
# Load development fixtures
invoke load_fixtures
```

### Testing

```bash
# Run all tests
invoke test
# Run specific app tests
invoke test <app_name>
```

### Production Tasks

```bash
# Full release process (static files, migrations, fixtures)
invoke release
# Start production server
invoke start
```

### Docker Maintenance

```bash
# Clean up containers
docker kill $(docker ps -q); docker compose rm -f; docker volume rm $(docker volume ls -qf dangling=true)
# Rebuild after major changes
docker compose build
```

## Environment Configuration

- Uses `django-environ` for environment variable management
- `.env` file for local development settings
- Heroku-ready with `django-heroku` integration
- AWS S3 for production static/media files
