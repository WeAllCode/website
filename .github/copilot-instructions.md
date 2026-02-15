# WeAllCode Website - Django Application

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

WeAllCode is a Django web application for a nonprofit coding education organization that provides free educational resources and hands-on classes for children aged 7-17. The application manages class scheduling, user authentication, donations, and organizational content.

## Working Effectively

### Environment Setup & Build Process
**IMPORTANT**: Follow these exact steps to set up a working development environment:

1. **Copy environment configuration**:
   ```bash
   cp .env.sample .env
   ```

2. **Generate SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe())"
   ```
   Then update `.env` file with: `SECRET_KEY="<generated-key>"`

3. **Install uv package manager**:
   ```bash
   pip install uv
   ```

4. **Install Python 3.11 (required version)**:
   ```bash
   uv python install 3.11
   ```

5. **Install dependencies** - takes ~2.5 minutes. NEVER CANCEL:
   ```bash
   uv sync
   ```
   Set timeout to 5+ minutes.

6. **Setup PostgreSQL database**:
   ```bash
   sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib
   sudo systemctl start postgresql && sudo systemctl enable postgresql
   sudo -u postgres createdb weallcode_local
   sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
   ```

7. **Update .env for local database**:
   ```
   DB_HOST=localhost
   DB_NAME=weallcode_local
   DB_USER=postgres
   DB_PASSWORD=postgres
   ```

8. **Create environment setup script** (required due to compatibility issues):
   ```bash
   cat > setup_env.sh << 'EOF'
   #!/bin/bash
   set -a
   source .env
   set +a
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
   source .venv/bin/activate
   exec "$@"
   EOF
   chmod +x setup_env.sh
   ```

9. **Verify Django setup**:
   ```bash
   ./setup_env.sh python manage.py check
   ```

10. **Run database migrations** - takes ~4 seconds:
    ```bash
    ./setup_env.sh python manage.py migrate
    ```

11. **Load development fixtures** - takes ~1.5 seconds:
    ```bash
    ./setup_env.sh python manage.py loaddata fixtures/*.json
    ```

### Docker Setup (Alternative - Has SSL Issues)
**WARNING**: Docker build currently fails due to SSL certificate issues with PyPI in sandboxed environments.

```bash
# This fails due to SSL issues - documented for future reference
docker compose up --build  # FAILS: SSL certificate verification
```

Use the local Python setup above instead.

## Running the Application

### Development Server
```bash
./setup_env.sh python manage.py runserver 0.0.0.0:8000
```
- Access at: http://localhost:8000
- **ALWAYS** use the `setup_env.sh` wrapper script - direct Django commands will fail due to missing environment variables

### Production-like Server (using invoke tasks)
```bash
./setup_env.sh invoke start  # Uses gunicorn
```

### Common Invoke Tasks
```bash
./setup_env.sh invoke --list                    # List all available tasks
./setup_env.sh invoke migrate                   # Run migrations  
./setup_env.sh invoke load-fixtures             # Load fixtures
./setup_env.sh invoke collect-static            # Collect static files
./setup_env.sh invoke release                   # Full release process (migrate + fixtures + static)
```

## Testing

### Unit Tests
**NOTE**: Unit tests currently have issues with debug toolbar and missing dependencies:
```bash
./setup_env.sh python manage.py test --debug-mode
# Known issues: debug toolbar conflicts, missing pytz dependency
```

### Linting - takes ~0.04 seconds:
```bash
./setup_env.sh ruff check .                     # Check for style issues
./setup_env.sh ruff check . --fix               # Auto-fix issues
./setup_env.sh ruff format .                    # Format code
```

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit run --all-files
```

### End-to-End Tests (Cypress)
Located in `/test` directory with Node.js package:
```bash
cd test
npm install                                     # Install Cypress dependencies
npm run test                                    # Run headless tests
npm start                                       # Open Cypress GUI
```
Requires Node.js 18.15.0+ as specified in test/package.json.

## Development Accounts

The application includes test accounts loaded via fixtures:

- **Admin**: `admin@sink.sendgrid.net` / `admin`
- **Mentor**: `mentor@sink.sendgrid.net` / `mentor`  
- **Guardian**: `guardian@sink.sendgrid.net` / `guardian`

**NOTE**: These accounts may not work in development fixtures - create new accounts via the signup flow.

## Known Issues & Workarounds

### Storage Backend Compatibility
The application has a temporary fix for django-storages compatibility:
- `SpooledTemporaryFile` import is disabled in `coderdojochi/settings.py`
- This affects S3 storage in production but not local development

### Docker SSL Issues
Docker builds fail in sandboxed environments due to SSL certificate verification:
```
Error: certificate verify failed: self-signed certificate in certificate chain
```
Use local Python setup instead.

### Debug Toolbar
Causes test failures - configure `DEBUG_TOOLBAR_CONFIG['IS_RUNNING_TESTS'] = False` if needed.

## Validation

**ALWAYS** validate changes by:
1. Running `./setup_env.sh python manage.py check`
2. Starting the development server successfully
3. Accessing http://localhost:8000 and verifying the homepage loads
4. Running linting: `./setup_env.sh ruff check .`
5. Testing login functionality at `/account/login/`

## Key Project Structure

```
/
├── .env                     # Environment configuration (create from .env.sample)
├── manage.py               # Django management script  
├── setup_env.sh           # Environment wrapper script (create this)
├── pyproject.toml         # Python dependencies
├── tasks.py               # Invoke task definitions
├── docker-compose.yml     # Docker setup (has SSL issues)
├── coderdojochi/          # Main Django app
│   ├── settings.py        # Django settings
│   ├── urls.py           # URL routing
│   └── migrations/       # Database migrations
├── weallcode/            # Secondary Django app
├── accounts/             # User account management
├── fixtures/             # Development data
└── test/                 # Cypress E2E tests
    └── package.json      # Node.js dependencies
```

## Always Use These Commands

**CRITICAL**: Always prefix Django commands with `./setup_env.sh` or they will fail:

✅ **CORRECT**:
```bash
./setup_env.sh python manage.py migrate
./setup_env.sh python manage.py runserver
./setup_env.sh invoke start
```

❌ **INCORRECT** (will fail):
```bash
python manage.py migrate                        # Missing environment variables
docker compose up --build                       # SSL certificate issues
```

## Time Expectations

Set appropriate timeouts for these operations:
- **uv sync**: ~2.5 minutes (set 5+ minute timeout)
- **Database migrations**: ~4 seconds  
- **Loading fixtures**: ~1.5 seconds
- **Ruff linting**: ~0.04 seconds
- **Django server startup**: ~2 seconds
- **Django check**: ~1 second

**NEVER CANCEL** long-running operations like `uv sync` - they need time to complete.

Fixes #1519.