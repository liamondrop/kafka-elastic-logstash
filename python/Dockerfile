FROM python:2

ARG SCHEMA_FILE
ENV SCHEMA_FILE=$SCHEMA_FILE
ENV PYTHONUSERBASE=/home/vendor

WORKDIR /home

ADD requirements.txt /home/requirements.txt
RUN pip install -r requirements.txt --user --upgrade
