FROM python:3.5-alpine

COPY requirements.txt /tmp/

RUN apk --no-cache add gcc make libc-dev musl-dev libffi-dev openssl-dev pcre-dev && \
    pip install --no-cache-dir -r /tmp/requirements.txt uwsgi && \
    addgroup -g 1000 kubeportal && \ 
    adduser -D -u 1000 -G kubeportal kubeportal && \
    mkdir /code/ && \
    mkdir /data/ && \
    chown 1000:1000 /code && \
    chown 1000:1000 /data

USER kubeportal

COPY . /code/

ENV KUBEPORTAL_STATIC_ROOT='/code/static-collected'
ENV KUBEPORTAL_STATICFILES_DIRS='/code/kubeportal/static'
RUN /code/manage.py collectstatic --noinput --configuration=Production

EXPOSE 8000

CMD ["/bin/sh", "/code/deployment/docker/docker-entry.sh"]

