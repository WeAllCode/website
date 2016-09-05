#!/usr/bin/env bash

service memcached start

./node_modules/.bin/gulp build

python manage.py collectstatic --noinput

while ! timeout 1 bash -c "echo > /dev/tcp/$POSTGRES_HOST/$POSTGRES_PORT"; do sleep 2; done

python manage.py migrate
if [[ "$DEBUG" = "True" ]]; then
    python manage.py loaddata fixtures/*.json
fi

gunicorn --config $DIR_BUILD/gunicorn.conf.py --log-config $DIR_BUILD/logging.conf coderdojochi.wsgi --reload
