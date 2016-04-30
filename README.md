
## Setup

### OSX

1. Install `git` and [brew](http://brew.sh/)
1. `brew tap caskroom/cask`
1. `brew cask install virtualbox`
1. `brew install docker docker-machine docker-compose`
1. `git clone https://github.com/USERNAME/coderdojochi.git`
1. `git remote add upstream https://github.com/CoderDojoChi/coderdojochi.git`
1. `git remote set-url --push upstream none`
1. `git fetch upstream`
1. `git checkout feature/docker`
1. `./resources/scripts/up -d`


