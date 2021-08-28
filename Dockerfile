FROM python:3.9.6-alpine

RUN adduser -DH -h /sandbox sandbox

RUN find / -perm +6000 -type f -exec chmod a-s {} \; || true

USER sandbox