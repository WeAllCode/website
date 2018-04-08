FROM python:2.7-stretch

RUN apt-get update \
  && apt-get install -y curl memcached python-memcache

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash - \
  && apt-get install -y nodejs

ENV DIR_BUILD /build
ENV DIR_SRC /src

RUN mkdir -p $DIR_BUILD \
  && mkdir -p $DIR_SRC

WORKDIR $DIR_SRC

COPY package.json $DIR_SRC/package.json
RUN npm install

COPY requirements.txt $DIR_SRC/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY gulp $DIR_SRC/gulp
COPY gulpfile.js $DIR_SRC/
COPY manage.py $DIR_SRC/
COPY coderdojochi $DIR_SRC/coderdojochi
COPY fixtures $DIR_SRC/fixtures

COPY gunicorn.conf.py $DIR_BUILD/gunicorn.conf.py
COPY logging.conf $DIR_BUILD/logging.conf
COPY memcached.conf /etc/memcached.conf
COPY deploy.sh $DIR_SRC/deploy.sh

CMD $DIR_SRC/deploy.sh
