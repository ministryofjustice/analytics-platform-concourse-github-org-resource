FROM appropriate/curl

RUN apk --no-cache add jq

COPY resource /opt/resource
RUN chmod +x /opt/resource/*
