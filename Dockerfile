FROM python:2.7

MAINTAINER CoderDojoChi

RUN apt-get update \
  && apt-get install -y memcached python-memcache

ENV DIR_BUILD /build
ENV DIR_SRC /src

RUN mkdir -p $DIR_BUILD
RUN mkdir -p $DIR_SRC

WORKDIR $DIR_SRC

COPY requirements.txt $DIR_SRC/
RUN pip install -r requirements.txt

COPY manage.py $DIR_SRC/
COPY coderdojochi $DIR_SRC/coderdojochi
COPY fixtures $DIR_SRC/fixtures

COPY deploy/gunicorn.conf.py $DIR_BUILD/gunicorn.conf.py
COPY deploy/memcached.conf /etc/memcached.conf
COPY deploy.sh $DIR_SRC/deploy.sh

CMD $DIR_SRC/deploy.sh
