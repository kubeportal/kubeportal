FROM python:3.8-buster

COPY requirements-prod.txt /tmp/

# Install psycopg2 only in Docker image
# to support developers with ARM CPU
RUN apt-get update && \
    apt-get install -y vim sqlite3 postgresql-client gcc make libc-dev musl-dev libffi-dev libssl-dev libpcre3-dev && \
    pip install --no-cache-dir -r /tmp/requirements-prod.txt uwsgi && \
    pip install --no-cache-dir psycopg2 && \   
    mkdir /code/ && \
    mkdir /data/

COPY . /code/

RUN /code/manage.py collectstatic --noinput --configuration=Production

ENV KUBEPORTAL_STATIC_ROOT='/code/static-collected'
ENV KUBEPORTAL_STATICFILES_DIRS='/code/kubeportal/static'

EXPOSE 8000

CMD ["/bin/sh", "/code/deployment/docker/docker-entry.sh"]

