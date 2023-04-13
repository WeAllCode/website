import environ
from invoke import task

env = environ.Env()


@task
def release(ctx):
    collect_static(ctx)
    migrate(ctx)
    load_fixtures(ctx)


@task(help={"port": "Port to use when serving traffic. Defaults to $PORT."})
def start(ctx, port=env.int("PORT", default=8000)):
    ctx.run(
        f"gunicorn coderdojochi.wsgi -w 2 -b 0.0.0.0:{port} --reload"
        " --log-file -"
    )


@task
def migrate(ctx):
    ctx.run("python3 manage.py migrate")


@task
def load_fixtures(ctx):
    if env.bool("ENABLE_DEV_FIXTURES", default=False):
        ctx.run("python3 manage.py loaddata fixtures/*.json")


@task
def collect_static(ctx):
    if not env.bool("DEBUG", default=False):
        ctx.run("python3 manage.py collectstatic --no-input")


@task(help={"app": "Specific app to run tests on. Defaults to all apps."})
def test(ctx, app=""):
    ctx.run(f"python3 manage.py test {app}")
