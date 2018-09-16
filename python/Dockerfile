FROM python:2

ENV PYTHONUSERBASE=/home/vendor

WORKDIR /home

COPY requirements.txt /home/requirements.txt
RUN pip install -r requirements.txt --user --upgrade
