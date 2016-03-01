FROM python:2.7

MAINTAINER CoderDojoChi

# RUN curl -sL https://deb.nodesource.com/setup_5.x | bash -
RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get autoremove -y \
  && apt-get install -y netcat

ENV DIR_BUILD /build
ENV DIR_SRC /src

RUN mkdir -p $DIR_BUILD
RUN mkdir -p $DIR_SRC

WORKDIR $DIR_SRC

COPY requirements.txt $DIR_SRC/
RUN pip install -r requirements.txt

# COPY package.json $DIR_BUILD/
# RUN npm install --prefix $DIR_BUILD

COPY manage.py $DIR_SRC/

# COPY ./resources/js/.jshintrc $DIR_BUILD/
# COPY ./resources/js/build $DIR_BUILD/
# COPY ./resources/js/build/gulpfile.js $DIR_BUILD/

COPY coderdojochi $DIR_SRC/coderdojochi

COPY fixtures /fixtures

# RUN $DIR_BUILD/node_modules/.bin/gulp --gulpfile $DIR_BUILD/gulpfile.js build

COPY ./deploy/gunicorn.conf.py $DIR_BUILD/gunicorn.conf.py
COPY ./deploy.sh $DIR_BUILD/deploy.sh

CMD $DIR_BUILD/deploy.sh
