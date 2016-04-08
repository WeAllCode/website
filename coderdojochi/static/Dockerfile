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

COPY package.json $DIR_BUILD/package.json
RUN npm install --prefix $DIR_BUILD

COPY . $DIR_BUILD

RUN $DIR_BUILD/node_modules/.bin/gulp --gulpfile $DIR_BUILD/gulpfile.js build

# COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/mysite_nginx.conf /etc/nginx/sites-enabled/mysite_nginx.conf
