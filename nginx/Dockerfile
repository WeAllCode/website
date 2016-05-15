FROM nginx:1.9

MAINTAINER CoderDojoChi

ENV DIR_BUILD /build
ENV DIR_SRC /src

RUN mkdir -p $DIR_BUILD
RUN mkdir -p $DIR_SRC

WORKDIR $DIR_SRC

COPY nginx.conf /etc/nginx/nginx.conf
