# Custom-build Django application for CoderDojoChi

We, the community and staff, have been building a custom Django application to handle out many parts of our organization.


## Initial Setup

1. Fork and clone this repository locally.

1. Download and install Docker for [Mac][docker-mac] or [Windows][docker-windows]*.

1. Navigate into the project directory via terminal and run `docker-compose build`.

1. Once complete, run `docker-compose up -d`.

1. Load up your browser and go to [localhost]

1. To view logs, you can run `docker logs -f cdc-app`

1. When you are done, you can stop the project via `docker-compose down`

**Note:** Docker for Mac requires OSX Yosemite 10.10.3 or above. Docker for Windows requires Microsoft Windows 10 Professional or Enterprise 64-bit. For previous versions download [Docker Toolbox][docker-toolbox].

### Debugging Accounts

#### Admin
username: **admin@admin.com**  
password: **admin**

#### Guardian
username: **guardian@guardian.com**  
password: **guardian**


## Continual work

After the initial project setup, you will only need to run `docker-compose build` and `docker-compose up -d`. You can speed the set up by running the command together like so `docker-compose build && docker-compose up -d`.

## Useful Information

### Set up main repository as `upstream`

To setup the main respository as `upstream`, you can add a new remote called `upstream`.

```console
git remote add upstream https://github.com/coderdojochi/coderdojochi
```

### Update local code from `upsteam`

To grab the latest code from the main repo (named `upstream`), run the following.

```console
git fetch upstream --prune
git checkout develop
git merge upstream/develop develop
```

### Creating a new branch

Create a new branch based off of `upstream`'s `develop` branch.

```console
git fetch upsteam --prune
git checkout -b feature/a-good-name upsteam/develop
git push -u origin feature/a-good-name
```

### Pull Request

Pull requests are always welcome. Make sure your pull request does one task only. That is, if it's fixing a bug, the pull request fixes only that bug. If you're adding a feature, make sure the pull request adds that one feature, not multiple at once.

Follow the "Creating a new branch" step above. Be sure to always push to your `origin` remote, not `upstream`.


### Running commands on the docker container

#### Run Django management commands
When running any Django commands, you'll need to run them within the Docker container.

```console
docker exec -it cdc-app  --rm app python manage.py <command>
```



[docker-mac]: https://www.docker.com/docker-mac
[docker-windows]: https://www.docker.com/docker-windows
[docker-toolbox]: https://www.docker.com/products/docker-toolbox
[localhost]: http://localhost/
