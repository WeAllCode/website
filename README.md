
## Setup

### First Time

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

### Following times

1. `docker-machine start coderdojochi`
1. `eval "$(docker-machine env coderdojochi)"`
1. `docker-compose up`
1. To get the URL for your local instance: `docker-machine ip coderdojochi`

### Fetch latest code from CoderDojoChi repository
1. `git fetch upstream`
1. `git checkout develop`
1. `git merge upstream/develop`

### Misc commands
1. Rebuild docker container from scratch: `docker kill $(docker ps -q); docker-compose rm -f; docker-compose build && docker-compose up`
1. Run Django management commands: `docker-compose run --rm app python manage.py <command>`
1. Make migrations: `docker-compose run --rm app python manage.py makemigrations`
1. Run migrations: `docker-compose run --rm app python manage.py migrate coderdojochi`
