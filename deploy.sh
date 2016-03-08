#!/usr/bin/env bash

python manage.py collectstatic --noinput

while ! timeout 1 bash -c "echo > /dev/tcp/$POSTGRES_HOST/$POSTGRES_PORT"; do sleep 2; done

python manage.py migrate
python manage.py loaddata \
    /fixtures/coderdojochi.json \
    /fixtures/sites.json \
    /fixtures/socialaccount.json

python manage.py runserver 80
