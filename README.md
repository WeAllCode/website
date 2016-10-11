
# Setup

## First Time

1. Install `git` and [brew](http://brew.sh/)

1. `brew tap caskroom/cask`

1. `brew cask install virtualbox`

1. `brew install docker docker-machine docker-compose`

1. Fork `https://github.com/coderdojochi/coderdojochi`

1. `git clone http://github.com/USERNAME/coderdojochi`

1. `cd coderdojochi`

1. `git remote add upstream https://github.com/CoderDojoChi/coderdojochi`

1. `docker-machine create --driver virtualbox coderdojochi` (takes 1 minute)

1. `docker-machine start coderdojochi`

1. `eval "$(docker-machine env coderdojochi)"`

1. `docker-compose up` (for the first time, depending on your PC, it'll take 5-10 minutes)




## Following times

1. `docker-machine start coderdojochi`

1. `eval "$(docker-machine env coderdojochi)"`

1. `docker-compose up`

1. To get the URL for your local instance: `docker-machine ip coderdojochi`

## Fetch latest code from CoderDojoChi repository

To grab the latest code from the upstream (main) repo, do the following:
```bash
git fetch upstream && git checkout develop && git merge upstream/develop
```




## Misc commands

##### Rebuild docker container from scratch

```bash
docker kill $(docker ps -q); docker-compose rm -f; docker-compose build && docker-compose up
```

##### Run Django management commands
```bash
docker-compose run --rm app python manage.py <command>
```

##### Make migrations
```bash
docker-compose run --rm app python manage.py makemigrations
```

##### Run migrations
```bash
docker-compose run --rm app python manage.py migrate coderdojochi
```

# Getting Started
Once the app is running (you'll see `app_1 | Installed X object(s) from X fixture(s)`), load up the browser and go to [192.168.99.100](http://192.168.99.100/).

To log into the admin, click the menu item 'My Dojo'.

## Admin
username: **admin@admin.com**
password: **admin**

## Guardian
username: **guardian@guardian.com**
password: **guardian**
