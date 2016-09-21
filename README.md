
## Setup

### First Time

1. Install `git` and [brew](http://brew.sh/)
1. `brew tap caskroom/cask`
1. `brew cask install virtualbox`
1. `brew install hub docker docker-machine docker-compose`
1. `hub fork coderdojochi/coderdojochi`
1. `cd coderdojochi`
1. `docker-machine create --driver virtualbox coderdojochi` (takes 1 minute)
1. `docker-machine start coderdojochi`
1. `eval "$(docker-machine env coderdojochi)"`
1. `docker-compose up` (for the first time, depending on your PC, it'll take 5-10 minutes)

### Following times

1. `docker-machine start coderdojochi`
1. `eval "$(docker-machine env coderdojochi)"`
1. `docker-compose up`

### Misc commands
1. Run Django management commands like so... `docker-compose run app python manage.py <command>`
1. Rebuild docker container (when all else fails)... `docker kill $(docker ps -q); docker-compose rm —all -f; docker-compose build && docker-compose up`
