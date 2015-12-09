FROM python:2.7

MAINTAINER CoderDojoChi

RUN apt-get update
RUN apt-get upgrade -y

RUN curl -sL https://deb.nodesource.com/setup_5.x | bash -
RUN apt-get install -y nodejs

ENV DIR_BUILD /build
ENV DIR_SRC /src

RUN mkdir -p $DIR_BUILD
RUN mkdir -p $DIR_SRC

WORKDIR $DIR_SRC

COPY requirements.txt $DIR_SRC/
RUN pip install -r requirements.txt
RUN pip uninstall -q -y South

COPY package.json $DIR_BUILD/
RUN npm install --prefix $DIR_BUILD

COPY manage.py $DIR_SRC/

COPY ./resources/js/.jshintrc $DIR_BUILD/
COPY ./resources/js/build $DIR_BUILD/
COPY ./resources/js/build/gulpfile.js $DIR_BUILD/

COPY coderdojochi $DIR_SRC/coderdojochi

RUN python manage.py makemigrations
RUN python manage.py migrate

COPY fixtures $DIR_BUILD/fixtures
RUN python manage.py loaddata $DIR_BUILD/fixtures/*.json
# RUN python manage.py syncdb

CMD $DIR_BUILD/node_modules/.bin/gulp --gulpfile $DIR_BUILD/gulpfile.js
