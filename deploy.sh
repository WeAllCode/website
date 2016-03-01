#!/usr/bin/env bash

python manage.py collectstatic --noinput

wait_for_port_open() {
 tries=0
 until [ $tries -ge 20 ]
 do
   nc $1 -z $2 && break
   echo "Retrying to connect to $1:$2"
   tries=$[$tries+1]
   sleep 2
 done
}

wait_for_port_open "$DB_PORT_5432_TCP_ADDR" "$DB_PORT_5432_TCP_PORT"

python manage.py migrate
python manage.py loaddata \
    /fixtures/coderdojochi.json \
    /fixtures/sites.json \
    /fixtures/socialaccount.json

gunicorn --config $DIR_BUILD/gunicorn.conf.py coderdojochi.wsgi
