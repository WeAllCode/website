FROM python:2
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y \
  memcached \
  python-memcache

COPY config/memcached.conf /etc/memcached.conf

RUN mkdir /src
WORKDIR /src

COPY src/requirements.txt /src/
RUN pip install -r requirements.txt

COPY src /src/


# COPY deploy.sh $DIR_SRC/deploy.sh

# CMD $DIR_SRC/deploy.sh
