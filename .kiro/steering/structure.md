# Project Structure

## Root Directory

- `manage.py` - Django management script
- `pyproject.toml` - uv dependencies and tool configuration
- `tasks.py` - Invoke task definitions for common operations
- `docker-compose.yml` - Development environment setup
- `Dockerfile` - Container configuration

## Main Applications

### `coderdojochi/` - Core Application

Primary Django app containing the main business logic:

- `models/` - Data models split by domain:

  - `user.py` - Custom user model (CDCUser) with mentor/guardian roles
  - `session.py` - Class sessions with enrollment and capacity management
  - `course.py` - Course definitions with age restrictions
  - `mentor.py`, `guardian.py`, `student.py` - User role models
  - `location.py`, `meeting.py`, `donation.py` - Supporting models

- `views/` - View logic organized by user type:

  - `guardian/` - Parent/guardian specific views
  - `mentor/` - Mentor specific views
  - `public/` - Public-facing views

- `templates/` - Django templates organized by feature
- `static/` - CSS, JavaScript, and images
- `migrations/` - Database migration files
- `emailtemplates/` - Email notification templates

### `weallcode/` - Public Website

Handles the public-facing marketing website:

- `views/` - Public pages (home, programs, team, etc.)
- `templates/weallcode/` - Public website templates
- `static/weallcode/` - Public website assets
- `models/` - Staff and board member models

### `accounts/` - Authentication

Extends django-allauth for custom authentication:

- `templates/account/` - Login, signup, and account management templates
- Custom user registration forms and social auth integration

## Supporting Directories

### `fixtures/` - Development Data

- JSON fixture files for development database seeding
- `db_views/` - SQL view definitions for reporting

### `test/` - End-to-End Testing

- Cypress test suite for browser automation
- Integration tests for key user workflows

## Configuration Patterns

### Models Organization

- Models are split into separate files by domain in `models/` directory
- All models imported in `models/__init__.py` for easy access
- Common base classes in `models/common.py`

### URL Patterns

- Main URL routing in `coderdojochi/urls.py`
- App-specific URLs in respective `urls.py` files
- Clear URL namespacing (e.g., `/classes/`, `/mentors/`, `/admin/`)

### Templates

- Base templates in each app's `templates/` directory
- Shared components in `snippets/` subdirectories
- Email templates separate from web templates

### Static Files

- App-specific static files in each app's `static/` directory
- Production uses AWS S3 via django-storages
- Development serves files locally

## Development Conventions

### Code Style

- Black formatter with 79 character line length
- isort for import organization with Django-aware sections
- Migrations excluded from formatting

### Database

- PostgreSQL for all environments
- Migrations in each app's `migrations/` directory
- Custom user model extends AbstractUser

### Environment Configuration

- `.env` file for local development
- Environment-specific settings in `settings.py`
- Heroku deployment ready with django-heroku
