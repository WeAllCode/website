#!/usr/bin/env bash

service memcached start

python manage.py collectstatic --clear --noinput

python manage.py migrate

if [[ "$DEBUG" = "True" ]]; then
    python manage.py loaddata fixtures/*.json
fi

gunicorn --config gunicorn.conf.py --log-config logging.conf coderdojochi.wsgi --reload
