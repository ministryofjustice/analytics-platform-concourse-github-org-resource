FROM python:3.6.5-alpine3.4

RUN apk --no-cache add ca-certificates curl

WORKDIR /usr/src/app

RUN curl -o /usr/local/bin/fly "https://concourse.services.dev.mojanalytics.xyz/api/v1/cli?arch=amd64&platform=linux" && \
    chmod +x /usr/local/bin/fly

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY moj_analytics /usr/local/lib/python3.6/site-packages/moj_analytics
COPY resource /opt/resource
RUN chmod +x /opt/resource/*
