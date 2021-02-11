FROM python:3-alpine

WORKDIR /eos

RUN apk add --no-cache --virtual .build-deps gcc musl-dev
RUN apk add --no-cache libxslt-dev

COPY requirements.txt /eos
RUN python3 -m pip install -r requirements.txt

RUN apk del .build-deps

COPY . ./
RUN python3 -m pip install /eos/


CMD "eos"
