FROM nginx:1.9

MAINTAINER CoderDojoChi

RUN apt-get update \
  && apt-get install -y curl

RUN curl -sL https://deb.nodesource.com/setup_5.x | bash -
RUN apt-get install -y nodejs

ENV DIR_BUILD /build
ENV DIR_SRC /src

RUN mkdir -p $DIR_BUILD
RUN mkdir -p $DIR_SRC

WORKDIR $DIR_SRC

COPY package.json $DIR_SRC/package.json
RUN npm install

COPY . $DIR_SRC

RUN $DIR_SRC/node_modules/.bin/gulp --gulpfile $DIR_SRC/gulpfile.js build

COPY nginx/nginx.conf /etc/nginx/nginx.conf
