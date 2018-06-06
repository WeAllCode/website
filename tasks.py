from invoke import task
import os


@task
def release(ctx):
    collect_static(ctx)
    migrate(ctx)
    load_fixtures(ctx)


@task(help={"port": "Port to use when serving traffic. Defaults to $PORT."})
def start(ctx, port=os.environ.get("PORT", 8000)):
    ctx.run(f"gunicorn coderdojochi.wsgi -w 2 -b 0.0.0.0:{port} --reload --log-file -")


@task
def migrate(ctx):
    ctx.run("python manage.py migrate")


@task
def load_fixtures(ctx):
    # ctx.run("python manage.py loaddata 01-defaults")

    if os.environ.get("ENABLE_DEV_FIXTURES", False):
        ctx.run("python manage.py loaddata fixtures/*.json")


@task
def collect_static(ctx):
    ctx.run("python manage.py collectstatic --no-input")


@task(help={"app": "Specific app to run tests on. Defaults to all apps."})
def test(ctx, app=""):
    ctx.run(f"python manage.py test {app}")
    format(ctx)


@task
def format(ctx):
    ctx.run("autopep8 -iaarj4 --exclude=\"**/migrations/*\" --max-line-length=\"120\" .")
