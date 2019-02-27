FROM python:3.5-alpine
RUN apk --no-cache add gcc make libc-dev musl-dev libffi-dev openssl-dev pcre-dev
RUN mkdir /code/
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r /code/requirements.txt uwsgi
COPY . /code/

EXPOSE 8000

CMD ["/bin/sh", "/code/deployment/docker/docker-entry.sh"]
