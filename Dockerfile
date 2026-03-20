FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /email_adapter

RUN apt update

RUN apt install telnet

WORKDIR /email_adapter

ADD . /email_adapter/

RUN pip install -r requirements.txt

CMD uvicorn --host 0.0.0.0 server_api.api.app:app
