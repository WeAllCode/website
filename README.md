
## Setup

1. `./resources/scripts/init` to setup the docker machine the site container will run on. This should only need to be run the very first time.
1. `./resources/scripts/build` to build the site's docker container.
1. `./resources/scripts/makemigrations` to ensure migrations are up to date.
1. `./resources/scripts/migrate` to migrate the db.
1. `./resources/scripts/load_fixtures` to load test data.
1. `./resources/scripts/ip` to get the IP address to access at, served off port 80.
1. `./resources/scripts/serve` to serve the site.
