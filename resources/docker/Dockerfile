FROM python:2.7

MAINTAINER Coder Dojo Chicago

RUN apt-get update
RUN apt-get upgrade -y

RUN curl -sL https://deb.nodesource.com/setup | bash -
RUN apt-get install -y nodejs

ENV DIR_BUILD /build
RUN mkdir -p $DIR_BUILD

COPY package.json $DIR_BUILD/
RUN npm install --prefix $DIR_BUILD

COPY ./resources/js/.jshintrc $DIR_BUILD/
COPY ./resources/js/build $DIR_BUILD/
COPY ./resources/js/build/gulpfile.js $DIR_BUILD/
RUN $DIR_BUILD/node_modules/.bin/gulp --gulpfile $DIR_BUILD/gulpfile.js

CMD echo 'hello'
# CMD python manage.py runserver 0.0.0.0:8000
