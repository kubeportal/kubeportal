FROM python:3.8-buster

COPY requirements-prod.txt /tmp/

RUN apt-get update && \
    apt-get install -y postgresql-client gcc make libc-dev musl-dev libffi-dev libssl-dev libpcre3-dev && \
    pip install --no-cache-dir -r /tmp/requirements-prod.txt uwsgi && \
    mkdir /code/ && \
    mkdir /data/

COPY . /code/

ENV KUBEPORTAL_STATIC_ROOT='/code/static-collected'
ENV KUBEPORTAL_STATICFILES_DIRS='/code/kubeportal/static'

EXPOSE 8000

CMD ["/bin/sh", "/code/deployment/docker/docker-entry.sh"]

