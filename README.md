# Custom-build Django application for We All Code

We, the community and staff, have been building a custom Django application to handle out many parts of our organization.

## Initial Setup

1. Fork and clone this repository locally.
2. Download and install [OrbStack][orbstack] for Mac/Linux or [Docker for Windows][docker-windows].
3. Copy the `.env.sample` file to `.env`.

   ```sh
   cp .env.sample .env
   ```

4. Run the following to get a random Django secret key.

   ```sh
   python -c "import secrets; print(secrets.token_urlsafe())"
   ```

5. Enter the output inside the `.env` file for `SECRET_KEY`. Be sure to include the double quotes (`"`) around the key. It'll look like the following `SECRET_KEY="<unique-key-here>"`.
6. Navigate into the project directory via terminal and run `docker compose up --build`
7. Load up your browser and go to http://127.0.0.1:8000.
8. When you are done, you can stop the project via `ctrl+c`

### Debugging Accounts

#### Admin

```txt
username: admin@sink.sendgrid.net
password: admin
```

#### Mentor

```txt
username: mentor@sink.sendgrid.net
password: mentor
```

#### Guardian

```txt
username: guardian@sink.sendgrid.net
password: guardian
```

## Continual work

After the initial project setup, you will only need to run `docker compose up --build`.

## Useful Information

### Set up main repository as `upstream`

To setup the main respository as `upstream`, you can add a new remote called `upstream`.

```console
git remote add upstream https://github.com/WeAllCode/website.git
```

### Update local code from `upstream`

To grab the latest code from the main repo (named `upstream`), run the following.

```console
git fetch upstream --prune
git checkout main
git merge upstream/main main
```

### Creating a new branch

Create a new branch based off of `upstream`'s `main` branch.

```console
git fetch upstream --prune
git checkout -b feature/a-good-name upstream/main
git push -u origin feature/a-good-name
```

### Pull Request

Pull requests are always welcome. Make sure your pull request does one task only. That is, if it's fixing a bug, the pull request fixes only that bug. If you're adding a feature, make sure the pull request adds that one feature, not multiple at once.

Follow the "Creating a new branch" step above. Be sure to always push to your `origin` remote, not `upstream`.

### Running commands on the docker container

- Running a command on a Docker app in a new container.

```console
docker compose run --rm app <command>
```

Examples:

```console
docker compose run --rm app /bin/bash
docker compose run --rm app uv lock
docker compose run --rm app python manage.py makemigrations
docker compose run --rm app python manage.py migrate
```

- Cleaning up the docker containers:

```console
docker kill $(docker ps -q); docker compose rm -f; docker volume rm $(docker volume ls -qf dangling=true);
```

- Rebuild docker containers after major changes:

```console
docker compose build
```

[orbstack]: https://orbstack.dev/
[docker-mac]: https://www.docker.com/docker-mac
[docker-windows]: https://www.docker.com/docker-windows
[docker-toolbox]: https://www.docker.com/products/docker-toolbox
[localhost]: http://localhost/
