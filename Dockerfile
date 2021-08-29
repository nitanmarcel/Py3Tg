FROM jamiehewland/alpine-pypy:alpine3.11

RUN adduser -DH -h /sandbox sandbox

RUN find / -perm +6000 -type f -exec chmod a-s {} \; || true

USER sandbox