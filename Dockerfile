FROM python:3-alpine

RUN apk --no-cache add ca-certificates

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -U pip && pip install --no-cache-dir -r requirements.txt
COPY moj_analytics /tmp/moj_analytics
RUN  pip install /tmp/moj_analytics && rm -rf /tmp/moj_analytics
COPY resource /opt/resource
RUN chmod +x /opt/resource/*
