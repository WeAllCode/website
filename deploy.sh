#!/usr/bin/env bash

service memcached start

python manage.py collectstatic --noinput

while ! timeout 1 bash -c "echo > /dev/tcp/$POSTGRES_HOST/$POSTGRES_PORT"; do sleep 2; done

python manage.py migrate
python manage.py loaddata fixtures/*.json

gunicorn --config $DIR_BUILD/gunicorn.conf.py coderdojochi.wsgi --reload
