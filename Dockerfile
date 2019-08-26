FROM python:3.5

COPY requirements.txt /tmp/

RUN apk --no-cache add gcc make libc-dev musl-dev libffi-dev openssl-dev pcre-dev && \
    pip install --no-cache-dir -r /tmp/requirements.txt uwsgi && \
    mkdir /code/ && \
    mkdir /data/

COPY . /code/

ENV KUBEPORTAL_STATIC_ROOT='/code/static-collected'
ENV KUBEPORTAL_STATICFILES_DIRS='/code/kubeportal/static'
RUN /code/manage.py collectstatic --noinput --configuration=Production

EXPOSE 8000

CMD ["/bin/sh", "/code/deployment/docker/docker-entry.sh"]

