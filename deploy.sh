#!/usr/bin/env bash

python manage.py collectstatic --noinput

while ! timeout 1 bash -c "echo > /dev/tcp/$DB_PORT_5432_TCP_ADDR/$DB_PORT_5432_TCP_PORT"; do sleep 10; done

python manage.py migrate
python manage.py loaddata \
    /fixtures/coderdojochi.json \
    /fixtures/sites.json \
    /fixtures/socialaccount.json

gunicorn --config $DIR_BUILD/gunicorn.conf.py coderdojochi.wsgi
