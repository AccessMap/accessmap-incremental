FROM python:3.8-buster
MAINTAINER Nick Bolten <nbolten@gmail.com>

RUN apt-get update && apt-get install -y osmium-tool osmosis

RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip install -r /app/requirements.txt
RUN pip install .

ENTRYPOINT osm_osw
